"""Production readiness checklist for public sales."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from modules.config import app_env, secret_or_env, validate_runtime_config
from modules.supabase_db import supabase_db_mode
from modules.billing import billing_config_status


def _ui(ja: str, pt: str, en: str) -> str:
    lang = st.session_state.get("lang", "ja")
    if lang == "ja":
        return ja
    if lang == "en":
        return en
    return pt


def _mask(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return _ui("未設定", "Não configurado", "Not set")
    if len(value) <= 10:
        return _ui("設定済み", "Configurado", "Set")
    return f"{value[:6]}...{value[-4:]}"


def _status_card(label: str, status: str, note: str) -> str:
    tone = "ok" if status == "OK" else ("warn" if status == "確認" else "bad")
    color = {"ok": "#22c55e", "warn": "#f59e0b", "bad": "#ef4444"}[tone]
    status_label = {"OK": "OK", "確認": _ui("確認", "Verificar", "Check"), "NG": _ui("NG", "Pendente", "Missing")}.get(status, status)
    return (
        '<div class="cs-card" style="min-height:118px;">'
        f'<div style="font-size:0.78rem;color:{color};font-weight:800;margin-bottom:8px;">{html.escape(status_label)}</div>'
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
        _ui("本番モード", "Modo de produção", "Production mode"),
        "OK" if env in {"prod", "production"} else "確認",
        _ui(f"現在: {env}。販売時は APP_ENV=production 推奨。", f"Atual: {env}. Para venda, use APP_ENV=production.", f"Current: {env}. Use APP_ENV=production for sales."),
    ))
    items.append((
        _ui("AI APIキー", "Chave da API de IA", "AI API key"),
        "OK" if anthropic.startswith("sk-ant-") else "NG",
        f"ANTHROPIC_API_KEY: {_mask(anthropic)}",
    ))
    items.append((
        "Supabase Auth",
        "OK" if supabase_url and supabase_anon else "NG",
        _ui("ログイン・新規登録に必要。URLとAnon Keyをセットで設定。", "Necessário para login e cadastro. Configure URL e Anon Key juntos.", "Required for sign in and sign up. Set URL and Anon Key together."),
    ))
    items.append((
        _ui("Supabase DB保存", "Salvamento no Supabase DB", "Supabase DB storage"),
        "OK" if supabase_url and supabase_service else "NG",
        _ui(f"現在: {supabase_db_mode()}。一般販売では商品/Core/生成物の個人別保存に必須。", f"Atual: {supabase_db_mode()}. Essencial para salvar produtos/Core/conteúdos por usuário.", f"Current: {supabase_db_mode()}. Required to save products/Cores/generated content per user."),
    ))
    items.append((
        _ui("パスワード再設定URL", "URL de redefinição de senha", "Password reset URL"),
        "OK" if app_base_url else "確認",
        _ui("APP_BASE_URLを公開URLに設定し、SupabaseのRedirect URLにも追加。", "Defina APP_BASE_URL como URL pública e adicione também aos Redirect URLs do Supabase.", "Set APP_BASE_URL to the public URL and add it to Supabase Redirect URLs."),
    ))
    items.append((
        _ui("利用上限", "Limite de uso", "Usage limit"),
        "OK" if monthly_limit.isdigit() and int(monthly_limit) > 0 else "確認",
        _ui(f"月間LLM上限: {monthly_limit}。販売時はプランごとに調整。", f"Limite mensal de LLM: {monthly_limit}. Ajuste por plano na venda.", f"Monthly LLM limit: {monthly_limit}. Adjust per plan for sales."),
    ))
    items.append((
        _ui("プラン別上限", "Limites por plano", "Plan limits"),
        "OK" if plan_limits else "確認",
        _ui("TASK_DESTROYER_PLAN_LIMITSで free/starter/pro/team などを上書き可能。", "Use TASK_DESTROYER_PLAN_LIMITS para sobrescrever free/starter/pro/team.", "Use TASK_DESTROYER_PLAN_LIMITS to override free/starter/pro/team."),
    ))
    items.append((
        _ui("Stripe課金", "Cobrança Stripe", "Stripe billing"),
        "OK" if billing_status["ready"] else "確認",
        (_ui("未設定: ", "Não configurado: ", "Missing: ") + ", ".join(billing_status["missing"] + [f"{p}:price" for p in billing_status["missing_prices"]]))
        if not billing_status["ready"] else _ui("Stripe/Billing API/Price ID設定済み。", "Stripe/Billing API/Price ID configurados.", "Stripe/Billing API/Price IDs are set."),
    ))
    items.append((
        _ui("規約同意", "Aceite dos termos", "Terms consent"),
        "OK" if terms_version else "確認",
        _ui(f"同意バージョン: {terms_version}。規約更新時は日付を更新。", f"Versão dos termos: {terms_version}. Atualize a data quando os termos mudarem.", f"Terms version: {terms_version}. Update the date when terms change."),
    ))
    items.append((
        _ui("ローカルJSONユーザー", "Usuários JSON locais", "Local JSON users"),
        "確認" if users else "OK",
        _ui("一般販売ではSupabase Auth推奨。JSONユーザーは開発・社内検証向け。", "Para venda pública, use Supabase Auth. Usuários JSON são para desenvolvimento/testes internos.", "Use Supabase Auth for public sales. JSON users are for development/internal testing."),
    ))
    return items


def page_production_check(users: list[dict[str, Any]]) -> None:
    st.markdown(f'<div class="breadcrumb">🛡️ {_ui("販売準備", "Preparação de venda", "Launch Prep")} › {_ui("本番チェック", "Checklist", "Production Check")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-header">🛡️ {_ui("本番準備チェック", "Checklist de produção", "Launch Checklist")}</div>', unsafe_allow_html=True)
    st.caption(_ui(
        "一般販売前に必要な設定だけを確認します。ここがOKに近いほど、個人ログイン販売へ進めやすくなります。",
        "Confira apenas as configurações necessárias antes da venda pública.",
        "Check only the settings needed before public sales.",
    ))

    result = validate_runtime_config(users)
    if result["errors"]:
        st.error(_ui("販売前に修正が必要です。", "Correções necessárias antes da venda.", "Fix these before selling."))
        for item in result["errors"]:
            st.markdown(f"- {item}")
    elif result["warnings"]:
        st.warning(_ui("販売前に確認したい項目があります。", "Há itens para verificar antes da venda.", "Some items need checking before launch."))
        for item in result["warnings"]:
            st.markdown(f"- {item}")
    else:
        st.success(_ui("基本設定は販売向けに整っています。", "As configurações básicas estão prontas para venda.", "Basic settings are ready for sales."))

    items = _readiness_items(users)
    st.markdown(
        '<div class="cs-grid-2">'
        + "".join(_status_card(label, status, note) for label, status, note in items)
        + "</div>",
        unsafe_allow_html=True,
    )

    with st.expander(_ui("Supabaseで最後に確認すること", "Últimas verificações no Supabase", "Final Supabase Checks"), expanded=False):
        st.markdown(
            _ui(
                "- `supabase_schema.sql` をSQL Editorで実行済み\n- `products` / `cores` / `generated_contents` にRLSが有効\n- 別ユーザーでログインした時に、他ユーザーの商品が表示されない\n- AuthのSite URLとRedirect URLに公開URLを追加済み\n- Email confirmation / Password recovery のメールが届く\n- 一般販売で登録数が増える前に、Supabase AuthのSMTP設定を自社/契約メール送信サービスに切り替える\n- `SUPABASE_SERVICE_ROLE_KEY` はサーバー側Secretsのみで管理\n- テストユーザーで商品保存、Core生成、再ログイン後の復元を確認",
                "- `supabase_schema.sql` executado no SQL Editor\n- RLS ativo em `products` / `cores` / `generated_contents`\n- Um usuário não vê produtos de outro usuário\n- URL pública adicionada em Site URL e Redirect URLs\n- Emails de confirmação e recuperação chegam corretamente\n- Antes da venda pública, configure SMTP próprio/contratado no Supabase Auth\n- `SUPABASE_SERVICE_ROLE_KEY` apenas em Secrets do servidor\n- Teste salvar produto, gerar Core e restaurar após novo login",
                "- `supabase_schema.sql` has been run in SQL Editor\n- RLS is enabled on `products` / `cores` / `generated_contents`\n- One user cannot see another user's products\n- Public URL is added to Site URL and Redirect URLs\n- Email confirmation and password recovery emails arrive correctly\n- Before public sales, switch Supabase Auth SMTP to your own email provider\n- Keep `SUPABASE_SERVICE_ROLE_KEY` only in server Secrets\n- Test product save, Core generation, and restore after sign-in",
            )
        )

    with st.expander(_ui("Supabase設定の進め方", "Como configurar Supabase", "How to Configure Supabase"), expanded=False):
        st.markdown(
            _ui(
                "1. Supabaseで新しいプロジェクトを作る\n2. Project Settings → API から `Project URL` と `anon public key` をコピーする\n3. Project Settings → API から `service_role key` をコピーする。これは公開しない\n4. Streamlit Secretsに `SUPABASE_URL`、`SUPABASE_ANON_KEY`、`SUPABASE_SERVICE_ROLE_KEY` を貼る\n5. SupabaseのSQL Editorで、このリポジトリの `supabase_schema.sql` を全部実行する\n6. Authentication → URL Configuration で、公開URLを Site URL と Redirect URLs に入れる\n7. 一般販売前に Authentication → SMTP Settings を設定して、確認メール/再設定メールの送信上限を実運用向けにする\n8. アプリを再起動して、新規登録・ログイン・保存・再ログイン復元を確認する\n\n`service_role key` は管理者用の強いキーです。画面やGitHubには出さず、Streamlit Secretsだけに入れてください。",
                "1. Crie um projeto no Supabase\n2. Em Project Settings → API, copie `Project URL` e `anon public key`\n3. Copie também `service_role key`; não publique essa chave\n4. Cole `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` no Streamlit Secrets\n5. Rode todo o `supabase_schema.sql` no SQL Editor\n6. Em Authentication → URL Configuration, adicione a URL pública em Site URL e Redirect URLs\n7. Antes da venda pública, configure SMTP em Authentication → SMTP Settings\n8. Reinicie o app e teste cadastro, login, salvamento e restauração\n\n`service_role key` é uma chave administrativa forte. Não coloque em tela nem no GitHub; use apenas Streamlit Secrets.",
                "1. Create a Supabase project\n2. Copy `Project URL` and `anon public key` from Project Settings → API\n3. Copy `service_role key`; never publish it\n4. Add `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` to Streamlit Secrets\n5. Run the full `supabase_schema.sql` in SQL Editor\n6. Add the public URL to Site URL and Redirect URLs in Authentication → URL Configuration\n7. Before public sales, configure SMTP in Authentication → SMTP Settings\n8. Restart the app and test sign up, sign in, save, and restore\n\n`service_role key` is a powerful admin key. Keep it out of the UI and GitHub; use Streamlit Secrets only.",
            )
        )

    with st.expander(_ui("販売前のユーザー分離テスト", "Teste de separação de usuários", "User Isolation Test"), expanded=False):
        st.markdown(
            _ui(
                "1. Supabase AuthでテストユーザーAとBを作成する\n2. Aでログインし、商品名に`A_ONLY_TEST`を含む商品を保存する\n3. AでCore生成とShopifyコード生成を1回ずつ実行し、ログアウトする\n4. Bでログインし、保存済み商品に`A_ONLY_TEST`が表示されないことを確認する\n5. Bで商品名に`B_ONLY_TEST`を含む商品を保存し、ログアウトする\n6. Aで再ログインし、`A_ONLY_TEST`だけが見えて`B_ONLY_TEST`が見えないことを確認する\n7. Supabase SQL Editorで`products`、`cores`、`generated_contents`の`workspace_id`がユーザーごとに分かれていることを確認する\n\nこのテストが通れば、個人ごとの商品・Core・生成物の分離は販売前チェックとして一段安心です。",
                "1. Crie usuários de teste A e B no Supabase Auth\n2. Entre como A e salve um produto com `A_ONLY_TEST` no nome\n3. Gere Core e código Shopify como A, depois saia\n4. Entre como B e confirme que `A_ONLY_TEST` não aparece\n5. Salve um produto com `B_ONLY_TEST` como B, depois saia\n6. Entre novamente como A e confirme que vê apenas `A_ONLY_TEST`, não `B_ONLY_TEST`\n7. No SQL Editor, confirme que `workspace_id` em `products`, `cores`, `generated_contents` é separado por usuário\n\nSe passar, a separação de produto/Core/conteúdo por usuário está bem mais segura para venda.",
                "1. Create test users A and B in Supabase Auth\n2. Sign in as A and save a product with `A_ONLY_TEST` in the name\n3. Generate Core and Shopify code as A, then sign out\n4. Sign in as B and confirm `A_ONLY_TEST` is not visible\n5. Save a product with `B_ONLY_TEST` as B, then sign out\n6. Sign in again as A and confirm only `A_ONLY_TEST` is visible, not `B_ONLY_TEST`\n7. In SQL Editor, confirm `workspace_id` in `products`, `cores`, and `generated_contents` is separated by user\n\nIf this passes, per-user product/Core/content isolation is much safer for launch.",
            )
        )

    with st.expander(_ui("Stripe課金の設定チェック", "Verificação de cobrança Stripe", "Stripe Billing Check"), expanded=False):
        billing_status = billing_config_status()
        if billing_status["ready"]:
            st.success(_ui("Stripe課金の基本設定はそろっています。", "A configuração básica do Stripe está pronta.", "Basic Stripe billing settings are ready."))
        else:
            if billing_status["missing"]:
                st.warning(_ui("未設定: ", "Não configurado: ", "Missing: ") + ", ".join(billing_status["missing"]))
            if billing_status["missing_prices"]:
                st.warning(_ui("Price ID未設定プラン: ", "Planos sem Price ID: ", "Plans missing Price ID: ") + ", ".join(billing_status["missing_prices"]))
            if billing_status["invalid_json"]:
                st.error(_ui("JSON形式を確認: ", "Verifique o formato JSON: ", "Check JSON format: ") + ", ".join(billing_status["invalid_json"]))
            if billing_status["invalid_plans"]:
                st.error(_ui("未対応プラン名: ", "Planos não suportados: ", "Unsupported plan names: ") + ", ".join(billing_status["invalid_plans"]))
        st.markdown(
            _ui(
                "- 料金はStripeのPrice側で後から変更できます\n- アプリ側は`STRIPE_PLAN_PRICE_MAP`に`{\"pro\":\"price_xxx\"}`のように対応を入れます\n- Checkout完了後、Webhookで`workspaces.plan`と`monthly_call_limit`が更新されます",
                "- Os preços podem ser alterados depois no Stripe Price\n- No app, configure `STRIPE_PLAN_PRICE_MAP` como `{\"pro\":\"price_xxx\"}`\n- Após o checkout, o webhook atualiza `workspaces.plan` e `monthly_call_limit`",
                "- Prices can be changed later in Stripe Price\n- In the app, map plans in `STRIPE_PLAN_PRICE_MAP` like `{\"pro\":\"price_xxx\"}`\n- After checkout, the webhook updates `workspaces.plan` and `monthly_call_limit`",
            )
        )
