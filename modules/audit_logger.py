"""Append-only audit logs for production support."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class AuditLogger:
    """Write small operational events without storing prompts or generated text."""

    def __init__(self, data_dir: Path, workspace_id: str):
        self.data_dir = Path(data_dir)
        self.workspace_id = str(workspace_id or "default")
        self.audit_dir = self.data_dir / "audit_logs"
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    @property
    def log_path(self) -> Path:
        period = datetime.now().strftime("%Y-%m")
        return self.audit_dir / f"audit_{period}.jsonl"

    def _actor(self) -> str:
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx

            if get_script_run_ctx(suppress_warning=True) is None:
                return "unknown"
            from modules.auth import current_user
            user = current_user()
            return user.get("email") or user.get("name") or "unknown"
        except Exception:
            return "unknown"

    def log(self, event_type: str, action: str, status: str = "ok",
            product_id: str = "", detail: Optional[dict[str, Any]] = None,
            actor: str = "") -> None:
        entry = {
            "timestamp": _now(),
            "workspace_id": self.workspace_id,
            "actor": actor or self._actor(),
            "event_type": str(event_type or "event"),
            "action": str(action or ""),
            "status": str(status or "ok"),
            "product_id": str(product_id or ""),
            "detail": detail or {},
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def recent(self, limit: int = 30) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        try:
            for path in sorted(self.audit_dir.glob("audit_*.jsonl"), reverse=True):
                for line in reversed(path.read_text().splitlines()):
                    try:
                        events.append(json.loads(line))
                    except Exception:
                        continue
                    if len(events) >= limit:
                        return events
        except Exception:
            return events
        return events

    def stats(self) -> dict[str, Any]:
        events = self.recent(500)
        errors = [e for e in events if e.get("status") in {"error", "blocked"}]
        llm_calls = [e for e in events if e.get("event_type") == "llm"]
        return {
            "recent_count": len(events),
            "recent_errors": len(errors),
            "recent_llm_calls": len(llm_calls),
            "recent_events": events[:20],
        }
