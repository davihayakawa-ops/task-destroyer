"""Terms, privacy, and consent gate for public deployments."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st

from modules.auth import current_user
from modules.config import secret_or_env


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def terms_version() -> str:
    return secret_or_env("TASK_DESTROYER_TERMS_VERSION", "2026-05-18")


def _safe_user_key(email: str) -> str:
    raw = str(email or "unknown").strip().lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _consent_path(data_dir: Path, email: str) -> Path:
    consents_dir = Path(data_dir) / "consents"
    consents_dir.mkdir(parents=True, exist_ok=True)
    return consents_dir / f"{_safe_user_key(email)}.json"


def load_consent(data_dir: Path, email: str) -> dict:
    path = _consent_path(data_dir, email)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def has_current_consent(data_dir: Path, email: str) -> bool:
    data = load_consent(data_dir, email)
    return data.get("terms_version") == terms_version() and data.get("accepted") is True


def record_consent(data_dir: Path, user: dict, audit_logger: Optional[object] = None) -> None:
    email = user.get("email", "")
    entry = {
        "email": email,
        "name": user.get("name", ""),
        "workspace": user.get("workspace", ""),
        "terms_version": terms_version(),
        "accepted": True,
        "accepted_at": _now(),
    }
    _consent_path(data_dir, email).write_text(json.dumps(entry, ensure_ascii=False, indent=2))
    if audit_logger:
        audit_logger.log(
            "legal", "accept_terms", "ok",
            actor=email,
            detail={"terms_version": terms_version()},
        )


def _ui(ja: str, pt: str, en: str) -> str:
    lang = st.session_state.get("lang", "ja")
    if lang == "ja":
        return ja
    if lang == "en":
        return en
    return pt


def render_consent_gate(data_dir: Path, audit_logger: Optional[object] = None) -> bool:
    user = current_user()
    email = user.get("email", "")
    if email == "local-dev":
        return True
    if has_current_consent(data_dir, email):
        return True

    st.markdown("## " + _ui(
        "Task Destroyer 利用開始前の確認",
        "Confirmação antes de usar o Task Destroyer",
        "Before you start using Task Destroyer",
    ))
    st.caption(f"Terms version: {terms_version()}")

    if st.session_state.get("lang", "ja") == "en":
        st.markdown("""
### Key Terms
- This app helps generate product pages, ad copy, image prompts, video scripts, and social posts.
- Do not publish AI outputs as-is. You are responsible for checking facts, laws, and platform rules.
- Check medical claims, guaranteed results, No.1 claims, reviews, prices, and comparisons against the rules of your sales market.
- You may not use this app for misuse, rights infringement, false advertising, spam, or illegal products.

### Disclaimer
- We do not guarantee accuracy, legality, sales results, or ad approval.
- You are responsible for compliance with Shopify, ad platforms, social platforms, and local laws.

### Privacy
- Product info, generated outputs, operation logs, API usage, and consent records are stored to run the app.
- Audit logs do not store prompt or generated text. They store operation type, result, character counts, and error type.
- Inputs may be sent to external AI APIs for generation.
""")
    elif st.session_state.get("lang", "ja") == "pt":
        st.markdown("""
### Pontos principais dos termos
- Este app ajuda a gerar páginas de produto, anúncios, prompts de imagem, roteiros de vídeo e textos para redes sociais.
- Não publique resultados de IA sem revisar. Você deve conferir fatos, leis e regras das plataformas.
- Verifique alegações médicas, garantias, No.1, reviews, preços e comparações conforme o mercado de venda.
- O app não pode ser usado para abuso, violação de direitos, propaganda falsa, spam ou produtos ilegais.

### Isenção
- Não garantimos exatidão, legalidade, vendas ou aprovação em anúncios.
- A conformidade com Shopify, plataformas de anúncios, redes sociais e leis locais é responsabilidade do usuário.

### Privacidade
- Informações de produto, conteúdos gerados, logs, uso de API e consentimentos são salvos para operar o app.
- Logs de auditoria não salvam prompts nem textos gerados. Salvam tipo de operação, resultado, contagem de caracteres e tipo de erro.
- As entradas podem ser enviadas para APIs externas de IA para geração.
""")
    else:
        st.markdown("""
### 利用規約の要点
- 本アプリは商品ページ、広告文、画像プロンプト、動画台本、SNS文の生成支援ツールです。
- 生成結果はそのまま公開せず、利用者自身が事実確認、法令確認、プラットフォーム規約確認を行ってください。
- 医療効果、効果保証、No.1表示、レビュー表現、価格表示、比較表現などは販売先のルールに合わせて確認してください。
- 不正利用、第三者権利侵害、虚偽広告、スパム、違法商品の販売支援には利用できません。

### 免責
- AI生成物の正確性、適法性、売上成果、広告審査通過は保証しません。
- Shopify、広告媒体、SNS、各国法規制への適合は利用者の責任で確認してください。

### プライバシー
- 商品情報、生成物、操作ログ、API使用量、同意履歴をアプリ運用のために保存します。
- 監査ログにはプロンプト本文や生成本文を保存せず、操作種別、結果、文字数、エラー種別などの運用情報のみ保存します。
- API生成のため、入力内容は外部AI APIに送信される場合があります。
""")

    agree = st.checkbox(_ui(
        "上記の利用規約・免責・プライバシー内容を確認し、同意します。",
        "Li e concordo com os termos, isenção e privacidade acima.",
        "I have reviewed and agree to the terms, disclaimer, and privacy notes above.",
    ))
    if st.button(_ui("同意して開始", "Concordar e começar", "Agree and start"), type="primary", disabled=not agree):
        record_consent(data_dir, user, audit_logger)
        st.rerun()

    if st.button(_ui("ログアウト", "Sair", "Sign out")):
        from modules.auth import logout
        logout()
    return False
