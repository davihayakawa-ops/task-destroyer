"""商品準備ステータス + 管理者向け翻訳確認UIをまとめたモジュール。

page_product_input() の末尾セクション（Phase 3 承認ゲート + Phase 4 翻訳確認）を担う。
"""
import streamlit as st

from .permissions import (
    get_current_role,
    get_current_user,
    can_perform_action,
)
from .product_input_logic import (
    PRODUCT_FIELD_LABELS_JA,
    PRODUCT_TRANSLATABLE_FIELDS,
    product_prep_status_label,
)


def render_product_prep_ui(svc: dict, is_ja: bool) -> None:
    """商品準備ステータスと翻訳確認UIを描画する。

    Args:
        svc: サービス辞書 (storage, translator を含む)
        is_ja: 現在の表示言語が日本語なら True
    """
    pid = st.session_state.get("product_id", "")
    if not pid:
        return

    try:
        proj = svc["storage"].load_product(pid) or {}
    except Exception:
        proj = {}

    status = proj.get("product_prep_status", "draft")
    role   = get_current_role()

    st.markdown("---")
    s_ja, s_pt = product_prep_status_label(status)
    st.markdown(
        f"**{'商品準備ステータス' if is_ja else 'Status da Preparação'}**: "
        f"{s_ja if is_ja else s_pt}"
    )

    if status == "rejected" and proj.get("product_prep_review_note"):
        st.warning(
            ("**差し戻しコメント**: " if is_ja else "**Comentário de revisão**: ")
            + proj["product_prep_review_note"]
        )

    # ── researcher: 提出ボタン ────────────────────────────────────────────────
    if role == "product_researcher" and status in ("draft", "rejected"):
        if can_perform_action("product_prep_done"):
            _not_saved = not (proj.get("name") or proj.get("description"))
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "📤 " + ("そのまま提出" if is_ja else "Enviar sem tradução"),
                    key="pi_submit_prep", use_container_width=True,
                ):
                    if _not_saved:
                        st.error("先に「保存」ボタンで商品情報を保存してください。"
                                 if is_ja else "Salve as informações primeiro.")
                    else:
                        svc["storage"].submit_product_prep(pid, get_current_user())
                        st.success("Daviに提出しました。" if is_ja else "Enviado para revisão.")
                        st.rerun()
            with col2:
                if st.button(
                    "🌐 " + ("日本語に変換して提出" if is_ja else "Traduzir e enviar"),
                    type="primary", key="pi_translate_submit", use_container_width=True,
                ):
                    if _not_saved:
                        st.error("先に「保存」ボタンで商品情報を保存してください。"
                                 if is_ja else "Salve as informações primeiro.")
                    else:
                        tr_src = {
                            k: v
                            for k, v in (proj.get("input_original") or proj).items()
                            if k in PRODUCT_TRANSLATABLE_FIELDS and v and str(v).strip()
                        }
                        if not tr_src:
                            st.error("翻訳対象のテキストがありません。先に商品情報を保存してください。"
                                     if is_ja else "Nenhum texto para traduzir. Salve primeiro.")
                        else:
                            with st.spinner("翻訳中..." if is_ja else "Traduzindo..."):
                                try:
                                    tr_result = svc["translator"].translate_product_fields(tr_src)
                                    save_ok = svc["storage"].save_product_translation(
                                        pid, tr_result, get_current_user()
                                    )
                                    if save_ok:
                                        svc["storage"].submit_product_prep(pid, get_current_user())
                                        st.success("翻訳・提出が完了しました。"
                                                   if is_ja else "Traduzido e enviado.")
                                        st.rerun()
                                    else:
                                        st.error("翻訳の保存に失敗しました。先に「保存」ボタンで保存してください。"
                                                 if is_ja else "Falha ao salvar. Salve primeiro.")
                                except Exception as exc:
                                    exc_str = str(exc).lower()
                                    if any(w in exc_str for w in ("credit", "balance", "low")):
                                        st.error("クレジット残高が不足しています。"
                                                 if is_ja else "Saldo insuficiente.")
                                    else:
                                        st.error(("翻訳に失敗しました: " if is_ja else "Falha: ")
                                                 + str(exc)[:200])
                                    svc["storage"].mark_product_translation_failed(
                                        pid, get_current_user(), str(exc)
                                    )
                                    svc["storage"].log_activity(
                                        pid, "日本語翻訳失敗（提出時）",
                                        str(exc)[:100], get_current_user()
                                    )

    elif status == "waiting_review":
        st.info("管理者が確認中です。" if is_ja else "Aguardando revisão do administrador.")
    elif status == "approved":
        st.success(
            ("承認者: " if is_ja else "Aprovado por: ")
            + proj.get("product_prep_approved_by", "")
            + "  (" + proj.get("product_prep_approved_at", "") + ")"
        )

    # ── admin: 商品情報（日本語確認用）表示（Phase 4）────────────────────────
    if role != "admin":
        return

    tr_status = proj.get("translation_status", "not_translated")
    input_ja  = proj.get("input_ja") or {}
    orig      = proj.get("input_original") or {}
    core_src  = proj.get("core_source_data") or {}

    st.markdown("---")
    st.markdown("**🌐 " + ("商品情報（日本語確認用）" if is_ja else "Dados do produto (revisão)") + "**")

    # 翻訳ステータスバッジ
    if tr_status == "translated":
        st.caption(
            "✅ 翻訳済み — " + proj.get("translated_by", "")
            + ("  " + proj.get("translated_at", "") if proj.get("translated_at") else "")
            + "　📦 Core生成には日本語データを使用します"
        )
    elif tr_status == "not_needed":
        st.caption("✅ 日本語入力　📦 Core生成には日本語データを使用します")
    elif tr_status == "failed":
        st.caption("⚠️ 翻訳失敗 — 再試行できます")
    else:
        st.caption("📝 未翻訳 — Iago/Kaueが「日本語に変換して提出」を使うか、下のボタンで変換してください")

    # タブ切り替え（翻訳済み）/ 原文のみ（未翻訳）
    if input_ja:
        tab_ja, tab_pt = st.tabs(
            ["🇯🇵 日本語確認用" if is_ja else "🇯🇵 Japonês",
             "🇧🇷 原文 Português" if is_ja else "🇧🇷 Original"]
        )
        with tab_ja:
            for fk in PRODUCT_TRANSLATABLE_FIELDS:
                fv = input_ja.get(fk, "")
                if fv and str(fv).strip():
                    st.markdown(f"**{PRODUCT_FIELD_LABELS_JA.get(fk, fk)}**: {fv}")
            if core_src:
                st.caption("⚙️ Core生成用データも作成済みです")
        with tab_pt:
            orig_disp = orig or {k: proj.get(k, "") for k in PRODUCT_TRANSLATABLE_FIELDS}
            for fk in PRODUCT_TRANSLATABLE_FIELDS:
                fv = orig_disp.get(fk, "")
                if fv and str(fv).strip():
                    st.markdown(f"**{PRODUCT_FIELD_LABELS_JA.get(fk, fk)}**: {fv}")
            st.caption("🗂️ 原文は保持されています（input_original）")
    else:
        orig_disp = orig or {k: proj.get(k, "") for k in PRODUCT_TRANSLATABLE_FIELDS}
        if any(orig_disp.get(k) for k in PRODUCT_TRANSLATABLE_FIELDS):
            with st.expander(
                "📄 " + ("原文データ" if is_ja else "Dados originais"),
                expanded=False,
            ):
                for fk in PRODUCT_TRANSLATABLE_FIELDS:
                    fv = orig_disp.get(fk, "")
                    if fv and str(fv).strip():
                        st.markdown(f"**{PRODUCT_FIELD_LABELS_JA.get(fk, fk)}**: {fv}")

    # 管理者による翻訳ボタン
    btn_lbl = (
        ("🔄 再翻訳" if is_ja else "🔄 Retraduzir")
        if tr_status == "translated"
        else ("🔄 日本語に変換" if is_ja else "🔄 Traduzir para japonês")
    )
    if st.button(btn_lbl, key="pi_translate_btn"):
        fields_src = (
            {k: v for k, v in orig.items() if v and str(v).strip()}
            if orig
            else {k: v for k, v in proj.items()
                  if k in PRODUCT_TRANSLATABLE_FIELDS and v and str(v).strip()}
        )
        if not fields_src:
            st.warning("翻訳対象のテキストがありません。先に商品情報を保存してください。"
                       if is_ja else "Nenhum texto para traduzir. Salve primeiro.")
        else:
            with st.spinner("翻訳中..." if is_ja else "Traduzindo..."):
                try:
                    translated = svc["translator"].translate_product_fields(fields_src)
                    save_ok = svc["storage"].save_product_translation(
                        pid, translated, get_current_user()
                    )
                    if save_ok:
                        st.success("翻訳が完了しました。" if is_ja else "Tradução concluída.")
                        st.rerun()
                    else:
                        st.error("翻訳の保存に失敗しました。先に「保存」ボタンで商品情報を保存してから再度翻訳してください。"
                                 if is_ja else "Falha ao salvar tradução. Salve as informações primeiro.")
                except Exception as exc:
                    exc_str = str(exc).lower()
                    if any(w in exc_str for w in ("credit", "balance", "low")):
                        st.error("クレジット残高が不足しています。Anthropicアカウントを確認してください。"
                                 if is_ja else "Saldo de crédito insuficiente.")
                    else:
                        st.error(("翻訳に失敗しました: " if is_ja else "Falha: ") + str(exc)[:200])
                    svc["storage"].mark_product_translation_failed(
                        pid, get_current_user(), str(exc)
                    )
                    svc["storage"].log_activity(
                        pid, "日本語翻訳失敗（商品入力）", str(exc)[:100], get_current_user()
                    )
