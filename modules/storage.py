import io
import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional
import uuid

from .audit_logger import AuditLogger
from .generated_content import ITEM_COMPAT_KEYS, combine_generated_items

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = Path(__file__).resolve().parent.parent / DATA_DIR

DEFAULT_SHOP_ID = "default"
DEFAULT_SHOP_NAME = "共通"

# Directories included in backup ZIPs (secrets/env files are never included)
_BACKUP_DIRS = [
    "projects", "core_library", "activity_logs",
    "delete_logs", "bulk_packs", "ab_tests", "reviews",
    "performance_notes", "category_templates", "trash", "audit_logs",
    "consents",
]

# API error patterns used for diagnostics
_ERROR_PATTERNS = [
    "Your credit balance is too low",
    "Anthropic APIエラー",
    "invalid_request_error",
    "Error code: 400",
]


# Fields captured as input_original snapshot on every product save
_TRANSLATABLE_FIELDS = (
    "name", "description", "price", "category", "target",
    "use_scenes", "notes", "competitor_urls", "weaknesses",
    "features", "age", "gender", "prohibited", "brand_tone",
)

# Product fields that the Core engine consumes (non-metadata)
_CORE_FIELDS = (
    "name", "category", "price", "target", "gender", "age",
    "product_url", "features", "weaknesses", "brand_tone",
    "prohibited", "description", "use_scenes", "competitor_urls",
    "notes", "assignee", "final_reviewer",
)

_TRANSLATION_DEFAULTS = {
    "input_original_language": "pt-BR",
    "input_original":          {},
    "input_ja":                {},
    "core_source_data":        {},
    "translation_status":      "not_translated",
    "translated_at":           "",
    "translated_by":           "",
}


def _fill_translation_defaults(data: dict) -> dict:
    for k, v in _TRANSLATION_DEFAULTS.items():
        if k not in data:
            data[k] = v
    return data


def _is_empty_data(data: dict) -> bool:
    """Return True when a project has no meaningful content."""
    return (
        not str(data.get("name") or "").strip()
        and not str(data.get("product_url") or "").strip()
        and not str(data.get("description") or "").strip()
    )


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sanitize_shop_id(value: str) -> str:
    raw = str(value or "").strip().lower()
    chars = []
    last_dash = False
    for ch in raw:
        if ch.isascii() and ch.isalnum():
            chars.append(ch)
            last_dash = False
        elif not last_dash:
            chars.append("-")
            last_dash = True
    cleaned = "".join(chars).strip("-")
    return cleaned or f"shop-{str(uuid.uuid4())[:8]}"


def _safe_file_stem(value: str, fallback: str = "") -> str:
    raw = str(value or "").strip()
    if raw.endswith(".json"):
        raw = raw[:-5]
    chars = []
    for ch in raw:
        if ch.isascii() and (ch.isalnum() or ch in ("-", "_")):
            chars.append(ch)
    cleaned = "".join(chars).strip("._-")
    return cleaned or fallback or str(uuid.uuid4())[:8]


def _shop_data_dir(shop_id: str) -> Path:
    shop_id = _sanitize_shop_id(shop_id)
    if shop_id == DEFAULT_SHOP_ID:
        return DATA_DIR
    return DATA_DIR / "shops" / shop_id


def _registry_path() -> Path:
    return DATA_DIR / "shop_registry.json"


def _read_shop_registry() -> list:
    shops = [{"id": DEFAULT_SHOP_ID, "name": DEFAULT_SHOP_NAME}]
    path = _registry_path()
    if path.exists():
        try:
            loaded = json.loads(path.read_text())
            if isinstance(loaded, list):
                shops = loaded
        except Exception:
            pass

    seen = set()
    normalized = []
    for shop in shops:
        if not isinstance(shop, dict):
            continue
        shop_id = _sanitize_shop_id(shop.get("id") or shop.get("name") or "")
        if not shop_id or shop_id in seen:
            continue
        seen.add(shop_id)
        normalized.append({
            "id": shop_id,
            "name": str(shop.get("name") or shop_id),
            "created_at": shop.get("created_at", ""),
        })
    if DEFAULT_SHOP_ID not in seen:
        normalized.insert(0, {"id": DEFAULT_SHOP_ID, "name": DEFAULT_SHOP_NAME, "created_at": ""})
    normalized.sort(key=lambda s: (s["id"] != DEFAULT_SHOP_ID, s["name"].lower()))
    return normalized


def _write_shop_registry(shops: list) -> None:
    _ensure_dir(DATA_DIR)
    _registry_path().write_text(json.dumps(shops, ensure_ascii=False, indent=2))


def _is_under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _workspace_db_id_from_session() -> str:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx(suppress_warning=True) is None:
            return ""
        import streamlit as st
    except Exception:
        return ""
    try:
        user = st.session_state.get("auth_user") or {}
    except Exception:
        return ""
    return str(user.get("workspace_db_id") or "").strip()


