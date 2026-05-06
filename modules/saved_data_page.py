import streamlit as st

from .i18n import t, tl
from .permissions import get_current_role, get_current_user, can_perform_action
from .product_input_logic import (
    PRODUCT_FIELD_LABELS_JA,
    PRODUCT_TRANSLATABLE_FIELDS,
    product_prep_status_label,
)
from .project_utils import (
    is_empty_project_entry,
    load_project_session,
    do_delete_project,
    ensure_product_id,
)


def page_saved_data(svc: dict) -> None:
    st.markdown('<div class="section-header">💾 ' + t("nav.saved_data") + '</div>',
                unsafe_allow_html=True)
    is_ja = st.session_state.get("lang", "ja") == "ja"

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💼 " + t("saved_data.products_tab"),
        "📚 " + t("saved_data.cores_tab"),
        "🔍 " + ("診断" if is_ja else "Diagnóstico"),
        "🗃️ " + ("バックアップ" if is_ja else "Backup"),
        "🗑️ " + ("ゴミ箱" if is_ja else "Lixeira"),
    ])

    with tab1:
        all_products = svc["storage"].list_products()

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
                from modules.storage import Storage as _Storage
                _s = _Storage()
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
                        try:
                            from modules.storage import Storage as _Storage
                            _storage = _Storage()
                            has_approved = _storage.has_approved_content(pid)
                        except Exception:
                            has_approved = False
                        st.markdown("---")
                        st.markdown(f"**⚠️ {t('saved_data.confirm_delete_title')}**")
                        st.markdown(t("saved_data.confirm_delete_msg"))
                        if has_approved:
                            st.markdown(
                                f'<div class="cs-warning">⚠️ {t("saved_data.approved_warning")}</div>',
                                unsafe_allow_html=True,
                            )
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

                    # ── 商品準備ステータス（Phase 3 承認ゲート） ──────────────────────
                    if not is_empty:
                        _sd_status = p.get("product_prep_status", "draft")
                        _sd_s_ja, _sd_s_pt = product_prep_status_label(_sd_status)
                        st.markdown("---")
                        st.markdown(
                            f"**{'商品準備ステータス' if is_ja else 'Status da Preparação'}**: "
                            f"{_sd_s_ja if is_ja else _sd_s_pt}"
                        )
                        if _sd_status == "rejected" and p.get("product_prep_review_note"):
                            st.warning(
                                ("**差し戻しコメント**: " if is_ja else "**Comentário de revisão**: ")
                                + p["product_prep_review_note"]
                            )
                        if _sd_status == "approved" and p.get("product_prep_approved_by"):
                            st.caption(
                                ("承認者: " if is_ja else "Aprovado por: ")
                                + p["product_prep_approved_by"]
                                + "  (" + p.get("product_prep_approved_at", "") + ")"
                            )
                        # Admin approve/reject UI (shown only when waiting_review)
                        if get_current_role() == "admin" and _sd_status == "waiting_review":
                            st.markdown("**" + ("承認・差し戻し" if is_ja else "Aprovar / Recusar") + "**")
                            _apv_col1, _apv_col2 = st.columns(2)
                            with _apv_col1:
                                if st.button(
                                    "✅ " + ("承認する" if is_ja else "Aprovar"),
                                    key=f"approve_prep_{pid}", type="primary",
                                    use_container_width=True,
                                ):
                                    svc["storage"].approve_product_prep(pid, get_current_user())
                                    st.success("承認しました。" if is_ja else "Aprovado.")
                                    st.rerun()
                            with _apv_col2:
                                _rej_note = st.text_input(
                                    "差し戻しコメント" if is_ja else "Motivo da recusa",
                                    key=f"rej_note_{pid}",
                                    placeholder="理由を入力..." if is_ja else "Digite o motivo...",
                                )
                                if st.button(
                                    "❌ " + ("差し戻す" if is_ja else "Recusar"),
                                    key=f"reject_prep_{pid}",
                                    use_container_width=True,
                                ):
                                    svc["storage"].reject_product_prep(pid, get_current_user(), _rej_note)
                                    st.success("差し戻しました。" if is_ja else "Recusado.")
                                    st.rerun()

                        # ── 日本語確認用翻訳（Phase 4） ──────────────────────────────────
                        if get_current_role() == "admin":
                            _tr_orig   = p.get("input_original") or {}
                            _tr_ja     = p.get("input_ja") or {}
                            _tr_status = p.get("translation_status", "not_translated")
                            _tr_has_orig = any(str(v).strip() for v in _tr_orig.values() if v)
                            st.markdown("---")
                            st.markdown("**🌐 " + ("日本語確認用翻訳" if is_ja else "Tradução para revisão") + "**")

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

                            # 翻訳ボタン（管理者のみ）
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
        from modules.storage import Storage as _StorageDx
        _sdx = _StorageDx()
        try:
            dx = _sdx.get_diagnostics()
        except Exception as _dxe:
            st.error(f"診断情報の取得に失敗しました: {_dxe}")
            dx = {}

        if dx:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("📦 " + ("プロジェクト数" if is_ja else "Projetos"), dx.get("total_projects", 0))
            with c2:
                st.metric("✅ " + ("正常" if is_ja else "Normais"), dx.get("normal_projects", 0))
            with c3:
                st.metric("⚠️ " + ("空" if is_ja else "Vazios"), dx.get("empty_projects", 0))
            with c4:
                st.metric("🗑️ " + ("ゴミ箱" if is_ja else "Lixeira"), dx.get("trash_count", 0))

            c5, c6 = st.columns(2)
            with c5:
                st.metric("🗃️ " + ("バックアップ数" if is_ja else "Backups"), dx.get("backup_count", 0))
            with c6:
                last_bk = dx.get("last_backup_at") or ("—" if is_ja else "None")
                st.metric("🕐 " + ("最終バックアップ" if is_ja else "Último Backup"), last_bk)

            st.markdown("---")
            st.markdown("**" + ("読み込み対象フォルダ" if is_ja else "Diretório de dados") + "**")
            st.code(dx.get("data_dir", ""))

            counts = dx.get("dir_file_counts", {})
            if counts:
                st.markdown("**" + ("フォルダ別ファイル数" if is_ja else "Arquivos por pasta") + "**")
                rows = "\n".join(f"- `{k}/` : {v}件" for k, v in sorted(counts.items()))
                st.markdown(rows)

            errors = dx.get("error_content_files", [])
            if errors:
                st.markdown("---")
                st.markdown("**⚠️ " + ("APIエラー文が含まれる可能性のあるファイル（要確認）" if is_ja
                             else "Arquivos com possível erro de API (verificar)") + "**")
                for ef in errors:
                    st.markdown(f"- `{ef['file']}` — 商品名: {ef['name']} — パターン: `{ef['pattern']}`")
                st.caption("自動削除・上書きはしません。手動で確認してください。" if is_ja
                           else "Nenhuma ação automática. Verifique manualmente.")
            else:
                st.success("APIエラー文を含むファイルは検出されませんでした。" if is_ja
                           else "Nenhum arquivo com erro de API detectado.")

    # ── Tab 4: バックアップ ────────────────────────────────────────────────────
    with tab4:

        # ── セクション1: 全保存データをバックアップ ──────────────────────────
        st.markdown("### 🗃️ " + ("全保存データをバックアップ" if is_ja else "Backup de todos os dados"))

        # バックアップ対象の統計情報を取得（常に表示）
        try:
            from modules.storage import Storage as _BkStorage
            _bk_s = _BkStorage()
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
                        from modules.storage import Storage as _BkStorage2
                        _bk_s2 = _BkStorage2()
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
                        from modules.storage import Storage as _RestoreStorage
                        _rst_s = _RestoreStorage()
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
            from modules.storage import Storage as _ListBkStorage
            _lbk_s = _ListBkStorage()
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
        from modules.storage import Storage as _StorageTr
        _str = _StorageTr()
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
