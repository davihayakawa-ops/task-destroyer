import html

import streamlit as st

from .i18n import t, tl
from .permissions import get_current_user, can_perform_action
from .product_input_logic import (
    PRODUCT_FIELD_LABELS_JA,
    PRODUCT_TRANSLATABLE_FIELDS,
)
from .project_utils import (
    is_empty_project_entry,
    load_project_session,
    do_delete_project,
    ensure_product_id,
)


def _current_storage():
    from modules.storage import Storage as _Storage
    return _Storage(st.session_state.get("shop_id", "default"))


_SAVED_DATA_CSS = """
<style>
.sd-hero {
    background: #111827;
    border: 1px solid #263244;
    border-radius: 10px;
    padding: 16px 18px;
    margin: 0 0 16px;
}
.sd-hero h3 {
    color: #f8fafc;
    font-size: 1rem;
    font-weight: 850;
    margin: 0 0 6px;
}
.sd-hero p {
    color: #a8b3c7;
    font-size: .82rem;
    line-height: 1.65;
    margin: 0;
}
.sd-action-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin: 0 0 18px;
}
.sd-action-card,
.sd-kpi {
    background: #111827;
    border: 1px solid #263244;
    border-radius: 8px;
    padding: 13px 14px;
}
.sd-action-card strong {
    color: #f8fafc;
    display: block;
    font-size: .84rem;
    margin-bottom: 5px;
}
.sd-action-card span {
    color: #94a3b8;
    display: block;
    font-size: .74rem;
    line-height: 1.55;
}
.sd-kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin: 12px 0 16px;
}
.sd-kpi {
    min-height: 92px;
}
.sd-kpi-label {
    color: #94a3b8;
    font-size: .74rem;
    font-weight: 750;
    margin-bottom: 8px;
}
.sd-kpi-value {
    color: #f8fafc;
    font-size: 1.85rem;
    font-weight: 900;
    letter-spacing: 0;
    line-height: 1;
}
.sd-kpi-note {
    color: #64748b;
    font-size: .7rem;
    margin-top: 8px;
}
.sd-path,
.sd-list {
    background: #151a24;
    border: 1px solid #263244;
    border-radius: 8px;
    color: #cbd5e1;
    font-size: .8rem;
    line-height: 1.8;
    padding: 12px 14px;
}
.sd-path {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    overflow-x: auto;
    white-space: nowrap;
}
.sd-list code,
.sd-path code {
    color: #f8fafc;
}
@media (max-width: 900px) {
    .sd-action-grid,
    .sd-kpi-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def _hero_html(title: str, body: str) -> str:
    return (
        '<div class="sd-hero">'
        f"<h3>{html.escape(title)}</h3>"
        f"<p>{html.escape(body)}</p>"
        "</div>"
    )


def _lt(ja: str, pt: str, en: str, lang: str) -> str:
    if lang == "ja":
        return ja
    if lang == "en":
        return en
    return pt


def page_saved_data(svc: dict) -> None:
    lang = st.session_state.get("lang", "ja")
    is_ja = lang == "ja"
    st.markdown(_SAVED_DATA_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">📁 ' +
        _lt("保存済み商品", "Produtos salvos", "Saved Products", lang) +
        '</div>',
        unsafe_allow_html=True,
    )

    all_products = [
        p for p in svc["storage"].list_products()
        if not is_empty_project_entry(p)
    ]
    current_pid = st.session_state.get("product_id", "")

    st.markdown(
        _hero_html(
            _lt("商品プロジェクトを開く", "Abrir projeto de produto", "Open a Product Project", lang),
            _lt(
                "過去に保存した商品、Core、Shopifyコード、画像・動画・SNS生成物を読み込みます。ここは管理画面ではなく、作業を再開するための保存ライブラリです。",
                "Carregue produtos, Core, código Shopify e materiais gerados anteriormente. Esta é uma biblioteca para continuar o trabalho, não uma tela de administração.",
                "Load previously saved products, Cores, Shopify code, and generated assets. This is a library for resuming work, not an admin screen.",
                lang,
            ),
        ),
        unsafe_allow_html=True,
    )

    db_ready = False
    try:
        from modules.supabase_db import supabase_db_configured
        from modules.storage import Storage as _Storage
        db_ready = supabase_db_configured()
        local_count = svc["storage"].local_file_product_count()
        all_local_count = _Storage.all_local_file_product_count()
    except Exception:
        local_count = 0
        all_local_count = 0
    if db_ready and st.session_state.get("auth_user", {}).get("workspace_db_id"):
        with st.expander(
            _lt("過去データを探す・復元する", "Encontrar ou restaurar dados antigos", "Find or Restore Previous Data", lang),
            expanded=not bool(all_products),
        ):
            st.caption(
                _lt(
                    f"Cloud内のローカル保存: このショップ {local_count} 件 / 全ショップ {all_local_count} 件",
                    f"Dados locais na Cloud: esta loja {local_count} / todas as lojas {all_local_count}",
                    f"Local saves in Cloud: this shop {local_count} / all shops {all_local_count}",
                    lang,
                )
            )
            if all_local_count:
                if st.button(
                    _lt("全ショップからこのアカウントへ移行する", "Migrar todas as lojas para esta conta", "Move all shops to this account", lang),
                    type="primary",
                    use_container_width=True,
                ):
                    result = svc["storage"].migrate_all_local_files_to_supabase()
                    if result.get("ok"):
                        st.success(result.get("message"))
                        st.rerun()
                    else:
                        st.error(result.get("message"))
            else:
                st.info(
                    _lt(
                        "Cloud内に古いローカル保存は見つかりません。バックアップZIPがある場合はここから復元できます。",
                        "Nenhum dado local antigo foi encontrado na Cloud. Se você tiver um ZIP de backup, restaure aqui.",
                        "No old local saves were found in Cloud. If you have a backup ZIP, restore it here.",
                        lang,
                    )
                )
            backup_file = st.file_uploader(
                _lt("バックアップZIPから復元", "Restaurar de ZIP de backup", "Restore from backup ZIP", lang),
                type=["zip"],
            )
            if backup_file is not None and st.button(
                _lt("このバックアップを復元する", "Restaurar este backup", "Restore this backup", lang),
                use_container_width=True,
            ):
                result = svc["storage"].import_backup_zip_to_supabase(backup_file.getvalue())
                if result.get("ok"):
                    st.success(result.get("message"))
                    st.rerun()
                else:
                    st.error(result.get("message"))

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.markdown(
            f'<div class="sd-kpi"><div class="sd-kpi-label">{_lt("保存済み商品", "Produtos salvos", "Saved products", lang)}</div>'
            f'<div class="sd-kpi-value">{len(all_products)}</div>'
            f'<div class="sd-kpi-note">{_lt("開くとCoreも復元", "Core também é restaurado", "Core is restored too", lang)}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        current_name = st.session_state.get("product_info", {}).get("name") or "—"
        st.markdown(
            f'<div class="sd-kpi"><div class="sd-kpi-label">{_lt("現在の商品", "Produto atual", "Current product", lang)}</div>'
            f'<div class="sd-kpi-value" style="font-size:1rem;line-height:1.35;">{html.escape(str(current_name))}</div>'
            f'<div class="sd-kpi-note">ID: {html.escape(str(current_pid or "—"))}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="sd-action-grid" style="grid-template-columns:1fr 1fr;">'
            f'<div class="sd-action-card"><strong>{_lt("読み込む", "Carregar", "Load", lang)}</strong><span>{_lt("商品情報・Core・生成済み内容をまとめて復元します。", "Restaura informações, Core e conteúdos gerados.", "Restores product info, Core, and generated content.", lang)}</span></div>'
            f'<div class="sd-action-card"><strong>{_lt("保存する", "Salvar", "Save", lang)}</strong><span>{_lt("商品入力画面で保存すると、この一覧に残ります。", "Ao salvar na tela de produto, ele aparece nesta lista.", "Saving from Product Info keeps it in this list.", lang)}</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    ctrl_col1, ctrl_col2 = st.columns([3, 1])
    with ctrl_col1:
        search = st.text_input(
            "🔍",
            placeholder=_lt("商品名で検索", "Buscar por nome do produto", "Search by product name", lang),
            label_visibility="collapsed",
        )
    with ctrl_col2:
        if st.button("＋ " + _lt("新規商品", "Novo produto", "New Product", lang), use_container_width=True):
            for key in (
                "product_id", "core_text", "core_status", "core_strategy",
                "core_safety", "core_focus", "core_tone",
            ):
                st.session_state.pop(key, None)
            st.session_state["product_info"] = {}
            st.session_state["generated"] = {}
            for key in ("image_prompts", "video_scripts", "ads_sns_items"):
                st.session_state.pop(key, None)
            st.session_state["page"] = "product_input"
            st.rerun()

    products = all_products
    if search:
        q = search.lower()
        products = [
            p for p in products
            if q in str(p.get("name", "")).lower()
            or q in str(p.get("category", "")).lower()
        ]

    tab_projects, tab_cores = st.tabs([
        _lt("商品プロジェクト", "Projetos de produto", "Product Projects", lang),
        _lt("現在のCore履歴", "Histórico do Core atual", "Current Core History", lang),
    ])

    with tab_projects:
        if not products:
            msg = _lt(
                "保存済みの商品プロジェクトがありません。商品情報を入力して保存すると、ここから再開できます。",
                "Nenhum projeto salvo. Salve as informações do produto para continuar daqui depois.",
                "No saved product projects yet. Save product info first, then you can resume from here.",
                lang,
            )
            st.markdown(f'<div class="cs-info">💡 {msg}</div>', unsafe_allow_html=True)
        else:
            for p in products:
                pid = p["id"]
                name = p.get("name") or "—"
                category = p.get("category", "")
                is_current = pid == current_pid
                header = (
                    ("✅ " if is_current else "📦 ") +
                    f"{name}" +
                    (f" / {category}" if category else "")
                )
                with st.expander(header, expanded=is_current):
                    info_col, action_col = st.columns([3, 1])
                    with info_col:
                        rows = [
                            (_lt("最終更新", "Atualizado", "Updated", lang), p.get("updated_at", "-")),
                            (_lt("価格", "Preço", "Price", lang), p.get("price", "-")),
                            (_lt("ターゲット", "Público-alvo", "Target", lang), p.get("target", "-")),
                            (_lt("説明", "Descrição", "Description", lang), p.get("description", "-")),
                        ]
                        for label, value in rows:
                            if value:
                                st.markdown(f"**{label}:** {value}")
                        st.caption(f"ID: {pid}")
                    with action_col:
                        if st.button(
                            "📂 " + _lt("この商品を開く", "Abrir produto", "Open product", lang),
                            key=f"library_load_{pid}",
                            use_container_width=True,
                            type="primary" if not is_current else "secondary",
                        ):
                            load_project_session(pid, p, svc)
                            st.session_state["page"] = "product_input"
                            st.success(
                                f"{name} " +
                                _lt("を読み込みました", "carregado", "loaded", lang)
                            )
                            st.rerun()
                        if is_current:
                            st.markdown(
                                '<div class="cs-success">✅ ' +
                                _lt("現在開いています", "Aberto agora", "Currently open", lang) +
                                '</div>',
                                unsafe_allow_html=True,
                            )
                        if can_perform_action("delete_project") and st.button(
                            "🗑️ " + _lt("削除", "Excluir", "Delete", lang),
                            key=f"library_prepare_delete_{pid}",
                            use_container_width=True,
                        ):
                            st.session_state["library_confirm_delete_id"] = pid
                            st.session_state["library_confirm_delete_name"] = name
                            st.rerun()
                    if st.session_state.get("library_confirm_delete_id") == pid:
                        st.markdown(
                            '<div class="cs-warning">⚠️ ' +
                            _lt(
                                "この商品を保存済み一覧から削除します。Coreや生成物もこの商品からは開けなくなります。",
                                "Este produto será removido da lista. Core e conteúdos gerados deixarão de abrir por este produto.",
                                "This product will be removed from the saved list. Its Cores and generated assets will no longer open from this product.",
                                lang,
                            ) +
                            '</div>',
                            unsafe_allow_html=True,
                        )
                        delete_reason = st.text_input(
                            _lt("削除理由（任意）", "Motivo da exclusão (opcional)", "Reason (optional)", lang),
                            key=f"library_delete_reason_{pid}",
                        )
                        confirm_col, cancel_col = st.columns(2)
                        with confirm_col:
                            if st.button(
                                "🗑️ " + _lt("削除する", "Excluir", "Delete", lang),
                                key=f"library_delete_{pid}",
                                type="primary",
                                use_container_width=True,
                            ):
                                result = do_delete_project(pid, p.get("file_path", ""), delete_reason)
                                if result.get("success"):
                                    if st.session_state.get("product_id") == pid:
                                        for key in ("product_id", "product_info", "core_text", "core_status"):
                                            st.session_state.pop(key, None)
                                        st.session_state["generated"] = {}
                                    st.session_state.pop("library_confirm_delete_id", None)
                                    st.session_state.pop("library_confirm_delete_name", None)
                                    st.success(
                                        _lt(
                                            "削除しました。Supabase保存分も一覧から非表示になります。",
                                            "Excluído. O item salvo no Supabase também ficará oculto.",
                                            "Deleted. The Supabase saved item will also be hidden from the list.",
                                            lang,
                                        )
                                    )
                                    st.rerun()
                                st.error(
                                    _lt("削除に失敗しました: ", "Falha ao excluir: ", "Delete failed: ", lang)
                                    + str(result.get("message", ""))
                                )
                        with cancel_col:
                            if st.button(
                                "✖ " + _lt("キャンセル", "Cancelar", "Cancel", lang),
                                key=f"library_cancel_delete_{pid}",
                                use_container_width=True,
                            ):
                                st.session_state.pop("library_confirm_delete_id", None)
                                st.session_state.pop("library_confirm_delete_name", None)
                                st.rerun()

    with tab_cores:
        if not current_pid:
            st.markdown(
                '<div class="cs-info">💡 ' +
                _lt("先に商品プロジェクトを開いてください。", "Abra um projeto primeiro.", "Open a product project first.", lang) +
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            cores = svc["storage"].list_cores(current_pid)
            if not cores:
                st.markdown(
                    '<div class="cs-info">💡 ' +
                    _lt("この商品の保存済みCoreはまだありません。", "Este produto ainda não tem Core salvo.", "This product has no saved Core yet.", lang) +
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                for c in reversed(cores):
                    with st.expander(f"📝 {c.get('version_label', 'Core')} ({c.get('created_at', '-')})"):
                        core_text = c.get("core", {}).get("text", "")
                        st.text_area(
                            "Core",
                            value=core_text[:2000] + ("..." if len(core_text) > 2000 else ""),
                            height=220,
                            key=f"library_core_{c['id']}",
                            disabled=True,
                        )
                        if st.button(
                            "📂 " + _lt("このCoreを使う", "Usar este Core", "Use this Core", lang),
                            key=f"library_use_core_{c['id']}",
                            use_container_width=True,
                        ):
                            st.session_state["core_text"] = core_text
                            st.session_state["core_status"] = c.get("status", "ai_generated")
                            st.session_state["page"] = "core_generation"
                            st.success(_lt("Coreを読み込みました", "Core carregado", "Core loaded", lang))
                            st.rerun()

    return

    if is_ja:
        st.markdown(
            _hero_html(
                "保存済みデータを管理",
                "普段は商品プロジェクトから読み込みます。診断・バックアップ・ゴミ箱は、データ整理や復元が必要な時だけ使う管理メニューです。",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="sd-action-grid">
                <div class="sd-action-card"><strong>商品を読み込む</strong><span>過去に保存した商品を開いて、Core生成やShopifyコード作成を続けます。</span></div>
                <div class="sd-action-card"><strong>安全に保管する</strong><span>バックアップを作成して、復元が必要な時に戻せます。</span></div>
                <div class="sd-action-card"><strong>状態を確認する</strong><span>診断は管理用です。通常操作では開かなくても問題ありません。</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            _hero_html(
                "Gerenciar dados salvos",
                "No uso normal, abra os projetos de produto. Diagnóstico, backup e lixeira são menus de administração para organização e restauração.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="sd-action-grid">
                <div class="sd-action-card"><strong>Abrir produto</strong><span>Continue a partir de um produto salvo para gerar Core ou código Shopify.</span></div>
                <div class="sd-action-card"><strong>Guardar com segurança</strong><span>Crie backups e restaure dados quando necessário.</span></div>
                <div class="sd-action-card"><strong>Verificar estado</strong><span>O diagnóstico é administrativo. Não precisa ser aberto no uso normal.</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "商品" if is_ja else "Produtos",
        "Core",
        "管理診断" if is_ja else "Diagnóstico",
        "バックアップ" if is_ja else "Backup",
        "ゴミ箱" if is_ja else "Lixeira",
    ])

    with tab1:
        all_products = svc["storage"].list_products()
        st.markdown(
            _hero_html(
                "商品プロジェクト" if is_ja else "Projetos de produto",
                "保存済みの商品を読み込みます。不要な削除や翻訳確認は、商品行を開いて操作します。"
                if is_ja else
                "Abra produtos salvos. Exclusão e revisão de tradução ficam dentro de cada item.",
            ),
            unsafe_allow_html=True,
        )

        # ── Display options ──────────────────────────────────────────────
        ctrl_col1, ctrl_col2 = st.columns([3, 2])
        with ctrl_col1:
            search = st.text_input("🔍", placeholder=t("saved_data.search_placeholder"),
                                   label_visibility="collapsed")
        with ctrl_col2:
            show_empty = st.checkbox("空データも表示する" if is_ja else "Mostrar projetos vazios", value=False)

        # ── Separate empty / normal ──────────────────────────────────────
        empty_products = [p for p in all_products if is_empty_project_entry(p)]
        normal_products = [p for p in all_products if not is_empty_project_entry(p)]

        if search:
            normal_products = [p for p in normal_products
                               if search.lower() in p.get("name", "").lower()]

        products = normal_products + (empty_products if show_empty else [])

        # ── Bulk cleanup button (only when empty entries exist) ──────────
        if empty_products:
            _empty_warn = (f"空データが {len(empty_products)} 件あります。整理ボタンで一括削除できます。"
                           if is_ja else
                           f"{len(empty_products)} projeto(s) vazio(s) encontrado(s). Use o botão abaixo para limpar.")
            st.markdown(f'<div class="cs-warning">⚠️ {_empty_warn}</div>', unsafe_allow_html=True)
            if can_perform_action("cleanup_empty") and st.button("🧹 " + ("空プロジェクトを整理する（ゴミ箱へ移動）" if is_ja
                                   else "Limpar projetos vazios (mover para lixeira)"),
                         type="secondary", use_container_width=False):
                if not can_perform_action("cleanup_empty"):
                    st.warning("この操作は許可されていません。" if is_ja else "Operação não permitida.")
                    st.rerun()
                _s = _current_storage()
                # Auto-backup before cleanup
                try:
                    bk = _s.create_backup("before_empty_cleanup")
                    st.info(("自動バックアップ作成: " if is_ja else "Backup automático criado: ") + bk.name)
                except Exception as _be:
                    st.warning(("バックアップ作成に失敗しました: " if is_ja else "Falha no backup: ") + str(_be))
                cleaned = 0
                for ep in empty_products:
                    r = _s.delete_project(ep["id"], "auto_cleanup", "空データ自動整理",
                                          file_path=ep.get("file_path", ""), use_trash=True)
                    if r.get("success"):
                        cleaned += 1
                st.success((f"空プロジェクト {cleaned} 件をゴミ箱に移動しました" if is_ja
                             else f"{cleaned} projeto(s) vazio(s) movido(s) para a lixeira"))
                st.rerun()

        if not products:
            _no_result = ("該当なし" if is_ja else "Nenhum resultado") if search else t("saved_data.search_placeholder")
            st.markdown(f'<div class="cs-info">💡 {_no_result}</div>', unsafe_allow_html=True)
        else:
            for p in products:
                pid = p["id"]
                disp_name = p.get("name") or "—"
                is_empty = is_empty_project_entry(p)
                header = f"{'⚠️ [空] ' if is_empty else ''}📦 {disp_name}  ({p.get('category', '')})"

                with st.expander(header):
                    col_info, col_actions = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"**{t('status.last_updated')}:** {p.get('updated_at', '-')}")
                        st.markdown(f"**{'価格' if is_ja else 'Preço'}:** {p.get('price', '-')}")
                        st.markdown(f"**{'ターゲット' if is_ja else 'Público-alvo'}:** {p.get('target', '-')}")
                        if p.get("assignee"):
                            st.markdown(f"**{t('product_input.assignee')}:** {p.get('assignee', '-')}")
                        if is_empty:
                            st.caption(f"ID: {pid} | file_path: {p.get('file_path', 'N/A')}")
                    with col_actions:
                        if not is_empty:
                            if st.button("📂 " + t("saved_data.load_btn"), key=f"load_{pid}",
                                         use_container_width=True):
                                load_project_session(pid, p, svc)
                                st.success(f"'{p.get('name')}' " + ("を読み込みました" if is_ja else "carregado"))
                                st.rerun()

                        if can_perform_action("delete_project") and st.button("🗑️ " + t("saved_data.delete_btn"), key=f"del_{pid}",
                                     use_container_width=True):
                            if not can_perform_action("delete_project"):
                                st.warning("この操作は許可されていません。" if is_ja else "Operação não permitida.")
                                st.rerun()
                            st.session_state["confirm_delete_id"] = pid
                            st.session_state["confirm_delete_file_path"] = p.get("file_path", "")
                            st.session_state["confirm_delete_name"] = disp_name
                            st.rerun()

                    # Confirmation dialog
                    if st.session_state.get("confirm_delete_id") == pid:
                        if not can_perform_action("delete_project"):
                            st.warning("この操作は許可されていません。" if is_ja else "Operação não permitida.")
                            st.session_state.pop("confirm_delete_id", None)
                            st.session_state.pop("confirm_delete_file_path", None)
                            st.session_state.pop("confirm_delete_name", None)
                            st.rerun()
                        st.markdown("---")
                        st.markdown(f"**⚠️ {t('saved_data.confirm_delete_title')}**")
                        st.markdown(t("saved_data.confirm_delete_msg"))
                        delete_reason = st.text_input(
                            t("saved_data.delete_reason_label"),
                            key=f"del_reason_{pid}",
                        )
                        dcol1, dcol2 = st.columns(2)
                        with dcol1:
                            if st.button("🗑️ " + t("saved_data.delete_confirm_btn"),
                                         key=f"do_del_{pid}", type="primary",
                                         use_container_width=True):
                                if not can_perform_action("delete_project"):
                                    st.warning("この操作は許可されていません。" if is_ja else "Operação não permitida.")
                                    st.rerun()
                                file_path = st.session_state.get("confirm_delete_file_path",
                                                                  p.get("file_path", ""))
                                result = do_delete_project(pid, file_path, delete_reason)

                                if result["success"]:
                                    if st.session_state.get("product_id") == pid:
                                        for k in ("product_id", "product_info", "core_text",
                                                  "core_status", "assignee", "reviewer"):
                                            st.session_state[k] = "" if isinstance(
                                                st.session_state.get(k), str) else {}
                                        st.session_state["generated"] = {}
                                        for _cat in ("image_prompts", "video_scripts", "ads_sns_items"):
                                            st.session_state.pop(_cat, None)
                                    st.session_state.pop("confirm_delete_id", None)
                                    st.session_state.pop("confirm_delete_file_path", None)
                                    st.session_state.pop("confirm_delete_name", None)
                                    if result.get("trash_path"):
                                        _del_ok = ("ゴミ箱に移動しました。ゴミ箱タブから復元できます。"
                                                   if is_ja else "Movido para a lixeira. Restaure na aba Lixeira.")
                                    else:
                                        _del_ok = t("saved_data.deleted_msg")
                                    st.success(_del_ok)
                                    if result.get("deleted_paths"):
                                        st.caption(("削除ファイル数: " if is_ja else "Arquivos excluídos: ") + str(len(result["deleted_paths"])))
                                    st.rerun()
                                else:
                                    from pathlib import Path
                                    fp_str = file_path
                                    fp_exists = Path(fp_str).exists() if fp_str else False
                                    _del_fail = ("削除に失敗しました" if is_ja else "Falha ao excluir")
                                    _detail_lbl = ("詳細" if is_ja else "Detalhe")
                                    st.error(
                                        f"{_del_fail}\n\n"
                                        f"- project_id: `{pid}`\n"
                                        f"- file_path: `{fp_str}`\n"
                                        f"- file_exists: `{fp_exists}`\n\n"
                                        f"{_detail_lbl}: {result['message']}"
                                    )
                        with dcol2:
                            if st.button("✖ " + t("saved_data.delete_cancel_btn"),
                                         key=f"cancel_del_{pid}", use_container_width=True):
                                st.session_state.pop("confirm_delete_id", None)
                                st.session_state.pop("confirm_delete_file_path", None)
                                st.session_state.pop("confirm_delete_name", None)
                                st.rerun()

                        # ── 日本語確認用翻訳（Phase 4） ──────────────────────────────────
                        _tr_orig   = p.get("input_original") or {}
                        _tr_ja     = p.get("input_ja") or {}
                        _tr_status = p.get("translation_status", "not_translated")
                        _tr_has_orig = any(str(v).strip() for v in _tr_orig.values() if v)
                        st.markdown("---")
                        st.markdown("**🌐 " + ("日本語確認用翻訳" if is_ja else "Tradução para revisão") + "**")

                        if True:
                            # 原文表示
                            if _tr_has_orig:
                                with st.expander(
                                    "📄 " + ("原文 Português" if is_ja else "Original em Português"),
                                    expanded=False,
                                ):
                                    for _fk, _fv in _tr_orig.items():
                                        if _fv and str(_fv).strip():
                                            st.markdown(f"**{PRODUCT_FIELD_LABELS_JA.get(_fk, _fk)}**: {_fv}")
                            else:
                                st.caption("💡 " + ("原文データがありません。先に商品情報を保存してください。"
                                                    if is_ja else "Nenhum dado original. Salve as informações primeiro."))

                            # 翻訳ステータス表示
                            if _tr_status == "translated":
                                st.caption(
                                    "✅ " + ("翻訳済み — " if is_ja else "Traduzido — ")
                                    + p.get("translated_by", "") + "  " + p.get("translated_at", "")
                                )
                                if _tr_ja:
                                    with st.expander(
                                        "🇯🇵 " + ("日本語確認用訳" if is_ja else "Tradução japonesa"),
                                        expanded=True,
                                    ):
                                        for _fk, _fv in _tr_ja.items():
                                            if _fv and str(_fv).strip():
                                                st.markdown(f"**{PRODUCT_FIELD_LABELS_JA.get(_fk, _fk)}**: {_fv}")
                                _tr_core_src = p.get("core_source_data") or {}
                                if _tr_core_src:
                                    with st.expander(
                                        "⚙️ " + ("Core生成用データ（日本語）" if is_ja else "Dados para Core (japonês)"),
                                        expanded=False,
                                    ):
                                        for _fk, _fv in _tr_core_src.items():
                                            if _fv and str(_fv).strip():
                                                st.markdown(f"**{PRODUCT_FIELD_LABELS_JA.get(_fk, _fk)}**: {_fv}")
                            elif _tr_status == "failed":
                                st.caption("⚠️ " + ("翻訳失敗（再試行できます）"
                                                     if is_ja else "Falha na tradução (tente novamente)"))
                            else:
                                st.caption("📝 " + ("未翻訳" if is_ja else "Não traduzido"))

                            # 翻訳ボタン
                            _btn_lbl = (
                                ("🔄 再翻訳" if is_ja else "🔄 Retraduzir")
                                if _tr_status == "translated"
                                else ("🔄 日本語に変換" if is_ja else "🔄 Traduzir para japonês")
                            )
                            if _tr_has_orig and st.button(_btn_lbl, key=f"translate_{pid}"):
                                _to_translate = {
                                    k: v for k, v in _tr_orig.items()
                                    if v and str(v).strip()
                                }
                                with st.spinner("翻訳中..." if is_ja else "Traduzindo..."):
                                    try:
                                        _translated = svc["translator"].translate_product_fields(_to_translate)
                                        svc["storage"].save_product_translation(
                                            pid, _translated, get_current_user()
                                        )
                                        # Ensure Core generation reads this project
                                        st.session_state["product_id"] = pid
                                        _refreshed = svc["storage"].load_product(pid) or {}
                                        st.session_state["product_info"] = {
                                            k: v for k, v in _refreshed.items()
                                            if k not in ("id", "file_path")
                                        }
                                        st.session_state["generation_target_market"] = _refreshed.get("target_market") or "japan"
                                        st.session_state["generation_output_language"] = _refreshed.get("output_language") or "ja"
                                        st.session_state["generation_market_note"] = _refreshed.get("market_note") or ""
                                        st.session_state["_market_loaded_for_product"] = pid
                                        st.success("翻訳が完了しました。" if is_ja else "Tradução concluída.")
                                        st.rerun()
                                    except Exception as _te:
                                        _te_str = str(_te).lower()
                                        if any(w in _te_str for w in ("credit", "balance", "low", "crédito")):
                                            st.error("クレジット残高が不足しています。Anthropicアカウントを確認してください。"
                                                     if is_ja else "Saldo de crédito insuficiente.")
                                        else:
                                            st.error(("翻訳に失敗しました: " if is_ja else "Falha: ") + str(_te)[:200])
                                        svc["storage"].mark_product_translation_failed(
                                            pid, get_current_user(), str(_te)
                                        )
                                        svc["storage"].log_activity(
                                            pid, "日本語翻訳失敗", str(_te)[:100], get_current_user()
                                        )

    with tab2:
        pid = ensure_product_id()
        cores = svc["storage"].list_cores(pid)
        if not cores:
            st.markdown('<div class="cs-info">💡 ' + ("保存済みCoreがありません。" if is_ja else "Nenhum Core salvo.") + '</div>',
                        unsafe_allow_html=True)
        else:
            for c in reversed(cores):
                with st.expander(f"📝 {c['version_label']} — {c.get('status', '')} ({c['created_at']})"):
                    core_text = c["core"].get("text", "")
                    st.text_area("Core" + ("内容" if is_ja else " (conteúdo)"),
                                 value=core_text[:1000] + "..." if len(core_text) > 1000 else core_text,
                                 height=200, key=f"saved_core_{c['id']}", disabled=True)
                    if st.button("📂 " + ("このCoreを使用" if is_ja else "Usar este Core"), key=f"use_core_{c['id']}"):
                        st.session_state["core_text"] = core_text
                        st.session_state["core_status"] = c.get("status", "ai_generated")
                        st.success("Coreを読み込みました" if is_ja else "Core carregado")
                        st.rerun()

    # ── Tab 3: 診断 ───────────────────────────────────────────────────────────
    with tab3:
        st.markdown(
            _hero_html(
                "管理診断" if is_ja else "Diagnóstico administrativo",
                "保存データの健康状態を確認する管理画面です。通常の作業では、問題が起きた時だけ見れば十分です。"
                if is_ja else
                "Tela administrativa para verificar o estado dos dados salvos. No fluxo normal, use apenas quando houver algum problema.",
            ),
            unsafe_allow_html=True,
        )
        _sdx = _current_storage()
        try:
            dx = _sdx.get_diagnostics()
        except Exception as _dxe:
            st.error(f"診断情報の取得に失敗しました: {_dxe}")
            dx = {}

        if dx:
            errors = dx.get("error_content_files", [])
            last_bk = dx.get("last_backup_at") or "—"
            audit_stats = dx.get("audit_stats", {}) or {}
            kpi_items = [
                ("保存プロジェクト" if is_ja else "Projetos salvos", dx.get("total_projects", 0),
                 "読み込み可能な商品数" if is_ja else "Produtos disponíveis"),
                ("正常データ" if is_ja else "Dados normais", dx.get("normal_projects", 0),
                 "通常利用できる保存データ" if is_ja else "Itens prontos para uso"),
                ("空データ" if is_ja else "Dados vazios", dx.get("empty_projects", 0),
                 "必要なら整理できます" if is_ja else "Podem ser limpos se necessário"),
                ("ゴミ箱" if is_ja else "Lixeira", dx.get("trash_count", 0),
                 "復元または完全削除できます" if is_ja else "Pode restaurar ou excluir"),
                ("バックアップ" if is_ja else "Backups", dx.get("backup_count", 0),
                 "保存済みZIPの数" if is_ja else "Quantidade de ZIPs salvos"),
                ("最終バックアップ" if is_ja else "Último backup", last_bk,
                 "直近の保管日時" if is_ja else "Data mais recente"),
                ("直近エラー" if is_ja else "Erros recentes", audit_stats.get("recent_errors", 0),
                 "生成・操作ログ内の失敗" if is_ja else "Falhas em geração/operações"),
                ("直近生成" if is_ja else "Gerações recentes", audit_stats.get("recent_llm_calls", 0),
                 "監査ログ内のLLMイベント" if is_ja else "Eventos LLM no log"),
            ]
            st.markdown(
                '<div class="sd-kpi-grid">'
                + "".join(
                    '<div class="sd-kpi">'
                    f'<div class="sd-kpi-label">{html.escape(str(label))}</div>'
                    f'<div class="sd-kpi-value">{html.escape(str(value))}</div>'
                    f'<div class="sd-kpi-note">{html.escape(str(note))}</div>'
                    '</div>'
                    for label, value, note in kpi_items
                )
                + "</div>",
                unsafe_allow_html=True,
            )

            if errors:
                st.markdown('<div class="cs-warning">⚠️ ' + (
                    "確認が必要なファイルがあります。下の技術情報を開いて内容を確認してください。"
                    if is_ja else
                    "Há arquivos que precisam de verificação. Abra as informações técnicas abaixo."
                ) + '</div>', unsafe_allow_html=True)
            else:
                st.success("APIエラー文を含むファイルは検出されませんでした。" if is_ja
                           else "Nenhum arquivo com erro de API detectado.")

            with st.expander("技術情報を表示" if is_ja else "Mostrar informações técnicas", expanded=False):
                st.markdown("**" + ("読み込み対象フォルダ" if is_ja else "Diretório de dados") + "**")
                data_dir = html.escape(str(dx.get("data_dir", "")))
                st.markdown(f'<div class="sd-path"><code>{data_dir}</code></div>',
                            unsafe_allow_html=True)

                counts = dx.get("dir_file_counts", {})
                if counts:
                    st.markdown("**" + ("フォルダ別ファイル数" if is_ja else "Arquivos por pasta") + "**")
                    rows = "".join(
                        f"<div><code>{html.escape(str(k))}/</code> : {html.escape(str(v))}"
                        + (" 件" if is_ja else " arquivos")
                        + "</div>"
                        for k, v in sorted(counts.items())
                    )
                    st.markdown(f'<div class="sd-list">{rows}</div>', unsafe_allow_html=True)

                if errors:
                    st.markdown("**⚠️ " + ("APIエラー文が含まれる可能性のあるファイル" if is_ja
                                 else "Arquivos com possível erro de API") + "**")
                    for ef in errors:
                        st.markdown(
                            f"- `{ef['file']}` — "
                            + ("商品名" if is_ja else "Produto")
                            + f": {ef['name']} — "
                            + ("パターン" if is_ja else "Padrão")
                            + f": `{ef['pattern']}`"
                        )
                    st.caption("自動削除・上書きはしません。手動で確認してください。" if is_ja
                               else "Nenhuma ação automática. Verifique manualmente.")

                recent_events = audit_stats.get("recent_events", [])
                if recent_events:
                    st.markdown("**" + ("直近の運用ログ" if is_ja else "Logs operacionais recentes") + "**")
                    rows = []
                    for ev in recent_events[:12]:
                        rows.append(
                            "<div>"
                            f"<code>{html.escape(str(ev.get('timestamp', '')))}</code> "
                            f"{html.escape(str(ev.get('status', '')))} "
                            f"{html.escape(str(ev.get('event_type', '')))} / "
                            f"{html.escape(str(ev.get('action', '')))} "
                            f"<span style='color:#94a3b8;'>"
                            f"{html.escape(str(ev.get('actor', '')))}"
                            "</span>"
                            "</div>"
                        )
                    st.markdown(f'<div class="sd-list">{"".join(rows)}</div>', unsafe_allow_html=True)

    # ── Tab 4: バックアップ ────────────────────────────────────────────────────
    with tab4:
        st.markdown(
            _hero_html(
                "バックアップと復元" if is_ja else "Backup e restauração",
                "保存データをZIPで保管します。復元は現在のデータに影響するため、必要な時だけ実行してください。"
                if is_ja else
                "Guarde os dados salvos em ZIP. A restauração afeta os dados atuais, então use apenas quando necessário.",
            ),
            unsafe_allow_html=True,
        )

        # ── セクション1: 全保存データをバックアップ ──────────────────────────
        st.markdown("### 🗃️ " + ("全保存データをバックアップ" if is_ja else "Backup de todos os dados"))

        # バックアップ対象の統計情報を取得（常に表示）
        try:
            _bk_s = _current_storage()
            _bk_stats = _bk_s.get_backup_stats()
        except Exception as _bk_stats_exc:
            _bk_stats = {"project_count": 0, "dir_file_counts": {}, "total_file_count": 0}
            st.error(f"統計情報の取得に失敗しました: {_bk_stats_exc}")

        _bk_proj_count = _bk_stats["project_count"]
        _bk_dir_counts = _bk_stats["dir_file_counts"]
        _bk_total_files = _bk_stats["total_file_count"]

        # 保存データ件数
        st.metric(
            "📦 " + ("保存データ件数" if is_ja else "Projetos salvos"),
            _bk_proj_count,
        )

        # バックアップ対象フォルダ + 各フォルダ内ファイル数
        if _bk_dir_counts:
            st.markdown("**" + ("バックアップ対象フォルダ" if is_ja else "Pastas incluídas no backup") + "**")
            for _d, _c in sorted(_bk_dir_counts.items()):
                st.markdown(f"　`data/{_d}/` : {_c}" + (" ファイル" if is_ja else " arquivos"))
            st.caption(
                ("合計 " if is_ja else "Total ") + str(_bk_total_files) +
                (" ファイル（APIキー・.env・Secretsは除外）" if is_ja
                 else " arquivos (APIkeys, .env, Secrets excluídos)")
            )
        else:
            st.caption("バックアップ対象ファイルがありません" if is_ja else "Nenhum arquivo para backup")

        st.markdown("---")

        # 保存データ0件 → ボタンを出さずにメッセージのみ
        if _bk_proj_count == 0:
            st.markdown('<div class="cs-warning">⚠️ ' + (
                "現在バックアップできる保存データはありません。"
                if is_ja else
                "Não há dados salvos para backup no momento."
            ) + '</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                ("data/ 配下の保存データをZIPにまとめてダウンロードします。"
                 "APIキー・.env・Secretsは含まれません。"
                 if is_ja else
                 "Compacta todos os dados salvos em data/ como ZIP para download. "
                 "Chaves de API, .env e Secrets não são incluídos.")
            )
            if not can_perform_action("backup"):
                st.warning("バックアップ操作は管理者のみ利用できます。" if is_ja else "Backup é restrito a administradores.")
            elif st.button(
                "⚡ " + ("全保存データをバックアップ" if is_ja else "Gerar ZIP de Backup"),
                type="primary",
                key="saved_data_bk_generate",
                use_container_width=False,
            ):
                if not can_perform_action("backup"):
                    st.warning("この操作は許可されていません。" if is_ja else "Operação não permitida.")
                    st.rerun()
                with st.spinner("バックアップ作成中..." if is_ja else "Criando backup..."):
                    try:
                        _bk_s2 = _current_storage()
                        _bk_bytes, _bk_fname, _bk_zip_count = _bk_s2.create_backup_bytes()
                        st.session_state["_bk_ready_bytes"] = _bk_bytes
                        st.session_state["_bk_ready_fname"] = _bk_fname
                        st.session_state["_bk_ready_count"] = _bk_zip_count
                        st.session_state["_bk_ready_err"] = None
                    except Exception as _bk_exc:
                        st.session_state["_bk_ready_bytes"] = None
                        st.session_state["_bk_ready_fname"] = None
                        st.session_state["_bk_ready_count"] = 0
                        st.session_state["_bk_ready_err"] = str(_bk_exc)

            _bk_err = st.session_state.get("_bk_ready_err")
            _bk_data = st.session_state.get("_bk_ready_bytes")
            _bk_fname = st.session_state.get("_bk_ready_fname", "backup.zip")
            _bk_zip_count = st.session_state.get("_bk_ready_count", 0)

            if _bk_err:
                st.error(("バックアップ作成失敗: " if is_ja else "Falha no backup: ") + _bk_err)
            elif _bk_data:
                st.success("✅ " + (
                    f"バックアップ作成完了 — {_bk_zip_count} ファイルをZIPに含めました。下のボタンでダウンロードしてください。"
                    if is_ja else
                    f"Backup criado — {_bk_zip_count} arquivos incluídos. Clique abaixo para baixar."
                ))
                st.download_button(
                    label="⬇️ " + (f"ZIPをダウンロード ({_bk_fname})"
                                   if is_ja else f"Baixar ZIP ({_bk_fname})"),
                    data=_bk_data,
                    file_name=_bk_fname,
                    mime="application/zip",
                    key="saved_data_bk_download",
                    disabled=not can_perform_action("backup"),
                )
                if can_perform_action("backup") and st.button("🗑️ " + ("キャッシュをクリア" if is_ja else "Limpar cache"),
                             key="saved_data_bk_clear"):
                    st.session_state.pop("_bk_ready_bytes", None)
                    st.session_state.pop("_bk_ready_fname", None)
                    st.session_state.pop("_bk_ready_count", None)
                    st.session_state.pop("_bk_ready_err", None)
                    st.rerun()

        st.markdown("---")

        # ── セクション2: バックアップから復元 ────────────────────────────────
        st.markdown("### 🔄 " + ("バックアップから復元" if is_ja else "Restaurar de Backup"))
        st.markdown('<div class="cs-warning">⚠️ ' + (
            "復元前に現在のデータが自動バックアップされます。ZIPファイルの内容がdata/配下に上書き展開されます。"
            if is_ja else
            "O estado atual será salvo automaticamente antes da restauração. O ZIP será extraído sobre data/."
        ) + '</div>', unsafe_allow_html=True)

        _can_restore = can_perform_action("restore")
        if not _can_restore:
            st.warning("復元操作は管理者のみ利用できます。" if is_ja else "Restauração é restrita a administradores.")
        _restore_upload = (st.file_uploader(
            "バックアップZIPをアップロード" if is_ja else "Enviar ZIP de backup",
            type=["zip"],
            key="saved_data_bk_upload",
        ) if _can_restore else None)
        if _restore_upload:
            if st.button(
                "🔄 " + ("このZIPで復元する" if is_ja else "Restaurar com este ZIP"),
                type="primary",
                key="saved_data_bk_restore_btn",
            ):
                if not can_perform_action("restore"):
                    st.warning("この操作は許可されていません。" if is_ja else "Operação não permitida.")
                    st.rerun()
                with st.spinner("復元中..." if is_ja else "Restaurando..."):
                    try:
                        _rst_s = _current_storage()
                        _rst_res = _rst_s.restore_from_backup(_restore_upload.read())
                    except Exception as _rst_exc:
                        _rst_res = {"success": False, "message": str(_rst_exc)}
                if _rst_res["success"]:
                    st.success(_rst_res["message"])
                    st.caption(("事前バックアップ: " if is_ja else "Backup pré-restauração: ") +
                               str(_rst_res.get("pre_backup", "")))
                    st.rerun()
                else:
                    st.error(_rst_res["message"])

        st.markdown("---")

        # ── セクション3: 保存済みバックアップ一覧 ────────────────────────────
        st.markdown("### 📋 " + ("保存済みバックアップ一覧" if is_ja else "Backups Disponíveis"))
        try:
            _lbk_s = _current_storage()
            _bk_list = _lbk_s.list_backups()
        except Exception:
            _bk_list = []

        if not _bk_list:
            st.markdown('<div class="cs-info">💡 ' + (
                "バックアップがありません。上のボタンで作成してください。"
                if is_ja else
                "Nenhum backup disponível. Use o botão acima para criar um."
            ) + '</div>', unsafe_allow_html=True)
        else:
            st.caption(("data/backups/ に保存済みのZIPファイル一覧です。"
                        if is_ja else "Arquivos ZIP salvos em data/backups/."))
            for _bk_item in _bk_list:
                with st.expander(
                    f"🗃️ {_bk_item['filename']}  "
                    f"({_bk_item['created_at']},  {_bk_item['size_kb']} KB)"
                ):
                    st.caption(_bk_item["path"])
                    try:
                        with open(_bk_item["path"], "rb") as _bf:
                            _bitem_data = _bf.read()
                        st.download_button(
                            "⬇️ " + ("ダウンロード" if is_ja else "Baixar"),
                            data=_bitem_data,
                            file_name=_bk_item["filename"],
                            mime="application/zip",
                            key=f"saved_data_bk_dl_{_bk_item['filename']}",
                            disabled=not can_perform_action("backup"),
                        )
                    except Exception:
                        st.caption("ファイルが読み込めません" if is_ja else "Arquivo não legível")

    # ── Tab 5: ゴミ箱 ─────────────────────────────────────────────────────────
    with tab5:
        st.markdown(
            _hero_html(
                "ゴミ箱" if is_ja else "Lixeira",
                "削除した商品はここから復元できます。完全削除は戻せないため、確認してから実行してください。"
                if is_ja else
                "Produtos excluídos podem ser restaurados aqui. A exclusão definitiva não pode ser desfeita.",
            ),
            unsafe_allow_html=True,
        )
        _str = _current_storage()
        try:
            trash_list = _str.list_trash()
        except Exception as _tre:
            st.error(f"ゴミ箱の読み込みに失敗しました: {_tre}")
            trash_list = []

        if not trash_list:
            st.markdown('<div class="cs-info">💡 ' + (
                "ゴミ箱は空です。" if is_ja else "A lixeira está vazia."
            ) + '</div>', unsafe_allow_html=True)
        else:
            st.markdown(("ゴミ箱内のデータを復元または完全削除できます。" if is_ja
                          else "Você pode restaurar ou excluir permanentemente os itens da lixeira."))
            for item in trash_list:
                _hdr = f"🗑️ {item['product_name']}  ({item['deleted_at']})"
                with st.expander(_hdr):
                    col_i, col_a = st.columns([3, 1])
                    with col_i:
                        st.markdown(f"**{'商品名' if is_ja else 'Nome'}:** {item['product_name']}")
                        st.markdown(f"**{'削除日時' if is_ja else 'Excluído em'}:** {item['deleted_at']}")
                        st.markdown(f"**{'削除者' if is_ja else 'Excluído por'}:** {item['deleted_by'] or '—'}")
                        st.markdown(f"**{'理由' if is_ja else 'Motivo'}:** {item['reason'] or '—'}")
                        st.caption(f"ID: {item['product_id']} | 元ファイル: {item['original_path'] or '—'}")
                    with col_a:
                        if can_perform_action("restore") and st.button("↩️ " + ("復元" if is_ja else "Restaurar"),
                                     key=f"tr_restore_{item['filename']}", use_container_width=True,
                                     type="primary"):
                            if not can_perform_action("restore"):
                                st.warning("この操作は許可されていません。" if is_ja else "Operação não permitida.")
                                st.rerun()
                            res = _str.restore_from_trash(item["filename"])
                            if res["success"]:
                                st.success(res["message"])
                                st.rerun()
                            else:
                                st.error(res["message"])

                        if can_perform_action("purge_trash") and st.button("💀 " + ("完全削除" if is_ja else "Excluir"),
                                     key=f"tr_purge_{item['filename']}", use_container_width=True):
                            if not can_perform_action("purge_trash"):
                                st.warning("この操作は許可されていません。" if is_ja else "Operação não permitida.")
                                st.rerun()
                            st.session_state[f"confirm_purge_{item['filename']}"] = True
                            st.rerun()

                    if st.session_state.get(f"confirm_purge_{item['filename']}"):
                        st.markdown("---")
                        st.warning("⚠️ " + ("この操作は元に戻せません。本当に完全削除しますか？"
                                            if is_ja else "Esta ação é irreversível. Confirmar?"))
                        pc1, pc2 = st.columns(2)
                        with pc1:
                            if st.button("🗑️ " + ("完全削除する" if is_ja else "Excluir definitivamente"),
                                         key=f"tr_do_purge_{item['filename']}", type="primary",
                                         use_container_width=True):
                                if not can_perform_action("purge_trash"):
                                    st.warning("この操作は許可されていません。" if is_ja else "Operação não permitida.")
                                    st.rerun()
                                res = _str.purge_trash(item["filename"])
                                st.session_state.pop(f"confirm_purge_{item['filename']}", None)
                                if res["success"]:
                                    st.success(res["message"])
                                    st.rerun()
                                else:
                                    st.error(res["message"])
                        with pc2:
                            if st.button("✖ " + ("キャンセル" if is_ja else "Cancelar"),
                                         key=f"tr_cancel_purge_{item['filename']}",
                                         use_container_width=True):
                                st.session_state.pop(f"confirm_purge_{item['filename']}", None)
                                st.rerun()


# ── Page: My Projects dashboard ──────────────────────────────────────────────
# The definition below intentionally overrides the older saved-data screen above.
# The old implementation is kept in the file for now because it still documents
# the backup/trash tools, but the product-facing app should open this simpler
# project dashboard.

_MY_PROJECTS_CSS = """
<style>
.mp-shell {
    color: #f8fafc;
}
.mp-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
    margin: 2px 0 18px;
}
.mp-kicker {
    color: #6ee72f;
    font-size: .78rem;
    font-weight: 850;
    margin-bottom: 10px;
}
.mp-title {
    color: #f8fafc;
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: 0;
    line-height: 1.15;
    margin: 0;
}
.mp-sub {
    color: #aab7c7;
    font-size: .88rem;
    line-height: 1.7;
    margin-top: 10px;
}
.mp-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin: 18px 0 18px;
}
.mp-kpi {
    background: linear-gradient(145deg, rgba(17,24,39,.96), rgba(5,12,11,.96));
    border: 1px solid rgba(92, 255, 45, .26);
    border-radius: 8px;
    box-shadow: 0 0 0 1px rgba(15,23,42,.42), 0 12px 40px rgba(0,0,0,.18);
    min-height: 112px;
    overflow: hidden;
    padding: 18px 18px 16px;
    position: relative;
}
.mp-kpi:after {
    background: linear-gradient(90deg, transparent, rgba(106,255,47,.4));
    bottom: 18px;
    content: "";
    height: 2px;
    position: absolute;
    right: 18px;
    width: 84px;
}
.mp-kpi-top {
    align-items: center;
    color: #cbd5e1;
    display: flex;
    font-size: .78rem;
    font-weight: 800;
    gap: 8px;
}
.mp-kpi-value {
    color: #f8fafc;
    font-size: 2rem;
    font-weight: 950;
    line-height: 1;
    margin-top: 12px;
}
.mp-kpi-note {
    color: #8a96a8;
    font-size: .72rem;
    margin-top: 10px;
}
.mp-controls {
    align-items: center;
    display: grid;
    gap: 10px;
    grid-template-columns: minmax(240px, 1fr) 166px 156px 92px;
    margin: 4px 0 16px;
}
.mp-card {
    background:
        radial-gradient(circle at 15% 10%, rgba(103,255,34,.09), transparent 34%),
        linear-gradient(145deg, rgba(18,27,39,.98), rgba(4,11,12,.99));
    border: 1px solid rgba(106,255,47,.25);
    border-radius: 8px;
    box-shadow: 0 16px 42px rgba(0,0,0,.18);
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    margin-bottom: 8px;
    min-height: 304px;
    overflow: hidden;
    padding: 16px;
    position: relative;
}
.mp-card:hover {
    border-color: rgba(113,255,47,.44);
    box-shadow: 0 0 0 1px rgba(90,255,42,.08), 0 18px 52px rgba(0,0,0,.26);
}
.mp-card-top {
    align-items: center;
    display: grid;
    gap: 14px;
    grid-template-columns: 72px 1fr;
    min-height: 82px;
    padding-right: 58px;
}
.mp-thumb {
    align-items: center;
    background: radial-gradient(circle at 40% 25%, rgba(103,255,34,.22), rgba(18,26,38,.95) 55%);
    border: 1px solid rgba(148,163,184,.18);
    border-radius: 8px;
    display: flex;
    height: 72px;
    justify-content: center;
    overflow: hidden;
    width: 72px;
}
.mp-thumb img {
    height: 100%;
    object-fit: cover;
    width: 100%;
}
.mp-thumb span {
    color: #71ff2f;
    font-size: 1.6rem;
    font-weight: 900;
}
.mp-name-row {
    align-items: center;
    display: flex;
    gap: 8px;
    min-height: 72px;
}
.mp-name {
    color: #f8fafc;
    display: -webkit-box;
    font-size: 1.08rem;
    font-weight: 900;
    line-height: 1.28;
    margin: 0;
    min-height: 0;
    overflow: hidden;
    overflow-wrap: normal;
    word-break: keep-all;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
}
.mp-status {
    border: 1px solid rgba(59,130,246,.48);
    border-radius: 6px;
    color: #60a5fa;
    font-size: .68rem;
    font-weight: 850;
    padding: 2px 7px;
    position: absolute;
    right: 0;
    top: 0;
}
.mp-status.done {
    border-color: rgba(106,255,47,.5);
    color: #78ff39;
}
.mp-status.draft {
    border-color: rgba(148,163,184,.35);
    color: #aab7c7;
}
.mp-meta {
    border-top: 1px solid rgba(148,163,184,.15);
    color: #8a96a8;
    font-size: .7rem;
    margin: 16px 0 12px;
    padding-top: 12px;
}
.mp-step-title {
    color: #8a96a8;
    font-size: .68rem;
    font-weight: 850;
    margin-bottom: 2px;
}
.mp-steps {
    display: grid;
    gap: 6px;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    margin: 8px 0 0;
    min-height: 43px;
}
.mp-step {
    align-items: center;
    color: #8f9bae;
    display: flex;
    flex-direction: column;
    font-size: .58rem;
    gap: 4px;
    text-align: center;
}
.mp-dot {
    align-items: center;
    background: #2b313c;
    border: 1px solid rgba(148,163,184,.22);
    border-radius: 999px;
    color: #9ca3af;
    display: flex;
    font-size: .62rem;
    font-weight: 900;
    height: 21px;
    justify-content: center;
    width: 21px;
}
.mp-dot.ok {
    background: linear-gradient(135deg, #62df31, #2fa819);
    border-color: rgba(167,255,131,.35);
    color: #fff;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .mp-card) {
    gap: 8px !important;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .mp-card) > div[data-testid="stHorizontalBlock"] {
    margin: 0 0 26px !important;
    position: relative;
    z-index: 2;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .mp-card) button {
    border-radius: 7px !important;
    font-size: .76rem !important;
    min-height: 34px;
    padding: .26rem .45rem !important;
}
.mp-panel {
    background: rgba(17,24,39,.84);
    border: 1px solid rgba(148,163,184,.20);
    border-radius: 8px;
    margin-bottom: 12px;
    padding: 14px;
}
.mp-side-panel {
    align-items: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 72px;
    text-align: center;
}
.mp-panel-title {
    color: #f8fafc;
    font-size: .76rem;
    font-weight: 900;
    margin-bottom: 8px;
}
.mp-activity {
    border-bottom: 1px solid rgba(148,163,184,.12);
    color: #aab7c7;
    font-size: .64rem;
    line-height: 1.45;
    padding: 8px 0;
}
.mp-side-panel .mp-activity {
    width: 100%;
}
.mp-activity:last-child {
    border-bottom: 0;
}
.mp-delete-box {
    background: rgba(127,29,29,.24);
    border: 1px solid rgba(248,113,113,.35);
    border-radius: 8px;
    color: #fecaca;
    font-size: .76rem;
    line-height: 1.45;
    margin: 8px 0 12px;
    padding: 10px 12px;
}
.mp-empty {
    background: rgba(17,24,39,.84);
    border: 1px dashed rgba(106,255,47,.35);
    border-radius: 8px;
    color: #aab7c7;
    padding: 28px;
    text-align: center;
}
@media (max-width: 1100px) {
    .mp-kpi-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .mp-controls {
        grid-template-columns: 1fr;
    }
}
@media (max-width: 760px) {
    .mp-head {
        display: block;
    }
    .mp-kpi-grid {
        grid-template-columns: 1fr;
    }
    .mp-card {
        min-height: 0 !important;
        margin-bottom: 0;
        padding-bottom: 16px;
    }
    .mp-card-top,
    .mp-name,
    .mp-steps {
        min-height: 0;
    }
}
</style>
"""


def _mp_text(ja: str, pt: str, en: str, lang: str) -> str:
    return _lt(ja, pt, en, lang)


def _mp_parse_dt(value: str):
    from datetime import datetime

    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _mp_truncate(value: str, limit: int = 92) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[:limit - 1] + "…"


def _mp_has_generated(storage, product_id: str, content_type: str) -> bool:
    try:
        entry = storage.load_generated(product_id, content_type)
    except Exception:
        entry = None
    if not entry:
        return False
    content = entry.get("content")
    if isinstance(content, dict):
        if content.get("text"):
            return True
        items = content.get("items")
        if isinstance(items, dict) and any(str(v).strip() for v in items.values()):
            return True
        return bool(content)
    return bool(content)


def _mp_project_status(storage, product: dict) -> dict:
    product_id = product.get("id", "")
    try:
        has_core = bool(storage.list_cores(product_id))
    except Exception:
        has_core = False
    steps = {
        "core": has_core,
        "shopify": _mp_has_generated(storage, product_id, "product_page"),
        "image": _mp_has_generated(storage, product_id, "image_prompt"),
        "video": _mp_has_generated(storage, product_id, "video_script"),
        "sns": _mp_has_generated(storage, product_id, "ads_sns"),
    }
    steps["export"] = all(steps.values())
    done = sum(1 for ok in steps.values() if ok)
    if done >= len(steps):
        state = "done"
    elif done == 0:
        state = "draft"
    else:
        state = "progress"
    return {"steps": steps, "done": done, "total": len(steps), "state": state}


def _mp_next_page(status: dict) -> str:
    steps = status.get("steps", {})
    if not steps.get("core"):
        return "core_generation"
    if not steps.get("shopify"):
        return "product_page"
    if not (steps.get("image") and steps.get("video") and steps.get("sns")):
        return "related_assets"
    return "export_center"


def _mp_status_label(state: str, lang: str) -> str:
    if state == "done":
        return _mp_text("生成済み", "Gerado", "Generated", lang)
    if state == "draft":
        return _mp_text("下書き", "Rascunho", "Draft", lang)
    return _mp_text("作成中", "Em andamento", "In Progress", lang)


def _mp_open_project(pid: str, product: dict, svc: dict, target_page: str) -> None:
    load_project_session(pid, product, svc)
    st.session_state["page"] = target_page
    st.rerun()


def _mp_duplicate_project(product: dict, svc: dict, lang: str) -> dict:
    import uuid

    storage = svc["storage"]
    source_id = product.get("id", "")
    new_id = str(uuid.uuid4())[:8]
    suffix = _mp_text(" コピー", " cópia", " copy", lang)
    new_data = {
        k: v for k, v in dict(product).items()
        if k not in ("id", "file_path", "created_at", "updated_at")
    }
    base_name = str(product.get("name") or _mp_text("無題の商品", "Produto sem nome", "Untitled product", lang))
    new_data["name"] = _mp_truncate(base_name + suffix, 80)
    new_data["source_project_id"] = source_id
    storage.save_product(new_id, new_data)

    try:
        latest_core = storage.load_latest_core(source_id)
        if latest_core and isinstance(latest_core.get("core"), dict):
            storage.save_core(new_id, dict(latest_core["core"]), latest_core.get("version_label", ""))
    except Exception:
        pass

    for content_type in ("product_page", "image_prompt", "video_script", "ads_sns"):
        try:
            entry = storage.load_generated(source_id, content_type)
            content = entry.get("content") if isinstance(entry, dict) else None
            if isinstance(content, dict):
                storage.save_generated(new_id, content_type, dict(content))
        except Exception:
            pass
    return {"id": new_id, **new_data}


def _mp_deleted_product_ids() -> set[str]:
    raw_ids = st.session_state.get("mp_deleted_product_ids") or []
    if isinstance(raw_ids, str):
        raw_ids = [raw_ids]
    return {str(pid).strip() for pid in raw_ids if str(pid or "").strip()}


def _mp_mark_product_deleted(product_id: str) -> None:
    product_id = str(product_id or "").strip()
    if not product_id:
        return
    deleted_ids = _mp_deleted_product_ids()
    deleted_ids.add(product_id)
    st.session_state["mp_deleted_product_ids"] = sorted(deleted_ids)


def _mp_queue_delete(product_id: str) -> None:
    product_id = str(product_id or "").strip()
    if product_id:
        st.session_state["mp_delete_request_id"] = product_id


def _mp_delete_project(product: dict, svc: dict, lang: str) -> dict:
    pid = str(product.get("id") or "")
    if not pid:
        return {
            "success": False,
            "message": _mp_text("削除対象が見つかりません。", "Projeto não encontrado.", "Project not found.", lang),
        }
    reason = _mp_text("マイプロジェクト画面から削除", "Excluído em Meus projetos", "Deleted from My Projects", lang)
    try:
        result = svc["storage"].delete_project(
            pid,
            get_current_user(),
            reason,
            file_path=product.get("file_path", ""),
            cloud_local_id=product.get("_db_local_id", ""),
            cloud_product_row_id=product.get("_db_product_row_id", ""),
            use_trash=True,
        )
    except Exception as exc:
        result = {"success": False, "message": str(exc)}
    if result.get("success"):
        _mp_mark_product_deleted(pid)
        try:
            remaining = svc["storage"].load_product(pid)
        except Exception:
            remaining = None
        if remaining:
            result["warning"] = _mp_text(
                "削除済みとして一覧から外しました。保存先に古い行が残っている可能性があるため、次回も見える場合はクラウドDBの状態を確認します。",
                "Removido da lista como excluído. Pode haver uma linha antiga no banco; se aparecer novamente, verificaremos o banco na nuvem.",
                "Removed from the list as deleted. An old cloud row may remain; if it appears again, check the cloud DB state.",
                lang,
            )
        if st.session_state.get("product_id") == pid:
            for key in (
                "product_id", "product_info", "core_text", "core_status", "core_strategy",
                "core_safety", "core_focus", "core_tone", "generated",
                "image_prompts", "video_scripts", "ads_sns_items",
            ):
                st.session_state.pop(key, None)
    return result


def _mp_process_queued_delete(svc: dict, lang: str) -> None:
    pid = str(st.session_state.pop("mp_delete_request_id", "") or "").strip()
    if not pid:
        return

    product = {"id": pid}
    try:
        loaded = svc["storage"].load_product(pid)
        if isinstance(loaded, dict):
            product.update(loaded)
            product["id"] = pid
    except Exception:
        pass

    result = _mp_delete_project(product, svc, lang)
    st.session_state["mp_last_delete_result"] = result
    if result.get("success"):
        st.rerun()


def _mp_product_thumb(product: dict) -> str:
    image = product.get("product_image")
    if isinstance(image, dict) and image.get("data_url"):
        src = html.escape(str(image["data_url"]))
        return f'<div class="mp-thumb"><img src="{src}" alt=""></div>'
    name = str(product.get("name") or "?").strip()
    initial = html.escape(name[:1].upper() or "T")
    return f'<div class="mp-thumb"><span>{initial}</span></div>'


def _mp_card_html(product: dict, status: dict, lang: str) -> str:
    name = html.escape(str(product.get("name") or _mp_text("無題の商品", "Produto sem nome", "Untitled product", lang)))
    updated_label = _mp_text("更新日", "Atualizado", "Updated", lang)
    updated = html.escape(str(product.get("updated_at") or "-"))
    state = status["state"]
    status_label = html.escape(_mp_status_label(state, lang))
    status_class = "done" if state == "done" else ("draft" if state == "draft" else "")
    step_labels = [
        ("core", "Core"),
        ("shopify", "Shopify"),
        ("image", _mp_text("画像", "Imagem", "Image", lang)),
        ("video", _mp_text("動画", "Vídeo", "Video", lang)),
        ("sns", "SNS"),
        ("export", _mp_text("出力", "Export", "Export", lang)),
    ]
    steps_html = "".join(
        '<div class="mp-step">'
        f'<div class="mp-dot {"ok" if status["steps"].get(key) else ""}">{"✓" if status["steps"].get(key) else "−"}</div>'
        f'<div>{html.escape(label)}</div>'
        '</div>'
        for key, label in step_labels
    )
    return (
        '<div class="mp-card">'
        '<div class="mp-card-top">'
        f'{_mp_product_thumb(product)}'
        '<div>'
        '<div class="mp-name-row">'
        f'<h3 class="mp-name">{name}</h3>'
        f'<span class="mp-status {status_class}">{status_label}</span>'
        '</div>'
        '</div>'
        '</div>'
        f'<div class="mp-meta">{updated_label}: {updated}</div>'
        f'<div class="mp-step-title">{_mp_text("生成状況", "Status", "Progress", lang)}</div>'
        f'<div class="mp-steps">{steps_html}</div>'
        '</div>'
    )


def _mp_render_delete_confirm(product: dict, svc: dict, lang: str, key_prefix: str) -> None:
    pid = str(product.get("id") or "")
    if st.session_state.get("mp_confirm_delete_id") != pid:
        return
    name = html.escape(str(product.get("name") or _mp_text("このプロジェクト", "este projeto", "this project", lang)))
    st.markdown(
        '<div class="mp-delete-box">'
        + _mp_text("削除しますか？", "Excluir este projeto?", "Delete this project?", lang)
        + f"<br><strong>{name}</strong>"
        + "</div>",
        unsafe_allow_html=True,
    )
    d1, d2 = st.columns(2)
    with d1:
        if st.button(_mp_text("削除する", "Excluir", "Delete", lang), key=f"{key_prefix}_delete_yes_{pid}", use_container_width=True):
            result = _mp_delete_project(product, svc, lang)
            if result.get("success"):
                st.session_state.pop("mp_confirm_delete_id", None)
                st.success(_mp_text("削除しました。", "Projeto excluído.", "Project deleted.", lang))
                st.rerun()
            st.error(result.get("message") or _mp_text("削除に失敗しました。", "Falha ao excluir.", "Delete failed.", lang))
    with d2:
        if st.button(_mp_text("やめる", "Cancelar", "Cancel", lang), key=f"{key_prefix}_delete_no_{pid}", use_container_width=True):
            st.session_state.pop("mp_confirm_delete_id", None)
            st.rerun()


def _mp_kpi(label: str, value: int, note: str, icon: str) -> str:
    return (
        '<div class="mp-kpi">'
        f'<div class="mp-kpi-top"><span>{html.escape(icon)}</span><span>{html.escape(label)}</span></div>'
        f'<div class="mp-kpi-value">{value}</div>'
        f'<div class="mp-kpi-note">{html.escape(note)}</div>'
        '</div>'
    )


def _mp_current_product_label(lang: str) -> str:
    info = st.session_state.get("product_info") or {}
    return str(info.get("name") or _mp_text("未選択", "Não selecionado", "Not selected", lang))


def page_saved_data(svc: dict) -> None:
    lang = st.session_state.get("lang", "ja")
    storage = svc["storage"]
    st.markdown(_MY_PROJECTS_CSS, unsafe_allow_html=True)
    _mp_process_queued_delete(svc, lang)

    last_delete_result = st.session_state.pop("mp_last_delete_result", None)
    if isinstance(last_delete_result, dict):
        if last_delete_result.get("success"):
            st.success(_mp_text("削除しました。", "Projeto excluído.", "Project deleted.", lang))
            if last_delete_result.get("warning"):
                st.warning(str(last_delete_result["warning"]))
        else:
            st.error(
                last_delete_result.get("message")
                or _mp_text("削除に失敗しました。", "Falha ao excluir.", "Delete failed.", lang)
            )

    deleted_ids = _mp_deleted_product_ids()
    all_products = [
        p for p in storage.list_products()
        if not is_empty_project_entry(p) and str(p.get("id") or "") not in deleted_ids
    ]
    status_by_id = {p["id"]: _mp_project_status(storage, p) for p in all_products}

    now = None
    from datetime import datetime

    now = datetime.now()
    updated_this_week = 0
    for product in all_products:
        parsed = _mp_parse_dt(product.get("updated_at"))
        if parsed and (now - parsed.replace(tzinfo=None)).days <= 7:
            updated_this_week += 1

    in_progress = sum(1 for s in status_by_id.values() if s["state"] == "progress")
    completed = sum(1 for s in status_by_id.values() if s["state"] == "done")

    st.markdown('<div class="mp-shell">', unsafe_allow_html=True)
    st.markdown(
        '<div class="mp-head">'
        '<div>'
        f'<div class="mp-kicker">{_mp_text("ホーム / マイプロジェクト", "Início / Meus projetos", "Home / My Projects", lang)}</div>'
        f'<h1 class="mp-title">{_mp_text("マイプロジェクト", "Meus projetos", "My Projects", lang)}</h1>'
        f'<div class="mp-sub">{_mp_text("あなたのプロジェクトを管理・追跡・再利用できます", "Gerencie, acompanhe e reutilize seus projetos.", "Manage, track, and reuse your projects.", lang)}</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    top_col, new_col = st.columns([4, 1.35])
    with new_col:
        if st.button("＋ " + _mp_text("新規プロジェクト", "Novo projeto", "New Project", lang), type="primary", use_container_width=True):
            for key in (
                "product_id", "core_text", "core_status", "core_strategy",
                "core_safety", "core_focus", "core_tone",
            ):
                st.session_state.pop(key, None)
            st.session_state["product_info"] = {}
            st.session_state["generated"] = {}
            for key in ("image_prompts", "video_scripts", "ads_sns_items"):
                st.session_state.pop(key, None)
            st.session_state["page"] = "product_input"
            st.rerun()

    st.markdown(
        '<div class="mp-kpi-grid">'
        + _mp_kpi(
            _mp_text("総プロジェクト", "Total de projetos", "Total Projects", lang),
            len(all_products),
            _mp_text("すべてのプロジェクト", "Todos os projetos", "All projects", lang),
            "▣",
        )
        + _mp_kpi(
            _mp_text("進行中", "Em andamento", "In Progress", lang),
            in_progress,
            _mp_text("作成中のプロジェクト", "Projetos em andamento", "Projects being created", lang),
            "▷",
        )
        + _mp_kpi(
            _mp_text("今週更新", "Atualizados na semana", "Updated This Week", lang),
            updated_this_week,
            _mp_text("7日以内に更新", "Atualizados em 7 dias", "Updated within 7 days", lang),
            "□",
        )
        + _mp_kpi(
            _mp_text("完了", "Concluídos", "Completed", lang),
            completed,
            _mp_text("主要生成物がそろったプロジェクト", "Projetos com materiais principais", "Projects with core assets", lang),
            "✓",
        )
        + '</div>',
        unsafe_allow_html=True,
    )

    search_col, status_col, sort_col, view_col = st.columns([3, 1.25, 1.25, .9])
    with search_col:
        query = st.text_input(
            "🔍",
            placeholder=_mp_text("プロジェクトを検索...", "Buscar projetos...", "Search projects...", lang),
            label_visibility="collapsed",
        )
    with status_col:
        status_filter = st.selectbox(
            _mp_text("状態", "Status", "Status", lang),
            ["all", "progress", "draft", "done"],
            format_func=lambda v: {
                "all": _mp_text("すべて", "Todos", "All", lang),
                "progress": _mp_text("進行中", "Em andamento", "In Progress", lang),
                "draft": _mp_text("下書き", "Rascunho", "Draft", lang),
                "done": _mp_text("生成済み", "Gerado", "Generated", lang),
            }[v],
            label_visibility="collapsed",
        )
    with sort_col:
        sort_key = st.selectbox(
            _mp_text("並び順", "Ordenar", "Sort", lang),
            ["updated_desc", "name_asc"],
            format_func=lambda v: {
                "updated_desc": _mp_text("更新日（新しい順）", "Atualização recente", "Newest Updated", lang),
                "name_asc": _mp_text("名前順", "Nome", "Name", lang),
            }[v],
            label_visibility="collapsed",
        )
    with view_col:
        view_mode = st.radio(
            _mp_text("表示", "Visual", "View", lang),
            ["grid", "list"],
            horizontal=True,
            format_func=lambda v: "▦" if v == "grid" else "☰",
            label_visibility="collapsed",
        )

    products = list(all_products)
    if query:
        q = query.lower()
        products = [
            p for p in products
            if q in str(p.get("name", "")).lower()
            or q in str(p.get("category", "")).lower()
            or q in str(p.get("description", "")).lower()
        ]
    if status_filter != "all":
        products = [p for p in products if status_by_id.get(p["id"], {}).get("state") == status_filter]
    if sort_key == "name_asc":
        products.sort(key=lambda p: str(p.get("name") or "").lower())
    else:
        products.sort(key=lambda p: _mp_parse_dt(p.get("updated_at")) or datetime.min, reverse=True)

    main_col, side_col = st.columns([5.15, 1.0], gap="large")
    with main_col:
        if not products:
            st.markdown(
                '<div class="mp-empty">'
                + _mp_text(
                    "表示できるプロジェクトがありません。新規プロジェクトを作成するか、検索条件を変えてください。",
                    "Nenhum projeto para mostrar. Crie um novo projeto ou altere os filtros.",
                    "No projects to show. Create a new project or adjust the filters.",
                    lang,
                )
                + '</div>',
                unsafe_allow_html=True,
            )
        elif view_mode == "grid":
            per_row = 2 if len(products) <= 2 else 3
            for start in range(0, len(products), per_row):
                cols = st.columns(per_row)
                for col, product in zip(cols, products[start:start + per_row]):
                    pid = product["id"]
                    status = status_by_id[pid]
                    with col:
                        st.markdown(_mp_card_html(product, status, lang), unsafe_allow_html=True)
                        if st.button(_mp_text("開く", "Abrir", "Open", lang), key=f"mp_open_{pid}", type="primary", use_container_width=True):
                            _mp_open_project(pid, product, svc, "product_input")
        else:
            for product in products:
                pid = product["id"]
                status = status_by_id[pid]
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2.5, 1, 1.8])
                    with c1:
                        st.markdown(f"**{product.get('name') or '—'}**")
                        st.caption(f"{_mp_text('更新日', 'Atualizado', 'Updated', lang)}: {product.get('updated_at') or '—'}")
                    with c2:
                        st.caption(_mp_text("状態", "Status", "Status", lang))
                        st.markdown(_mp_status_label(status["state"], lang))
                    with c3:
                        if st.button(_mp_text("開く", "Abrir", "Open", lang), key=f"mp_list_open_{pid}", type="primary", use_container_width=True):
                            _mp_open_project(pid, product, svc, "product_input")

        st.caption(
            _mp_text("全", "Total", "Total", lang)
            + f" {len(all_products)} "
            + _mp_text("件中", " | mostrando", "| showing", lang)
            + f" {len(products)} "
            + _mp_text("件を表示", "itens", "items", lang)
        )

    with side_col:
        st.markdown(
            '<div class="mp-panel mp-side-panel">'
            f'<div class="mp-panel-title">{_mp_text("最近のアクティビティ", "Atividade recente", "Recent Activity", lang)}</div>'
            + "".join(
                '<div class="mp-activity">'
                f'<strong>{html.escape(_mp_truncate(p.get("name") or "—", 28))}</strong><br>'
                f'{html.escape(str(p.get("updated_at") or "-"))}'
                '</div>'
                for p in sorted(all_products, key=lambda x: _mp_parse_dt(x.get("updated_at")) or datetime.min, reverse=True)[:5]
            )
            + (
                '<div class="mp-activity">—</div>' if not all_products else ""
            )
            + '</div>',
            unsafe_allow_html=True,
        )
        if all_products:
            st.markdown(
                '<div class="mp-panel mp-side-panel">'
                f'<div class="mp-panel-title">{_mp_text("プロジェクト削除", "Excluir projeto", "Delete Project", lang)}</div>'
                f'<div class="mp-activity">{_mp_text("消したいプロジェクトを選んで削除します。", "Escolha o projeto para excluir.", "Choose a project to delete.", lang)}</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            delete_options = {str(p.get("id") or ""): str(p.get("name") or p.get("id") or "") for p in all_products}
            delete_target = st.selectbox(
                _mp_text("削除対象", "Projeto", "Project", lang),
                list(delete_options.keys()),
                format_func=lambda pid: delete_options.get(pid, pid),
                key="mp_side_delete_target",
                label_visibility="collapsed",
            )
            if st.button(
                "🗑️ " + _mp_text("選択したプロジェクトを削除", "Excluir selecionado", "Delete Selected", lang),
                key="mp_side_delete_run",
                use_container_width=True,
            ):
                _mp_queue_delete(delete_target)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
