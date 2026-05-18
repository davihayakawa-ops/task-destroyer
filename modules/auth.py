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
import streamlit.components.v1 as components

from modules.config import secret_or_env
from modules.supabase_auth import send_password_reset as supabase_password_reset
from modules.supabase_auth import sign_in as supabase_sign_in
from modules.supabase_auth import sign_up as supabase_sign_up
from modules.supabase_auth import supabase_configured
from modules.supabase_auth import update_password_with_recovery


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


def _query_value(key: str) -> str:
    try:
        value = st.query_params.get(key, "")
    except Exception:
        value = ""
    if isinstance(value, list):
        return str(value[0] if value else "")
    return str(value or "")


def _capture_supabase_recovery_hash() -> None:
    components.html(
        """
        <script>
        const parentLocation = window.parent.location;
        const hash = parentLocation.hash || "";
        if (hash.length > 1 && !parentLocation.search.includes("td_auth_hash=1")) {
            const hashParams = new URLSearchParams(hash.slice(1));
            const shouldCapture = hashParams.has("access_token") || hashParams.has("error") || hashParams.get("type") === "recovery";
            if (shouldCapture) {
                const next = new URL(parentLocation.href);
                hashParams.forEach((value, key) => next.searchParams.set(key, value));
                next.searchParams.set("td_auth_hash", "1");
                next.hash = "";
                parentLocation.replace(next.toString());
            }
        }
        </script>
        """,
        height=0,
    )


def _clear_auth_query_params() -> None:
    try:
        for key in (
            "access_token", "refresh_token", "expires_in", "token_type",
            "type", "td_auth_hash", "error", "error_code", "error_description",
        ):
            if key in st.query_params:
                del st.query_params[key]
    except Exception:
        pass


def _render_password_recovery_form() -> bool:
    error = _query_value("error")
    error_description = _query_value("error_description").replace("+", " ")
    access_token = _query_value("access_token")
    refresh_token = _query_value("refresh_token")
    recovery_type = _query_value("type")

    if error:
        st.error(error_description or "再設定リンクが無効、または期限切れです。もう一度パスワード再設定メールを送信してください。")
        if st.button("ログイン画面に戻る", use_container_width=True):
            _clear_auth_query_params()
            st.rerun()
        return True

    if not access_token or recovery_type != "recovery":
        return False

    st.markdown("### パスワードを再設定")
    st.caption("新しいパスワードを入力してください。変更後はログイン画面に戻ります。")
    with st.form("td_supabase_recovery_update_form"):
        new_password = st.text_input("New password", type="password", key="td_recovery_new_password")
        new_password_confirm = st.text_input("New password confirmation", type="password", key="td_recovery_new_password_confirm")
        submitted = st.form_submit_button("パスワードを変更 / Update password", type="primary")
    if submitted:
        if new_password != new_password_confirm:
            st.error("確認用パスワードが一致しません。")
        else:
            ok, message = update_password_with_recovery(access_token, refresh_token, new_password)
            if ok:
                _clear_auth_query_params()
                st.success(message)
            else:
                st.error(message)
    return True


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
    if supabase_configured():
        return ensure_supabase_authentication()

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


