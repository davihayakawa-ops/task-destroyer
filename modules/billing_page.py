"""User-facing billing and plan page."""

from __future__ import annotations

import html

import requests
import streamlit as st

from modules.auth import current_user
from modules.config import secret_or_env
from modules.billing import PLAN_DEFAULT_LIMITS, billing_config_status, plan_limits


PLAN_LABELS = {
    "free": "Free",
    "starter": "Starter",
    "pro": "Pro",
    "team": "Team",
}


def _ui(ja: str, pt: str, en: str) -> str:
    lang = st.session_state.get("lang", "ja")
    if lang == "ja":
        return ja
    if lang == "en":
        return en
    return pt


def _checkout_endpoint() -> str:
    base = secret_or_env("BILLING_API_BASE_URL")
    if not base:
        return ""
    return base.rstrip("/") + "/stripe/checkout-session"


def _plan_card(plan: str, limit: int, current_plan: str, checkout_ready: bool) -> str:
    active = plan == current_plan
    border = "#3b82f6" if active else "#253044"
    badge = _ui("現在のプラン", "Plano atual", "Current plan") if active else _ui("アップグレード可能", "Upgrade disponível", "Upgrade available")
    ready_note = _ui("決済設定OK", "Pagamento configurado", "Checkout ready") if checkout_ready else _ui("決済API未設定", "API de pagamento não configurada", "Billing API not set")
    return (
        f'<div class="cs-card" style="border-color:{border};min-height:128px;">'
        f'<div style="font-size:.74rem;color:#8ab4ff;font-weight:800;margin-bottom:8px;">{html.escape(badge)}</div>'
        f'<div style="font-size:1.25rem;font-weight:900;margin-bottom:8px;">{html.escape(PLAN_LABELS.get(plan, plan.title()))}</div>'
        f'<div style="color:#9aa4b2;font-size:.9rem;">{html.escape(_ui("月", "Mês", "Monthly"))} {limit:,} calls</div>'
        f'<div style="color:#64748b;font-size:.78rem;margin-top:8px;">{html.escape(ready_note)}</div>'
        '</div>'
    )


def _create_checkout(workspace_id: str, plan: str, email: str) -> tuple[bool, str]:
    endpoint = _checkout_endpoint()
    api_key = secret_or_env("BILLING_API_KEY")
    if not endpoint or not api_key:
        return False, _ui(
            "BILLING_API_BASE_URL と BILLING_API_KEY を設定してください。",
            "Configure BILLING_API_BASE_URL e BILLING_API_KEY.",
            "Set BILLING_API_BASE_URL and BILLING_API_KEY.",
        )

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
        return False, _ui("Checkout作成APIに接続できませんでした: ", "Não foi possível conectar à API de checkout: ", "Could not connect to the checkout API: ") + str(exc)[:200]

    if response.status_code >= 400:
        return False, _ui("Checkout作成に失敗しました: ", "Falha ao criar checkout: ", "Checkout creation failed: ") + response.text[:300]

    try:
        data = response.json()
    except Exception:
        return False, _ui(
            "Checkout作成APIの応答を読み込めませんでした。",
            "Não foi possível ler a resposta da API de checkout.",
            "Could not read the checkout API response.",
        )

    url = str(data.get("url") or "")
    if not url:
        return False, _ui("Checkout URLが返りませんでした。", "A URL de checkout não foi retornada.", "Checkout URL was not returned.")
    return True, url


