"""Supabase database repository for the public-sales architecture.

This module is intentionally separate from the current file-based Storage.
It gives us a safe migration path: add Supabase tables and repository first,
then move one feature at a time from files to DB.
"""

from typing import Any, Optional

from modules.config import secret_or_env


def _normalize_workspace_slug(value: str, fallback: str = "workspace") -> str:
    raw = str(value or fallback or "workspace").strip().lower()
    chars = []
    last_dash = False
    for ch in raw:
        if ch.isascii() and ch.isalnum():
            chars.append(ch)
            last_dash = False
        elif not last_dash:
            chars.append("-")
            last_dash = True
    return "".join(chars).strip("-") or "workspace"


def _private_slug(base_slug: str, user_id: str) -> str:
    suffix = _normalize_workspace_slug(user_id, "user")[:12] or "user"
    return _normalize_workspace_slug(f"{base_slug}-{suffix}", suffix)


def supabase_db_configured() -> bool:
    return bool(
        secret_or_env("SUPABASE_URL")
        and secret_or_env("SUPABASE_SERVICE_ROLE_KEY")
    )


def supabase_db_mode() -> str:
    if not secret_or_env("SUPABASE_URL"):
        return "disabled"
    if not secret_or_env("SUPABASE_SERVICE_ROLE_KEY"):
        return "auth_only"
    return "service"


def supabase_db_client():
    try:
        from supabase import create_client
    except Exception as exc:
        raise RuntimeError("supabase package is not installed. Run pip install -r requirements.txt") from exc
    return create_client(
        secret_or_env("SUPABASE_URL"),
        secret_or_env("SUPABASE_SERVICE_ROLE_KEY"),
    )


