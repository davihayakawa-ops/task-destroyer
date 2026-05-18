"""Account settings page."""

import streamlit as st

from modules.auth import current_user
from modules.supabase_auth import supabase_configured, update_current_password


def _ui(ja: str, pt: str, en: str) -> str:
    lang = st.session_state.get("lang", "ja")
    if lang == "ja":
        return ja
    if lang == "en":
        return en
    return pt


def page_account_settings() -> None:
    user = current_user()
    provider = user.get("provider", "local")

    st.markdown("## 👤 " + _ui("アカウント設定", "Configurações da conta", "Account Settings"))
    st.markdown("---")

    col_email, col_role, col_workspace = st.columns(3)
    with col_email:
        st.metric(_ui("メール", "Email", "Email"), user.get("email") or "-")
    with col_role:
        st.metric(_ui("権限", "Função", "Role"), user.get("role") or "member")
    with col_workspace:
        st.metric(_ui("ワークスペース", "Workspace", "Workspace"), user.get("workspace_name") or user.get("workspace") or "-")

    st.markdown("### " + _ui("パスワード変更", "Alterar senha", "Change Password"))
    st.caption(_ui(
        "ログイン中のアカウントのパスワードを変更します。再設定メールを待たずに変更できます。",
        "Altere a senha da conta logada sem depender do email de redefinição.",
        "Change the password for the signed-in account without waiting for a reset email.",
    ))

    if not supabase_configured() or provider != "supabase":
        st.info(_ui(
            "この環境はローカルログインです。パスワード変更はSupabaseログイン利用時に有効です。",
            "Este ambiente usa login local. A alteração de senha fica disponível com login Supabase.",
            "This environment uses local login. Password changes are available when Supabase login is enabled.",
        ))
        return

    with st.form("td_account_password_form"):
        new_password = st.text_input("New password", type="password", key="td_account_new_password")
        confirm_password = st.text_input("New password confirmation", type="password", key="td_account_confirm_password")
        submitted = st.form_submit_button(
            _ui("パスワードを変更", "Alterar senha", "Update password"),
            type="primary",
        )

    if submitted:
        if new_password != confirm_password:
            st.error(_ui("確認用パスワードが一致しません。", "A confirmação da senha não confere.", "Password confirmation does not match."))
            return
        ok, message = update_current_password(new_password)
        if ok:
            st.success(message)
        else:
            st.error(message)
