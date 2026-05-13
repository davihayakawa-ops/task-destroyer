import json
import streamlit as st

from .i18n import t, tl
from .permissions import can_perform_action
from .project_utils import is_empty_project_entry, load_project_session, status_badge


# ── Page: New Dashboard (Phase 1 — dummy data) ────────────────────────────────

_ND_CSS = """
<style>
/* ════════════════════════════════════════════════════════════════
   NEW DASHBOARD  — nd- prefix  (isolated from existing cs- styles)
   ════════════════════════════════════════════════════════════════ */

/* ── Header ──────────────────────────────────────────────────── */
.nd-header {
    background: linear-gradient(135deg,#0a0a0a 0%,#0d1117 60%,#071207 100%);
    border:1px solid #1a2e1a; border-radius:14px; padding:22px 28px;
    margin-bottom:22px; position:relative; overflow:hidden;
}
.nd-header::before {
    content:''; position:absolute; top:0;left:0;right:0; height:1px;
    background:linear-gradient(90deg,transparent,#22c55e55,transparent);
}
.nd-header::after {
    content:''; position:absolute; bottom:0;right:0;
    width:240px; height:120px;
    background:radial-gradient(ellipse at 80% 80%,#22c55e08,transparent 70%);
    pointer-events:none;
}
.nd-header-eyebrow {
    font-size:.62rem; color:#374151; letter-spacing:.18em;
    text-transform:uppercase; font-weight:700; margin-bottom:8px;
}
.nd-header-title {
    font-size:1.65rem; font-weight:900; color:#f0f0f0;
    letter-spacing:-.03em; line-height:1.1; margin-bottom:5px;
}
.nd-header-sub {
    font-size:.75rem; color:#4b5563; letter-spacing:.06em;
}
.nd-status-dot {
    display:inline-block; width:6px; height:6px; background:#22c55e;
    border-radius:50%; margin-right:5px; box-shadow:0 0 7px #22c55e;
    animation:nd-blink 2.4s ease-in-out infinite;
}
@keyframes nd-blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.nd-badge-sys {
    display:inline-block; background:#052e0f; border:1px solid #22c55e33;
    color:#22c55e; font-size:.62rem; font-weight:700; padding:2px 8px;
    border-radius:3px; letter-spacing:.14em; text-transform:uppercase;
}
.nd-credit-wrap { text-align:right; }
.nd-credit-val { font-size:.82rem; color:#22c55e; font-weight:700; }
.nd-credit-label { font-size:.62rem; color:#374151; text-transform:uppercase;
    letter-spacing:.1em; margin-top:2px; }
.nd-credit-bar { background:#0f1f0f; border-radius:2px; height:3px;
    margin:5px 0 0 auto; width:110px; overflow:hidden; }
.nd-credit-fill { background:linear-gradient(90deg,#22c55e,#16a34a);
    height:100%; border-radius:2px; box-shadow:0 0 5px #22c55e55; }

/* ── KPI Cards ───────────────────────────────────────────────── */
.nd-kpi {
    background:#0d0d0d; border:1px solid #1e1e1e; border-radius:11px;
    padding:18px 20px; position:relative; overflow:hidden;
    transition:border-color .2s;
}
.nd-kpi:hover { border-color:#22c55e33; }
.nd-kpi::after {
    content:''; position:absolute; bottom:0;left:0;right:0; height:2px;
    background:linear-gradient(90deg,transparent,var(--ac,#22c55e),transparent);
    opacity:.35;
}
.nd-kpi-icon { font-size:1.3rem; margin-bottom:8px; opacity:.8; }
.nd-kpi-val {
    font-size:2rem; font-weight:900; color:#f0f0f0;
    letter-spacing:-.04em; line-height:1; margin-bottom:4px;
}
.nd-kpi-lbl { font-size:.68rem; color:#4b5563; text-transform:uppercase;
    letter-spacing:.09em; font-weight:600; }
.nd-kpi-delta { font-size:.68rem; margin-top:7px; }
.nd-up { color:#22c55e; } .nd-dn { color:#ef4444; }
.nd-nt { color:#4b5563; }

/* ── Section label ───────────────────────────────────────────── */
.nd-sec-lbl {
    font-size:.65rem; color:#374151; text-transform:uppercase;
    letter-spacing:.14em; font-weight:700; margin-bottom:14px;
    padding-bottom:8px; border-bottom:1px solid #141414;
}

/* ── Content Cards ───────────────────────────────────────────── */
.nd-card {
    background:#0d0d0d; border:1px solid #1e1e1e; border-radius:12px;
    padding:18px 20px; margin-bottom:14px;
    transition:border-color .2s,box-shadow .2s;
}
.nd-card:hover { border-color:#22c55e22; box-shadow:0 0 18px rgba(34,197,94,.04); }
.nd-card-hd {
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:13px; gap:10px;
}
.nd-card-ttl {
    font-size:.88rem; font-weight:700; color:#e8e8e8;
    display:flex; align-items:center; gap:8px;
}
.nd-card-meta { display:flex; align-items:center; gap:6px; flex-shrink:0; }
.nd-preview {
    background:#080808; border:1px solid #0f0f0f; border-radius:8px;
    padding:12px 14px; font-size:.77rem; color:#4b5563;
    line-height:1.8; min-height:72px; white-space:pre-wrap;
    word-break:break-word; font-family:'SF Mono','Monaco',monospace;
}
.nd-preview.filled { color:#b0b0b0; font-family:-apple-system,sans-serif; }
.nd-preview.code { color:#7dd3fc; font-family:'SF Mono','Monaco',monospace; }

/* ── Badges ──────────────────────────────────────────────────── */
.nd-b {
    display:inline-block; font-size:.62rem; font-weight:700;
    padding:2px 7px; border-radius:3px; letter-spacing:.1em;
    text-transform:uppercase; white-space:nowrap;
}
.nd-b-ok  { background:#052e0f; color:#22c55e; border:1px solid #22c55e33; }
.nd-b-ai  { background:#0a0a1e; color:#818cf8; border:1px solid #818cf833; }
.nd-b-pnd { background:#1a1500; color:#f59e0b; border:1px solid #f59e0b33; }
.nd-b-rev { background:#1a0a00; color:#f97316; border:1px solid #f9731633; }
.nd-b-dft { background:#111;    color:#4b5563; border:1px solid #1e1e1e; }
.nd-b-tag { background:#111; color:#6b7280; border:1px solid #1a1a1a;
    font-size:.6rem; }

/* ── Project Table ───────────────────────────────────────────── */
.nd-tbl {
    width:100%; border-collapse:collapse; font-size:.8rem;
    margin-top:6px;
}
.nd-tbl th {
    text-align:left; font-size:.63rem; text-transform:uppercase;
    letter-spacing:.1em; color:#374151; font-weight:700;
    padding:7px 12px; border-bottom:1px solid #1a1a1a;
}
.nd-tbl td { padding:10px 12px; color:#b0b0b0; border-bottom:1px solid #0d0d0d; }
.nd-tbl tr:hover td { background:#0a0a0a; }
.nd-tbl td.name { font-weight:600; color:#e8e8e8; }
.nd-tbl td.date { color:#374151; font-size:.73rem; }
.nd-row-action {
    display:inline-block; background:#141414; border:1px solid #1e1e1e;
    color:#6b7280; font-size:.62rem; font-weight:600; padding:2px 7px;
    border-radius:4px; cursor:pointer; text-decoration:none;
    letter-spacing:.05em; transition:all .15s;
}
.nd-row-action:hover { border-color:#22c55e55; color:#22c55e; }

/* ── Export Tiles ────────────────────────────────────────────── */
.nd-ex-tile {
    background:#0d0d0d; border:1px solid #1e1e1e; border-radius:11px;
    padding:16px 18px; margin-bottom:10px;
    display:flex; align-items:center; gap:14px;
    transition:all .15s;
}
.nd-ex-tile:hover { border-color:#22c55e33; background:#0a120a; }
.nd-ex-tile.soon { opacity:.5; cursor:not-allowed; }
.nd-ex-ico { font-size:1.5rem; min-width:34px; text-align:center; }
.nd-ex-ttl { font-size:.85rem; font-weight:600; color:#e8e8e8; }
.nd-ex-dsc { font-size:.72rem; color:#4b5563; margin-top:2px; }
.nd-ex-badge {
    margin-left:auto; font-size:.6rem; background:#111;
    border:1px solid #1e1e1e; color:#374151; padding:2px 7px;
    border-radius:3px; white-space:nowrap; font-weight:600;
    text-transform:uppercase; letter-spacing:.09em;
}
.nd-ex-badge.live { background:#052e0f; border-color:#22c55e33; color:#22c55e; }

/* ── Sidebar additions ───────────────────────────────────────── */
.nd-sidebar-sec {
    font-size:.58rem; color:#2a2a2a; text-transform:uppercase;
    letter-spacing:.16em; font-weight:700; padding:10px 4px 2px;
    margin-top:2px;
}
.nd-sidebar-footer {
    font-size:.68rem; color:#374151; padding:10px 4px 0;
    border-top:1px solid #111; margin-top:6px; line-height:1.8;
}

/* ── Usage bar (sidebar) ─────────────────────────────────────── */
.nd-use-bar { background:#0d0d0d; border-radius:2px; height:3px;
    margin:4px 0; overflow:hidden; }
.nd-use-fill { background:linear-gradient(90deg,#22c55e,#16a34a);
    height:100%; border-radius:2px; box-shadow:0 0 4px #22c55e66; }

/* ── Misc ────────────────────────────────────────────────────── */
.nd-divider { border:none; border-top:1px solid #141414; margin:20px 0; }
.nd-empty { text-align:center; padding:36px 20px;
    color:#374151; font-size:.82rem; }
.nd-scroll { max-height:400px; overflow-y:auto; }
</style>
"""

