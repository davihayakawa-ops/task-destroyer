"""Production readiness checklist for public sales."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from modules.config import app_env, secret_or_env, validate_runtime_config
from modules.supabase_db import supabase_db_mode
from modules.billing import billing_config_status


def _mask(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return "未設定"
    if len(value) <= 10:
        return "設定済み"
    return f"{value[:6]}...{value[-4:]}"


def _status_card(label: str, status: str, note: str) -> str:
    tone = "ok" if status == "OK" else ("warn" if status == "確認" else "bad")
    color = {"ok": "#22c55e", "warn": "#f59e0b", "bad": "#ef4444"}[tone]
    return (
        '<div class="cs-card" style="min-height:118px;">'
        f'<div style="font-size:0.78rem;color:{color};font-weight:800;margin-bottom:8px;">{html.escape(status)}</div>'
        f'<div style="font-size:1.02rem;font-weight:800;margin-bottom:8px;">{html.escape(label)}</div>'
        f'<div style="font-size:0.86rem;color:#9aa4b2;line-height:1.65;">{html.escape(note)}</div>'
        '</div>'
    )


def _readiness_items(users: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    env = app_env()
    anthropic = secret_or_env("ANTHROPIC_API_KEY")
    supabase_url = secret_or_env("SUPABASE_URL")
    supabase_anon = secret_or_env("SUPABASE_ANON_KEY")
    supabase_service = secret_or_env("SUPABASE_SERVICE_ROLE_KEY")
    app_base_url = secret_or_env("APP_BASE_URL")
    monthly_limit = secret_or_env("TASK_DESTROYER_MONTHLY_CALL_LIMIT", "1000")
    plan_limits = secret_or_env("TASK_DESTROYER_PLAN_LIMITS")
    billing_status = billing_config_status()
    terms_version = secret_or_env("TASK_DESTROYER_TERMS_VERSION", "2026-05-18")

    items: list[tuple[str, str, str]] = []
    items.append((
        "本番モード",
        "OK" if env in {"prod", "production"} else "確認",
        f"現在: {env}。販売時は APP_ENV=production 推奨。",
    ))
    items.append((
        "AI APIキー",
        "OK" if anthropic.startswith("sk-ant-") else "NG",
        f"ANTHROPIC_API_KEY: {_mask(anthropic)}",
    ))
    items.append((
        "Supabase Auth",
        "OK" if supabase_url and supabase_anon else "NG",
        "ログイン・新規登録に必要。URLとAnon Keyをセットで設定。",
    ))
    items.append((
        "Supabase DB保存",
        "OK" if supabase_url and supabase_service else "NG",
        f"現在: {supabase_db_mode()}。一般販売では商品/Core/生成物の個人別保存に必須。",
    ))
    items.append((
        "パスワード再設定URL",
        "OK" if app_base_url else "確認",
        "APP_BASE_URLを公開URLに設定し、SupabaseのRedirect URLにも追加。",
    ))
    items.append((
        "利用上限",
        "OK" if monthly_limit.isdigit() and int(monthly_limit) > 0 else "確認",
        f"月間LLM上限: {monthly_limit}。販売時はプランごとに調整。",
    ))
    items.append((
        "プラン別上限",
        "OK" if plan_limits else "確認",
        "TASK_DESTROYER_PLAN_LIMITSで free/starter/pro/team などを上書き可能。",
    ))
    items.append((
        "Stripe課金",
        "OK" if billing_status["ready"] else "確認",
        "未設定: " + ", ".join(billing_status["missing"] + [f"{p}:price" for p in billing_status["missing_prices"]])
        if not billing_status["ready"] else "Stripe/Billing API/Price ID設定済み。",
    ))
    items.append((
        "規約同意",
        "OK" if terms_version else "確認",
        f"同意バージョン: {terms_version}。規約更新時は日付を更新。",
    ))
    items.append((
        "ローカルJSONユーザー",
        "確認" if users else "OK",
        "一般販売ではSupabase Auth推奨。JSONユーザーは開発・社内検証向け。",
    ))
    return items


def page_production_check(users: list[dict[str, Any]]) -> None:
    st.markdown('<div class="breadcrumb">🛡️ 販売準備 › 本番チェック</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🛡️ 本番準備チェック</div>', unsafe_allow_html=True)
    st.caption("一般販売前に必要な設定だけを確認します。ここがOKに近いほど、個人ログイン販売へ進めやすくなります。")

    result = validate_runtime_config(users)
    if result["errors"]:
        st.error("販売前に修正が必要です。")
        for item in result["errors"]:
            st.markdown(f"- {item}")
    elif result["warnings"]:
        st.warning("販売前に確認したい項目があります。")
        for item in result["warnings"]:
            st.markdown(f"- {item}")
    else:
        st.success("基本設定は販売向けに整っています。")

    items = _readiness_items(users)
    st.markdown(
        '<div class="cs-grid-2">'
        + "".join(_status_card(label, status, note) for label, status, note in items)
        + "</div>",
        unsafe_allow_html=True,
    )

    with st.expander("Supabaseで最後に確認すること", expanded=False):
        st.markdown(
            "- `supabase_schema.sql` をSQL Editorで実行済み\n"
            "- `products` / `cores` / `generated_contents` にRLSが有効\n"
            "- 別ユーザーでログインした時に、他ユーザーの商品が表示されない\n"
            "- AuthのSite URLとRedirect URLに公開URLを追加済み\n"
            "- Email confirmation / Password recovery のメールが届く\n"
            "- `SUPABASE_SERVICE_ROLE_KEY` はサーバー側Secretsのみで管理\n"
            "- テストユーザーで商品保存、Core生成、再ログイン後の復元を確認"
        )

    with st.expander("販売前のユーザー分離テスト", expanded=False):
        st.markdown(
            "1. Supabase AuthでテストユーザーAとBを作成する\n"
            "2. Aでログインし、商品名に`A_ONLY_TEST`を含む商品を保存する\n"
            "3. AでCore生成とShopifyコード生成を1回ずつ実行し、ログアウトする\n"
            "4. Bでログインし、保存済み商品に`A_ONLY_TEST`が表示されないことを確認する\n"
            "5. Bで商品名に`B_ONLY_TEST`を含む商品を保存し、ログアウトする\n"
            "6. Aで再ログインし、`A_ONLY_TEST`だけが見えて`B_ONLY_TEST`が見えないことを確認する\n"
            "7. Supabase SQL Editorで`products`、`cores`、`generated_contents`の`workspace_id`がユーザーごとに分かれていることを確認する\n\n"
            "このテストが通れば、個人ごとの商品・Core・生成物の分離は販売前チェックとして一段安心です。"
        )

    with st.expander("Stripe課金の設定チェック", expanded=False):
        billing_status = billing_config_status()
        if billing_status["ready"]:
            st.success("Stripe課金の基本設定はそろっています。")
        else:
            if billing_status["missing"]:
                st.warning("未設定: " + ", ".join(billing_status["missing"]))
            if billing_status["missing_prices"]:
                st.warning("Price ID未設定プラン: " + ", ".join(billing_status["missing_prices"]))
            if billing_status["invalid_json"]:
                st.error("JSON形式を確認: " + ", ".join(billing_status["invalid_json"]))
            if billing_status["invalid_plans"]:
                st.error("未対応プラン名: " + ", ".join(billing_status["invalid_plans"]))
        st.markdown(
            "- 料金はStripeのPrice側で後から変更できます\n"
            "- アプリ側は`STRIPE_PLAN_PRICE_MAP`に`{\"pro\":\"price_xxx\"}`のように対応を入れます\n"
            "- Checkout完了後、Webhookで`workspaces.plan`と`monthly_call_limit`が更新されます"
        )
