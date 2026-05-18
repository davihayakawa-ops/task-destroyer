"""User-facing billing and plan page."""

from __future__ import annotations

import html

import requests
import streamlit as st

from modules.auth import current_user
from modules.config import secret_or_env
from modules.billing import PLAN_DEFAULT_LIMITS, plan_limits


PLAN_LABELS = {
    "free": "Free",
    "starter": "Starter",
    "pro": "Pro",
    "team": "Team",
}


def _checkout_endpoint() -> str:
    base = secret_or_env("BILLING_API_BASE_URL")
    if not base:
        return ""
    return base.rstrip("/") + "/stripe/checkout-session"


def _plan_card(plan: str, limit: int, current_plan: str, checkout_ready: bool) -> str:
    active = plan == current_plan
    border = "#3b82f6" if active else "#253044"
    badge = "現在のプラン" if active else "アップグレード可能"
    return (
        f'<div class="cs-card" style="border-color:{border};min-height:128px;">'
        f'<div style="font-size:.74rem;color:#8ab4ff;font-weight:800;margin-bottom:8px;">{html.escape(badge)}</div>'
        f'<div style="font-size:1.25rem;font-weight:900;margin-bottom:8px;">{html.escape(PLAN_LABELS.get(plan, plan.title()))}</div>'
        f'<div style="color:#9aa4b2;font-size:.9rem;">月 {limit:,} calls</div>'
        f'<div style="color:#64748b;font-size:.78rem;margin-top:8px;">{"決済設定OK" if checkout_ready else "決済API未設定"}</div>'
        '</div>'
    )


def _create_checkout(workspace_id: str, plan: str, email: str) -> tuple[bool, str]:
    endpoint = _checkout_endpoint()
    api_key = secret_or_env("BILLING_API_KEY")
    if not endpoint or not api_key:
        return False, "BILLING_API_BASE_URL と BILLING_API_KEY を設定してください。"

    try:
        response = requests.post(
            endpoint,
            headers={"X-Billing-Api-Key": api_key},
            json={
                "workspace_id": workspace_id,
                "plan": plan,
                "customer_email": email,
            },
            timeout=20,
        )
    except Exception as exc:
        return False, f"Checkout作成APIに接続できませんでした: {str(exc)[:200]}"

    if response.status_code >= 400:
        return False, f"Checkout作成に失敗しました: {response.text[:300]}"

    try:
        data = response.json()
    except Exception:
        return False, "Checkout作成APIの応答を読み込めませんでした。"

    url = str(data.get("url") or "")
    if not url:
        return False, "Checkout URLが返りませんでした。"
    return True, url


def page_billing(svc: dict) -> None:
    user = current_user()
    usage = svc["usage_limiter"].summary()
    current_plan = (user.get("plan") or usage.get("plan") or "free").lower()
    if current_plan == "default":
        current_plan = "free"
    limits = plan_limits()
    checkout_ready = bool(_checkout_endpoint() and secret_or_env("BILLING_API_KEY"))

    st.markdown('<div class="breadcrumb">💳 課金 › プラン</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">💳 プラン・課金</div>', unsafe_allow_html=True)
    st.caption("現在のプランと月間生成上限を確認できます。アップグレードすると、決済完了後に自動でプランが反映されます。")

    col1, col2, col3 = st.columns(3)
    col1.metric("現在のプラン", PLAN_LABELS.get(current_plan, current_plan.title()))
    col2.metric("今月の利用", f'{usage["used"]:,} calls')
    col3.metric("月間上限", f'{usage["limit"]:,} calls' if usage["is_limited"] else "無制限")

    ordered = ["free", "starter", "pro", "team"]
    st.markdown(
        '<div class="cs-grid-2">'
        + "".join(_plan_card(plan, limits.get(plan, PLAN_DEFAULT_LIMITS.get(plan, 0)), current_plan, checkout_ready) for plan in ordered)
        + "</div>",
        unsafe_allow_html=True,
    )

    workspace_id = user.get("workspace_db_id") or ""
    if not workspace_id:
        st.warning("Supabaseログイン後のワークスペースIDが必要です。一般販売ではSupabase Authでログインしてください。")
        return

    if not checkout_ready:
        st.info("アップグレードボタンを使うには、BILLING_API_BASE_URL と BILLING_API_KEY を設定してください。")
        return

    st.markdown("### アップグレード")
    cols = st.columns(3)
    for i, plan in enumerate(["starter", "pro", "team"]):
        with cols[i]:
            if plan == current_plan:
                st.button(f"{PLAN_LABELS[plan]} 利用中", disabled=True, use_container_width=True)
                continue
            if st.button(f"{PLAN_LABELS[plan]}へ進む", key=f"checkout_{plan}", type="primary", use_container_width=True):
                ok, result = _create_checkout(workspace_id, plan, user.get("email", ""))
                if ok:
                    st.session_state["checkout_url"] = result
                    st.success("Checkout URLを作成しました。")
                else:
                    st.error(result)

    checkout_url = st.session_state.get("checkout_url")
    if checkout_url:
        st.link_button("Stripe決済ページを開く", checkout_url, type="primary", use_container_width=True)

