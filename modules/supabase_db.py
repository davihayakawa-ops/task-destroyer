"""Supabase database repository for the public-sales architecture.

This module is intentionally separate from the current file-based Storage.
It gives us a safe migration path: add Supabase tables and repository first,
then move one feature at a time from files to DB.
"""

from typing import Any, Optional

from modules.config import secret_or_env


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

        slug = user.get("workspace") or user_id
        existing = (
            self.client.table("workspaces")
            .select("*")
            .eq("slug", slug)
            .limit(1)
            .execute()
        )
        workspace = existing.data[0] if existing.data else None
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

    def upsert_product(self, workspace_id: str, local_id: str, data: dict[str, Any]) -> dict[str, Any]:
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
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

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
    return True, ""
