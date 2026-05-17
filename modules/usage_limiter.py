"""Workspace-scoped API usage limits."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.config import secret_or_env


def _secret_or_env(key: str, default: str = "") -> str:
    return secret_or_env(key, default)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class UsageLimiter:
    """Track and limit LLM calls for one workspace."""

    def __init__(self, data_dir: Path, workspace_id: str):
        self.data_dir = Path(data_dir)
        self.workspace_id = str(workspace_id or "default")
        self.usage_dir = self.data_dir / "usage"
        self.usage_dir.mkdir(parents=True, exist_ok=True)

    @property
    def period(self) -> str:
        return datetime.now().strftime("%Y-%m")

    @property
    def monthly_limit(self) -> int:
        raw = _secret_or_env("TASK_DESTROYER_MONTHLY_CALL_LIMIT", "1000")
        try:
            value = int(raw)
        except ValueError:
            value = 1000
        return max(value, 0)

    @property
    def usage_path(self) -> Path:
        return self.usage_dir / f"api_usage_{self.period}.json"

    def _read(self) -> dict[str, Any]:
        if not self.usage_path.exists():
            return {
                "workspace_id": self.workspace_id,
                "period": self.period,
                "used_calls": 0,
                "events": [],
            }
        try:
            data = json.loads(self.usage_path.read_text())
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("workspace_id", self.workspace_id)
        data.setdefault("period", self.period)
        data.setdefault("used_calls", 0)
        data.setdefault("events", [])
        if not isinstance(data["events"], list):
            data["events"] = []
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.usage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def summary(self) -> dict[str, Any]:
        data = self._read()
        used = int(data.get("used_calls") or 0)
        limit = self.monthly_limit
        remaining = max(limit - used, 0) if limit else 0
        percent = 0 if limit == 0 else min(int((used / limit) * 100), 100)
        return {
            "workspace_id": self.workspace_id,
            "period": self.period,
            "used": used,
            "limit": limit,
            "remaining": remaining,
            "percent": percent,
            "is_limited": limit > 0,
            "is_exhausted": limit > 0 and used >= limit,
        }

    def try_consume(self, action: str = "llm_generate") -> tuple[bool, str]:
        limit = self.monthly_limit
        if limit <= 0:
            return True, ""

        data = self._read()
        used = int(data.get("used_calls") or 0)
        if used >= limit:
            return False, f"[API利用上限：{self.period} は {used}/{limit} calls に達しています。管理者に上限追加を依頼してください]"

        data["used_calls"] = used + 1
        events = data.setdefault("events", [])
        events.append({
            "timestamp": _now(),
            "action": action,
            "used_calls": data["used_calls"],
            "limit": limit,
        })
        if len(events) > 500:
            data["events"] = events[-500:]
        self._write(data)
        return True, ""
