import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import uuid

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = Path(__file__).resolve().parent.parent / DATA_DIR


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Storage:
    """JSON file-based storage. Swappable to Supabase by replacing this module."""

    def __init__(self):
        _ensure_dir(DATA_DIR / "projects")
        _ensure_dir(DATA_DIR / "core_library")
        _ensure_dir(DATA_DIR / "approvals")
        _ensure_dir(DATA_DIR / "activity_logs")
        _ensure_dir(DATA_DIR / "delete_logs")

    # ── Product Info ──────────────────────────────────────────────────────────

    def save_product(self, product_id: str, data: dict) -> str:
        data["updated_at"] = _now()
        path = DATA_DIR / "projects" / f"{product_id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return product_id

    def load_product(self, product_id: str) -> Optional[dict]:
        path = DATA_DIR / "projects" / f"{product_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def list_products(self) -> list[dict]:
        result = []
        proj_dir = DATA_DIR / "projects"
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
                    **data,
                }
                result.append(entry)
            except Exception:
                pass
        return result

    # ── Core Library ──────────────────────────────────────────────────────────

    def save_core(self, product_id: str, core_data: dict, version_label: str = "") -> str:
        core_id = str(uuid.uuid4())[:8]
        entry = {
            "id": core_id,
            "product_id": product_id,
            "version_label": version_label or _now(),
            "created_at": _now(),
            "status": core_data.get("status", "ai_generated"),
            "core": core_data,
        }
        path = DATA_DIR / "core_library" / f"{product_id}_{core_id}.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2))
        return core_id

    def list_cores(self, product_id: str) -> list[dict]:
        result = []
        for p in sorted((DATA_DIR / "core_library").glob(f"{product_id}_*.json")):
            try:
                result.append(json.loads(p.read_text()))
            except Exception:
                pass
        return result

    def load_latest_core(self, product_id: str) -> Optional[dict]:
        cores = self.list_cores(product_id)
        if not cores:
            return None
        return cores[-1]

    # ── Generated Content ─────────────────────────────────────────────────────

    def save_generated(self, product_id: str, content_type: str, content: dict) -> str:
        content_id = str(uuid.uuid4())[:8]
        entry = {
            "id": content_id,
            "product_id": product_id,
            "content_type": content_type,
            "created_at": _now(),
            "status": "ai_generated",
            "content": content,
        }
        path = DATA_DIR / "projects" / f"{product_id}_{content_type}_{content_id}.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2))
        return content_id

    def load_generated(self, product_id: str, content_type: str) -> Optional[dict]:
        matches = sorted((DATA_DIR / "projects").glob(f"{product_id}_{content_type}_*.json"))
        if not matches:
            return None
        try:
            return json.loads(matches[-1].read_text())
        except Exception:
            return None

    def load_all_generated(self, product_id: str) -> dict:
        """Load the latest generated text for every content_type saved for this product.
        Returns {content_type: text_string}."""
        # Collect unique content_types from file names {pid}_{ct}_{id}.json
        content_types = set()
        for p in (DATA_DIR / "projects").glob(f"{product_id}_*.json"):
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
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            if text:
                result[ct] = text
        return result

    # ── Approval ──────────────────────────────────────────────────────────────

    def update_approval(self, product_id: str, content_type: str, status: str, comment: str = "") -> bool:
        entry = {
            "product_id": product_id,
            "content_type": content_type,
            "status": status,
            "comment": comment,
            "updated_at": _now(),
        }
        path = DATA_DIR / "approvals" / f"{product_id}_{content_type}.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2))
        return True

    def get_approval(self, product_id: str, content_type: str) -> Optional[dict]:
        path = DATA_DIR / "approvals" / f"{product_id}_{content_type}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    # ── Activity Log ──────────────────────────────────────────────────────────

    def log_activity(self, product_id: str, action: str, detail: str = "", user: str = ""):
        entry = {
            "product_id": product_id,
            "action": action,
            "detail": detail,
            "user": user,
            "timestamp": _now(),
        }
        log_path = DATA_DIR / "activity_logs" / f"{product_id}.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_activity_log(self, product_id: str) -> list[dict]:
        log_path = DATA_DIR / "activity_logs" / f"{product_id}.jsonl"
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

    def has_approved_content(self, product_id: str) -> bool:
        for p in (DATA_DIR / "approvals").glob(f"{product_id}_*.json"):
            try:
                data = json.loads(p.read_text())
                if data.get("status") in ("approved", "ready", "published"):
                    return True
            except Exception:
                pass
        return False

    def delete_project(self, product_id: str, deleted_by: str = "",
                       reason: str = "", file_path: str = "") -> dict:
        # Normalise: strip whitespace and any accidental .json suffix
        product_id = str(product_id).strip()
        if product_id.endswith(".json"):
            product_id = product_id[:-5]

        deleted = []
        project_file = None
        searched = []

        # 1. Trust the absolute path from list_products() if provided
        if file_path:
            fp = Path(file_path)
            searched.append(str(fp))
            if fp.exists():
                project_file = fp

        # 2. Fall back: search all plausible locations
        if project_file is None:
            candidates = [
                DATA_DIR / "projects" / f"{product_id}.json",
                Path("data") / "projects" / f"{product_id}.json",
                Path("data/projects") / f"{product_id}.json",
            ]
            for c in candidates:
                s = str(c.resolve())
                if s not in searched:
                    searched.append(s)
                if c.exists():
                    project_file = c
                    break

        if project_file is None:
            # Ghost entry: main file already gone (prev deployment or manual deletion).
            # Clean up any remaining associated files and treat as success.
            try:
                for p in list((DATA_DIR / "projects").glob(f"{product_id}_*.json")):
                    deleted.append(str(p))
                    p.unlink()
                for p in list((DATA_DIR / "core_library").glob(f"{product_id}_*.json")):
                    deleted.append(str(p))
                    p.unlink()
                for p in list((DATA_DIR / "approvals").glob(f"{product_id}_*.json")):
                    deleted.append(str(p))
                    p.unlink()
                log_file = DATA_DIR / "activity_logs" / f"{product_id}.jsonl"
                if log_file.exists():
                    deleted.append(str(log_file))
                    log_file.unlink()
            except Exception:
                pass
            try:
                self.save_delete_log(product_id, deleted_by, reason, deleted)
            except Exception:
                pass
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

            for p in list((DATA_DIR / "core_library").glob(f"{product_id}_*.json")):
                deleted.append(str(p))
                p.unlink()

            for p in list((DATA_DIR / "approvals").glob(f"{product_id}_*.json")):
                deleted.append(str(p))
                p.unlink()

            log_file = DATA_DIR / "activity_logs" / f"{product_id}.jsonl"
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

        return {
            "success": True,
            "message": "削除しました",
            "deleted_paths": deleted,
        }

    def save_delete_log(self, product_id: str, deleted_by: str, reason: str, files: list):
        _ensure_dir(DATA_DIR / "delete_logs")
        entry = {
            "product_id": product_id,
            "deleted_by": deleted_by,
            "reason": reason,
            "files": files,
            "deleted_at": _now(),
        }
        path = DATA_DIR / "delete_logs" / f"{product_id}_{str(uuid.uuid4())[:8]}.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2))
