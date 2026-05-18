"""Account settings page."""

import streamlit as st

from modules.auth import current_user
from modules.supabase_auth import supabase_configured, update_current_password


def page_account_settings() -> None:
    user = current_user()
    provider = user.get("provider", "local")

    st.markdown("## 👤 アカウント設定")
    st.markdown("---")

    col_email, col_role, col_workspace = st.columns(3)
    with col_email:
        st.metric("メール", user.get("email") or "-")
    with col_role:
        st.metric("権限", user.get("role") or "member")
    with col_workspace:
        st.metric("ワークスペース", user.get("workspace_name") or user.get("workspace") or "-")

    st.markdown("### パスワード変更")
    st.caption("ログイン中のアカウントのパスワードを変更します。再設定メールを待たずに変更できます。")

    if not supabase_configured() or provider != "supabase":
        st.info("この環境はローカルログインです。パスワード変更はSupabaseログイン利用時に有効です。")
        return

    with st.form("td_account_password_form"):
        new_password = st.text_input("New password", type="password", key="td_account_new_password")
        confirm_password = st.text_input("New password confirmation", type="password", key="td_account_confirm_password")
        submitted = st.form_submit_button("パスワードを変更 / Update password", type="primary")

    if submitted:
        if new_password != confirm_password:
            st.error("確認用パスワードが一致しません。")
            return
        ok, message = update_current_password(new_password)
        if ok:
            st.success(message)
        else:
            st.error(message)
