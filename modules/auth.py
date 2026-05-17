"""Lightweight authentication helpers for the Streamlit app.

Set TASK_DESTROYER_USERS as JSON in env or Streamlit Secrets:
[
  {"email":"admin@example.com","password_hash":"...","role":"admin","workspace":"admin"},
  {"email":"user@example.com","password":"temporary-pass","role":"member","workspace":"client-a"}
]

If no users are configured, the app runs in local development mode.
"""

import hashlib
import hmac
import json
from typing import Any

import streamlit as st

from modules.config import secret_or_env


def _secret_or_env(key: str, default: str = "") -> str:
    return secret_or_env(key, default)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _normalize_workspace(value: str) -> str:
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
    return "".join(chars).strip("-") or "default"


def load_users() -> list[dict[str, Any]]:
    raw = _secret_or_env("TASK_DESTROYER_USERS")
    if not raw:
        return []
    try:
        users = json.loads(raw)
    except Exception:
        return []
    if not isinstance(users, list):
        return []

    normalized = []
    for user in users:
        if not isinstance(user, dict):
            continue
        email = str(user.get("email") or user.get("username") or "").strip().lower()
        if not email:
            continue
        role = str(user.get("role") or "member").strip().lower()
        if role not in {"admin", "member"}:
            role = "member"
        workspace = _normalize_workspace(user.get("workspace") or email.split("@")[0])
        normalized.append({
            "email": email,
            "name": str(user.get("name") or email),
            "role": role,
            "workspace": workspace,
            "password_hash": str(user.get("password_hash") or "").strip(),
            "password": str(user.get("password") or ""),
        })
    return normalized


def auth_is_configured() -> bool:
    return bool(_secret_or_env("TASK_DESTROYER_USERS"))


def _verify_password(user: dict[str, Any], password: str) -> bool:
    expected_hash = user.get("password_hash", "")
    if expected_hash:
        return hmac.compare_digest(_hash_password(password), expected_hash)
    return bool(user.get("password")) and hmac.compare_digest(password, user.get("password"))


def ensure_authentication() -> bool:
    users = load_users()
    if auth_is_configured() and not users:
        st.error("ログイン設定 TASK_DESTROYER_USERS を読み込めません。JSON形式を確認してください。")
        return False

    if not users:
        st.session_state.setdefault("auth_user", {
            "email": "local-dev",
            "name": "Local Dev",
            "role": "admin",
            "workspace": "default",
        })
        return True

    if st.session_state.get("auth_user"):
        return True

    st.markdown("## Task Destroyer")
    st.caption("ログインしてください / Please sign in")
    with st.form("td_login_form"):
        email = st.text_input("Email").strip().lower()
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("ログイン / Sign in", type="primary")

    if submitted:
        user = next((u for u in users if u["email"] == email), None)
        if user and _verify_password(user, password):
            st.session_state["auth_user"] = {
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "workspace": user["workspace"],
            }
            st.session_state["shop_id"] = user["workspace"]
            st.session_state["shop_name"] = user["workspace"]
            st.session_state.pop("_market_loaded_for_product", None)
            st.rerun()
        st.error("メールアドレスまたはパスワードが違います。")

    return False


def current_user() -> dict[str, str]:
    user = st.session_state.get("auth_user") or {}
    return {
        "email": str(user.get("email") or "local-dev"),
        "name": str(user.get("name") or "Local Dev"),
        "role": str(user.get("role") or "admin"),
        "workspace": str(user.get("workspace") or "default"),
    }


def logout():
    for key in ("auth_user", "product_id", "product_info", "core_text", "generated"):
        st.session_state.pop(key, None)
    st.rerun()