class Storage:
    """JSON file-based storage. Swappable to Supabase by replacing this module."""

    @classmethod
    def list_shops(cls) -> list:
        return _read_shop_registry()

    @classmethod
    def create_shop(cls, name: str) -> dict:
        clean_name = str(name or "").strip()
        if not clean_name:
            clean_name = "New Shop"
        shops = _read_shop_registry()
        existing_ids = {s["id"] for s in shops}
        base_id = _sanitize_shop_id(clean_name)
        shop_id = base_id
        if shop_id == DEFAULT_SHOP_ID:
            shop_id = f"{shop_id}-{str(uuid.uuid4())[:4]}"
        while shop_id in existing_ids:
            shop_id = f"{base_id}-{str(uuid.uuid4())[:4]}"
        shop = {"id": shop_id, "name": clean_name, "created_at": _now()}
        shops.append(shop)
        _write_shop_registry(shops)
        return shop

    @classmethod
    def delete_shop(cls, shop_id: str) -> dict:
        shop_id = _sanitize_shop_id(shop_id or "")
        if shop_id == DEFAULT_SHOP_ID:
            return {"success": False, "message": "共通ショップは削除できません。"}

        shops = _read_shop_registry()
        target = next((s for s in shops if s["id"] == shop_id), None)
        if not target:
            return {"success": False, "message": "ショップが見つかりません。"}

        data_dir = _shop_data_dir(shop_id)
        if data_dir.exists():
            shutil.rmtree(data_dir)
        remaining = [s for s in shops if s["id"] != shop_id]
        _write_shop_registry(remaining)
        return {
            "success": True,
            "message": f"{target['name']} を削除しました。",
            "deleted_shop_id": shop_id,
        }

    @classmethod
    def get_shop_name(cls, shop_id: str) -> str:
        shop_id = _sanitize_shop_id(shop_id or DEFAULT_SHOP_ID)
        for shop in _read_shop_registry():
            if shop["id"] == shop_id:
                return shop["name"]
        return DEFAULT_SHOP_NAME

    def __init__(self, shop_id: str = DEFAULT_SHOP_ID):
        self.shop_id = _sanitize_shop_id(shop_id or DEFAULT_SHOP_ID)
        self.shop_name = self.get_shop_name(self.shop_id)
        self.data_dir = _shop_data_dir(self.shop_id)
        self.audit = AuditLogger(self.data_dir, self.shop_id)
        _ensure_dir(self.data_dir / "projects")
        _ensure_dir(self.data_dir / "core_library")
        _ensure_dir(self.data_dir / "activity_logs")
        _ensure_dir(self.data_dir / "audit_logs")
        _ensure_dir(self.data_dir / "consents")
        _ensure_dir(self.data_dir / "delete_logs")
        _ensure_dir(self.data_dir / "backups")
        _ensure_dir(self.data_dir / "trash")

    # ── Product Info ──────────────────────────────────────────────────────────

    def save_product(self, product_id: str, data: dict) -> str:
        product_id = _safe_file_stem(product_id)
        data["updated_at"] = _now()
        path = self.data_dir / "projects" / f"{product_id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        self.audit.log("storage", "save_product", "ok", product_id=product_id)
        self._mirror_product_to_supabase(product_id, data)
        return product_id

    def _mirror_product_to_supabase(self, product_id: str, data: dict) -> None:
        """Best-effort product mirror for account-isolated public sales."""
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return
        try:
            from modules.supabase_db import SupabaseRepository, supabase_db_configured

            if not supabase_db_configured():
                return
            SupabaseRepository().upsert_product(workspace_db_id, product_id, data)
            self.audit.log("supabase", "mirror_product", "ok", product_id=product_id)
        except Exception as exc:
            self.audit.log(
                "supabase",
                "mirror_product",
                "error",
                product_id=product_id,
                detail={"message": str(exc)[:300]},
            )

    def _supabase_product_row(self, workspace_db_id: str, product_id: str):
        from modules.supabase_db import SupabaseRepository, supabase_db_configured

        if not supabase_db_configured():
            return None, None
        repo = SupabaseRepository()
        row = repo.load_product(workspace_db_id, product_id)
        if not row:
            row = repo.upsert_product(workspace_db_id, product_id, self._load_product_file(product_id) or {})
        return repo, row

    def _load_product_file(self, product_id: str) -> Optional[dict]:
        product_id = _safe_file_stem(product_id)
        path = self.data_dir / "projects" / f"{product_id}.json"
        if not path.exists():
            return None
        return _fill_translation_defaults(json.loads(path.read_text()))

    def _load_product_from_supabase(self, product_id: str) -> Optional[dict]:
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return None
        try:
            from modules.supabase_db import SupabaseRepository, supabase_db_configured

            if not supabase_db_configured():
                return None
            row = SupabaseRepository().load_product(workspace_db_id, product_id)
            data = row.get("data") if row else None
            if not isinstance(data, dict):
                return None
            return _fill_translation_defaults(data)
        except Exception as exc:
            self.audit.log(
                "supabase",
                "load_product",
                "error",
                product_id=product_id,
                detail={"message": str(exc)[:300]},
            )
            return None

    def load_product(self, product_id: str) -> Optional[dict]:
        return self._load_product_from_supabase(product_id) or self._load_product_file(product_id)

    def list_products(self) -> List[dict]:
        db_products = self._list_products_from_supabase()
        if db_products:
            return db_products
        result = []
        proj_dir = self.data_dir / "projects"
        for p in sorted(proj_dir.glob("*.json")):
            # Generated content files always have underscores in their stem
            # (pattern: {pid}_{content_type}_{id}.json).
            # Real product files are plain {pid}.json with no underscore.
            if "_" in p.stem:
                continue
            try:
                data = json.loads(p.read_text())
                if not isinstance(data, dict):
                    continue
                # Skip generated-content wrappers that sneak through
                if "content_type" in data or "content" in data:
                    continue
                entry = {
                    "id": p.stem,
                    "file_path": str(p.resolve()),  # absolute path → reliable deletion
                    **_fill_translation_defaults(data),
                }
                result.append(entry)
            except Exception:
                pass
        return result

    def local_file_product_count(self) -> int:
        return len(self._list_local_product_files())

    @classmethod
    def all_local_file_product_count(cls) -> int:
        return len(cls._collect_local_product_files_all_shops())

    @classmethod
    def _collect_local_product_files_all_shops(cls) -> list[tuple[str, Path]]:
        seen = set()
        found: list[tuple[str, Path]] = []
        shop_ids = [DEFAULT_SHOP_ID]
        for shop in _read_shop_registry():
            shop_id = _sanitize_shop_id(shop.get("id") or "")
            if shop_id and shop_id not in shop_ids:
                shop_ids.append(shop_id)

        shops_root = DATA_DIR / "shops"
        if shops_root.exists():
            for child in sorted(shops_root.iterdir()):
                if child.is_dir():
                    shop_id = _sanitize_shop_id(child.name)
                    if shop_id and shop_id not in shop_ids:
                        shop_ids.append(shop_id)

        for shop_id in shop_ids:
            storage = cls(shop_id)
            for path in storage._list_local_product_files():
                resolved = str(path.resolve())
                if resolved in seen:
                    continue
                seen.add(resolved)
                found.append((shop_id, path))
        return found

    def _list_local_product_files(self) -> list[Path]:
        proj_dir = self.data_dir / "projects"
        files = []
        for p in sorted(proj_dir.glob("*.json")):
            if "_" in p.stem:
                continue
            try:
                data = json.loads(p.read_text())
            except Exception:
                continue
            if isinstance(data, dict) and "content_type" not in data and "content" not in data:
                files.append(p)
        return files

    def migrate_all_local_files_to_supabase(self) -> dict:
        """Copy local JSON saves from every shop folder into the current Supabase workspace."""
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return {"ok": False, "message": "Supabaseログイン後に実行してください。"}
        try:
            from modules.supabase_db import SupabaseRepository, supabase_db_configured

            if not supabase_db_configured():
                return {"ok": False, "message": "Supabase DB設定が未完了です。"}
            repo = SupabaseRepository()
        except Exception as exc:
            return {"ok": False, "message": f"Supabase接続に失敗しました: {str(exc)[:200]}"}

        counts = {"products": 0, "cores": 0, "generated": 0, "shops": 0, "skipped_cores": 0, "skipped_generated": 0}
        touched_shops = set()
        for shop_id, product_file in self._collect_local_product_files_all_shops():
            source_storage = Storage(shop_id)
            product_id = _safe_file_stem(product_file.stem)
            try:
                product_data = json.loads(product_file.read_text())
            except Exception:
                continue
            if not isinstance(product_data, dict):
                continue
            source_tag = _sanitize_shop_id(shop_id or DEFAULT_SHOP_ID)
            target_product_id = product_id if source_tag == self.shop_id else _safe_file_stem(f"{source_tag}-{product_id}")
            if source_tag != self.shop_id:
                product_data = dict(product_data)
                product_data.setdefault("source_shop", source_storage.shop_name)
                product_data.setdefault("source_local_id", product_id)

            product_row = repo.upsert_product(workspace_db_id, target_product_id, _fill_translation_defaults(product_data))
            counts["products"] += 1
            touched_shops.add(source_tag)

            existing_cores = repo.list_cores(workspace_db_id, target_product_id)
            if existing_cores:
                counts["skipped_cores"] += len(existing_cores)
            else:
                for core_file in sorted((source_storage.data_dir / "core_library").glob(f"{product_id}_*.json")):
                    try:
                        core_entry = json.loads(core_file.read_text())
                    except Exception:
                        continue
                    core_data = core_entry.get("core") if isinstance(core_entry, dict) else None
                    if isinstance(core_data, dict):
                        repo.save_core(
                            workspace_db_id,
                            product_row["id"],
                            target_product_id,
                            core_data,
                            str(core_entry.get("version_label") or core_entry.get("created_at") or ""),
                        )
                        counts["cores"] += 1

            existing_generated_types = {
                _safe_file_stem(row.get("content_type") or "", "generated")
                for row in repo.list_generated(workspace_db_id, target_product_id)
            }
            for generated_file in sorted((source_storage.data_dir / "projects").glob(f"{product_id}_*.json")):
                parts = generated_file.stem.split("_")
                if len(parts) < 3:
                    continue
                content_type = _safe_file_stem("_".join(parts[1:-1]), "generated")
                if content_type in existing_generated_types:
                    counts["skipped_generated"] += 1
                    continue
                try:
                    generated_entry = json.loads(generated_file.read_text())
                except Exception:
                    continue
                content = generated_entry.get("content") if isinstance(generated_entry, dict) else None
                if isinstance(content, dict):
                    repo.save_generated(workspace_db_id, product_row["id"], target_product_id, content_type, content)
                    existing_generated_types.add(content_type)
                    counts["generated"] += 1

        counts["shops"] = len(touched_shops)
        return {
            "ok": True,
            "message": (
                f"{counts['shops']}ショップから、{counts['products']}件の商品、"
                f"{counts['cores']}件のCore、{counts['generated']}件の生成物を移行しました。"
            ),
            **counts,
        }

    def migrate_local_files_to_supabase(self) -> dict:
        """Copy current shop's local JSON files into the logged-in Supabase workspace."""
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return {"ok": False, "message": "Supabaseログイン後に実行してください。"}
        try:
            from modules.supabase_db import SupabaseRepository, supabase_db_configured

            if not supabase_db_configured():
                return {"ok": False, "message": "Supabase DB設定が未完了です。"}
            repo = SupabaseRepository()
        except Exception as exc:
            return {"ok": False, "message": f"Supabase接続に失敗しました: {str(exc)[:200]}"}

        counts = {"products": 0, "cores": 0, "generated": 0, "skipped_cores": 0, "skipped_generated": 0}
        for product_file in self._list_local_product_files():
            product_id = _safe_file_stem(product_file.stem)
            try:
                product_data = json.loads(product_file.read_text())
            except Exception:
                continue
            if not isinstance(product_data, dict):
                continue

            product_row = repo.upsert_product(workspace_db_id, product_id, _fill_translation_defaults(product_data))
            counts["products"] += 1

            existing_cores = repo.list_cores(workspace_db_id, product_id)
            if existing_cores:
                counts["skipped_cores"] += len(existing_cores)
            else:
                for core_file in sorted((self.data_dir / "core_library").glob(f"{product_id}_*.json")):
                    try:
                        core_entry = json.loads(core_file.read_text())
                    except Exception:
                        continue
                    core_data = core_entry.get("core") if isinstance(core_entry, dict) else None
                    if isinstance(core_data, dict):
                        repo.save_core(
                            workspace_db_id,
                            product_row["id"],
                            product_id,
                            core_data,
                            str(core_entry.get("version_label") or core_entry.get("created_at") or ""),
                        )
                        counts["cores"] += 1

            existing_generated_types = {
                _safe_file_stem(row.get("content_type") or "", "generated")
                for row in repo.list_generated(workspace_db_id, product_id)
            }
            for generated_file in sorted((self.data_dir / "projects").glob(f"{product_id}_*.json")):
                parts = generated_file.stem.split("_")
                if len(parts) < 3:
                    continue
                content_type = _safe_file_stem("_".join(parts[1:-1]), "generated")
                if content_type in existing_generated_types:
                    counts["skipped_generated"] += 1
                    continue
                try:
                    generated_entry = json.loads(generated_file.read_text())
                except Exception:
                    continue
                content = generated_entry.get("content") if isinstance(generated_entry, dict) else None
                if isinstance(content, dict):
                    repo.save_generated(workspace_db_id, product_row["id"], product_id, content_type, content)
                    existing_generated_types.add(content_type)
                    counts["generated"] += 1

        return {
            "ok": True,
            "message": (
                f"{counts['products']}件の商品、{counts['cores']}件のCore、"
                f"{counts['generated']}件の生成物を移行しました。"
            ),
            **counts,
        }

    def _list_products_from_supabase(self) -> List[dict]:
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return []
        try:
            from modules.supabase_db import SupabaseRepository, supabase_db_configured

            if not supabase_db_configured():
                return []
            rows = SupabaseRepository().list_products(workspace_db_id)
        except Exception as exc:
            self.audit.log(
                "supabase",
                "list_products",
                "error",
                detail={"message": str(exc)[:300]},
            )
            return []

        result = []
        for row in rows:
            local_id = _safe_file_stem(row.get("local_id") or row.get("id") or "")
            data = row.get("data") if isinstance(row.get("data"), dict) else {}
            local_path = self.data_dir / "projects" / f"{local_id}.json"
            result.append({
                "id": local_id,
                "file_path": str(local_path.resolve()) if local_path.exists() else "",
                **_fill_translation_defaults(data),
            })
        return result

    # ── Core Library ──────────────────────────────────────────────────────────

    def save_core(self, product_id: str, core_data: dict, version_label: str = "") -> str:
        product_id = _safe_file_stem(product_id)
        core_id = str(uuid.uuid4())[:8]
        entry = {
            "id": core_id,
            "product_id": product_id,
            "version_label": version_label or _now(),
            "created_at": _now(),
            "status": core_data.get("status", "ai_generated"),
            "core": core_data,
        }
        path = self.data_dir / "core_library" / f"{product_id}_{core_id}.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2))
        self._mirror_core_to_supabase(product_id, core_data, version_label)
        return core_id

    def _mirror_core_to_supabase(self, product_id: str, core_data: dict, version_label: str = "") -> None:
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return
        try:
            repo, product_row = self._supabase_product_row(workspace_db_id, product_id)
            if not repo or not product_row:
                return
            repo.save_core(workspace_db_id, product_row["id"], product_id, core_data, version_label)
            self.audit.log("supabase", "mirror_core", "ok", product_id=product_id)
        except Exception as exc:
            self.audit.log(
                "supabase",
                "mirror_core",
                "error",
                product_id=product_id,
                detail={"message": str(exc)[:300]},
            )

    def list_cores(self, product_id: str) -> List[dict]:
        product_id = _safe_file_stem(product_id)
        db_cores = self._list_cores_from_supabase(product_id)
        if db_cores:
            return db_cores
        result = []
        for p in sorted((self.data_dir / "core_library").glob(f"{product_id}_*.json")):
            try:
                result.append(json.loads(p.read_text()))
            except Exception:
                pass
        return result

    def _list_cores_from_supabase(self, product_id: str) -> List[dict]:
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return []
        try:
            from modules.supabase_db import SupabaseRepository, supabase_db_configured

            if not supabase_db_configured():
                return []
            rows = SupabaseRepository().list_cores(workspace_db_id, product_id)
        except Exception as exc:
            self.audit.log(
                "supabase",
                "list_cores",
                "error",
                product_id=product_id,
                detail={"message": str(exc)[:300]},
            )
            return []

        result = []
        for row in rows:
            core_data = row.get("data") if isinstance(row.get("data"), dict) else {}
            result.append({
                "id": str(row.get("id") or ""),
                "product_id": product_id,
                "version_label": str(row.get("version_label") or row.get("created_at") or ""),
                "created_at": str(row.get("created_at") or ""),
                "status": str(row.get("status") or core_data.get("status") or "ai_generated"),
                "core": core_data,
            })
        return result

    def load_latest_core(self, product_id: str) -> Optional[dict]:
        cores = self.list_cores(product_id)
        if not cores:
            return None
        return cores[-1]

    # ── Generated Content ─────────────────────────────────────────────────────

    def save_generated(self, product_id: str, content_type: str, content: dict) -> str:
        product_id = _safe_file_stem(product_id)
        content_type = _safe_file_stem(content_type, "generated")
        content_id = str(uuid.uuid4())[:8]
        entry = {
            "id": content_id,
            "product_id": product_id,
            "content_type": content_type,
            "created_at": _now(),
            "status": "ai_generated",
            "content": content,
        }
        path = self.data_dir / "projects" / f"{product_id}_{content_type}_{content_id}.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2))
        self._mirror_generated_to_supabase(product_id, content_type, content)
        return content_id

    def _mirror_generated_to_supabase(self, product_id: str, content_type: str, content: dict) -> None:
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return
        try:
            repo, product_row = self._supabase_product_row(workspace_db_id, product_id)
            if not repo or not product_row:
                return
            repo.save_generated(workspace_db_id, product_row["id"], product_id, content_type, content)
            self.audit.log("supabase", "mirror_generated", "ok", product_id=product_id, detail={"content_type": content_type})
        except Exception as exc:
            self.audit.log(
                "supabase",
                "mirror_generated",
                "error",
                product_id=product_id,
                detail={"content_type": content_type, "message": str(exc)[:300]},
            )

    def load_generated(self, product_id: str, content_type: str) -> Optional[dict]:
        product_id = _safe_file_stem(product_id)
        content_type = _safe_file_stem(content_type, "generated")
        db_entry = self._load_generated_from_supabase(product_id, content_type)
        if db_entry:
            return db_entry
        matches = sorted((self.data_dir / "projects").glob(f"{product_id}_{content_type}_*.json"))
        if not matches:
            return None
        try:
            return json.loads(matches[-1].read_text())
        except Exception:
            return None

    def _load_generated_from_supabase(self, product_id: str, content_type: str) -> Optional[dict]:
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return None
        try:
            from modules.supabase_db import SupabaseRepository, supabase_db_configured

            if not supabase_db_configured():
                return None
            row = SupabaseRepository().load_generated(workspace_db_id, product_id, content_type)
        except Exception as exc:
            self.audit.log(
                "supabase",
                "load_generated",
                "error",
                product_id=product_id,
                detail={"content_type": content_type, "message": str(exc)[:300]},
            )
            return None
        if not row:
            return None
        content = row.get("data") if isinstance(row.get("data"), dict) else {}
        return {
            "id": str(row.get("id") or ""),
            "product_id": product_id,
            "content_type": content_type,
            "created_at": str(row.get("created_at") or ""),
            "status": str(content.get("status") or "ai_generated"),
            "content": content,
        }

    def load_all_generated(self, product_id: str) -> dict:
        """Load the latest generated text for every content_type saved for this product.
        Returns {content_type: text_string}."""
        product_id = _safe_file_stem(product_id)
        db_result = self._load_all_generated_from_supabase(product_id)
        if db_result:
            return db_result
        # Collect unique content_types from file names {pid}_{ct}_{id}.json
        content_types = set()
        for p in (self.data_dir / "projects").glob(f"{product_id}_*.json"):
            parts = p.stem.split("_")
            if len(parts) >= 3:
                ct = "_".join(parts[1:-1])  # everything between pid and trailing id
                if ct:
                    content_types.add(ct)

        result = {}
        for ct in content_types:
            entry = self.load_generated(product_id, ct)
            if not entry:
                continue
            content = entry.get("content", {})
            text = ""
            if isinstance(content, dict):
                text = content.get("text", "")
                items = content.get("items")
                if not text and isinstance(items, dict):
                    text = combine_generated_items(items)
            else:
                text = str(content)
            if text:
                result[ct] = text
                compat_key = ITEM_COMPAT_KEYS.get(ct)
                if compat_key:
                    result[compat_key] = text
        return result

    def _load_all_generated_from_supabase(self, product_id: str) -> dict:
        workspace_db_id = _workspace_db_id_from_session()
        if not workspace_db_id:
            return {}
        try:
            from modules.supabase_db import SupabaseRepository, supabase_db_configured

            if not supabase_db_configured():
                return {}
            rows = SupabaseRepository().list_generated(workspace_db_id, product_id)
        except Exception as exc:
            self.audit.log(
                "supabase",
                "list_generated",
                "error",
                product_id=product_id,
                detail={"message": str(exc)[:300]},
            )
            return {}

        latest_by_type = {}
        for row in rows:
            content_type = _safe_file_stem(row.get("content_type") or "", "generated")
            latest_by_type[content_type] = row

        result = {}
        for ct, row in latest_by_type.items():
            content = row.get("data") if isinstance(row.get("data"), dict) else {}
            text = ""
            if isinstance(content, dict):
                text = content.get("text", "")
                items = content.get("items")
                if not text and isinstance(items, dict):
                    text = combine_generated_items(items)
            else:
                text = str(content)
            if text:
                result[ct] = text
                compat_key = ITEM_COMPAT_KEYS.get(ct)
                if compat_key:
                    result[compat_key] = text
        return result

    # ── Product Input Translation ─────────────────────────────────────────────

    def save_product_translation(self, product_id: str, input_ja: dict, translated_by: str) -> bool:
        """Save Japanese translation and build core_source_data for Core generation.

        input_original is never touched. core_source_data is a merged copy of
        all Core-relevant product fields with Japanese translations overlaid.
        """
        data = self.load_product(product_id)
        if not data:
            return False
        data["input_ja"] = input_ja
        # Build core_source_data: Core-relevant fields with translations applied
        core_source = {k: data.get(k, "") for k in _CORE_FIELDS}
        core_source.update({k: v for k, v in input_ja.items() if k in _CORE_FIELDS and v})
        data["core_source_data"] = core_source
        data["translation_status"] = "translated"
        data["translated_at"] = _now()
        data["translated_by"] = translated_by
        self.save_product(product_id, data)
        self.log_activity(product_id, "日本語翻訳", "translated", translated_by)
        return True

    def mark_product_translation_failed(self, product_id: str, failed_by: str,
                                        error: str = "") -> bool:
        data = self.load_product(product_id)
        if not data:
            return False
        data["translation_status"] = "failed"
        data["translated_at"] = _now()
        data["translated_by"] = failed_by
        data["translation_error"] = str(error)[:300]
        self.save_product(product_id, data)
        self.log_activity(product_id, "日本語翻訳失敗", data["translation_error"], failed_by)
        return True

    # ── Activity Log ──────────────────────────────────────────────────────────

    def log_activity(self, product_id: str, action: str, detail: str = "", user: str = ""):
        product_id = _safe_file_stem(product_id)
        entry = {
            "product_id": product_id,
            "action": action,
            "detail": detail,
            "user": user,
            "timestamp": _now(),
        }
        log_path = self.data_dir / "activity_logs" / f"{product_id}.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_activity_log(self, product_id: str) -> List[dict]:
        product_id = _safe_file_stem(product_id)
        log_path = self.data_dir / "activity_logs" / f"{product_id}.jsonl"
        if not log_path.exists():
            return []
        entries = []
        for line in log_path.read_text().splitlines():
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
        return entries

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete_project(self, product_id: str, deleted_by: str = "",
                       reason: str = "", file_path: str = "",
                       use_trash: bool = True) -> dict:
        product_id = _safe_file_stem(product_id)

        deleted = []
        project_file = None
        searched = []
        projects_dir = (self.data_dir / "projects").resolve()

        # 1. Accept the provided absolute path only when it is inside this workspace.
        if file_path:
            fp = Path(file_path).expanduser().resolve()
            searched.append(str(fp))
            if (
                fp.exists()
                and fp.is_file()
                and fp.suffix == ".json"
                and fp.name == f"{product_id}.json"
                and _is_under(fp, projects_dir)
            ):
                project_file = fp

        # 2. Fall back: search all plausible locations
        if project_file is None:
            candidates = [
                self.data_dir / "projects" / f"{product_id}.json",
            ]
            for c in candidates:
                s = str(c.resolve())
                if s not in searched:
                    searched.append(s)
                if c.exists() and _is_under(c, projects_dir):
                    project_file = c.resolve()
                    break

        # ── Trash mode: move main file only, keep associated files intact ──────
        if use_trash and project_file is not None:
            _ensure_dir(self.data_dir / "trash")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            trash_name = f"{product_id}_deleted_{ts}.json"
            trash_path = self.data_dir / "trash" / trash_name
            try:
                data = json.loads(project_file.read_text())
                data["_trash_meta"] = {
                    "product_id": product_id,
                    "original_path": str(project_file.resolve()),
                    "deleted_at": _now(),
                    "deleted_by": deleted_by,
                    "reason": reason,
                }
                trash_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
                project_file.unlink()
            except Exception as e:
                return {
                    "success": False,
                    "message": f"ゴミ箱移動中にエラーが発生しました: {e}",
                    "deleted_paths": [],
                }
            try:
                self.save_delete_log(product_id, deleted_by, reason, [str(project_file)])
            except Exception:
                pass
            self.audit.log("storage", "delete_project", "ok", product_id=product_id, actor=deleted_by,
                           detail={"mode": "trash"})
            return {
                "success": True,
                "message": "ゴミ箱に移動しました",
                "deleted_paths": [str(project_file)],
                "trash_path": str(trash_path),
            }

        if project_file is None:
            # Ghost entry: main file already gone (prev deployment or manual deletion).
            # Clean up any remaining associated files and treat as success.
            try:
                for p in list((self.data_dir / "projects").glob(f"{product_id}_*.json")):
                    if not _is_under(p, projects_dir):
                        continue
                    deleted.append(str(p))
                    p.unlink()
                for p in list((self.data_dir / "core_library").glob(f"{product_id}_*.json")):
                    deleted.append(str(p))
                    p.unlink()
                log_file = self.data_dir / "activity_logs" / f"{product_id}.jsonl"
                if log_file.exists():
                    deleted.append(str(log_file))
                    log_file.unlink()
            except Exception:
                pass
            try:
                self.save_delete_log(product_id, deleted_by, reason, deleted)
            except Exception:
                pass
            self.audit.log("storage", "delete_project", "ok", product_id=product_id, actor=deleted_by,
                           detail={"mode": "cleanup", "deleted_count": len(deleted)})
            return {
                "success": True,
                "message": "削除しました",
                "deleted_paths": deleted,
            }

        try:
            deleted.append(str(project_file))
            project_file.unlink()

            # Delete all generated-content files for this product
            proj_dir = project_file.parent
            for p in list(proj_dir.glob(f"{product_id}_*.json")):
                deleted.append(str(p))
                p.unlink()

            for p in list((self.data_dir / "core_library").glob(f"{product_id}_*.json")):
                deleted.append(str(p))
                p.unlink()

            log_file = self.data_dir / "activity_logs" / f"{product_id}.jsonl"
            if log_file.exists():
                deleted.append(str(log_file))
                log_file.unlink()

        except Exception as e:
            return {
                "success": False,
                "message": f"削除中にエラーが発生しました: {e}",
                "deleted_paths": deleted,
            }

        # Write delete log — must never crash so it never reverts a successful delete
        try:
            self.save_delete_log(product_id, deleted_by, reason, deleted)
        except Exception:
            pass
        self.audit.log("storage", "delete_project", "ok", product_id=product_id, actor=deleted_by,
                       detail={"mode": "delete", "deleted_count": len(deleted)})

        return {
            "success": True,
            "message": "削除しました",
            "deleted_paths": deleted,
        }

    def save_delete_log(self, product_id: str, deleted_by: str, reason: str, files: list):
        product_id = _safe_file_stem(product_id)
        _ensure_dir(self.data_dir / "delete_logs")
        entry = {
            "product_id": product_id,
            "deleted_by": deleted_by,
            "reason": reason,
            "files": files,
            "deleted_at": _now(),
        }
        path = self.data_dir / "delete_logs" / f"{product_id}_{str(uuid.uuid4())[:8]}.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2))

    # ── Backup ────────────────────────────────────────────────────────────────

    def _zip_data_dirs(self, zf: zipfile.ZipFile) -> int:
        """Write all backup-eligible files into an open ZipFile. Returns file count."""
        count = 0
        for dir_name in _BACKUP_DIRS:
            dir_path = self.data_dir / dir_name
            if not dir_path.exists():
                continue
            for file_path in sorted(dir_path.rglob("*")):
                if not file_path.is_file():
                    continue
                name_lower = file_path.name.lower()
                if name_lower in (".env", "secrets.toml") or "secret" in name_lower:
                    continue
                arc_name = str(file_path.relative_to(self.data_dir))
                zf.write(file_path, arc_name)
                count += 1
        return count

    def create_backup(self, label: str = "manual") -> Path:
        """Create a ZIP backup of all data directories. Returns path to the ZIP file.
        Never includes .env, secrets, or files outside self.data_dir."""
        _ensure_dir(self.data_dir / "backups")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if label == "manual":
            zip_name = f"task_destroyer_backup_{ts}.zip"
        else:
            zip_name = f"backup_before_{label}_{ts}.zip"
        zip_path = self.data_dir / "backups" / zip_name
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            file_count = self._zip_data_dirs(zf)
        self.audit.log("storage", "create_backup", "ok",
                       detail={"filename": zip_name, "file_count": file_count})
        return zip_path

    def create_backup_bytes(self) -> tuple:
        """Create a ZIP backup in memory. Returns (bytes, filename, file_count).
        Also saves a copy to data/backups/ for the backup list.
        Never includes .env, secrets, or files outside self.data_dir."""
        _ensure_dir(self.data_dir / "backups")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"task_destroyer_backup_{ts}.zip"

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            file_count = self._zip_data_dirs(zf)
        zip_bytes = buf.getvalue()

        try:
            zip_path = self.data_dir / "backups" / zip_name
            zip_path.write_bytes(zip_bytes)
        except Exception:
            pass
        self.audit.log("storage", "create_backup_bytes", "ok",
                       detail={"filename": zip_name, "file_count": file_count})

        return zip_bytes, zip_name, file_count

    def get_backup_stats(self) -> dict:
        """Return stats about what would be included in a backup, without creating ZIP.
        Used to display pre-backup information and to decide whether backup is possible."""
        try:
            project_count = len(self.list_products())
        except Exception:
            project_count = 0

        dir_counts = {}
        total = 0
        for dir_name in _BACKUP_DIRS:
            dp = self.data_dir / dir_name
            if not dp.exists():
                continue
            count = 0
            for fp in dp.rglob("*"):
                if not fp.is_file():
                    continue
                name_lower = fp.name.lower()
                if name_lower in (".env", "secrets.toml") or "secret" in name_lower:
                    continue
                count += 1
            if count > 0:
                dir_counts[dir_name] = count
            total += count

        return {
            "project_count": project_count,
            "dir_file_counts": dir_counts,
            "total_file_count": total,
        }

    def list_backups(self) -> List[dict]:
        """Return list of available backup ZIPs, newest first."""
        backup_dir = self.data_dir / "backups"
        if not backup_dir.exists():
            return []
        result = []
        for p in sorted(backup_dir.glob("*.zip"), reverse=True):
            try:
                stat = p.stat()
                result.append({
                    "filename": p.name,
                    "path": str(p),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                })
            except Exception:
                pass
        return result

    def restore_from_backup(self, zip_source) -> dict:
        """Restore self.data_dir from a backup ZIP (bytes or file path).
        Auto-creates a pre-restore backup first."""
        try:
            pre_backup = self.create_backup("before_restore")
        except Exception as e:
            return {"success": False, "message": f"事前バックアップに失敗しました: {e}"}

        try:
            if isinstance(zip_source, (str, Path)):
                zp = Path(zip_source).expanduser().resolve()
                if not _is_under(zp, self.data_dir / "backups"):
                    return {"success": False, "message": "ワークスペース外のZIPは復元できません"}
                if not zp.exists():
                    return {"success": False, "message": f"ZIPファイルが見つかりません: {zip_source}"}
                zip_data = zp.read_bytes()
            else:
                zip_data = zip_source  # bytes / BytesIO

            if hasattr(zip_data, "read"):
                zip_data = zip_data.read()

            if not zipfile.is_zipfile(io.BytesIO(zip_data)):
                return {"success": False, "message": "有効なZIPファイルではありません"}

            restored = 0
            with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zf:
                for member in zf.namelist():
                    member_path = Path(member)
                    # Security: reject absolute paths and path traversal.
                    if member_path.is_absolute() or any(part == ".." for part in member_path.parts):
                        continue
                    if not member_path.parts or member.endswith("/"):
                        continue
                    if member_path.parts[0] not in _BACKUP_DIRS:
                        continue
                    # Never restore env/secret files
                    base = Path(member).name.lower()
                    if base in (".env", "secrets.toml") or "secret" in base:
                        continue
                    target = (self.data_dir / member_path).resolve()
                    if not _is_under(target, self.data_dir):
                        continue
                    _ensure_dir(target.parent)
                    with zf.open(member) as src:
                        target.write_bytes(src.read())
                    restored += 1

            self.audit.log("storage", "restore_from_backup", "ok",
                           detail={"restored_count": restored, "pre_backup": str(pre_backup)})
            return {
                "success": True,
                "message": f"{restored} ファイルを復元しました",
                "pre_backup": str(pre_backup),
                "restored_count": restored,
            }
        except Exception as e:
            self.audit.log("storage", "restore_from_backup", "error",
                           detail={"message": str(e)[:300]})
            return {"success": False, "message": f"復元中にエラーが発生しました: {e}"}

    # ── Trash ─────────────────────────────────────────────────────────────────

    def list_trash(self) -> List[dict]:
        """Return list of files in data/trash/, newest first."""
        trash_dir = self.data_dir / "trash"
        if not trash_dir.exists():
            return []
        result = []
        for p in sorted(trash_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(p.read_text())
                meta = data.get("_trash_meta", {})
                stat = p.stat()
                result.append({
                    "filename": p.name,
                    "path": str(p),
                    "product_name": str(data.get("name") or "—"),
                    "product_id": meta.get("product_id", p.stem.split("_deleted_")[0]),
                    "original_path": meta.get("original_path", ""),
                    "deleted_at": meta.get("deleted_at",
                                  datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")),
                    "deleted_by": meta.get("deleted_by", ""),
                    "reason": meta.get("reason", ""),
                })
            except Exception:
                pass
        return result

    def restore_from_trash(self, filename: str) -> dict:
        """Move a file from trash back to its original location."""
        trash_path = (self.data_dir / "trash" / Path(str(filename)).name).resolve()
        if not _is_under(trash_path, self.data_dir / "trash"):
            return {"success": False, "message": "不正なファイル名です"}
        if not trash_path.exists():
            return {"success": False, "message": "ゴミ箱にファイルが見つかりません"}
        try:
            data = json.loads(trash_path.read_text())
            meta = data.get("_trash_meta", {})
            original_path = meta.get("original_path", "")
            if not original_path:
                return {"success": False, "message": "元のパス情報がありません"}

            orig = Path(original_path).expanduser().resolve()
            projects_dir = (self.data_dir / "projects").resolve()
            if not _is_under(orig, projects_dir) or orig.suffix != ".json":
                return {"success": False, "message": "復元先がワークスペース外です"}
            _ensure_dir(orig.parent)
            # Remove trash metadata before restoring
            clean_data = {k: v for k, v in data.items() if k != "_trash_meta"}
            orig.write_text(json.dumps(clean_data, ensure_ascii=False, indent=2))
            trash_path.unlink()
            self.audit.log("storage", "restore_from_trash", "ok",
                           product_id=str(meta.get("product_id") or ""),
                           detail={"filename": trash_path.name})
            return {"success": True, "message": "復元しました", "restored_to": str(orig)}
        except Exception as e:
            self.audit.log("storage", "restore_from_trash", "error",
                           detail={"filename": trash_path.name, "message": str(e)[:300]})
            return {"success": False, "message": f"復元中にエラーが発生しました: {e}"}

    def purge_trash(self, filename: str) -> dict:
        """Permanently delete a single file from trash."""
        trash_path = (self.data_dir / "trash" / Path(str(filename)).name).resolve()
        if not _is_under(trash_path, self.data_dir / "trash"):
            return {"success": False, "message": "不正なファイル名です"}
        if not trash_path.exists():
            return {"success": False, "message": "ファイルが見つかりません"}
        try:
            trash_path.unlink()
            self.audit.log("storage", "purge_trash", "ok", detail={"filename": trash_path.name})
            return {"success": True, "message": "完全削除しました"}
        except Exception as e:
            self.audit.log("storage", "purge_trash", "error",
                           detail={"filename": trash_path.name, "message": str(e)[:300]})
            return {"success": False, "message": f"削除中にエラーが発生しました: {e}"}

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def get_diagnostics(self) -> dict:
        """Return diagnostic information about the data directory."""
        try:
            projects = self.list_products()
        except Exception:
            projects = []

        normal = [p for p in projects if not _is_empty_data(p)]
        empty = [p for p in projects if _is_empty_data(p)]

        # Scan for API error strings in project files
        error_files = []
        try:
            for p in (self.data_dir / "projects").glob("*.json"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    for pattern in _ERROR_PATTERNS:
                        if pattern in text:
                            try:
                                d = json.loads(text)
                                name = d.get("name") or p.stem
                            except Exception:
                                name = p.stem
                            error_files.append({
                                "file": p.name,
                                "name": name,
                                "pattern": pattern,
                            })
                            break
                except Exception:
                    pass
        except Exception:
            pass

        backups = self.list_backups()
        trash = self.list_trash()
        audit_stats = self.audit.stats()

        dir_sizes = {}
        for dir_name in _BACKUP_DIRS + ["backups"]:
            dp = self.data_dir / dir_name
            if dp.exists():
                count = sum(1 for _ in dp.rglob("*") if _.is_file())
                dir_sizes[dir_name] = count

        return {
            "total_projects": len(projects),
            "normal_projects": len(normal),
            "empty_projects": len(empty),
            "trash_count": len(trash),
            "backup_count": len(backups),
            "last_backup_at": backups[0]["created_at"] if backups else None,
            "data_dir": str(self.data_dir),
            "dir_file_counts": dir_sizes,
            "error_content_files": error_files,
            "audit_stats": audit_stats,
        }
