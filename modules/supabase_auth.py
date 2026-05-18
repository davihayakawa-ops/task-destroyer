"""Optional Supabase Auth adapter.

The app keeps JSON auth as a local/dev fallback. When SUPABASE_URL and
SUPABASE_ANON_KEY are configured, login is handled by Supabase Auth.
"""

from typing import Any

import streamlit as st

from modules.config import secret_or_env
from modules.supabase_db import bootstrap_user_workspace


def supabase_configured() -> bool:
    return bool(secret_or_env("SUPABASE_URL") and secret_or_env("SUPABASE_ANON_KEY"))


def _client():
    try:
        from supabase import create_client
    except Exception as exc:
        raise RuntimeError("supabase package is not installed. Run pip install -r requirements.txt") from exc
    return create_client(secret_or_env("SUPABASE_URL"), secret_or_env("SUPABASE_ANON_KEY"))


def _meta_get(user: Any, key: str, default: str = "") -> str:
    app_meta = getattr(user, "app_metadata", None) or {}
    user_meta = getattr(user, "user_metadata", None) or {}
    value = app_meta.get(key) or user_meta.get(key) or default
    return str(value or "").strip()


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


def auth_user_from_supabase_user(user: Any) -> dict[str, str]:
    email = str(getattr(user, "email", "") or "").strip().lower()
    user_id = str(getattr(user, "id", "") or "").strip()
    name = _meta_get(user, "name", email or user_id or "User")
    role = _meta_get(user, "role", "member").lower()
    if role not in {"admin", "member"}:
        role = "member"
    workspace = _normalize_workspace(_meta_get(user, "workspace", user_id or email.split("@")[0]))
    return {
        "email": email,
        "name": name,
        "role": role,
        "workspace": workspace,
        "provider": "supabase",
        "user_id": user_id,
    }


def sign_in(email: str, password: str) -> tuple[bool, str]:
    try:
        result = _client().auth.sign_in_with_password({
            "email": email.strip().lower(),
            "password": password,
        })
    except Exception as exc:
        return False, f"ログインに失敗しました: {str(exc)[:200]}"

    user = getattr(result, "user", None)
    session = getattr(result, "session", None)
    if not user:
        return False, "メールアドレスまたはパスワードが違います。"

    auth_user = auth_user_from_supabase_user(user)
    ok, message = bootstrap_user_workspace(auth_user)
    if not ok:
        return False, message
    st.session_state["auth_user"] = auth_user
    if session:
        st.session_state["supabase_access_token"] = str(getattr(session, "access_token", "") or "")
        st.session_state["supabase_refresh_token"] = str(getattr(session, "refresh_token", "") or "")
    return True, ""


def sign_up(email: str, password: str) -> tuple[bool, str]:
    try:
        result = _client().auth.sign_up({
            "email": email.strip().lower(),
            "password": password,
        })
    except Exception as exc:
        return False, f"登録に失敗しました: {str(exc)[:200]}"

    user = getattr(result, "user", None)
    if user:
        auth_user = auth_user_from_supabase_user(user)
        ok, message = bootstrap_user_workspace(auth_user)
        if not ok:
            return False, message
        st.session_state["auth_user"] = auth_user
        return True, ""
    return True, "確認メールを送信しました。メール認証後にログインしてください。"


def send_password_reset(email: str) -> tuple[bool, str]:
    clean_email = email.strip().lower()
    if not clean_email:
        return False, "メールアドレスを入力してください。"

    options = {}
    redirect_to = secret_or_env("APP_BASE_URL")
    if redirect_to:
        options["redirect_to"] = redirect_to

    try:
        auth = _client().auth
        if options:
            auth.reset_password_email(clean_email, options=options)
        else:
            auth.reset_password_email(clean_email)
    except Exception as exc:
        return False, f"再設定メールを送信できませんでした: {str(exc)[:200]}"

    return True, "パスワード再設定メールを送信しました。メールの案内に従ってください。"