def page_billing(svc: dict) -> None:
    user = current_user()
    usage = svc["usage_limiter"].summary()
    current_plan = (user.get("plan") or usage.get("plan") or "free").lower()
    if current_plan == "default":
        current_plan = "free"
    limits = plan_limits()
    billing_status = billing_config_status()
    checkout_ready = bool(billing_status["checkout_ready"])

    st.markdown(f'<div class="breadcrumb">💳 {_ui("課金", "Faturamento", "Billing")} › {_ui("プラン", "Plano", "Plan")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-header">💳 {_ui("プラン・課金", "Plano e faturamento", "Plan & Billing")}</div>', unsafe_allow_html=True)
    st.caption(_ui(
        "現在のプランと月間生成上限を確認できます。アップグレードすると、決済完了後に自動でプランが反映されます。",
        "Confira o plano atual e o limite mensal de geração. Após o pagamento, o plano é aplicado automaticamente.",
        "Check the current plan and monthly generation limit. Upgrades are applied automatically after checkout.",
    ))

    col1, col2, col3 = st.columns(3)
    col1.metric(_ui("現在のプラン", "Plano atual", "Current plan"), PLAN_LABELS.get(current_plan, current_plan.title()))
    col2.metric(_ui("今月の利用", "Uso do mês", "This month's usage"), f'{usage["used"]:,} calls')
    col3.metric(_ui("月間上限", "Limite mensal", "Monthly limit"), f'{usage["limit"]:,} calls' if usage["is_limited"] else _ui("無制限", "Ilimitado", "Unlimited"))
    source_label = "Supabase DB" if usage.get("source") == "supabase" else _ui("ローカルJSON", "JSON local", "Local JSON")
    st.caption(f'{_ui("利用回数の保存先", "Origem do uso", "Usage source")}: {source_label}')

    if usage["is_limited"]:
        if usage["is_exhausted"]:
            st.error(_ui(
                "今月の生成上限に達しています。追加で生成するには上位プランへ変更してください。",
                "O limite mensal foi atingido. Faça upgrade para gerar mais.",
                "Monthly generation limit reached. Upgrade to generate more.",
            ))
        elif usage["percent"] >= 80:
            st.warning(_ui(
                f'残り {usage["remaining"]:,} calls です。多めに生成する予定がある場合は、先に上位プランを検討してください。',
                f'Restam {usage["remaining"]:,} calls. Considere um plano maior antes de gerar muito conteúdo.',
                f'{usage["remaining"]:,} calls remaining. Consider upgrading before generating heavily.',
            ))
        else:
            st.info(_ui(
                f'今月はあと {usage["remaining"]:,} calls 生成できます。',
                f'Você ainda pode gerar {usage["remaining"]:,} calls este mês.',
                f'You can generate {usage["remaining"]:,} more calls this month.',
            ))

    ordered = ["free", "starter", "pro", "team"]
    st.markdown(
        '<div class="cs-grid-2">'
        + "".join(_plan_card(plan, limits.get(plan, PLAN_DEFAULT_LIMITS.get(plan, 0)), current_plan, checkout_ready) for plan in ordered)
        + "</div>",
        unsafe_allow_html=True,
    )

    if not billing_status["ready"]:
        with st.expander(_ui("Stripe設定チェック", "Verificação do Stripe", "Stripe Setup Check"), expanded=False):
            if billing_status["missing"]:
                st.warning(_ui("未設定: ", "Não configurado: ", "Missing: ") + ", ".join(billing_status["missing"]))
            if billing_status["missing_prices"]:
                st.warning(_ui("Price ID未設定プラン: ", "Planos sem Price ID: ", "Plans missing Price ID: ") + ", ".join(billing_status["missing_prices"]))
            if billing_status["invalid_json"]:
                st.error(_ui("JSON形式を確認: ", "Verifique o formato JSON: ", "Check JSON format: ") + ", ".join(billing_status["invalid_json"]))
            if billing_status["invalid_plans"]:
                st.error(_ui("未対応プラン名: ", "Planos não suportados: ", "Unsupported plan names: ") + ", ".join(billing_status["invalid_plans"]))
            st.caption(_ui(
                "料金はStripe側のPriceで後から決められます。アプリ側にはPrice IDとプラン名の対応だけ設定します。",
                "Os preços podem ser definidos depois no Stripe. No app, configure apenas a relação entre Price ID e plano.",
                "Prices can be decided later in Stripe. The app only needs the mapping between Price ID and plan name.",
            ))

    workspace_id = user.get("workspace_db_id") or ""
    if not workspace_id:
        st.warning(_ui(
            "Supabaseログイン後のワークスペースIDが必要です。一般販売ではSupabase Authでログインしてください。",
            "É necessário um workspace ID após login Supabase. Para venda pública, use Supabase Auth.",
            "A workspace ID after Supabase login is required. Use Supabase Auth for public sales.",
        ))
        return

    if not checkout_ready:
        st.info(_ui(
            "アップグレードボタンを使うには、Stripe/Billing API設定と各有料プランのPrice IDを設定してください。",
            "Para usar upgrade, configure a API de cobrança/Stripe e os Price IDs dos planos pagos.",
            "To use upgrade buttons, configure the Stripe/Billing API and Price IDs for paid plans.",
        ))
        return

    st.markdown("### " + _ui("アップグレード", "Upgrade", "Upgrade"))
    cols = st.columns(3)
    for i, plan in enumerate(["starter", "pro", "team"]):
        with cols[i]:
            if plan == current_plan:
                st.button(f"{PLAN_LABELS[plan]} " + _ui("利用中", "em uso", "current"), disabled=True, use_container_width=True)
                continue
            if st.button(_ui(f"{PLAN_LABELS[plan]}へ進む", f"Ir para {PLAN_LABELS[plan]}", f"Go to {PLAN_LABELS[plan]}"), key=f"checkout_{plan}", type="primary", use_container_width=True):
                ok, result = _create_checkout(workspace_id, plan, user.get("email", ""))
                if ok:
                    st.session_state["checkout_url"] = result
                    st.success(_ui("Checkout URLを作成しました。", "URL de checkout criada.", "Checkout URL created."))
                else:
                    st.error(result)

    checkout_url = st.session_state.get("checkout_url")
    if checkout_url:
        st.link_button(_ui("Stripe決済ページを開く", "Abrir página de pagamento Stripe", "Open Stripe checkout page"), checkout_url, type="primary", use_container_width=True)
