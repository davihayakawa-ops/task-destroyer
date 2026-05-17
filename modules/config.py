"""Runtime configuration helpers."""

import os
import re
from typing import Any

import streamlit as st


def secret_or_env(key: str, default: str = "") -> str:
    try:
        value = st.secrets.get(key, "")
    except Exception:
        value = ""
    return str(value or os.getenv(key, default) or "").strip()


def app_env() -> str:
    return secret_or_env("APP_ENV", "development").lower() or "development"


def is_production() -> bool:
    return app_env() in {"prod", "production"}


def _looks_like_anthropic_key(value: str) -> bool:
    return bool(value and value != "your_api_key_here" and value.startswith("sk-ant-"))


def validate_runtime_config(users: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Return blocking errors and non-blocking warnings for the current config."""
    errors: list[str] = []
    warnings: list[str] = []

    anthropic_key = secret_or_env("ANTHROPIC_API_KEY")
    monthly_limit_raw = secret_or_env("TASK_DESTROYER_MONTHLY_CALL_LIMIT", "1000")
    users_raw = secret_or_env("TASK_DESTROYER_USERS")

    try:
        monthly_limit = int(monthly_limit_raw)
    except ValueError:
        monthly_limit = -1

    if not _looks_like_anthropic_key(anthropic_key):
        target = errors if is_production() else warnings
        target.append("ANTHROPIC_API_KEY が未設定、またはプレースホルダーのままです。")

    if monthly_limit < 0:
        errors.append("TASK_DESTROYER_MONTHLY_CALL_LIMIT は 0 以上の整数で設定してください。")
    elif is_production() and monthly_limit == 0:
        errors.append("本番環境では TASK_DESTROYER_MONTHLY_CALL_LIMIT を 1 以上にしてください。")

    if is_production() and not users_raw:
        errors.append("本番環境では TASK_DESTROYER_USERS を必ず設定してください。")

    if users_raw and not users:
        errors.append("TASK_DESTROYER_USERS を読み込めません。JSON形式を確認してください。")

    weak_users = []
    for user in users:
        email = user.get("email", "unknown")
        password = str(user.get("password") or "")
        password_hash = str(user.get("password_hash") or "")
        if is_production() and password:
            weak_users.append(email)
        if password_hash and not re.fullmatch(r"[0-9a-fA-F]{64}", password_hash):
            errors.append(f"{email} の password_hash は SHA-256 hex 64文字で設定してください。")
    if weak_users:
        errors.append("本番環境では plain password ではなく password_hash を使ってください: " + ", ".join(weak_users))

    return {"errors": errors, "warnings": warnings}


def render_config_guard(users: list[dict[str, Any]]) -> bool:
    """Render config issues. Return True when the app can continue."""
    result = validate_runtime_config(users)
    if result["errors"]:
        st.error("本番設定に問題があります。")
        for item in result["errors"]:
            st.markdown(f"- {item}")
        return False
    if result["warnings"] and not st.session_state.get("_config_warning_dismissed"):
        with st.expander("設定の確認", expanded=False):
            for item in result["warnings"]:
                st.warning(item)
            if st.button("この警告を閉じる", key="dismiss_config_warning"):
                st.session_state["_config_warning_dismissed"] = True
                st.rerun()
    return True