_ND_BADGE_HTML = {
    "ai_generated": '<span class="nd-b nd-b-ai">⚡ 生成済み</span>',
    "draft":        '<span class="nd-b nd-b-dft">○ 未生成</span>',
}


def page_new_dashboard(svc: dict) -> None:
    """Enterprise dashboard — Phase 2 (real data connected)."""
    import html as _html

    # ── Inject CSS ───────────────────────────────────────────────────────────────
    st.markdown(_ND_CSS, unsafe_allow_html=True)

    # ── Real data ────────────────────────────────────────────────────────────────
    _is_ja       = st.session_state.get("lang", "ja") == "ja"
    _gen         = st.session_state.get("generated", {})
    _pid         = st.session_state.get("product_id", "")
    _pinfo       = st.session_state.get("product_info", {})
    _product_name = _pinfo.get("name") or ("商品未選択" if _is_ja else "No product selected")
    _has_product  = bool(_pinfo.get("name") or _pinfo.get("product_url"))
    _has_core     = bool(st.session_state.get("core_text"))

    # Shopify: 9 sections → combined text
    _SHOPIFY_KEYS = [
        "shopify_common_css", "shopify_hero_section_code", "shopify_about_section_code",
        "shopify_problem_section_code", "shopify_features_section_code",
        "shopify_usage_scene_section_code", "shopify_comparison_section_code",
        "shopify_faq_section_code", "shopify_cta_section_code",
    ]
    _shopify_text = "\n\n".join(_gen[k] for k in _SHOPIFY_KEYS if _gen.get(k))

    def _content(key):
        return _shopify_text if key == "shopify_code" else str(_gen.get(key) or "")

    # Content spec: key / icon / title / tag / regen_page
    _SPECS = [
        ("product_page",  "📄", "商品ページ文章",         "TEXT", "product_page"),
        ("shopify_code",  "🛒", "Shopify Custom Liquid",   "CODE", "product_page"),
        ("image_prompt",  "🖼️", "画像プロンプト",          "EN",   "image_prompt"),
        ("video_script",  "🎬", "動画台本",               "JA",   "video_script"),
        ("ads_sns",       "📣", "広告 / SNS",             "JA",   "ads_sns"),
    ]

    # KPI counts (real)
    try:
        _all_projs = [p for p in svc["storage"].list_products() if not is_empty_project_entry(p)]
    except Exception:
        _all_projs = []
    _gen_count      = sum(1 for key, *_ in _SPECS if _content(key).strip())
    _remaining_count = max(len(_SPECS) - _gen_count, 0)

    _product_name = _pinfo.get("name") or ("商品未選択" if _is_ja else "No product selected")

    # ── Header ───────────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="nd-header">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;">
            <div>
              <div class="nd-header-eyebrow">TASK DESTROYER v2.0 ・ COMMERCE MODE ・ IMPERIAL DATA LINK</div>
              <div class="nd-header-title">⚡ {'ダッシュボード' if _is_ja else 'Painel'}</div>
              <div class="nd-header-sub" style="margin-top:6px;">
                <span class="nd-status-dot"></span>
                <span class="nd-badge-sys">SYSTEM ONLINE</span>
                &nbsp;&nbsp;{'現在のプロジェクト' if _is_ja else 'Projeto atual'}:
                <span style="color:#e8e8e8;font-weight:600;">{_product_name}</span>
              </div>
            </div>
            <div class="nd-credit-wrap">
              <div class="nd-credit-val">730 <span style="font-size:.7rem;font-weight:400;color:#374151;">/ 1,000</span></div>
              <div class="nd-credit-label">{'API Calls 残量' if _is_ja else 'API Calls restantes'}</div>
              <div class="nd-credit-bar"><div class="nd-credit-fill" style="width:73%;"></div></div>
              <div style="font-size:.6rem;color:#1e3a1e;margin-top:4px;letter-spacing:.1em;">▓▓▓▓▓▓▓░░░ 73% REMAINING</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── KPI Cards (real counts) ───────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    _kpis = [
        ("📦", str(len(_all_projs)), "総プロジェクト" if _is_ja else "Projetos",    "#22c55e"),
        ("⚡", str(_gen_count),      "生成コンテンツ" if _is_ja else "Conteúdos",   "#818cf8"),
        ("🧠", "1" if _has_core else "0", "Core" if _is_ja else "Core", "#22c55e"),
        ("📝", str(_remaining_count), "未生成" if _is_ja else "Pendentes", "#f59e0b"),
    ]
    for col, (ico, val, lbl, color) in zip([k1, k2, k3, k4], _kpis):
        with col:
            st.markdown(
                f'<div class="nd-kpi" style="--ac:{color};">'
                f'<div class="nd-kpi-icon">{ico}</div>'
                f'<div class="nd-kpi-val">{val}</div>'
                f'<div class="nd-kpi-lbl">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="nd-divider">', unsafe_allow_html=True)

    # ── Main Tabs ─────────────────────────────────────────────────────────────────
    tab_gen, tab_proj, tab_export = st.tabs([
        "⚡  " + ("生成コンテンツ" if _is_ja else "Conteúdos"),
        "📁  " + ("プロジェクト一覧" if _is_ja else "Projetos"),
        "📤  " + ("エクスポート＆連携" if _is_ja else "Exportar"),
    ])

    # ════════════════════════════════════════════════
    # Tab 1: 生成コンテンツ (real data)
    # ════════════════════════════════════════════════
    with tab_gen:
        proj_label = (
            f"生成コンテンツ — {_product_name}" + ("" if _has_product else " （商品未設定）")
            if _is_ja else
            f"Conteúdos — {_product_name}" + ("" if _has_product else " (produto não definido)")
        )
        st.markdown(f'<div class="nd-sec-lbl">{_html.escape(proj_label)}</div>',
                    unsafe_allow_html=True)

        # Language toggle
        lc1, lc2, _ = st.columns([1, 1, 5])
        with lc1:
            if st.button("🇯🇵 JA", key="nd_lang_ja", use_container_width=True,
                         type="primary" if _is_ja else "secondary"):
                st.session_state["lang"] = "ja"
                st.rerun()
        with lc2:
            if st.button("🇧🇷 PT", key="nd_lang_pt", use_container_width=True,
                         type="primary" if not _is_ja else "secondary"):
                st.session_state["lang"] = "pt"
                st.rerun()

        # Missing prerequisite warnings
        if not _has_product:
            st.markdown(
                '<div class="cs-warning" style="margin:12px 0;">⚠️ ' + (
                    '商品情報が未入力です。まず「商品入力」ページで商品を設定してください。'
                    if _is_ja else
                    'Informações do produto não preenchidas. Configure o produto na página "Entrada do Produto".'
                ) + '</div>',
                unsafe_allow_html=True,
            )
        elif not _has_core:
            st.markdown(
                '<div class="cs-info" style="margin:12px 0;">💡 ' + (
                    'Coreがまだ生成されていません。「Core生成・編集」でCoreを生成すると各コンテンツを生成できます。'
                    if _is_ja else
                    'Core não gerado ainda. Gere o Core em "Gerar/Editar Core" para gerar cada conteúdo.'
                ) + '</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        for key, icon, title, tag, regen_page in _SPECS:
            text       = _content(key)
            has_text   = bool(text.strip())
            badge_html = _ND_BADGE_HTML["ai_generated"] if has_text else _ND_BADGE_HTML["draft"]

            # Preview text (HTML-escaped so raw content is safe)
            if has_text:
                preview_raw = text[:320] + ("..." if len(text) > 320 else "")
                preview_escaped = _html.escape(preview_raw)
                preview_cls = "code" if key == "shopify_code" else "filled"
                word_count  = (
                    f"{sum(1 for k in _SHOPIFY_KEYS if _gen.get(k))} " + ("セクション" if _is_ja else "seções")
                    if key == "shopify_code"
                    else f"{len(text.split())} words"
                )
            else:
                preview_escaped = "（未生成）— " + ("右の「再生成」ボタンで生成してください" if _is_ja else 'Clique em "Gerar" para criar')
                preview_cls = ""
                word_count  = "未生成" if _is_ja else "Não gerado"

            st.markdown(
                f"""
                <div class="nd-card">
                  <div class="nd-card-hd">
                    <div class="nd-card-ttl">
                      {icon} {_html.escape(title)}
                      <span class="nd-b nd-b-tag">{tag}</span>
                    </div>
                    <div class="nd-card-meta">
                      <span style="font-size:.68rem;color:#374151;">{word_count}</span>
                      {badge_html}
                    </div>
                  </div>
                  <div class="nd-preview {preview_cls}">{preview_escaped}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ── Action buttons ────────────────────────────────────────────────
            ab1, ab2, ab3, _ = st.columns([1, 1, 1, 4])

            # Copy: toggle st.code() below card (Streamlit built-in copy button)
            with ab1:
                _copy_key = f"nd_copy_open_{key}"
                if st.button("📋 " + ("コピー" if _is_ja else "Copiar"), key=f"nd_copy_{key}",
                             disabled=not has_text, use_container_width=True):
                    st.session_state[_copy_key] = not st.session_state.get(_copy_key, False)

            # Download
            with ab2:
                _fname = f"{key}_{_product_name}.txt"
                st.download_button(
                    "⬇️ DL", data=(text or " ").encode("utf-8"),
                    file_name=_fname, mime="text/plain",
                    key=f"nd_dl_{key}", disabled=not has_text or not can_perform_action("export"),
                    use_container_width=True,
                )

            # Regenerate → navigate to generation page
            with ab3:
                if can_perform_action("regenerate") and st.button("✨ " + ("再生成" if _is_ja else "Gerar"), key=f"nd_regen_{key}",
                             use_container_width=True):
                    if not can_perform_action("regenerate"):
                        st.warning("この操作は許可されていません。" if _is_ja else "Operação não permitida.")
                        st.rerun()
                    st.session_state["page"] = regen_page
                    st.rerun()

            # Show copy code block when toggled
            if st.session_state.get(f"nd_copy_open_{key}") and has_text:
                lang_hint = "html" if key == "shopify_code" else "text"
                st.code(text, language=lang_hint)

            st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════
    # Tab 2: プロジェクト一覧 (real data)
    # ════════════════════════════════════════════════
    with tab_proj:
        _proj_count = len(_all_projs)
        st.markdown(
            f'<div class="nd-sec-lbl">' + (f"保存済みプロジェクト — {_proj_count} 件" if _is_ja else f"Projetos salvos — {_proj_count}") + '</div>',
            unsafe_allow_html=True,
        )

        search_q = st.text_input("🔍", placeholder="商品名で検索..." if _is_ja else "Buscar por nome...",
                                 label_visibility="collapsed", key="nd_proj_search")

        _projs_filtered = _all_projs
        if search_q:
            _projs_filtered = [p for p in _all_projs
                               if search_q.lower() in p.get("name","").lower()]

        if not _projs_filtered:
            _empty_msg = (
                ("🔍 該当するプロジェクトが見つかりません" if _is_ja else "🔍 Nenhum projeto encontrado") if search_q else
                ("💡 保存済みプロジェクトがありません。商品情報を入力して保存してください。" if _is_ja else "💡 Nenhum projeto salvo. Insira as informações do produto e salve.")
            )
            st.markdown(f'<div class="nd-empty">{_empty_msg}</div>', unsafe_allow_html=True)
        else:
            # Table header (HTML)
            st.markdown(
                '<div class="nd-scroll"><table class="nd-tbl"><thead><tr>'
                + ('<th>プロジェクト名</th><th>最終更新</th><th>ステータス</th><th style="width:160px">操作</th>'
                   if _is_ja else
                   '<th>Nome</th><th>Atualizado</th><th>Status</th><th style="width:160px">Ação</th>')
                + '</tr></thead></table></div>',
                unsafe_allow_html=True,
            )
            # Rows: use Streamlit columns for interactive buttons
            for p in _projs_filtered[:10]:
                pname = p.get("name") or "—"
                pupdated = p.get("updated_at", "-")
                ppid = p["id"]
                row_status = "draft"
                badge = _ND_BADGE_HTML.get(row_status, _ND_BADGE_HTML["draft"])

                tc1, tc2, tc3, tc4, tc5 = st.columns([3, 2, 1.5, 1, 1])
                with tc1:
                    st.markdown(
                        f'<div style="padding:8px 0;font-weight:600;color:#e8e8e8;'
                        f'font-size:.82rem;">{_html.escape(pname)}</div>',
                        unsafe_allow_html=True,
                    )
                with tc2:
                    st.markdown(
                        f'<div style="padding:8px 0;color:#374151;font-size:.73rem;">{pupdated}</div>',
                        unsafe_allow_html=True,
                    )
                with tc3:
                    st.markdown(
                        f'<div style="padding:8px 0;">{badge}</div>',
                        unsafe_allow_html=True,
                    )
                with tc4:
                    if st.button("📂 " + ("読込" if _is_ja else "Carregar"), key=f"nd_load_{ppid}", use_container_width=True):
                        load_project_session(ppid, p, svc)
                        st.success(f"'{pname}' " + ("を読み込みました" if _is_ja else "carregado"))
                        st.rerun()
                with tc5:
                    if can_perform_action("delete_project") and st.button("🗑 " + ("削除" if _is_ja else "Excluir"), key=f"nd_del_{ppid}", use_container_width=True):
                        if not can_perform_action("delete_project"):
                            st.warning("この操作は許可されていません。" if _is_ja else "Operação não permitida.")
                            st.rerun()
                        st.session_state["page"] = "saved_data"
                        st.session_state["confirm_delete_id"] = ppid
                        st.session_state["confirm_delete_file_path"] = p.get("file_path","")
                        st.session_state["confirm_delete_name"] = pname
                        st.rerun()

                st.markdown('<hr style="border:none;border-top:1px solid #0d0d0d;margin:0;">',
                            unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        pc1, pc2, pc3 = st.columns([1, 1, 4])
        with pc1:
            if st.button("📁 " + ("保存データ管理" if _is_ja else "Gestão de dados"), key="nd_go_saved", use_container_width=True):
                st.session_state["page"] = "saved_data"
                st.rerun()
        with pc2:
            if st.button("🧹 " + ("空データ整理" if _is_ja else "Limpar vazios"), key="nd_cleanup_empty", use_container_width=True):
                st.session_state["page"] = "saved_data"
                st.rerun()

    # ════════════════════════════════════════════════
    # Tab 3: エクスポート＆連携 (real downloads connected)
    # ════════════════════════════════════════════════
    with tab_export:
        _can_export = can_perform_action("export")
        if not _can_export:
            st.warning("出力操作は管理者のみ利用できます。" if _is_ja else "Operações de exportação são restritas a administradores.")
        st.markdown('<div class="nd-sec-lbl">' + ("エクスポート＆連携パネル" if _is_ja else "Painel de Exportação") + '</div>',
                    unsafe_allow_html=True)

        # Build combined text bundle for bulk download
        _all_text_parts = []
        for key, icon, title, *_ in _SPECS:
            txt = _content(key)
            if txt.strip():
                _all_text_parts.append(f"{'='*60}\n{title}\n{'='*60}\n{txt}")
        _all_text_bundle = "\n\n".join(_all_text_parts) or ("（生成済みコンテンツがありません）" if _is_ja else "(Nenhum conteúdo gerado)")
        _all_json_bundle = json.dumps(
            {k: _content(k) for k, *_ in _SPECS if _content(k).strip()},
            ensure_ascii=False, indent=2
        )

        _exports = [
            # (ico, title, desc, badge, is_soon, widget_fn)
            ("📄", "テキスト一括ダウンロード" if _is_ja else "Download em texto",
                   "全コンテンツを .txt でまとめてDL" if _is_ja else "Baixar todos os conteúdos em .txt", "live", False, "dl_txt"),
            ("📊", "JSON エクスポート",
                   "全データを JSON 形式でダウンロード" if _is_ja else "Baixar todos os dados em JSON", "live", False, "dl_json"),
            ("🛒", "Shopify セクション表示" if _is_ja else "Ver Seções Shopify",
                   "Shopifyコードを確認・コピー" if _is_ja else "Verificar e copiar código Shopify", "live", False, "shopify"),
            ("📋", "出力センターへ" if _is_ja else "Centro de Exportação",
                   "生成済みコンテンツの出力・管理" if _is_ja else "Gerenciar conteúdos gerados", "live", False, "output"),
            ("📁", "Google Drive に保存" if _is_ja else "Salvar no Google Drive",
                   "Google Driveへ自動アップロード" if _is_ja else "Upload automático ao Google Drive", "soon", True,  None),
            ("📝", "Word Docs に出力" if _is_ja else "Exportar para Word",
                   ".docx 形式で書き出し" if _is_ja else "Exportar em formato .docx", "soon", True,  None),
            ("📱", "SNS 投稿予約" if _is_ja else "Agendamento SNS",
                   "Buffer / Hootsuite 連携（準備中）" if _is_ja else "Integração Buffer/Hootsuite (em breve)", "soon", True,  None),
            ("✉️", "メール送信" if _is_ja else "Enviar por email",
                   "チームへコンテンツをメール送信" if _is_ja else "Enviar conteúdo ao time por email", "soon", True,  None),
        ]

        ex_col1, ex_col2 = st.columns(2)
        for i, (ico, ttl, dsc, badge_type, is_soon, wfn) in enumerate(_exports):
            badge_cls = "live" if badge_type == "live" else ""
            badge_lbl = "READY" if badge_type == "live" else "COMING SOON"
            tile_cls  = "nd-ex-tile soon" if is_soon else "nd-ex-tile"
            with (ex_col1 if i % 2 == 0 else ex_col2):
                st.markdown(
                    f'<div class="{tile_cls}">'
                    f'<div class="nd-ex-ico">{ico}</div>'
                    f'<div><div class="nd-ex-ttl">{ttl}</div>'
                    f'<div class="nd-ex-dsc">{dsc}</div></div>'
                    f'<div class="nd-ex-badge {badge_cls}">{badge_lbl}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if not is_soon:
                    if wfn == "dl_txt":
                        st.download_button(
                            "⬇️ " + ("一括ダウンロード (.txt)" if _is_ja else "Download em .txt"),
                            data=_all_text_bundle.encode("utf-8"),
                            file_name=f"task_destroyer_{_product_name}_all.txt",
                            mime="text/plain",
                            key=f"nd_ex_{i}",
                            use_container_width=True,
                            disabled=not _can_export,
                        )
                    elif wfn == "dl_json":
                        st.download_button(
                            "⬇️ " + ("JSON ダウンロード" if _is_ja else "Download JSON"),
                            data=_all_json_bundle.encode("utf-8"),
                            file_name=f"task_destroyer_{_product_name}.json",
                            mime="application/json",
                            key=f"nd_ex_{i}",
                            use_container_width=True,
                            disabled=not _can_export,
                        )
                    elif wfn == "shopify":
                        if _can_export and st.button("🛒 " + ("Shopifyページへ" if _is_ja else "Ver Shopify"), key=f"nd_ex_{i}",
                                     use_container_width=True):
                            st.session_state["page"] = "product_page"
                            st.rerun()
                    elif wfn == "output":
                        if _can_export and st.button("📤 " + ("出力センターへ" if _is_ja else "Centro de exportação"), key=f"nd_ex_{i}",
                                     use_container_width=True):
                            if not can_perform_action("export"):
                                st.warning("この操作は許可されていません。" if _is_ja else "Operação não permitida.")
                                st.rerun()
                            st.session_state["page"] = "output"
                            st.rerun()

        st.markdown('<hr class="nd-divider">', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:.7rem;color:#1e3a1e;letter-spacing:.15em;text-align:center;">'
            '// TASK DESTROYER EXPORT TERMINAL — ALL SYSTEMS NOMINAL //'
            '</div>',
            unsafe_allow_html=True,
        )