class SupabaseRepository:
    """Thin repository for workspace-scoped records."""

    def __init__(self, client=None):
        self.client = client or supabase_db_client()

    def ensure_profile_and_workspace(self, user: dict[str, str]) -> dict[str, Any]:
        user_id = user.get("user_id") or ""
        if not user_id:
            raise ValueError("Supabase user_id is required")

        profile = {
            "id": user_id,
            "email": user.get("email", ""),
            "display_name": user.get("name", ""),
            "role": user.get("role", "member"),
        }
        self.client.table("profiles").upsert(profile, on_conflict="id").execute()

        slug = _normalize_workspace_slug(user.get("workspace") or user_id, user_id)
        existing = (
            self.client.table("workspaces")
            .select("*")
            .eq("slug", slug)
            .limit(1)
            .execute()
        )
        workspace = existing.data[0] if existing.data else None
        if workspace and str(workspace.get("owner_id") or "") != user_id:
            slug = _private_slug(slug, user_id)
            existing = (
                self.client.table("workspaces")
                .select("*")
                .eq("slug", slug)
                .limit(1)
                .execute()
            )
            workspace = existing.data[0] if existing.data else None
            if workspace and str(workspace.get("owner_id") or "") != user_id:
                raise PermissionError("Workspace slug is already owned by another user")

        if not workspace:
            created = (
                self.client.table("workspaces")
                .insert({
                    "owner_id": user_id,
                    "slug": slug,
                    "name": user.get("name") or slug,
                })
                .execute()
            )
            workspace = created.data[0]

        self.client.table("workspace_members").upsert({
            "workspace_id": workspace["id"],
            "user_id": user_id,
            "role": "owner",
        }, on_conflict="workspace_id,user_id").execute()
        return workspace

    def list_products(self, workspace_id: str) -> list[dict[str, Any]]:
        result = (
            self.client.table("products")
            .select("*")
            .eq("workspace_id", workspace_id)
            .neq("status", "deleted")
            .order("updated_at", desc=True)
            .execute()
        )
        return result.data or []

    def upsert_product(
        self,
        workspace_id: str,
        local_id: str,
        data: dict[str, Any],
        revive_deleted: bool = False,
    ) -> dict[str, Any]:
        existing = self.find_product(workspace_id, local_id)
        if existing and existing.get("status") == "deleted" and not revive_deleted:
            return existing

        row = {
            "workspace_id": workspace_id,
            "local_id": local_id,
            "name": data.get("name", ""),
            "data": data,
            "status": "active",
        }
        result = self.client.table("products").upsert(
            row,
            on_conflict="workspace_id,local_id",
        ).execute()
        return result.data[0]

    def load_product(self, workspace_id: str, local_id: str) -> Optional[dict[str, Any]]:
        result = (
            self.client.table("products")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("local_id", local_id)
            .neq("status", "deleted")
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def find_product(self, workspace_id: str, local_id: str) -> Optional[dict[str, Any]]:
        result = (
            self.client.table("products")
            .select("id,status")
            .eq("workspace_id", workspace_id)
            .eq("local_id", local_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def soft_delete_product(self, workspace_id: str, local_id: str) -> bool:
        before = self.find_product(workspace_id, local_id)
        if not before:
            return True
        (
            self.client.table("products")
            .update({"status": "deleted"})
            .eq("workspace_id", workspace_id)
            .eq("local_id", local_id)
            .execute()
        )
        after = self.find_product(workspace_id, local_id)
        return bool(after and after.get("status") == "deleted")

    def delete_product(self, workspace_id: str, local_id: str) -> bool:
        return self.soft_delete_product(workspace_id, local_id)

    def load_workspace(self, workspace_id: str) -> Optional[dict[str, Any]]:
        result = (
            self.client.table("workspaces")
            .select("*")
            .eq("id", workspace_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def load_workspace_by_stripe(self, customer_id: str = "", subscription_id: str = "") -> Optional[dict[str, Any]]:
        query = self.client.table("workspaces").select("*")
        if subscription_id:
            result = query.eq("stripe_subscription_id", subscription_id).limit(1).execute()
            if result.data:
                return result.data[0]
        if customer_id:
            result = query.eq("stripe_customer_id", customer_id).limit(1).execute()
            if result.data:
                return result.data[0]
        return None

    def update_workspace_billing(self, workspace_id: str, billing: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "plan", "monthly_call_limit", "stripe_customer_id",
            "stripe_subscription_id", "subscription_status",
        }
        row = {k: v for k, v in billing.items() if k in allowed and v is not None}
        result = (
            self.client.table("workspaces")
            .update(row)
            .eq("id", workspace_id)
            .execute()
        )
        return result.data[0]

    def load_api_usage(self, workspace_id: str, period: str) -> Optional[dict[str, Any]]:
        result = (
            self.client.table("api_usage")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("period", period)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def upsert_api_usage(self, workspace_id: str, period: str, used_calls: int) -> dict[str, Any]:
        result = self.client.table("api_usage").upsert(
            {
                "workspace_id": workspace_id,
                "period": period,
                "used_calls": max(int(used_calls or 0), 0),
            },
            on_conflict="workspace_id,period",
        ).execute()
        return result.data[0]

    def save_core(self, workspace_id: str, product_row_id: str, local_product_id: str,
                  core_data: dict[str, Any], version_label: str = "") -> dict[str, Any]:
        result = self.client.table("cores").insert({
            "workspace_id": workspace_id,
            "product_id": product_row_id,
            "local_product_id": local_product_id,
            "version_label": version_label,
            "status": core_data.get("status", "ai_generated"),
            "data": core_data,
        }).execute()
        return result.data[0]

    def list_cores(self, workspace_id: str, local_product_id: str) -> list[dict[str, Any]]:
        result = (
            self.client.table("cores")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("local_product_id", local_product_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []

    def save_generated(self, workspace_id: str, product_row_id: str, local_product_id: str,
                       content_type: str, content: dict[str, Any]) -> dict[str, Any]:
        result = self.client.table("generated_contents").insert({
            "workspace_id": workspace_id,
            "product_id": product_row_id,
            "local_product_id": local_product_id,
            "content_type": content_type,
            "data": content,
        }).execute()
        return result.data[0]

    def load_generated(self, workspace_id: str, local_product_id: str, content_type: str) -> Optional[dict[str, Any]]:
        result = (
            self.client.table("generated_contents")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("local_product_id", local_product_id)
            .eq("content_type", content_type)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def list_generated(self, workspace_id: str, local_product_id: str) -> list[dict[str, Any]]:
        result = (
            self.client.table("generated_contents")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("local_product_id", local_product_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []

    def log_audit(self, workspace_id: str, event: dict[str, Any]) -> None:
        row = {
            "workspace_id": workspace_id,
            "actor_id": event.get("actor_id"),
            "actor_email": event.get("actor_email") or event.get("actor"),
            "event_type": event.get("event_type", "event"),
            "action": event.get("action", ""),
            "status": event.get("status", "ok"),
            "local_product_id": event.get("product_id", ""),
            "detail": event.get("detail", {}),
        }
        self.client.table("audit_logs").insert(row).execute()


def bootstrap_user_workspace(user: dict[str, str]) -> tuple[bool, str]:
    if not supabase_db_configured():
        return True, ""
    try:
        workspace = SupabaseRepository().ensure_profile_and_workspace(user)
    except Exception as exc:
        return False, f"Supabase DB初期化に失敗しました: {str(exc)[:200]}"

    user["workspace_db_id"] = str(workspace.get("id", ""))
    user["workspace"] = str(workspace.get("slug") or user.get("workspace") or "default")
    user["workspace_name"] = str(workspace.get("name") or user.get("name") or user["workspace"])
    user["plan"] = str(workspace.get("plan") or user.get("plan") or "free")
    user["workspace_monthly_call_limit"] = str(workspace.get("monthly_call_limit") or "")
    return True, ""
