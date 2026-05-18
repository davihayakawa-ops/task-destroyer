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


def _ui(ja: str, pt: str, en: str) -> str:
    lang = st.session_state.get("lang", "ja")
    if lang == "ja":
        return ja
    if lang == "en":
        return en
    return pt


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
        message = str(exc)[:200]
        if "Email not confirmed" in message:
            return False, _ui(
                "メール確認がまだ完了していません。受信箱の確認リンクを押してからログインしてください。",
                "A confirmação do email ainda não foi concluída. Abra o link recebido antes de entrar.",
                "Email confirmation is not complete yet. Open the confirmation link in your inbox before signing in.",
            )
        return False, _ui("ログインに失敗しました: ", "Falha ao entrar: ", "Sign in failed: ") + message

    user = getattr(result, "user", None)
    session = getattr(result, "session", None)
    if not user:
        return False, _ui(
            "メールアドレスまたはパスワードが違います。",
            "Email ou senha incorretos.",
            "Email or password is incorrect.",
        )

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
        message = str(exc)[:200]
        if "email rate limit exceeded" in message.lower():
            return False, _ui(
                "確認メールの送信回数制限に当たっています。少し待つか、管理画面でユーザーを作成してください。",
                "O limite de envio de emails de confirmação foi atingido. Aguarde um pouco ou crie o usuário no painel.",
                "The confirmation email rate limit was reached. Wait a bit or create the user from the admin dashboard.",
            )
        return False, _ui("登録に失敗しました: ", "Falha ao registrar: ", "Sign up failed: ") + message

    user = getattr(result, "user", None)
    session = getattr(result, "session", None)
    if user:
        auth_user = auth_user_from_supabase_user(user)
        ok, message = bootstrap_user_workspace(auth_user)
        if not ok:
            return False, message
        st.session_state["auth_user"] = auth_user
        if session:
            st.session_state["supabase_access_token"] = str(getattr(session, "access_token", "") or "")
            st.session_state["supabase_refresh_token"] = str(getattr(session, "refresh_token", "") or "")
        return True, ""
    return True, _ui(
        "確認メールを送信しました。メール認証後にログインしてください。",
        "Enviamos um email de confirmação. Entre depois de confirmar o email.",
        "Confirmation email sent. Sign in after confirming your email.",
    )


def send_password_reset(email: str) -> tuple[bool, str]:
    clean_email = email.strip().lower()
    if not clean_email:
        return False, _ui("メールアドレスを入力してください。", "Digite o email.", "Enter your email address.")

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
        message = str(exc)[:200]
        if "email rate limit exceeded" in message.lower():
            return False, _ui(
                "メール送信回数の上限に当たっています。しばらく待つか、Supabase管理画面でパスワードを変更してください。",
                "O limite de envio de email foi atingido. Aguarde um pouco ou altere a senha pelo painel do Supabase.",
                "Email rate limit reached. Wait a bit or change the password from the Supabase dashboard.",
            )
        return False, _ui("再設定メールを送信できませんでした: ", "Não foi possível enviar o email de redefinição: ", "Could not send reset email: ") + message

    return True, _ui(
        "パスワード再設定メールを送信しました。メールの案内に従ってください。",
        "Email de redefinição enviado. Siga as instruções do email.",
        "Password reset email sent. Follow the instructions in the email.",
    )


def update_password_with_recovery(access_token: str, refresh_token: str, new_password: str) -> tuple[bool, str]:
    if len(new_password or "") < 8:
        return False, _ui("新しいパスワードは8文字以上にしてください。", "A nova senha deve ter pelo menos 8 caracteres.", "New password must be at least 8 characters.")
    if not access_token or not refresh_token:
        return False, _ui(
            "再設定リンクの情報が不足しています。もう一度メールを送信してください。",
            "O link de redefinição não tem informações suficientes. Envie o email novamente.",
            "The reset link is missing required information. Send the reset email again.",
        )
    try:
        client = _client()
        client.auth.set_session(access_token, refresh_token)
        client.auth.update_user({"password": new_password})
    except Exception as exc:
        return False, _ui("パスワードを変更できませんでした: ", "Não foi possível alterar a senha: ", "Could not change password: ") + str(exc)[:200]
    return True, _ui(
        "パスワードを変更しました。新しいパスワードでログインしてください。",
        "Senha alterada. Entre com a nova senha.",
        "Password changed. Sign in with the new password.",
    )


def update_current_password(new_password: str) -> tuple[bool, str]:
    if len(new_password or "") < 8:
        return False, _ui("新しいパスワードは8文字以上にしてください。", "A nova senha deve ter pelo menos 8 caracteres.", "New password must be at least 8 characters.")

    access_token = str(st.session_state.get("supabase_access_token") or "")
    refresh_token = str(st.session_state.get("supabase_refresh_token") or "")
    if not access_token or not refresh_token:
        return False, _ui(
            "ログイン情報が古い可能性があります。一度ログアウトして、もう一度ログインしてから変更してください。",
            "A sessão pode estar antiga. Saia e entre novamente antes de alterar a senha.",
            "Your session may be stale. Sign out and sign in again before changing the password.",
        )

    try:
        client = _client()
        client.auth.set_session(access_token, refresh_token)
        result = client.auth.update_user({"password": new_password})
        session = getattr(result, "session", None)
        if session:
            st.session_state["supabase_access_token"] = str(getattr(session, "access_token", "") or "")
            st.session_state["supabase_refresh_token"] = str(getattr(session, "refresh_token", "") or "")
    except Exception as exc:
        return False, _ui("パスワードを変更できませんでした: ", "Não foi possível alterar a senha: ", "Could not change password: ") + str(exc)[:200]

    return True, _ui(
        "パスワードを変更しました。次回から新しいパスワードでログインできます。",
        "Senha alterada. Na próxima vez, entre com a nova senha.",
        "Password changed. Use the new password next time you sign in.",
    )
