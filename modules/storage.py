import io
import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional
import uuid

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = Path(__file__).resolve().parent.parent / DATA_DIR

# Directories included in backup ZIPs (secrets/env files are never included)
_BACKUP_DIRS = [
    "projects", "core_library", "approvals", "activity_logs",
    "delete_logs", "bulk_packs", "ab_tests", "reviews",
    "performance_notes", "category_templates", "trash",
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
    "features", "product_prep_review_note",
)

_TRANSLATION_DEFAULTS = {
    "input_original_language": "pt-BR",
    "input_original":          {},
    "input_ja":                {},
    "translation_status":      "not_translated",
    "translated_at":           "",
    "translated_by":           "",
}


def _fill_translation_defaults(data: dict) -> dict:
    for k, v in _TRANSLATION_DEFAULTS.items():
        if k not in data:
            data[k] = v
    return data


_PREP_DEFAULTS = {
    "product_prep_status":       "draft",
    "product_prep_approved":     False,
    "product_prep_approved_by":  "",
    "product_prep_approved_at":  "",
    "product_prep_review_note":  "",
    "product_prep_submitted_by": "",
    "product_prep_submitted_at": "",
}


def _fill_prep_defaults(data: dict) -> dict:
    """Backfill missing approval fields so old saved data never causes KeyError."""
    for k, v in _PREP_DEFAULTS.items():
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