def ensure_supabase_authentication() -> bool:
    if st.session_state.get("auth_user"):
        return True

    _capture_supabase_recovery_hash()
    st.markdown(
        """
        <style>
        .td-auth-wrap {
            max-width: 760px;
        }
        .td-auth-note {
            background: #111827;
            border: 1px solid #263244;
            border-radius: 10px;
            color: #cbd5e1;
            font-size: .88rem;
            line-height: 1.7;
            margin: 14px 0 18px;
            padding: 14px 16px;
        }
        .td-auth-note strong {
            color: #f8fafc;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("## Task Destroyer")
    st.caption("ログインしてください / Please sign in")
    st.markdown(
        """
        <div class="td-auth-wrap">
            <div class="td-auth-note">
                <strong>ログインすると、商品・Core・Shopifyコードが自分のアカウントに保存されます。</strong><br>
                初めて使う場合は新規登録してください。メール確認が必要な場合は、受信箱の確認リンクを押してからログインします。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if _render_password_recovery_form():
        return False

    tab_login, tab_signup, tab_reset = st.tabs(["ログイン", "新規登録", "パスワード再設定"])

    with tab_login:
        st.caption("登録済みのメールアドレスとパスワードでログインします。")
        with st.form("td_supabase_login_form"):
            email = st.text_input("Email", key="td_supabase_login_email").strip().lower()
            password = st.text_input("Password", type="password", key="td_supabase_login_password")
            submitted = st.form_submit_button("ログイン / Sign in", type="primary")
        if submitted:
            ok, message = supabase_sign_in(email, password)
            if ok:
                user = current_user()
                st.session_state["shop_id"] = user["workspace"]
                st.session_state["shop_name"] = user["workspace"]
                st.session_state.pop("_market_loaded_for_product", None)
                st.rerun()
            st.error(message or "ログインに失敗しました。")
            if "not confirmed" in str(message).lower():
                st.info("メール確認が未完了です。受信箱の確認リンクを押すか、管理者に確認済みにしてもらってください。")

    with tab_signup:
        st.caption("登録後、確認メールが届いた場合はリンクを押してからログインしてください。")
        with st.form("td_supabase_signup_form"):
            email = st.text_input("Email", key="td_supabase_signup_email").strip().lower()
            password = st.text_input("Password", type="password", key="td_supabase_signup_password")
            password_confirm = st.text_input("Password confirmation", type="password", key="td_supabase_signup_password_confirm")
            submitted = st.form_submit_button("アカウント作成 / Sign up", type="primary")
        if submitted:
            if len(password) < 8:
                st.error("パスワードは8文字以上にしてください。")
            elif password != password_confirm:
                st.error("確認用パスワードが一致しません。")
            else:
                ok, message = supabase_sign_up(email, password)
                if ok and st.session_state.get("auth_user"):
                    user = current_user()
                    st.session_state["shop_id"] = user["workspace"]
                    st.session_state["shop_name"] = user["workspace"]
                    st.session_state.pop("_market_loaded_for_product", None)
                    st.rerun()
                if ok:
                    st.success(message or "アカウントを作成しました。ログインしてください。")
                else:
                    st.error(message or "登録に失敗しました。")

    with tab_reset:
        st.caption("登録済みメールアドレスへ再設定メールを送ります。")
        with st.form("td_supabase_password_reset_form"):
            email = st.text_input("Email", key="td_supabase_reset_email").strip().lower()
            submitted = st.form_submit_button("再設定メールを送信 / Send reset email", type="primary")
        if submitted:
            ok, message = supabase_password_reset(email)
            if ok:
                st.success(message)
            else:
                st.error(message)

    return False


def current_user() -> dict[str, str]:
    user = st.session_state.get("auth_user") or {}
    return {
        "email": str(user.get("email") or "local-dev"),
        "name": str(user.get("name") or "Local Dev"),
        "role": str(user.get("role") or "admin"),
        "workspace": str(user.get("workspace") or "default"),
        "workspace_db_id": str(user.get("workspace_db_id") or ""),
        "workspace_name": str(user.get("workspace_name") or user.get("workspace") or "default"),
        "plan": str(user.get("plan") or ""),
        "workspace_monthly_call_limit": str(user.get("workspace_monthly_call_limit") or ""),
        "provider": str(user.get("provider") or "local"),
        "user_id": str(user.get("user_id") or ""),
    }


def logout():
    for key in (
        "auth_user", "supabase_access_token", "supabase_refresh_token",
        "product_id", "product_info", "core_text", "generated",
    ):
        st.session_state.pop(key, None)
    st.rerun()
