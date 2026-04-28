import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import uuid

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))


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
        for p in sorted((DATA_DIR / "projects").glob("*.json")):
            try:
                data = json.loads(p.read_text())
                result.append({"id": p.stem, **data})
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