class Storage:
    """JSON file-based storage. Swappable to Supabase by replacing this module."""

    def __init__(self):
        _ensure_dir(DATA_DIR / "projects")
        _ensure_dir(DATA_DIR / "core_library")
        _ensure_dir(DATA_DIR / "approvals")
        _ensure_dir(DATA_DIR / "activity_logs")
        _ensure_dir(DATA_DIR / "delete_logs")
        _ensure_dir(DATA_DIR / "backups")
        _ensure_dir(DATA_DIR / "trash")

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
        return _fill_translation_defaults(_fill_prep_defaults(json.loads(path.read_text())))

    def list_products(self) -> List[dict]:
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
                    **_fill_translation_defaults(_fill_prep_defaults(data)),
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

    def list_cores(self, product_id: str) -> List[dict]:
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

    # ── Product Prep Approval ─────────────────────────────────────────────────

    def submit_product_prep(self, product_id: str, submitted_by: str) -> bool:
        data = self.load_product(product_id)
        if not data:
            return False
        data["product_prep_status"] = "waiting_review"
        data["product_prep_submitted_by"] = submitted_by
        data["product_prep_submitted_at"] = _now()
        self.save_product(product_id, data)
        self.log_activity(product_id, "商品準備提出", "waiting_review", submitted_by)
        return True

    def approve_product_prep(self, product_id: str, approved_by: str, note: str = "") -> bool:
        data = self.load_product(product_id)
        if not data:
            return False
        data["product_prep_status"] = "approved"
        data["product_prep_approved"] = True
        data["product_prep_approved_by"] = approved_by
        data["product_prep_approved_at"] = _now()
        data["product_prep_review_note"] = note
        self.save_product(product_id, data)
        self.log_activity(product_id, "商品準備承認", "approved", approved_by)
        return True

    def reject_product_prep(self, product_id: str, rejected_by: str, note: str) -> bool:
        data = self.load_product(product_id)
        if not data:
            return False
        data["product_prep_status"] = "rejected"
        data["product_prep_approved"] = False
        data["product_prep_approved_by"] = ""
        data["product_prep_approved_at"] = _now()
        data["product_prep_review_note"] = note
        self.save_product(product_id, data)
        self.log_activity(product_id, "商品準備差し戻し", "rejected", rejected_by)
        return True

    # ── Product Input Translation ─────────────────────────────────────────────

    def save_product_translation(self, product_id: str, input_ja: dict, translated_by: str) -> bool:
        """Save Japanese translation of product fields. Never touches original product fields."""
        data = self.load_product(product_id)
        if not data:
            return False
        data["input_ja"] = input_ja
        data["translation_status"] = "translated"
        data["translated_at"] = _now()
        data["translated_by"] = translated_by
        self.save_product(product_id, data)
        self.log_activity(product_id, "日本語翻訳", "translated", translated_by)
        return True

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

    def get_activity_log(self, product_id: str) -> List[dict]:
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
                       reason: str = "", file_path: str = "",
                       use_trash: bool = True) -> dict:
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

        # ── Trash mode: move main file only, keep associated files intact ──────
        if use_trash and project_file is not None:
            _ensure_dir(DATA_DIR / "trash")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            trash_name = f"{product_id}_deleted_{ts}.json"
            trash_path = DATA_DIR / "trash" / trash_name
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

    # ── Backup ────────────────────────────────────────────────────────────────

    def _zip_data_dirs(self, zf: zipfile.ZipFile) -> int:
        """Write all backup-eligible files into an open ZipFile. Returns file count."""
        count = 0
        for dir_name in _BACKUP_DIRS:
            dir_path = DATA_DIR / dir_name
            if not dir_path.exists():
                continue
            for file_path in sorted(dir_path.rglob("*")):
                if not file_path.is_file():
                    continue
                name_lower = file_path.name.lower()
                if name_lower in (".env", "secrets.toml") or "secret" in name_lower:
                    continue
                arc_name = str(file_path.relative_to(DATA_DIR))
                zf.write(file_path, arc_name)
                count += 1
        return count

    def create_backup(self, label: str = "manual") -> Path:
        """Create a ZIP backup of all data directories. Returns path to the ZIP file.
        Never includes .env, secrets, or files outside DATA_DIR."""
        _ensure_dir(DATA_DIR / "backups")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if label == "manual":
            zip_name = f"task_destroyer_backup_{ts}.zip"
        else:
            zip_name = f"backup_before_{label}_{ts}.zip"
        zip_path = DATA_DIR / "backups" / zip_name
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            self._zip_data_dirs(zf)
        return zip_path

    def create_backup_bytes(self) -> tuple:
        """Create a ZIP backup in memory. Returns (bytes, filename, file_count).
        Also saves a copy to data/backups/ for the backup list.
        Never includes .env, secrets, or files outside DATA_DIR."""
        _ensure_dir(DATA_DIR / "backups")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"task_destroyer_backup_{ts}.zip"

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            file_count = self._zip_data_dirs(zf)
        zip_bytes = buf.getvalue()

        try:
            zip_path = DATA_DIR / "backups" / zip_name
            zip_path.write_bytes(zip_bytes)
        except Exception:
            pass

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
            dp = DATA_DIR / dir_name
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
        backup_dir = DATA_DIR / "backups"
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
        """Restore DATA_DIR from a backup ZIP (bytes or file path).
        Auto-creates a pre-restore backup first."""
        try:
            pre_backup = self.create_backup("before_restore")
        except Exception as e:
            return {"success": False, "message": f"事前バックアップに失敗しました: {e}"}

        try:
            if isinstance(zip_source, (str, Path)):
                zp = Path(zip_source)
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
                    # Security: reject path traversal
                    if member.startswith("/") or ".." in member:
                        continue
                    # Never restore env/secret files
                    base = Path(member).name.lower()
                    if base in (".env", "secrets.toml") or "secret" in base:
                        continue
                    target = DATA_DIR / member
                    _ensure_dir(target.parent)
                    with zf.open(member) as src:
                        target.write_bytes(src.read())
                    restored += 1

            return {
                "success": True,
                "message": f"{restored} ファイルを復元しました",
                "pre_backup": str(pre_backup),
                "restored_count": restored,
            }
        except Exception as e:
            return {"success": False, "message": f"復元中にエラーが発生しました: {e}"}

    # ── Trash ─────────────────────────────────────────────────────────────────

    def list_trash(self) -> List[dict]:
        """Return list of files in data/trash/, newest first."""
        trash_dir = DATA_DIR / "trash"
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
        trash_path = DATA_DIR / "trash" / filename
        if not trash_path.exists():
            return {"success": False, "message": "ゴミ箱にファイルが見つかりません"}
        try:
            data = json.loads(trash_path.read_text())
            meta = data.get("_trash_meta", {})
            original_path = meta.get("original_path", "")
            if not original_path:
                return {"success": False, "message": "元のパス情報がありません"}

            orig = Path(original_path)
            _ensure_dir(orig.parent)
            # Remove trash metadata before restoring
            clean_data = {k: v for k, v in data.items() if k != "_trash_meta"}
            orig.write_text(json.dumps(clean_data, ensure_ascii=False, indent=2))
            trash_path.unlink()
            return {"success": True, "message": "復元しました", "restored_to": str(orig)}
        except Exception as e:
            return {"success": False, "message": f"復元中にエラーが発生しました: {e}"}

    def purge_trash(self, filename: str) -> dict:
        """Permanently delete a single file from trash."""
        trash_path = DATA_DIR / "trash" / filename
        if not trash_path.exists():
            return {"success": False, "message": "ファイルが見つかりません"}
        try:
            trash_path.unlink()
            return {"success": True, "message": "完全削除しました"}
        except Exception as e:
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
            for p in (DATA_DIR / "projects").glob("*.json"):
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

        dir_sizes = {}
        for dir_name in _BACKUP_DIRS + ["backups"]:
            dp = DATA_DIR / dir_name
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
            "data_dir": str(DATA_DIR),
            "dir_file_counts": dir_sizes,
            "error_content_files": error_files,
        }
