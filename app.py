import streamlit as st
import json
import os
import uuid
import zipfile
import io
import base64
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
os.chdir(ROOT)

from modules.llm_client import LLMClient
from modules.storage import Storage
from modules.core_engine import CoreEngine
from modules.core_importer import CoreImporter
from modules.translator import Translator
from modules.japanese_refiner import JapaneseRefiner
from modules.generator_engine import GeneratorEngine
from modules.exporter import Exporter
from modules.checker import Checker
from modules.bulk_pack_generator import BulkPackGenerator
from modules.mode_registry import list_modes, get_mode
from modules.permissions import filter_nav_items
from modules.product_input_logic import PRODUCT_FIELD_LABELS_JA, PRODUCT_TRANSLATABLE_FIELDS, prepare_product_save_data
from modules.selection_pages import page_ads_sns as render_page_ads_sns, page_image_prompt as render_page_image_prompt, page_video_script as render_page_video_script
from modules.i18n import load_i18n, t, tl, resolve_option_index
from modules.project_utils import (
    STATUS_BADGE_CLASS, STATUS_LABEL_JA, STATUS_LABEL_PT,
    status_badge, ensure_product_id, load_project_session,
    is_empty_project_entry, do_delete_project,
)
from modules.saved_data_page import page_saved_data as _page_saved_data
from modules.dashboard_page import page_new_dashboard as _page_new_dashboard


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Task Destroyer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark theme CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global dark theme ── */
[data-testid="stAppViewContainer"] {
    background-color: #0b0f12;
    background-image:
        linear-gradient(rgba(110,255,170,0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(110,255,170,0.045) 1px, transparent 1px),
        radial-gradient(ellipse at 12% 0%,   rgba(34,197,94,0.07) 0%, transparent 42%),
        radial-gradient(ellipse at 88% 100%, rgba(34,197,94,0.04) 0%, transparent 38%);
    background-size: 32px 32px, 32px 32px, 100% 100%, 100% 100%;
    color: #e8e8e8;
}
[data-testid="stSidebar"] {
    background-color: #080b0e;
    background-image:
        linear-gradient(rgba(110,255,170,0.022) 1px, transparent 1px),
        linear-gradient(90deg, rgba(110,255,170,0.022) 1px, transparent 1px);
    background-size: 24px 24px;
    border-right: 1px solid rgba(34,197,94,0.14);
}
[data-testid="stSidebar"] * {
    color: #e8e8e8 !important;
}

/* ── Header bar ── */
.cs-header {
    padding: 8px 0 16px 0;
    border-bottom: 1px solid #1e1e1e;
    margin-bottom: 20px;
    background: transparent;
}
.cs-logo-img {
    width: 160px;
    height: auto;
    display: block;
    margin: 0 auto;
    background: transparent;
    border: none;
    box-shadow: none;
}

/* ── Buttons ── */
.stButton > button {
    background: #1a1a1a;
    color: #e8e8e8;
    border: 1px solid #333;
    border-radius: 8px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #222;
    border-color: #22c55e;
    color: #22c55e;
}

/* ── Primary button ── */
.btn-primary > button {
    background: #16a34a !important;
    color: white !important;
    border: none !important;
    font-weight: 600;
}
.btn-primary > button:hover {
    background: #22c55e !important;
    color: white !important;
}

/* ── Cards ── */
.cs-card {
    background: #141414;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.cs-card-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.cs-card-title span.icon {
    font-size: 1rem;
}

/* ── Status badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-success    { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.badge-draft      { background: #1c1c1c; color: #9ca3af; border: 1px solid #374151; }
.badge-ai         { background: #0c1a2e; color: #60a5fa; border: 1px solid #1e40af; }
.badge-generated  { background: #052e16; color: #4ade80; border: 1px solid #166534; }

/* ── Section header ── */
.section-header {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f0f0f0;
    padding-bottom: 10px;
    margin-bottom: 8px;
    border-bottom: 1px solid transparent;
    border-image: linear-gradient(
        90deg,
        rgba(34,197,94,0.65) 0%,
        rgba(34,197,94,0.18) 35%,
        transparent 70%
    ) 1;
}
.section-sub {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 24px;
}

/* ── Inputs ── */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background: #141414 !important;
    border: 1px solid #1e1e1e !important;
    color: #e8e8e8 !important;
    border-radius: 8px;
}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {
    border-color: #22c55e !important;
    box-shadow: 0 0 0 2px rgba(34,197,94,0.1) !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div {
    background: #141414 !important;
    border: 1px solid #1e1e1e !important;
    color: #e8e8e8 !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    background: transparent;
    color: #6b7280;
    border: none;
    border-bottom: 2px solid transparent;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #22c55e;
    border-bottom-color: #22c55e;
}

/* ── Divider ── */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(34,197,94,0.25) 20%,
        rgba(34,197,94,0.12) 50%,
        rgba(34,197,94,0.06) 75%,
        transparent 100%
    );
    margin: 16px 0;
}

/* ── Sidebar nav items ── */
.nav-item {
    padding: 10px 16px;
    border-radius: 8px;
    cursor: pointer;
    margin-bottom: 4px;
    color: #9ca3af;
    font-size: 0.875rem;
    transition: all 0.2s;
}
.nav-item:hover, .nav-item.active {
    background: #1a1a1a;
    color: #e8e8e8;
}

/* ── Generated content area ── */
.generated-box {
    background: #0a0a0a;
    border: 1px solid #1e1e1e;
    border-radius: 8px;
    padding: 16px;
    font-size: 0.875rem;
    line-height: 1.7;
    white-space: pre-wrap;
    color: #d1d5db;
}

/* ── Two-column translation ── */
.bilingual-col {
    background: #141414;
    border: 1px solid #1e1e1e;
    border-radius: 8px;
    padding: 16px;
}
.bilingual-label {
    font-size: 0.75rem;
    color: #22c55e;
    font-weight: 600;
    margin-bottom: 8px;
}

/* ── Warning / info boxes ── */
.cs-warning {
    background: #1c1410;
    border: 1px solid #78350f;
    border-radius: 8px;
    padding: 12px 16px;
    color: #fbbf24;
    font-size: 0.875rem;
}
.cs-info {
    background: #0c1a2e;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 12px 16px;
    color: #60a5fa;
    font-size: 0.875rem;
}
.cs-success {
    background: #052e16;
    border: 1px solid #166534;
    border-radius: 8px;
    padding: 12px 16px;
    color: #4ade80;
    font-size: 0.875rem;
}

/* ════════════════════════════════════════════════════════════════
   GRID DESIGN SYSTEM  — gd- additions
   ════════════════════════════════════════════════════════════════ */

/* ── Card glow on hover ── */
.cs-card {
    transition: box-shadow 0.25s, border-color 0.25s;
}
.cs-card:hover {
    border-color: rgba(34,197,94,0.22);
    box-shadow: 0 0 0 1px rgba(34,197,94,0.08),
                0 4px 24px rgba(0,0,0,0.45);
}

/* ── Sidebar header accent ── */
.cs-header {
    border-bottom: 1px solid transparent;
    border-image: linear-gradient(
        90deg,
        rgba(34,197,94,0.5) 0%,
        rgba(34,197,94,0.1) 60%,
        transparent 100%
    ) 1;
}

/* ── Column guide lines for saved-projects / instruction-sheet tables ── */
.ec-proj-table td,
.ec-proj-table th {
    border-right: 1px solid rgba(110,255,170,0.04);
}
.ec-proj-table td:last-child,
.ec-proj-table th:last-child {
    border-right: none;
}
.ins-tbl td,
.ins-tbl th {
    border-right: 1px solid rgba(110,255,170,0.05);
}
.ins-tbl td:last-child,
.ins-tbl th:last-child {
    border-right: none;
}

/* ── Export center divider tiles ── */
.ec-export-tile {
    border-top: 1px solid rgba(110,255,170,0.05);
}
.ec-export-tile:first-of-type {
    border-top: none;
}

/* ── INS / ND cards: subtle inner grid glow on left accent ── */
.ins-card,
.nd-card {
    position: relative;
    overflow: hidden;
}
.ins-card::after,
.nd-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(110,255,170,0.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(110,255,170,0.018) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
    border-radius: inherit;
}

/* ── Main content block: faint top scanning line ── */
[data-testid="stMain"] .block-container {
    background: transparent;
}
[data-testid="stMain"] .block-container::before {
    content: '';
    display: block;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(34,197,94,0.3) 15%,
        rgba(34,197,94,0.08) 50%,
        transparent 100%
    );
    margin-bottom: 4px;
}

/* ── Breadcrumb ── */
.sb-breadcrumb {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.75rem; margin-bottom: 14px;
    padding: 5px 12px;
    background: rgba(34,197,94,0.05);
    border: 1px solid rgba(34,197,94,0.12);
    border-radius: 6px;
}
.sb-bc-group { color: #6b7280; }
.sb-bc-sep   { color: #374151; font-size: 0.7rem; }
.sb-bc-page  { color: #4ade80; font-weight: 600; }

/* ── Sidebar nav mode toggle ── */
.sb-mode-label {
    font-size: 0.68rem; color: #374151;
    text-transform: uppercase; letter-spacing: .08em;
    margin-bottom: 6px;
}

/* ── Sidebar group expander tweaks ── */
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    font-size: 0.8rem !important;
    color: #9ca3af !important;
    font-weight: 600;
    letter-spacing: 0.03em;
    padding: 6px 4px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
    color: #e8e8e8 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    border: none !important;
    background: transparent !important;
    margin-bottom: 2px;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ──────────────────────────────────────────────────────

def init_state():
    defaults = {
        "lang": "ja",
        "i18n": {},
        "mode": "commerce",
        "page": "mode_selection",
        "product_id": "",
        "product_info": {},
        "core_text": "",
        "core_method": "auto",
        "core_status": "draft",
        "external_core_text": "",
        "generated": {},
        "assignee": "",
        "reviewer": "",
        "nav_mode": "simple",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Reload i18n when language changes
    lang = st.session_state["lang"]
    if not st.session_state["i18n"] or st.session_state["i18n"].get("_lang") != lang:
        i18n = load_i18n(lang)
        i18n["_lang"] = lang
        st.session_state["i18n"] = i18n


init_state()

# ── Services (cached per session) ─────────────────────────────────────────────

# Bump this string whenever new methods are added to any service class.
# Changing it invalidates the @st.cache_resource cache on Streamlit Cloud,
# forcing fresh service objects that reflect the latest code.
_SERVICES_VER = "20260504-p4b"


@st.cache_resource
def get_services(_v=_SERVICES_VER):
    llm = LLMClient()
    storage = Storage()
    return {
        "llm": llm,
        "storage": storage,
        "core_engine": CoreEngine(llm),
        "core_importer": CoreImporter(llm),
        "translator": Translator(llm),
        "refiner": JapaneseRefiner(llm),
        "generator": GeneratorEngine(llm),
        "exporter": Exporter(),
        "checker": Checker(llm),
        "bulk": BulkPackGenerator(llm),
    }


svc = get_services()




# ── Sidebar nav data ──────────────────────────────────────────────────────────
# (group_id, label_ja, label_pt, items)
# items: (page_id, label_ja, label_pt, unique_key_suffix)
_NAV_GROUPS = [
    ("home", "🏠 ホーム", "🏠 Início", [
        ("dashboard",       "🏠 ダッシュボード",   "🏠 Painel",          "dash"),
        ("mode_selection",  "🗂️ モード選択",       "🗂️ Seleção de Modo", "mode"),
    ]),
    ("product", "📦 商品", "📦 Produto", [
        ("product_input",   "📦 商品入力",         "📦 Entrada do Produto",  "pi"),
        ("external_core",   "📥 外部Core取り込み", "📥 Importar Core",        "ec"),
    ]),
    ("core", "✨ Core", "✨ Core", [
        ("core_generation", "✨ Core生成・編集",   "✨ Gerar/Editar Core", "cg"),
        ("core_generation", "📚 Coreライブラリ",  "📚 Biblioteca de Cores","cl"),
    ]),
    ("generate", "⚡ 生成", "⚡ Gerar", [
        ("product_page",    "📄 商品ページ",        "📄 Página do Produto",  "pp"),
        ("product_page",    "🛒 Shopifyコード",     "🛒 Código Shopify",     "sh"),
        ("image_prompt",    "🖼️ 画像プロンプト",   "🖼️ Prompts de Imagem", "ip"),
        ("video_script",    "🎬 動画台本",          "🎬 Roteiro de Vídeo",   "vs"),
        ("ads_sns",         "📣 広告・SNS",         "📣 Anúncios/SNS",       "as_"),
        ("bulk_pack",       "🔥 一括生成",          "🔥 Geração em Lote",    "bp"),
    ]),
    ("review", "✅ 確認", "✅ Verificação", [
        ("refinement",      "✍️ 日本語補正・翻訳", "✍️ Refinar/Traduzir",  "rf"),
        ("check",           "✅ チェック",          "✅ Verificação",        "ck"),
    ]),
    ("output", "📤 出力・管理", "📤 Saída / Gestão", [
        ("export_center",     "⚡ 生成＆エクスポート","⚡ Gerar & Exportar",   "exc"),
        ("output",            "📤 出力",              "📤 Exportar",           "out"),
        ("saved_data",        "💾 保存データ",        "💾 Dados Salvos",       "sv"),
        ("instruction_sheet", "📋 制作指示書",        "📋 Ficha de Produção",  "ins"),
    ]),
]

_BREADCRUMB_MAP_JA = {
    "dashboard":        ("🏠 ホーム",      "ダッシュボード"),
    "mode_selection":   ("🏠 ホーム",      "モード選択"),
    "product_input":    ("📦 商品",        "商品入力"),
    "external_core":    ("📦 商品",        "外部Core取り込み"),
    "core_generation":  ("✨ Core",        "Core生成・編集"),
    "product_page":     ("⚡ 生成",        "商品ページ"),
    "image_prompt":     ("⚡ 生成",        "画像プロンプト"),
    "video_script":     ("⚡ 生成",        "動画台本"),
    "ads_sns":          ("⚡ 生成",        "広告・SNS"),
    "bulk_pack":        ("⚡ 生成",        "一括生成"),
    "refinement":       ("✅ 確認",        "日本語補正・翻訳"),
    "check":            ("✅ 確認",        "チェック"),
    "export_center":    ("📤 出力・管理",  "生成＆エクスポート"),
    "output":           ("📤 出力・管理",  "出力"),
    "saved_data":       ("📤 出力・管理",  "保存データ"),
    "instruction_sheet":("📤 出力・管理",  "制作指示書"),
}
_BREADCRUMB_MAP_PT = {
    "dashboard":        ("🏠 Início",       "Painel"),
    "mode_selection":   ("🏠 Início",       "Seleção de Modo"),
    "product_input":    ("📦 Produto",      "Entrada do Produto"),
    "external_core":    ("📦 Produto",      "Importar Core"),
    "core_generation":  ("✨ Core",         "Gerar/Editar Core"),
    "product_page":     ("⚡ Gerar",        "Página do Produto"),
    "image_prompt":     ("⚡ Gerar",        "Prompts de Imagem"),
    "video_script":     ("⚡ Gerar",        "Roteiro de Vídeo"),
    "ads_sns":          ("⚡ Gerar",        "Anúncios/SNS"),
    "bulk_pack":        ("⚡ Gerar",        "Geração em Lote"),
    "refinement":       ("✅ Verificação",  "Refinar/Traduzir"),
    "check":            ("✅ Verificação",  "Verificação"),
    "export_center":    ("📤 Saída/Gestão", "Gerar & Exportar"),
    "output":           ("📤 Saída/Gestão", "Exportar"),
    "saved_data":       ("📤 Saída/Gestão", "Dados Salvos"),
    "instruction_sheet":("📤 Saída/Gestão", "Ficha de Produção"),
}


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────────────
        _logo_path = Path(__file__).parent / "static" / "td_logo.png"
        _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
        st.markdown(
            f'<div class="cs-header">'
            f'<img class="cs-logo-img" src="data:image/png;base64,{_logo_b64}" alt="Task Destroyer">'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Language switcher ─────────────────────────────────────────────
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            if st.button("🇯🇵 日本語", use_container_width=True,
                         type="primary" if st.session_state["lang"] == "ja" else "secondary"):
                st.session_state["lang"] = "ja"
                st.session_state["i18n"] = {}
                st.rerun()
        with lang_col2:
            if st.button("🇧🇷 Português", use_container_width=True,
                         type="primary" if st.session_state["lang"] == "pt" else "secondary"):
                st.session_state["lang"] = "pt"
                st.session_state["i18n"] = {}
                st.rerun()

        st.markdown("---")

        # ── Mode badge ────────────────────────────────────────────────────
        mode = get_mode(st.session_state["mode"])
        lang = st.session_state["lang"]
        is_ja = (lang == "ja")
        mode_name = mode["name_ja"] if is_ja else mode["name_pt"]
        st.markdown(
            f'<div style="font-size:0.75rem;color:#6b7280;margin-bottom:10px;">'
            f'{mode["icon"]} {mode_name}</div>',
            unsafe_allow_html=True,
        )

        # ── Simple / Full mode toggle ─────────────────────────────────────
        st.markdown(
            f'<div class="sb-mode-label">{"表示モード" if is_ja else "Modo de exibição"}</div>',
            unsafe_allow_html=True,
        )
        nm_c1, nm_c2 = st.columns(2)
        with nm_c1:
            if st.button(
                "シンプル" if is_ja else "Simples",
                key="nav_mode_simple",
                use_container_width=True,
                type="primary" if st.session_state["nav_mode"] == "simple" else "secondary",
            ):
                st.session_state["nav_mode"] = "simple"
                st.rerun()
        with nm_c2:
            if st.button(
                "詳細" if is_ja else "Completo",
                key="nav_mode_full",
                use_container_width=True,
                type="primary" if st.session_state["nav_mode"] == "full" else "secondary",
            ):
                st.session_state["nav_mode"] = "full"
                st.rerun()

        st.markdown("---")

        cur_page = st.session_state.get("page", "")

        # ── Simple mode: 5 flat items ─────────────────────────────────────
        if st.session_state["nav_mode"] == "simple":
            simple_items = [
                ("product_input",   "📦 " + ("商品入力"         if is_ja else "Entrada do Produto")),
                ("core_generation", "✨ " + ("Core生成"          if is_ja else "Gerar Core")),
                ("product_page",    "🛒 " + ("Shopifyコード"     if is_ja else "Código Shopify")),
                ("export_center",   "⚡ " + ("生成＆エクスポート" if is_ja else "Gerar & Exportar")),
                ("saved_data",      "💾 " + ("保存データ"        if is_ja else "Dados Salvos")),
            ]
            for page_id, label in simple_items:
                is_active = cur_page == page_id
                if st.button(
                    label,
                    key=f"snav_{page_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["page"] = page_id
                    st.rerun()

        # ── Full mode: grouped collapsible sections ───────────────────────
        else:
            for group_id, grp_ja, grp_pt, items in _NAV_GROUPS:
                filtered_items = filter_nav_items(items)
                if not filtered_items:
                    continue
                grp_label = grp_ja if is_ja else grp_pt
                # Auto-expand the group that contains the current page
                group_pages = {item[0] for item in filtered_items}
                auto_open   = cur_page in group_pages
                with st.expander(grp_label, expanded=auto_open):
                    for page_id, lbl_ja, lbl_pt, key_sfx in filtered_items:
                        label     = lbl_ja if is_ja else lbl_pt
                        is_active = cur_page == page_id
                        if st.button(
                            label,
                            key=f"fnav_{group_id}_{key_sfx}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                        ):
                            st.session_state["page"] = page_id
                            st.rerun()

        # ── Product info summary ──────────────────────────────────────────
        if st.session_state.get("product_info", {}).get("name"):
            st.markdown("---")
            prod_lbl = "商品" if is_ja else "Produto"
            st.markdown(
                f'<div style="font-size:0.75rem;color:#6b7280;">{prod_lbl}</div>'
                f'<div style="font-size:0.875rem;color:#e8e8e8;font-weight:600;">'
                f'{st.session_state["product_info"]["name"]}</div>',
                unsafe_allow_html=True,
            )
        if st.session_state.get("core_text"):
            core_status = st.session_state.get("core_status", "ai_generated")
            st.markdown(f'Core: {status_badge(core_status)}', unsafe_allow_html=True)

        # ── API usage footer ──────────────────────────────────────────────
        st.markdown(
            '<div class="nd-sidebar-footer">'
            '<div style="color:#1e3a1e;font-size:.6rem;letter-spacing:.1em;">API USAGE</div>'
            '<div class="nd-use-bar"><div class="nd-use-fill" style="width:73%;"></div></div>'
            '<div>730 / 1,000 calls</div>'
            '<div style="margin-top:4px;color:#1e2a1e;">v2.0 · Commerce</div>'
            '</div>',
            unsafe_allow_html=True,
        )


def render_breadcrumb():
    page    = st.session_state.get("page", "")
    is_ja   = st.session_state.get("lang", "ja") == "ja"
    bc_map  = _BREADCRUMB_MAP_JA if is_ja else _BREADCRUMB_MAP_PT
    if page not in bc_map:
        return
    grp, lbl = bc_map[page]
    st.markdown(
        f'<div class="sb-breadcrumb">'
        f'<span class="sb-bc-group">{grp}</span>'
        f'<span class="sb-bc-sep"> › </span>'
        f'<span class="sb-bc-page">{lbl}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Page: Mode Selection ──────────────────────────────────────────────────────

def page_mode_selection():
    st.markdown('<div class="section-header">🗂️ ' + t("mode.title") + '</div>', unsafe_allow_html=True)

    modes = list_modes()
    cols = st.columns(len(modes))
    lang = st.session_state["lang"]

    for i, mode in enumerate(modes):
        with cols[i]:
            name = mode["name_ja"] if lang == "ja" else mode["name_pt"]
            desc = mode["desc_ja"] if lang == "ja" else mode["desc_pt"]
            is_selected = st.session_state["mode"] == mode["id"]
            border_color = "#22c55e" if is_selected else "#1e1e1e"

            st.markdown(
                f'<div style="background:#141414;border:2px solid {border_color};'
                f'border-radius:12px;padding:24px;text-align:center;min-height:160px;">'
                f'<div style="font-size:2.5rem;">{mode["icon"]}</div>'
                f'<div style="font-size:1rem;font-weight:700;color:#f0f0f0;margin:12px 0 8px;">{name}</div>'
                f'<div style="font-size:0.8rem;color:#6b7280;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                t("mode.select_btn"),
                key=f"select_mode_{mode['id']}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                st.session_state["mode"] = mode["id"]
                st.session_state["page"] = "product_input"
                st.rerun()


# ── Page: Product Input ────────────────────────────────────────────────────────

def page_product_input():
    st.markdown('<div class="section-header">📦 ' + t("product_input.title") + '</div>',
                unsafe_allow_html=True)
    is_ja = st.session_state.get("lang", "ja") == "ja"

    # ── Phase 3: Project continuity UI ──────────────────────────────────────────
    if not st.session_state.get("product_id"):
        try:
            _recent = [p for p in svc["storage"].list_products()
                       if not is_empty_project_entry(p)][:5]
        except Exception:
            _recent = []
        if _recent:
            _resume_msg = ("以前のプロジェクトを継続しますか？選択すると保存済み内容（Core・生成コンテンツ含む）が復元されます。"
                           if is_ja else
                           "Deseja continuar um projeto anterior? Selecione para restaurar Core e conteúdos salvos.")
            st.markdown(
                f'<div class="cs-info" style="margin-bottom:8px;">💡 <strong>{_resume_msg}</strong></div>',
                unsafe_allow_html=True,
            )
            _btn_cols = st.columns(min(len(_recent), 3))
            for i, _rp in enumerate(_recent[:3]):
                with _btn_cols[i]:
                    _rp_label = (_rp.get("name") or "—")[:20]
                    if st.button(f"📂 {_rp_label}", key=f"pi_resume_{_rp['id']}",
                                 use_container_width=True):
                        load_project_session(_rp["id"], _rp, svc)
                        st.success(f"'{_rp.get('name')}' " + ("を読み込みました" if is_ja else "carregado"))
                        st.rerun()
            _or_new = "— または下記に新しい商品情報を入力して新規保存 —" if is_ja else "— ou insira novas informações abaixo para criar um novo projeto —"
            st.markdown(
                f'<div style="font-size:.75rem;color:#4b5563;margin:4px 0 12px;">{_or_new}</div>',
                unsafe_allow_html=True,
            )

    info = st.session_state.get("product_info", {})
    lang = st.session_state.get("lang", "ja")
    other_lang = "pt" if lang == "ja" else "ja"
    other_i18n = load_i18n(other_lang)

    # ── 表示切り替え: 日本語確認用 / 原文 Português ──────────────────────────
    _pi_input_ja_top = info.get("input_ja") or {}
    _pi_has_ja_top   = bool(_pi_input_ja_top)
    # Default to Japanese mode for admin when translation exists
    if _pi_has_ja_top:
        if st.session_state.get("pi_disp_mode") not in ("🇯🇵 日本語確認用", "🇧🇷 原文 Português"):
            st.session_state["pi_disp_mode"] = "🇯🇵 日本語確認用"
    _pi_show_ja = (
        _pi_has_ja_top
        and st.session_state.get("pi_disp_mode") == "🇯🇵 日本語確認用"
    )
    # Overlay Japanese translations onto info so all info.get() calls use Japanese
    if _pi_show_ja:
        info = {**info, **_pi_input_ja_top}

    def _other(key: str, default=None):
        """Retrieve a value from the other-language i18n dict."""
        parts = key.split(".")
        val = other_i18n
        for p in parts:
            val = val.get(p, default) if isinstance(val, dict) else default
        return val

    # ── Load localised option lists (tl() always returns a list) ─────
    categories   = tl("product_input.categories")
    price_opts   = tl("product_input.price_options")
    target_opts  = tl("product_input.target_options")
    gender_opts  = tl("product_input.gender_options")
    age_opts     = tl("product_input.age_options")
    tone_opts    = tl("product_input.brand_tone_options")
    free_input   = t("product_input.free_input") or "自由入力"

    def _other_list(key: str) -> list:
        parts = key.split(".")
        val = other_i18n
        for p in parts:
            val = val.get(p) if isinstance(val, dict) else None
            if val is None:
                return []
        return val if isinstance(val, list) else []

    # Other-language option lists for cross-language index resolution
    categories_o  = _other_list("product_input.categories")
    price_opts_o  = _other_list("product_input.price_options")
    target_opts_o = _other_list("product_input.target_options")
    gender_opts_o = _other_list("product_input.gender_options")
    age_opts_o    = _other_list("product_input.age_options")
    tone_opts_o   = _other_list("product_input.brand_tone_options")
    free_input_o  = _other("product_input.free_input", "")

    # ── Resolve saved brand_tone parts to multiselect defaults ────────
    ex_tone = info.get("brand_tone", "")
    ex_tone_parts = [s.strip() for s in ex_tone.split("、") if s.strip()]
    known_tone_idxs = set()
    custom_tone_parts = []
    for part in ex_tone_parts:
        found = False
        for i, opt in enumerate(tone_opts[:-1]):   # exclude free_input (last)
            if opt == part:
                known_tone_idxs.add(i)
                found = True
                break
        if not found:
            for i, opt in enumerate(tone_opts_o[:-1]):
                if opt == part:
                    known_tone_idxs.add(i)
                    found = True
                    break
        if not found:
            custom_tone_parts.append(part)

    known_tones_default = [tone_opts[i] for i in sorted(known_tone_idxs)
                           if i < len(tone_opts) - 1]
    if custom_tone_parts:
        known_tones_default.append(free_input)
    custom_tone_default = "、".join(custom_tone_parts)

    # ── 表示モード切り替えUI ──────────────────────────────────────────────
    if _pi_has_ja_top:
        _pi_disp_sel = st.radio(
            "表示モード / Modo de exibição",
            ["🇯🇵 日本語確認用", "🇧🇷 原文 Português"],
            index=0 if _pi_show_ja else 1,
            horizontal=True,
            key="pi_disp_mode",
            label_visibility="collapsed",
        )
        if _pi_show_ja:
            st.caption(
                "🇯🇵 日本語確認用データを表示中　—　"
                "保存すると日本語確認用データが更新されます（原文Portuguêsは保持）"
            )
        else:
            st.caption("🇧🇷 Português原文を表示中　—　保存すると原文データが更新されます")

    # ── 基本情報 ──────────────────────────────────────────────────────
    st.markdown(
        f'<div class="cs-card-title"><span class="icon">📦</span> '
        f'{t("product_input.section_basic")}</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input(
            t("product_input.name_required"),
            value=info.get("name", ""),
            placeholder=t("product_input.name_placeholder"),
        )
        cat_idx = resolve_option_index(info.get("category", ""), categories, categories_o)
        category = st.selectbox(t("product_input.category"), categories, index=cat_idx)
    with col2:
        product_url = st.text_input(
            t("product_input.url_optional"),
            value=info.get("product_url", ""),
            placeholder=t("product_input.url_placeholder"),
        )

    ex_price = info.get("price", "")
    price_idx = resolve_option_index(ex_price, price_opts, price_opts_o)
    price_mode = st.selectbox(t("product_input.price"), price_opts, index=price_idx)
    price = price_mode
    if price_mode == free_input:
        is_preset_price = ex_price in price_opts or ex_price in price_opts_o
        price = st.text_input(
            t("product_input.price_custom_label"),
            value="" if is_preset_price else ex_price,
            placeholder=t("product_input.price_custom_placeholder"),
        )

    st.markdown("---")

    # ── ターゲット設定 ────────────────────────────────────────────────
    st.markdown(
        f'<div class="cs-card-title"><span class="icon">👥</span> '
        f'{t("product_input.section_target")}</div>',
        unsafe_allow_html=True,
    )
    ex_target = info.get("target", "")
    target_idx = resolve_option_index(ex_target, target_opts, target_opts_o)
    target_mode = st.selectbox(t("product_input.target"), target_opts, index=target_idx)
    target = target_mode
    if target_mode == free_input:
        is_preset_target = ex_target in target_opts or ex_target in target_opts_o
        target = st.text_input(
            t("product_input.target_custom_label"),
            value="" if is_preset_target else ex_target,
            placeholder=t("product_input.target_custom_placeholder"),
        )

    col1, col2 = st.columns(2)
    with col1:
        gender_idx = resolve_option_index(info.get("gender", ""), gender_opts, gender_opts_o)
        gender = st.selectbox(t("product_input.gender"), gender_opts, index=gender_idx)
    with col2:
        ex_age = info.get("age", "")
        age_idx = resolve_option_index(ex_age, age_opts, age_opts_o)
        age_mode = st.selectbox(t("product_input.age"), age_opts, index=age_idx)
        age = age_mode
        if age_mode == free_input:
            is_preset_age = ex_age in age_opts or ex_age in age_opts_o
            age = st.text_input(
                t("product_input.age_custom_label"),
                value="" if is_preset_age else ex_age,
                placeholder=t("product_input.age_custom_placeholder"),
            )

    st.markdown("---")

    # ── 商品内容 ──────────────────────────────────────────────────────
    st.markdown(
        f'<div class="cs-card-title"><span class="icon">📝</span> '
        f'{t("product_input.section_content")}</div>',
        unsafe_allow_html=True,
    )
    description = st.text_area(
        t("product_input.description"),
        value=info.get("description", ""),
        height=150,
        placeholder=t("product_input.description_placeholder"),
    )

    col1, col2 = st.columns(2)
    with col1:
        features = st.text_area(
            t("product_input.features"),
            value=info.get("features", ""),
            height=110,
            placeholder=t("product_input.features_placeholder"),
        )
        use_scenes = st.text_area(
            t("product_input.usage_scene"),
            value=info.get("use_scenes", ""),
            height=110,
            placeholder=t("product_input.use_scenes_placeholder"),
        )
    with col2:
        weaknesses = st.text_area(
            t("product_input.weaknesses"),
            value=info.get("weaknesses", ""),
            height=110,
            placeholder=t("product_input.weaknesses_placeholder"),
        )
        competitor_urls = st.text_area(
            t("product_input.competitor_urls"),
            value=info.get("competitor_urls", ""),
            height=110,
            placeholder=t("product_input.competitor_url_placeholder"),
        )

    st.markdown("---")

    # ── 表現・トーン設定 ──────────────────────────────────────────────
    st.markdown(
        f'<div class="cs-card-title"><span class="icon">🎨</span> '
        f'{t("product_input.section_tone")}</div>',
        unsafe_allow_html=True,
    )
    brand_tone_selected = st.multiselect(
        t("product_input.brand_tone_multi_label"),
        tone_opts,
        default=known_tones_default,
    )
    brand_tone_custom_val = ""
    if free_input in brand_tone_selected:
        brand_tone_custom_val = st.text_input(
            t("product_input.brand_tone_custom_label"),
            value=custom_tone_default,
            placeholder=t("product_input.brand_tone_custom_placeholder"),
        )

    col1, col2 = st.columns(2)
    with col1:
        prohibited = st.text_area(
            t("product_input.forbidden_expressions"),
            value=info.get("prohibited", ""),
            height=100,
            placeholder=t("product_input.prohibited_placeholder"),
        )
    with col2:
        notes = st.text_area(
            t("product_input.notes"),
            value=info.get("notes", ""),
            height=100,
            placeholder=t("product_input.notes_placeholder"),
        )

    st.markdown("---")

    person_opts = tl("product_input.person_options")
    person_opts_o = _other_list("product_input.person_options")
    free_person = person_opts[-1] if person_opts else "自由入力"
    free_person_o = person_opts_o[-1] if person_opts_o else ""

    col_a, col_b = st.columns(2)
    with col_a:
        ex_assignee = st.session_state.get("assignee", "")
        assignee_idx = resolve_option_index(ex_assignee, person_opts, person_opts_o)
        assignee_mode = st.selectbox(t("product_input.assignee"), person_opts, index=assignee_idx,
                                     key="assignee_sel")
        assignee = assignee_mode
        if assignee_mode == free_person:
            is_preset_a = ex_assignee in person_opts or ex_assignee in person_opts_o
            assignee = st.text_input(
                t("product_input.assignee_custom_label"),
                value="" if is_preset_a else ex_assignee,
            )
    with col_b:
        ex_reviewer = st.session_state.get("reviewer", "")
        reviewer_idx = resolve_option_index(ex_reviewer, person_opts, person_opts_o)
        reviewer_mode = st.selectbox(t("product_input.reviewer"), person_opts, index=reviewer_idx,
                                     key="reviewer_sel")
        reviewer = reviewer_mode
        if reviewer_mode == free_person:
            is_preset_r = ex_reviewer in person_opts or ex_reviewer in person_opts_o
            reviewer = st.text_input(
                t("product_input.reviewer_custom_label"),
                value="" if is_preset_r else ex_reviewer,
            )

    # Normalize "選択なし" / "Sem seleção" to empty string
    sentinel_vals = set(person_opts[:1]) | set(person_opts_o[:1])
    if assignee in sentinel_vals:
        assignee = ""
    if reviewer in sentinel_vals:
        reviewer = ""

    if st.button("💾 " + t("product_input.save_button"), type="primary", use_container_width=True):
        _is_ja = st.session_state.get("lang", "ja") == "ja"
        if not name.strip() and not product_url.strip() and not description.strip():
            st.error(
                "商品名・URL・説明のいずれかを入力してください" if _is_ja
                else "Por favor, insira ao menos o nome, URL ou descrição do produto"
            )
        else:
            product_id = ensure_product_id()

            # ── Phase 3: duplicate name warning ──────────────────────────────
            if name.strip():
                try:
                    _dup = [ep for ep in svc["storage"].list_products()
                            if ep.get("name","").strip().lower() == name.strip().lower()
                            and ep["id"] != product_id
                            and not is_empty_project_entry(ep)]
                except Exception:
                    _dup = []
                if _dup:
                    _dup_msg = (f"「{name}」という商品名のプロジェクトが既に {len(_dup)} 件あります。このまま保存すると新しいプロジェクトとして登録されます。"
                                if is_ja else
                                f"Já existe(m) {len(_dup)} projeto(s) com o nome «{name}». Salvar criará um novo projeto.")
                    st.warning(_dup_msg)
                    for _dp in _dup[:2]:
                        _dp_col1, _dp_col2 = st.columns([3, 1])
                        with _dp_col1:
                            _upd_lbl = "更新日" if is_ja else "Atualizado"
                            st.caption(f"📦 {_dp.get('name')} — {_upd_lbl}: {_dp.get('updated_at','-')}")
                        with _dp_col2:
                            if st.button("このプロジェクトを使う" if is_ja else "Usar este projeto", key=f"use_existing_{_dp['id']}",
                                         use_container_width=True):
                                load_project_session(_dp["id"], _dp, svc)
                                st.success(f"'{_dp.get('name')}' " + ("を読み込みました" if is_ja else "carregado"))
                                st.rerun()

            tones = [tone for tone in brand_tone_selected if tone not in (free_input, free_input_o)]
            if brand_tone_custom_val.strip():
                tones.append(brand_tone_custom_val.strip())
            brand_tone = "、".join(tones)

            new_info = {
                "name": name, "category": category, "price": price,
                "target": target, "gender": gender, "age": age,
                "product_url": product_url, "features": features,
                "weaknesses": weaknesses, "brand_tone": brand_tone,
                "prohibited": prohibited, "description": description,
                "use_scenes": use_scenes, "competitor_urls": competitor_urls,
                "notes": notes,
                "assignee": assignee,
                "final_reviewer": reviewer,
            }
            _exist = svc["storage"].load_product(product_id) or {}
            _save_lang     = st.session_state.get("lang", "ja")
            _pi_save_in_ja = (
                st.session_state.get("pi_disp_mode") == "🇯🇵 日本語確認用"
                and _pi_has_ja_top
            )
            new_info = prepare_product_save_data(
                new_info,
                _exist,
                "admin",
                _save_lang,
                _pi_save_in_ja,
            )
            st.session_state["product_info"] = new_info
            st.session_state["assignee"] = assignee
            st.session_state["reviewer"] = reviewer
            svc["storage"].save_product(product_id, new_info)
            svc["storage"].log_activity(product_id, "商品情報保存", name, assignee)
            st.markdown('<div class="cs-success">✅ ' + t("product_input.saved_msg") + '</div>',
                        unsafe_allow_html=True)


# ── Page: Core Generation ──────────────────────────────────────────────────────

def page_core_generation():
    st.markdown('<div class="section-header">✨ ' + t("nav.core_generation") + '</div>',
                unsafe_allow_html=True)
    is_ja = st.session_state.get("lang", "ja") == "ja"

    product_info = st.session_state.get("product_info", {})
    if not product_info.get("name"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_product_warning") + '</div>',
                    unsafe_allow_html=True)
        return

    _cg_pid = st.session_state.get("product_id", "")
    try:
        _cg_project = svc["storage"].load_product(_cg_pid) or {}
    except Exception:
        _cg_project = {}

    # ── Core生成用データ解決（優先順位付き） ─────────────────────────────────
    _CG_CORE_FIELDS = ("name", "category", "price", "target", "gender", "age",
                       "product_url", "features", "weaknesses", "brand_tone",
                       "prohibited", "description", "use_scenes", "competitor_urls",
                       "notes", "assignee", "final_reviewer")

    def _cg_has_ja(text: str) -> bool:
        if not text:
            return False
        return sum(1 for c in text if '぀' <= c <= '鿿' or '一' <= c <= '鿿') >= 3

    # Priority 1: core_source_data がある
    _cg_core_source = _cg_project.get("core_source_data") or {}

    # Priority 2: input_ja がある → core_source_data を再ビルド
    if not _cg_core_source:
        _cg_input_ja = _cg_project.get("input_ja") or {}
        if _cg_input_ja:
            svc["storage"].save_product_translation(
                _cg_pid, _cg_input_ja,
                _cg_project.get("translated_by", "system (auto-rebuild)")
            )
            _cg_project = svc["storage"].load_product(_cg_pid) or {}
            _cg_core_source = _cg_project.get("core_source_data") or {}

    # Priority 3+4: 日本語入力判定 → そのまま使う
    if not _cg_core_source:
        _cg_lang     = _cg_project.get("input_original_language", "")
        _cg_tr_st    = _cg_project.get("translation_status", "not_translated")
        _cg_txt_keys = ("name", "description", "features", "target", "use_scenes", "notes")
        _cg_sample   = " ".join(str(_cg_project.get(k, "")) for k in _cg_txt_keys if _cg_project.get(k))
        _cg_is_ja    = (
            _cg_lang in ("ja", "japanese")
            or _cg_tr_st == "not_needed"
            or _cg_has_ja(_cg_sample)
        )
        if _cg_is_ja:
            _cg_auto = {k: _cg_project.get(k, "") for k in _CG_CORE_FIELDS}
            _cg_upd  = dict(_cg_project)
            _cg_upd["core_source_data"]       = _cg_auto
            _cg_upd["translation_status"]     = "not_needed"
            _cg_upd["input_original_language"] = "ja"
            svc["storage"].save_product(_cg_pid, _cg_upd)
            _cg_core_source = _cg_auto

    # Debug display (temporary)
    with st.expander("🔧 デバッグ情報（開発用）", expanded=False):
        st.markdown(f"- **product_id (session)**: `{_cg_pid}`")
        st.markdown(f"- **input_ja**: {'✅ あり (' + str(len(_cg_project.get('input_ja') or {})) + 'フィールド)' if _cg_project.get('input_ja') else '❌ なし'}")
        st.markdown(f"- **core_source_data**: {'✅ あり (' + str(len(_cg_core_source)) + 'フィールド)' if _cg_core_source else '❌ なし'}")
        st.markdown(f"- **input_original_language**: `{_cg_project.get('input_original_language', 'not set')}`")
        st.markdown(f"- **translation_status**: `{_cg_project.get('translation_status', 'not set')}`")
        st.markdown(f"- **Core生成に使用するデータ**: {'core_source_data ✅' if _cg_core_source else '現在の商品情報を自動使用'}")

    # Priority 5: すべて失敗 → 現在の商品情報をそのままCore生成に使う
    if not _cg_core_source:
        _fallback_source = {}
        for k in _CG_CORE_FIELDS:
            _fallback_source[k] = (
                _cg_project.get(k)
                or product_info.get(k)
                or st.session_state.get(k, "")
            )
        _cg_core_source = {k: v for k, v in _fallback_source.items() if v}
        if _cg_pid:
            _cg_upd2 = dict(_cg_project)
            _cg_upd2["core_source_data"] = _cg_core_source
            _cg_upd2["translation_status"] = _cg_upd2.get("translation_status", "not_needed")
            svc["storage"].save_product(_cg_pid, _cg_upd2)

    # Core method selection
    st.markdown("#### " + t("core_method.title"))
    method_col1, method_col2, method_col3, method_col4 = st.columns(4)

    methods = [
        ("auto", t("core_method.auto"), t("core_method.auto_desc")),
        ("import", t("core_method.import"), t("core_method.import_desc")),
        ("compare", t("core_method.compare"), t("core_method.compare_desc")),
        ("reuse", t("core_method.reuse"), t("core_method.reuse_desc")),
    ]

    for i, (method_id, label, desc) in enumerate(methods):
        with [method_col1, method_col2, method_col3, method_col4][i]:
            is_sel = st.session_state.get("core_method") == method_id
            border = "#22c55e" if is_sel else "#1e1e1e"
            st.markdown(
                f'<div style="background:#141414;border:1px solid {border};border-radius:8px;'
                f'padding:12px;text-align:center;cursor:pointer;min-height:90px;">'
                f'<div style="font-weight:700;font-size:0.875rem;color:#f0f0f0;">{label}</div>'
                f'<div style="font-size:0.75rem;color:#6b7280;margin-top:6px;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(label, key=f"method_{method_id}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state["core_method"] = method_id
                st.rerun()

    st.markdown("---")
    method = st.session_state.get("core_method", "auto")

    # ── Auto generation ──
    if method == "auto":
        st.markdown("**📦 " + ("商品情報からCore自動生成" if is_ja else "Gerar Core automaticamente") + "**")

        info_summary = "\n".join(
            f"- **{k}**: {v}" for k, v in product_info.items() if v
        )
        with st.expander("入力中の商品情報を確認" if is_ja else "Ver informações do produto", expanded=False):
            st.markdown(info_summary)

        col_gen, col_regen = st.columns([2, 1])
        with col_gen:
            if st.button("✨ " + t("core.generate_btn"), type="primary", use_container_width=True):
                with st.spinner(t("core.generating_msg")):
                    result = svc["core_engine"].generate_from_product(_cg_core_source)
                    st.session_state["core_text"] = result
                    st.session_state["core_status"] = "ai_generated"
                    pid = ensure_product_id()
                    svc["storage"].save_core(pid, {"text": result, "status": "ai_generated"}, "v1 AI初稿")
                    svc["storage"].log_activity(pid, "Core生成", "auto", st.session_state.get("assignee", ""))
                    st.rerun()

    # ── Reuse saved core ──
    elif method == "reuse":
        pid = ensure_product_id()
        cores = svc["storage"].list_cores(pid)
        if not cores:
            st.markdown('<div class="cs-info">💡 ' + ("保存済みCoreがありません。まずCoreを生成してください。" if is_ja else "Nenhum Core salvo. Gere um Core primeiro.") + '</div>',
                        unsafe_allow_html=True)
        else:
            options = [f"{c['version_label']} ({c.get('status', '')})" for c in cores]
            sel = st.selectbox("保存済みCoreを選択" if is_ja else "Selecionar Core salvo", options)
            if st.button("📂 " + ("このCoreを使用" if is_ja else "Usar este Core"), type="primary"):
                idx = options.index(sel)
                st.session_state["core_text"] = cores[idx]["core"].get("text", "")
                st.session_state["core_status"] = cores[idx].get("status", "ai_generated")
                st.success("Coreを読み込みました" if is_ja else "Core carregado")
                st.rerun()

    # ── Core editor ──
    if st.session_state.get("core_text"):
        st.markdown("---")
        st.markdown("#### ✏️ " + ("Core編集" if is_ja else "Editar Core"))

        core_status = st.session_state.get("core_status", "ai_generated")
        st.markdown(
            f'<div style="margin-bottom:12px;">{status_badge(core_status)}</div>',
            unsafe_allow_html=True,
        )

        edited_core = st.text_area(
            "Core" + ("（編集可能）" if is_ja else " (editável)"),
            value=st.session_state["core_text"],
            height=500,
            key="core_editor",
        )

        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("💾 " + t("core.save_btn"), type="primary", use_container_width=True):
                st.session_state["core_text"] = edited_core
                st.session_state["core_status"] = "edited"
                pid = ensure_product_id()
                svc["storage"].save_core(pid, {"text": edited_core, "status": "edited"}, "編集済み")
                svc["storage"].log_activity(pid, "Core編集・保存", "", st.session_state.get("assignee", ""))
                st.success(t("core.saved_msg"))

        with col2:
            if st.button("📋 " + ("コピー" if is_ja else "Copiar"), use_container_width=True):
                st.code(edited_core, language="")

        with col3:
            md_content = svc["exporter"].core_to_markdown(edited_core, product_info.get("name", ""))
            st.download_button(
                "⬇️ MD",
                data=md_content.encode("utf-8"),
                file_name=f"core_{product_info.get('name', 'product')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col4:
            if st.button("🔄 " + ("再生成" if is_ja else "Regerar"), use_container_width=True):
                with st.spinner(t("core.generating_msg")):
                    result = svc["core_engine"].generate_from_product(_cg_core_source)
                    st.session_state["core_text"] = result
                    st.session_state["core_status"] = "ai_generated"
                    st.rerun()
    else:
        if method == "auto":
            _hint = "「Core生成」ボタンを押してCoreを生成してください。" if is_ja else "Clique no botão Gerar Core para criar o Core."
            st.markdown(f'<div class="cs-info">💡 {_hint}</div>', unsafe_allow_html=True)


# ── Page: External Core Import ────────────────────────────────────────────────

def page_external_core():
    st.markdown('<div class="section-header">📥 ' + t("external_core.title") + '</div>',
                unsafe_allow_html=True)

    lang = st.session_state["lang"]
    is_ja = lang == "ja"
    sources = t("external_core.sources")
    source = st.selectbox(t("external_core.source_label"), sources if isinstance(sources, list) else [])

    pt_mode = st.checkbox(t("external_core.mode_pt"), value=False)

    external_text = st.text_area(
        t("external_core.paste_label"),
        placeholder=t("external_core.paste_placeholder"),
        height=250,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 " + t("external_core.analyze_btn"), type="primary", use_container_width=True):
            if not external_text.strip():
                st.warning("テキストを入力してください" if lang == "ja" else "Por favor insira o texto")
                return
            with st.spinner(t("external_core.analyzing_msg")):
                if pt_mode:
                    result = svc["core_importer"].activate_portuguese_core(external_text)
                else:
                    result = svc["core_importer"].import_and_normalize(external_text, source)

                st.session_state["core_text"] = result
                st.session_state["core_status"] = "ai_generated"
                pid = ensure_product_id()
                svc["storage"].save_core(
                    pid,
                    {"text": result, "status": "ai_generated", "source": source},
                    "外部取り込み"
                )
                svc["storage"].log_activity(pid, "外部Core取り込み", source, "")
                st.rerun()

    with col2:
        if st.button("🌐 " + ("言語判定のみ" if is_ja else "Detectar idioma"), use_container_width=True):
            if external_text.strip():
                detected = svc["core_importer"].detect_language(external_text)
                st.info(("検出言語" if is_ja else "Idioma detectado") + f": **{detected}**")

    if st.session_state.get("core_text") and "外部取り込み" in str(svc["storage"].list_cores(ensure_product_id())):
        st.markdown("---")
        st.markdown("**✅ " + ("標準化されたCore（編集して保存してください）" if is_ja else "Core padronizado (edite e salve)") + "**")
        edited = st.text_area("Core" + ("（編集可能）" if is_ja else " (editável)"), value=st.session_state["core_text"], height=400)
        if st.button("💾 " + ("このCoreを保存" if is_ja else "Salvar este Core"), type="primary"):
            st.session_state["core_text"] = edited
            st.session_state["core_status"] = "edited"
            pid = ensure_product_id()
            svc["storage"].save_core(pid, {"text": edited, "status": "edited"}, "外部取り込み・編集済み")
            st.success(t("core.saved_msg"))

    # Show current core if exists
    if st.session_state.get("core_text"):
        st.markdown("---")
        st.markdown("**" + ("現在のCore（確認用）" if is_ja else "Core atual (para referência)") + "**")
        st.markdown(
            f'<div class="generated-box">{st.session_state["core_text"][:2000]}...</div>'
            if len(st.session_state["core_text"]) > 2000
            else f'<div class="generated-box">{st.session_state["core_text"]}</div>',
            unsafe_allow_html=True,
        )
        if st.button("✏️ " + ("Core生成・編集画面へ" if is_ja else "Ir para Gerar/Editar Core")):
            st.session_state["page"] = "core_generation"
            st.rerun()


# ── Page: Product Page ────────────────────────────────────────────────────────

def render_generated_page(page_key: str, title: str, generate_fn, icon: str = "📄"):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)
    is_ja = st.session_state.get("lang", "ja") == "ja"

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        if st.button("✨ " + ("Core生成画面へ" if is_ja else "Ir para Gerar Core")):
            st.session_state["page"] = "core_generation"
            st.rerun()
        return

    product_info = st.session_state.get("product_info", {})
    core = st.session_state["core_text"]

    if st.button(f"✨ {t(f'{page_key}.generate_btn')}", type="primary", use_container_width=True):
        with st.spinner(t(f"{page_key}.generating_msg")):
            result = generate_fn(core, product_info)
            st.session_state["generated"][page_key] = result
            pid = ensure_product_id()
            svc["storage"].save_generated(pid, page_key, {"text": result})
            svc["storage"].log_activity(pid, f"{title}生成", "", st.session_state.get("assignee", ""))
            st.rerun()

    pid = ensure_product_id()

    # Content tabs
    if st.session_state["generated"].get(page_key):
        tab1, tab2 = st.tabs(["📄 " + ("生成結果" if is_ja else "Resultado"), "✏️ " + ("編集・保存" if is_ja else "Editar/Salvar")])

        with tab1:
            content = st.session_state["generated"][page_key]
            st.markdown(f'<div class="generated-box">{content}</div>', unsafe_allow_html=True)

        with tab2:
            content = st.session_state["generated"][page_key]
            edited = st.text_area("編集可能テキスト" if is_ja else "Texto editável", value=content, height=600, key=f"edit_{page_key}")

            col_s, col_d, col_c = st.columns(3)
            with col_s:
                if st.button("💾 " + ("保存" if is_ja else "Salvar"), type="primary", key=f"save_{page_key}", use_container_width=True):
                    st.session_state["generated"][page_key] = edited
                    svc["storage"].save_generated(pid, page_key, {"text": edited, "status": "edited"})
                    st.success(t("common.saved"))
            with col_d:
                st.download_button(
                    "⬇️ " + ("MD形式" if is_ja else "Markdown"),
                    data=svc["exporter"].to_markdown(title, edited).encode("utf-8"),
                    file_name=f"{page_key}_{product_info.get('name', 'output')}.md",
                    mime="text/markdown",
                    key=f"dl_{page_key}",
                    use_container_width=True,
                )
            with col_c:
                st.download_button(
                    "⬇️ JSON",
                    data=svc["exporter"].to_json({"title": title, "content": edited}).encode("utf-8"),
                    file_name=f"{page_key}_{product_info.get('name', 'output')}.json",
                    mime="application/json",
                    key=f"dl_json_{page_key}",
                    use_container_width=True,
                )
    else:
        st.markdown('<div class="cs-info">💡 ' + ("生成ボタンを押してコンテンツを生成してください。" if is_ja else "Clique no botão para gerar o conteúdo.") + '</div>',
                    unsafe_allow_html=True)


def page_product_page():
    st.markdown('<div class="section-header">📄 ' + t("product_page.title") + '</div>',
                unsafe_allow_html=True)
    is_ja = st.session_state.get("lang", "ja") == "ja"

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        if st.button("✨ " + ("Core生成画面へ" if is_ja else "Ir para Gerar Core")):
            st.session_state["page"] = "core_generation"
            st.rerun()
        return

    core = st.session_state["core_text"]
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "product")
    pid = ensure_product_id()

    tab_text, tab_liquid = st.tabs([
        "📝 " + ("商品ページ文章" if is_ja else "Texto da Página"),
        "🛒 Shopify Custom Liquid",
    ])

    # ── Tab 1: 商品ページ文章 ────────────────────────────────────────────
    with tab_text:
        if st.button("✨ " + t("product_page.generate_btn"), type="primary",
                     use_container_width=True, key="gen_product_text"):
            with st.spinner(t("product_page.generating_msg")):
                result = svc["generator"].generate_product_page(core, product_info)
                st.session_state["generated"]["product_page"] = result
                svc["storage"].save_generated(pid, "product_page", {"text": result})
                svc["storage"].log_activity(pid, "商品ページ文章生成", "", st.session_state.get("assignee", ""))
                st.rerun()

        if st.session_state["generated"].get("product_page"):
            content = st.session_state["generated"]["product_page"]
            edited = st.text_area("編集可能テキスト" if is_ja else "Texto editável", value=content, height=500, key="edit_product_page")
            col_s, col_d = st.columns(2)
            with col_s:
                if st.button("💾 " + ("保存" if is_ja else "Salvar"), type="primary", key="save_product_page", use_container_width=True):
                    st.session_state["generated"]["product_page"] = edited
                    svc["storage"].save_generated(pid, "product_page", {"text": edited, "status": "edited"})
                    st.success(t("common.saved"))
            with col_d:
                st.download_button("⬇️ " + (".txt ダウンロード" if is_ja else "Baixar .txt"),
                    data=edited.encode("utf-8"),
                    file_name=f"product_page_{product_name}.txt",
                    mime="text/plain", key="dl_product_text", use_container_width=True)
        else:
            st.markdown('<div class="cs-info">💡 ' + ("生成ボタンを押してください。" if is_ja else "Clique no botão para gerar.") + '</div>', unsafe_allow_html=True)

    # ── Tab 2: Shopify Custom Liquid (section-based) ─────────────────────
    with tab_liquid:

        # ── Section metadata ──────────────────────────────────────────────
        SECTIONS = [
            {
                "key": "shopify_common_css",
                "label": "00 共通CSS",
                "icon": "🎨",
                "num": "00",
                "instruction": (
                    "他のセクションより先に設置してください。<br>"
                    "Shopify管理画面 → オンラインストア → テーマ → カスタマイズ → "
                    "商品ページ → セクション追加 → <strong>Custom Liquid</strong> に貼り付け"
                ),
            },
            {
                "key": "shopify_hero_section_code",
                "label": "01 ファーストビュー",
                "icon": "🌟",
                "num": "01",
                "instruction": "商品ページの最上部に設置してください。",
            },
            {
                "key": "shopify_about_section_code",
                "label": "02 商品について",
                "icon": "📦",
                "num": "02",
                "instruction": "ファーストビューの次に設置。画像セクションを間に挟んでも OK。",
            },
            {
                "key": "shopify_problem_section_code",
                "label": "03 悩み・共感",
                "icon": "💭",
                "num": "03",
                "instruction": "商品についての後に設置。画像・動画セクションと組み合わせ可。",
            },
            {
                "key": "shopify_features_section_code",
                "label": "04 特徴カード",
                "icon": "✨",
                "num": "04",
                "instruction": "特徴を強調したい位置に設置してください。",
            },
            {
                "key": "shopify_usage_scene_section_code",
                "label": "05 使用シーン",
                "icon": "🏠",
                "num": "05",
                "instruction": "使用イメージが伝わる位置に設置。画像スライダーの前後がおすすめ。",
            },
            {
                "key": "shopify_comparison_section_code",
                "label": "06 比較表",
                "icon": "📊",
                "num": "06",
                "instruction": "他との違いを訴求したい位置に設置してください。",
            },
            {
                "key": "shopify_faq_section_code",
                "label": "07 FAQ",
                "icon": "❓",
                "num": "07",
                "instruction": "CTAの直前に設置するのがおすすめです。",
            },
            {
                "key": "shopify_cta_section_code",
                "label": "08 CTA",
                "icon": "🛒",
                "num": "08",
                "instruction": "ページの最下部に設置してください。",
            },
        ]

        ALL_SECTION_KEYS = [s["key"] for s in SECTIONS]

        def _html_preview(title: str, code: str) -> str:
            return (
                "<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n"
                "<meta charset=\"UTF-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                f"<title>Preview: {title}</title>\n"
                "<body style=\"margin:0;padding:0;background:#faf8f4;\">\n"
                f"{code}\n</body>\n</html>"
            )

        def _combined_html(sections_data: dict) -> str:
            parts = []
            for s in SECTIONS:
                code = sections_data.get(s["key"], "")
                if code:
                    parts.append(f"<!-- {s['label']} -->\n{code}")
            return "\n\n".join(parts)

        # ── Check what's already generated ───────────────────────────────
        gen = st.session_state["generated"]
        sections_ready = any(gen.get(s["key"]) for s in SECTIONS)

        # ── Output type selector ──────────────────────────────────────────
        output_options = [
            "セクション別コード（全セクション）",
            "00 共通CSS",
            "01 ファーストビュー",
            "02 商品について",
            "03 悩み・共感",
            "04 特徴カード",
            "05 使用シーン",
            "06 比較表",
            "07 FAQ",
            "08 CTA",
            "ページ全体コード（旧形式）",
        ]
        output_type = st.selectbox("📋 " + ("表示するセクションを選択" if is_ja else "Selecionar seção"), output_options,
                                   key="liquid_output_type")

        st.markdown("")

        # ── Generate buttons ──────────────────────────────────────────────
        gen_col1, gen_col2 = st.columns([3, 2])
        with gen_col1:
            if st.button("✨ " + ("セクション別コードを生成" if is_ja else "Gerar Código por Seção"), type="primary",
                         use_container_width=True, key="gen_sections"):
                with st.spinner("セクション別コードを生成中（9セクション × 個別生成。2〜3分かかります）..." if is_ja else "Gerando código por seção (9 seções × individual. 2–3 min)..."):
                    try:
                        generator = svc["generator"]
                        if not hasattr(generator, "generate_shopify_sections"):
                            from modules.generator_engine import GeneratorEngine
                            generator = GeneratorEngine(svc["llm"])
                        result = generator.generate_shopify_sections(core, product_info)
                        for s in SECTIONS:
                            code = result.get(s["key"], "")
                            gen[s["key"]] = code  # 空でも必ずセット（フォールバック済み）
                            if code:
                                svc["storage"].save_generated(pid, s["key"], {"text": code})
                        st.session_state["generated"] = gen
                        svc["storage"].log_activity(pid, "Shopifyセクション生成", "",
                                                    st.session_state.get("assignee", ""))
                        st.rerun()
                    except Exception as e:
                        st.error(("セクション別コード生成中にエラーが発生しました" if is_ja else "Erro ao gerar código por seção") + f": {e}")

        with gen_col2:
            if st.button("🛒 " + ("ページ全体コードを生成（旧形式）" if is_ja else "Gerar Código da Página Completa (legado)"),
                         use_container_width=True, key="gen_custom_liquid"):
                with st.spinner("Custom Liquidコードを生成中..." if is_ja else "Gerando código Custom Liquid..."):
                    result = svc["generator"].generate_custom_liquid(core, product_info)
                    gen["shopify_custom_liquid"] = result
                    st.session_state["generated"] = gen
                    svc["storage"].save_generated(pid, "shopify_custom_liquid", {"text": result})
                    svc["storage"].log_activity(pid, "Custom Liquid生成（全体）", "",
                                                st.session_state.get("assignee", ""))
                    st.rerun()

        if not sections_ready and not gen.get("shopify_custom_liquid"):
            st.markdown(
                '<div class="cs-info">💡 ' + (
                    '上のボタンを押してコードを生成してください。<br>「セクション別コードを生成」を選ぶと、各セクションを個別にShopifyへ貼り付けできます。'
                    if is_ja else
                    'Clique no botão acima para gerar o código.<br>"Gerar Código por Seção" permite colar cada seção individualmente no Shopify.'
                ) + '</div>',
                unsafe_allow_html=True,
            )

        # ── Section: ページ全体コード（旧形式）──────────────────────────
        if output_type == "ページ全体コード（旧形式）" and gen.get("shopify_custom_liquid"):
            liquid_code = gen["shopify_custom_liquid"]
            st.markdown("---")
            st.markdown(
                '<div class="cs-info">📌 Shopify管理画面 → オンラインストア → テーマ → '
                'カスタマイズ → 商品ページ → セクション追加 → <strong>Custom Liquid</strong> に貼り付け</div>',
                unsafe_allow_html=True,
            )
            st.code(liquid_code, language="html")
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button("⬇️ .txt",
                    data=liquid_code.encode("utf-8"),
                    file_name=f"shopify_full_{product_name}.txt",
                    mime="text/plain", key="dl_full_txt", use_container_width=True)
            with dl_col2:
                st.download_button("⬇️ .html 確認用",
                    data=_html_preview("Full Page", liquid_code).encode("utf-8"),
                    file_name=f"shopify_full_{product_name}.html",
                    mime="text/html", key="dl_full_html", use_container_width=True)

        # ── Section: セクション別（全表示）───────────────────────────────
        elif output_type == "セクション別コード（全セクション）":
            if not sections_ready:
                st.markdown(
                    '<div class="cs-warning">⚠️ ' + (
                        '「セクション別コードを生成」ボタンを押してください。'
                        if is_ja else
                        'Clique em "Gerar Código por Seção".'
                    ) + '</div>',
                    unsafe_allow_html=True,
                )
            else:
                # Combined download at top
                combined = _combined_html(gen)
                combined_col1, combined_col2 = st.columns(2)
                with combined_col1:
                    st.download_button("⬇️ 全セクション .txt（一括）",
                        data=combined.encode("utf-8"),
                        file_name=f"shopify_all_sections_{product_name}.txt",
                        mime="text/plain", key="dl_all_txt", use_container_width=True)
                with combined_col2:
                    st.download_button("⬇️ 全セクション .html（プレビュー確認用）",
                        data=_html_preview("All Sections", combined).encode("utf-8"),
                        file_name=f"shopify_all_sections_{product_name}.html",
                        mime="text/html", key="dl_all_html", use_container_width=True)
                st.markdown("---")

                for s in SECTIONS:
                    code = gen.get(s["key"], "")
                    with st.expander(f'{s["icon"]} {s["label"]}', expanded=False):
                        st.markdown(
                            f'<div class="cs-info">📌 {s["instruction"]}</div>',
                            unsafe_allow_html=True,
                        )
                        if code:
                            st.code(code, language="html")
                            dl1, dl2 = st.columns(2)
                            with dl1:
                                st.download_button(
                                    "⬇️ .txt",
                                    data=code.encode("utf-8"),
                                    file_name=f"shopify_{s['num']}_{product_name}.txt",
                                    mime="text/plain",
                                    key=f"dl_txt_{s['key']}",
                                    use_container_width=True,
                                )
                            with dl2:
                                st.download_button(
                                    "⬇️ .html 確認用",
                                    data=_html_preview(s["label"], code).encode("utf-8"),
                                    file_name=f"shopify_{s['num']}_{product_name}.html",
                                    mime="text/html",
                                    key=f"dl_html_{s['key']}",
                                    use_container_width=True,
                                )
                        else:
                            st.markdown('<div class="cs-warning">⚠️ ' + (
                                'このセクションは未生成です。「セクション別コードを生成」を押してください。'
                                if is_ja else
                                'Esta seção ainda não foi gerada. Clique em "Gerar Código por Seção".'
                            ) + '</div>', unsafe_allow_html=True)
                            with st.expander("🔍 " + ("デバッグ情報" if is_ja else "Informações de debug"), expanded=False):
                                present = [k for k in ALL_SECTION_KEYS if gen.get(k)]
                                missing = [k for k in ALL_SECTION_KEYS if not gen.get(k)]
                                st.write(f"探したキー: `{s['key']}`")
                                st.write(f"キーが存在するか: `{s['key'] in gen}`")
                                st.write("生成済みキー:", present)
                                st.write("未生成キー:", missing)

        # ── Section: 個別セクション表示 ──────────────────────────────────
        else:
            # Map selectbox value to section info
            section_map = {s["label"]: s for s in SECTIONS}
            # Also try matching by number prefix "00 共通CSS" → label
            label_lookup = {
                "00 共通CSS":          SECTIONS[0],
                "01 ファーストビュー": SECTIONS[1],
                "02 商品について":     SECTIONS[2],
                "03 悩み・共感":       SECTIONS[3],
                "04 特徴カード":       SECTIONS[4],
                "05 使用シーン":       SECTIONS[5],
                "06 比較表":           SECTIONS[6],
                "07 FAQ":              SECTIONS[7],
                "08 CTA":              SECTIONS[8],
            }
            sec = label_lookup.get(output_type)
            if sec:
                code = gen.get(sec["key"], "")
                st.markdown("---")
                st.markdown(
                    f'<div class="cs-info">📌 {sec["instruction"]}</div>',
                    unsafe_allow_html=True,
                )
                if code:
                    st.code(code, language="html")
                    dl1, dl2 = st.columns(2)
                    with dl1:
                        st.download_button(
                            "⬇️ .txt",
                            data=code.encode("utf-8"),
                            file_name=f"shopify_{sec['num']}_{product_name}.txt",
                            mime="text/plain",
                            key=f"dl_single_txt_{sec['key']}",
                            use_container_width=True,
                        )
                    with dl2:
                        st.download_button(
                            "⬇️ .html 確認用",
                            data=_html_preview(sec["label"], code).encode("utf-8"),
                            file_name=f"shopify_{sec['num']}_{product_name}.html",
                            mime="text/html",
                            key=f"dl_single_html_{sec['key']}",
                            use_container_width=True,
                        )
                else:
                    st.markdown(
                        '<div class="cs-warning">⚠️ ' + (
                            'このセクションはまだ生成されていません。「セクション別コードを生成」ボタンを押してください。'
                            if is_ja else
                            'Esta seção ainda não foi gerada. Clique em "Gerar Código por Seção".'
                        ) + '</div>',
                        unsafe_allow_html=True,
                    )
                    with st.expander("🔍 " + ("デバッグ情報" if is_ja else "Informações de debug"), expanded=False):
                        present = [k for k in ALL_SECTION_KEYS if gen.get(k)]
                        missing = [k for k in ALL_SECTION_KEYS if not gen.get(k)]
                        st.write(f"探したキー: `{sec['key']}`")
                        st.write(f"キーが存在するか: `{sec['key'] in gen}`")
                        st.write("生成済みキー:", present)
                        st.write("未生成キー:", missing)


def page_image_prompt():
    render_page_image_prompt(svc, t, ensure_product_id, status_badge)


def page_video_script():
    render_page_video_script(svc, t, ensure_product_id, status_badge)


def page_ads_sns():
    render_page_ads_sns(svc, t, ensure_product_id, status_badge)


# ── Page: Bulk Pack ────────────────────────────────────────────────────────────

def page_bulk_pack():
    st.markdown('<div class="section-header">⚡ ' + t("bulk_pack.title") + '</div>',
                unsafe_allow_html=True)
    is_ja = st.session_state.get("lang", "ja") == "ja"

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        return

    core = st.session_state["core_text"]
    product_info = st.session_state.get("product_info", {})

    packs = [
        ("shopify_pack", "🛒 " + t("bulk_pack.shopify_pack")),
        ("ads_pack",     "📣 " + t("bulk_pack.ads_pack")),
        ("sns_pack",     "📱 " + t("bulk_pack.sns_pack")),
        ("image_pack",   "🖼️ " + t("bulk_pack.image_pack")),
        ("video_pack",   "🎬 " + t("bulk_pack.video_pack")),
    ]

    cols = st.columns(3)
    selected_pack = st.session_state.get("selected_pack", "shopify_pack")

    for i, (pack_id, pack_label) in enumerate(packs):
        with cols[i % 3]:
            is_sel = selected_pack == pack_id
            if st.button(pack_label, key=f"pack_{pack_id}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state["selected_pack"] = pack_id
                st.rerun()

    st.markdown("---")

    pack_id = st.session_state.get("selected_pack", "shopify_pack")
    pack_label = dict(packs).get(pack_id, "パック" if is_ja else "Pacote")

    if st.button(f"⚡ {pack_label}" + ("を生成" if is_ja else " – Gerar"), type="primary", use_container_width=False):
        with st.spinner(t("bulk_pack.generating_msg")):
            if pack_id == "shopify_pack":
                result = svc["bulk"].generate_shopify_pack(core, product_info)
            elif pack_id == "ads_pack":
                result = svc["bulk"].generate_ads_pack(core, product_info)
            elif pack_id == "sns_pack":
                result = svc["bulk"].generate_sns_pack(core, product_info)
            elif pack_id == "image_pack":
                result = svc["bulk"].generate_image_pack(core, product_info)
            elif pack_id == "video_pack":
                result = svc["bulk"].generate_video_pack(core, product_info)
            else:
                result = {}

            st.session_state["generated"][f"bulk_{pack_id}"] = result
            pid = ensure_product_id()
            svc["storage"].save_generated(pid, f"bulk_{pack_id}", result)
            svc["storage"].log_activity(pid, f"一括生成：{pack_id}", "", "")
            st.rerun()

    if st.session_state["generated"].get(f"bulk_{pack_id}"):
        result = st.session_state["generated"][f"bulk_{pack_id}"]
        for key, value in result.items():
            with st.expander(f"📄 {key}", expanded=True):
                edited = st.text_area(("編集可能" if is_ja else "Editável") + f"（{key}）", value=value, height=400, key=f"bulk_edit_{pack_id}_{key}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 " + ("保存" if is_ja else "Salvar"), key=f"bulk_save_{pack_id}_{key}", use_container_width=True):
                        result[key] = edited
                        st.session_state["generated"][f"bulk_{pack_id}"] = result
                        st.success(t("common.saved"))
                with col2:
                    st.download_button(
                        "⬇️ " + ("ダウンロード" if is_ja else "Baixar"),
                        data=svc["exporter"].to_markdown(key, edited).encode("utf-8"),
                        file_name=f"{pack_id}_{key}.md",
                        mime="text/markdown",
                        key=f"bulk_dl_{pack_id}_{key}",
                        use_container_width=True,
                    )


# ── Page: Japanese Refinement & Translation ────────────────────────────────────

def page_refinement():
    st.markdown('<div class="section-header">✍️ ' + t("refinement.title") + '</div>',
                unsafe_allow_html=True)

    lang = st.session_state["lang"]
    is_ja = lang == "ja"
    tab1, tab2, tab3 = st.tabs([
        "🇯🇵 " + ("日本語補正" if is_ja else "Refinar japonês"),
        "🔄 PT→JA",
        "🔄 JA→PT",
    ])

    with tab1:
        modes = t("refinement.modes")
        if isinstance(modes, list):
            mode = st.selectbox(t("refinement.mode_label"), modes)
        else:
            mode = "自然な日本語"

        text_in = st.text_area(t("refinement.input_label"), height=200, key="refine_input")

        if st.button("✨ " + t("refinement.refine_btn"), type="primary"):
            if text_in.strip():
                with st.spinner(t("refinement.refining_msg")):
                    result = svc["refiner"].refine(text_in, mode)
                    st.session_state["refine_result"] = result
                    st.rerun()

        if st.session_state.get("refine_result"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="bilingual-label">{t("refinement.before")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="generated-box">{text_in}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="bilingual-label">{t("refinement.after")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="generated-box">{st.session_state["refine_result"]}</div>',
                            unsafe_allow_html=True)

    with tab2:
        st.markdown("**" + ("ポルトガル語 → 日本語（日本市場向け自然化）" if is_ja else "Português → Japonês (naturalização para mercado japonês)") + "**")
        pt_text = st.text_area("ポルトガル語テキスト" if is_ja else "Texto em Português", height=200, key="pt_input")
        if st.button("🔄 " + t("refinement.pt_to_ja_btn"), type="primary"):
            if pt_text.strip():
                with st.spinner("変換中..." if is_ja else "Convertendo..."):
                    result = svc["translator"].pt_to_ja(pt_text)
                    st.session_state["trans_result"] = result

        if st.session_state.get("trans_result") and st.session_state.get("pt_input"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="bilingual-label">Português</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="bilingual-col">{st.session_state.get("pt_input", "")}</div>',
                            unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="bilingual-label">日本語</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="bilingual-col">{st.session_state.get("trans_result", "")}</div>',
                            unsafe_allow_html=True)

    with tab3:
        st.markdown("**" + ("日本語 → ポルトガル語（ブラジル）" if is_ja else "Japonês → Português (Brasil)") + "**")
        ja_text = st.text_area("日本語テキスト" if is_ja else "Texto em Japonês", height=200, key="ja_input")
        if st.button("🔄 " + t("refinement.ja_to_pt_btn"), type="primary"):
            if ja_text.strip():
                with st.spinner("翻訳中..." if is_ja else "Traduzindo..."):
                    result = svc["translator"].ja_to_pt(ja_text)
                    st.session_state["ja_trans_result"] = result

        if st.session_state.get("ja_trans_result") and st.session_state.get("ja_input"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="bilingual-label">日本語</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="bilingual-col">{st.session_state.get("ja_input", "")}</div>',
                            unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="bilingual-label">Português</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="bilingual-col">{st.session_state.get("ja_trans_result", "")}</div>',
                            unsafe_allow_html=True)


# ── Page: Check ───────────────────────────────────────────────────────────────

def page_check():
    st.markdown('<div class="section-header">✅ ' + t("check.title") + '</div>',
                unsafe_allow_html=True)

    is_ja = st.session_state.get("lang", "ja") == "ja"

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        return

    core = st.session_state["core_text"]

    tab1, tab2 = st.tabs([
        "🔍 " + ("整合性チェック" if is_ja else "Verificar consistência"),
        "⚠️ " + ("リスク表現チェック" if is_ja else "Verificar riscos"),
    ])

    with tab1:
        content_type = st.selectbox("チェック対象" if is_ja else "Tipo de conteúdo", ["product_page", "image_prompt", "video_script", "ads_sns"])
        content = st.session_state["generated"].get(content_type, "")
        if content:
            if st.button("🔍 " + t("check.run_btn"), type="primary"):
                with st.spinner(t("check.checking_msg")):
                    result = svc["checker"].check_consistency(core, content, content_type)
                    st.session_state["check_result"] = result
                    st.rerun()
            if st.session_state.get("check_result"):
                st.markdown(f'<div class="generated-box">{st.session_state["check_result"]}</div>',
                            unsafe_allow_html=True)
        else:
            st.markdown('<div class="cs-info">💡 ' + ("先に対象コンテンツを生成してください。" if is_ja else "Gere o conteúdo antes de verificar.") + '</div>',
                        unsafe_allow_html=True)

    with tab2:
        text_to_check = st.text_area("チェックしたいテキストを入力" if is_ja else "Insira o texto para verificar", height=200)
        if st.button("⚠️ " + ("リスク表現をチェック" if is_ja else "Verificar expressões de risco"), type="primary"):
            if text_to_check.strip():
                with st.spinner(t("check.checking_msg")):
                    result = svc["checker"].check_risk_expressions(text_to_check)
                    st.session_state["risk_check_result"] = result
                    st.rerun()
        if st.session_state.get("risk_check_result"):
            st.markdown(f'<div class="generated-box">{st.session_state["risk_check_result"]}</div>',
                        unsafe_allow_html=True)


# ── Page: Output ──────────────────────────────────────────────────────────────

def page_output():
    st.markdown('<div class="section-header">📤 ' + t("output.title") + '</div>',
                unsafe_allow_html=True)
    is_ja = st.session_state.get("lang", "ja") == "ja"

    pid = ensure_product_id()
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "output")

    content_map = {
        "Core / 核": ("core_text", None),
        "商品ページ": ("generated.product_page", "product_page"),
        "画像プロンプト": ("generated.image_prompt", "image_prompt"),
        "動画台本": ("generated.video_script", "video_script"),
        "広告・SNS": ("generated.ads_sns", "ads_sns"),
    }

    export_data = {}

    for label, (state_key, content_type) in content_map.items():
        # Get content from session state
        if "." in state_key:
            parts = state_key.split(".")
            content = st.session_state.get(parts[0], {}).get(parts[1], "")
        else:
            content = st.session_state.get(state_key, "")

        if not content:
            continue

        export_data[label] = content

        with st.expander(f"📄 {label}", expanded=False):
            st.text_area(label, value=content, height=200, key=f"out_{label}")

    if export_data:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        all_text = "\n\n---\n\n".join(
            f"# {k}\n\n{v}" for k, v in export_data.items()
        )

        with col1:
            st.download_button(
                "⬇️ " + t("output.download_md"),
                data=all_text.encode("utf-8"),
                file_name=f"core_studio_{product_name}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "⬇️ " + t("output.download_json"),
                data=svc["exporter"].to_json(export_data).encode("utf-8"),
                file_name=f"core_studio_{product_name}.json",
                mime="application/json",
                use_container_width=True,
            )
        with col3:
            if "商品ページ" in export_data:
                html_content = svc["exporter"].product_page_to_html(
                    export_data["商品ページ"], product_name
                )
                st.download_button(
                    "⬇️ " + t("output.download_html"),
                    data=html_content.encode("utf-8"),
                    file_name=f"product_page_{product_name}.html",
                    mime="text/html",
                    use_container_width=True,
                )
    else:
        st.markdown('<div class="cs-info">💡 ' + ("生成されたコンテンツがありません。各ページでコンテンツを生成してください。" if is_ja else "Nenhum conteúdo gerado. Gere conteúdo nas páginas correspondentes.") + '</div>',
                    unsafe_allow_html=True)


# ── Page: Instruction Sheet ───────────────────────────────────────────────────

_INS_CSS = """
<style>
/* ════════════════════════════════════════════════════════════════
   INSTRUCTION SHEET  — ins- prefix
   ════════════════════════════════════════════════════════════════ */
.ins-card {
    background:#111827; border:1px solid #1f2937;
    border-radius:12px; padding:20px 24px; margin-bottom:16px;
}
.ins-card-title {
    font-size:0.72rem; font-weight:700; color:#4b5563;
    text-transform:uppercase; letter-spacing:.1em; margin-bottom:14px;
}
.ins-row { display:flex; gap:8px; margin-bottom:8px; align-items:baseline; }
.ins-key {
    font-size:0.78rem; color:#6b7280; min-width:100px; flex-shrink:0;
}
.ins-val { font-size:0.85rem; color:#e8e8e8; line-height:1.5; }
.ins-core-block {
    background:#0d1117; border-radius:8px; padding:14px;
    font-size:0.8rem; color:#9ca3af; white-space:pre-wrap;
    line-height:1.7; max-height:220px; overflow:hidden;
}
.ins-tbl { width:100%; border-collapse:collapse; }
.ins-tbl th {
    background:#0a0a0a; color:#4b5563; font-size:0.7rem;
    font-weight:700; text-transform:uppercase; letter-spacing:.07em;
    padding:8px 12px; text-align:left; border-bottom:1px solid #1f2937;
}
.ins-tbl td {
    padding:9px 12px; border-bottom:1px solid #161616;
    font-size:0.82rem; color:#d1d5db; vertical-align:middle;
}
.ins-tbl td:first-child { font-weight:600; color:#e8e8e8; }
.ins-check { color:#22c55e; }
.ins-dash  { color:#374151; }
.ins-notes {
    font-size:0.85rem; color:#9ca3af; line-height:1.7;
    background:#0d1117; border-radius:8px; padding:12px 14px;
}
</style>
"""


def page_instruction_sheet():
    st.markdown(_INS_CSS, unsafe_allow_html=True)

    is_ja = st.session_state.get("lang", "ja") == "ja"
    title = "制作指示書" if is_ja else "Ficha de Produção"
    st.markdown(f'<div class="section-header">📋 {title}</div>', unsafe_allow_html=True)

    pid          = ensure_product_id()
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name") or ("未設定" if is_ja else "Não definido")
    gen          = st.session_state.get("generated", {})
    core_text    = st.session_state.get("core_text", "")

    _SHOPIFY_KEYS = [
        "shopify_common_css", "shopify_hero_section_code", "shopify_about_section_code",
        "shopify_problem_section_code", "shopify_features_section_code",
        "shopify_usage_scene_section_code", "shopify_comparison_section_code",
        "shopify_faq_section_code", "shopify_cta_section_code",
    ]

    content_specs = [
        ("core",             "Core / 核"    if is_ja else "Core"),
        ("product_page",     "商品ページ"   if is_ja else "Página do Produto"),
        ("shopify_sections", "Shopify HTML"),
        ("image_prompt",     "画像プロンプト" if is_ja else "Prompts de Imagem"),
        ("video_script",     "動画台本"     if is_ja else "Roteiro de Vídeo"),
        ("ads_sns",          "広告・SNS"    if is_ja else "Anúncios/SNS"),
    ]

    # ── Download button (top) ─────────────────────────────────────────────────
    def _build_md() -> str:
        lines = [f"# 制作指示書 — {product_name}", ""]
        lines += ["## プロジェクト情報", ""]
        for key, label in [
            ("name",         "商品名"),
            ("category",     "カテゴリ"),
            ("price",        "価格"),
            ("target",       "ターゲット"),
            ("assignee",     "担当者"),
            ("final_reviewer","確認者"),
        ]:
            val = product_info.get(key, "")
            if val:
                lines.append(f"- **{label}**: {val}")
        lines += ["", "## Core サマリー", ""]
        lines.append(core_text[:1000] if core_text else "（未生成）")
        lines += ["", "## コンテンツ状況", ""]
        lines.append("| コンテンツ | 生成 |")
        lines.append("|-----------|------|")
        for ct, label in content_specs:
            if ct == "core":
                has_content = bool(core_text)
            elif ct == "shopify_sections":
                has_content = any(gen.get(k) for k in _SHOPIFY_KEYS)
            else:
                has_content = bool(gen.get(ct))
            lines.append(f"| {label} | {'✓' if has_content else '—'} |")
        notes = product_info.get("notes", "")
        if notes:
            lines += ["", "## 備考", "", notes]
        lines += ["", f"---", f"*生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"]
        return "\n".join(lines)

    dl_col, _ = st.columns([2, 6])
    with dl_col:
        md_bytes = _build_md().encode("utf-8")
        st.download_button(
            "⬇️ Markdownでダウンロード" if is_ja else "⬇️ Baixar como Markdown",
            data=md_bytes,
            file_name=f"instruction_{product_name}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # ── Project info card ─────────────────────────────────────────────────────
    info_title = "プロジェクト情報" if is_ja else "Informações do Projeto"
    rows_html = ""
    for key, label in [
        ("name",          "商品名"      if is_ja else "Produto"),
        ("category",      "カテゴリ"    if is_ja else "Categoria"),
        ("price",         "価格"        if is_ja else "Preço"),
        ("target",        "ターゲット"  if is_ja else "Público-alvo"),
        ("description",   "説明"        if is_ja else "Descrição"),
        ("assignee",      "担当者"      if is_ja else "Responsável"),
        ("final_reviewer","確認者"      if is_ja else "Revisor"),
        ("updated_at",    "最終更新"    if is_ja else "Atualizado"),
    ]:
        val = product_info.get(key, "")
        if not val:
            continue
        rows_html += (
            f'<div class="ins-row">'
            f'<div class="ins-key">{label}</div>'
            f'<div class="ins-val">{val}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="ins-card">'
        f'<div class="ins-card-title">📦 {info_title}</div>'
        f'{rows_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Core snapshot card ────────────────────────────────────────────────────
    core_title = "Core スナップショット" if is_ja else "Snapshot do Core"
    core_preview = (core_text[:600] + ("…" if len(core_text) > 600 else "")) if core_text else (
        "（Coreはまだ生成されていません）" if is_ja else "（Core ainda não gerado）"
    )
    st.markdown(
        f'<div class="ins-card">'
        f'<div class="ins-card-title">🧠 {core_title}</div>'
        f'<div class="ins-core-block">{core_preview}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Content status table ──────────────────────────────────────────────────
    tbl_title = "コンテンツ状況" if is_ja else "Status dos Conteúdos"
    th_name   = "コンテンツ"    if is_ja else "Conteúdo"
    th_gen    = "生成"          if is_ja else "Gerado"

    rows = ""
    for ct, label in content_specs:
        if ct == "core":
            has_content = bool(core_text)
        elif ct == "shopify_sections":
            has_content = any(gen.get(k) for k in _SHOPIFY_KEYS)
        else:
            has_content = bool(gen.get(ct))

        gen_icon = f'<span class="ins-check">✓</span>' if has_content else f'<span class="ins-dash">—</span>'
        rows += (
            f"<tr>"
            f"<td>{label}</td>"
            f"<td style='text-align:center'>{gen_icon}</td>"
            f"</tr>"
        )

    st.markdown(
        f'<div class="ins-card">'
        f'<div class="ins-card-title">📊 {tbl_title}</div>'
        f'<table class="ins-tbl">'
        f'<thead><tr><th>{th_name}</th><th>{th_gen}</th></tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Notes card ────────────────────────────────────────────────────────────
    notes = product_info.get("notes", "").strip()
    if notes:
        notes_title = "備考・担当者メモ" if is_ja else "Observações"
        st.markdown(
            f'<div class="ins-card">'
            f'<div class="ins-card-title">📝 {notes_title}</div>'
            f'<div class="ins-notes">{notes}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Footer ────────────────────────────────────────────────────────────────
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    footer_msg = f"生成日時: {now_str}" if is_ja else f"Gerado em: {now_str}"
    st.markdown(
        f'<div style="font-size:0.72rem;color:#374151;text-align:right;margin-top:8px">{footer_msg}</div>',
        unsafe_allow_html=True,
    )


# ── Page: Export Center ───────────────────────────────────────────────────────

def page_export_center():
    st.markdown("""<style>
.ec-preview-box{background:#0a0a0a;border:1px solid #1e1e1e;border-radius:8px;padding:14px;
  font-size:0.8125rem;line-height:1.75;color:#9ca3af;white-space:pre-wrap;
  max-height:200px;overflow:hidden;font-family:inherit}
.ec-empty-card{background:#0d0d0d;border:1px dashed #374151;border-radius:8px;padding:36px;
  text-align:center;color:#4b5563;font-size:0.875rem}
.ec-section-title{font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;
  letter-spacing:0.08em;margin-bottom:14px}
.ec-proj-table{width:100%;border-collapse:collapse}
.ec-proj-table th{background:#0a0a0a;color:#6b7280;font-size:0.72rem;font-weight:700;
  text-transform:uppercase;letter-spacing:.06em;padding:10px 12px;text-align:left;
  border-bottom:1px solid #1e1e1e}
.ec-proj-table td{padding:10px 12px;border-bottom:1px solid #161616;font-size:0.8125rem;
  color:#d1d5db;vertical-align:middle}
.ec-proj-name{font-weight:600;color:#e8e8e8}
.ec-proj-sub{font-size:0.72rem;color:#6b7280;margin-top:2px}
.ec-export-tile{display:flex;align-items:center;gap:12px;background:#141414;
  border:1px solid #1e1e1e;border-radius:10px;padding:13px 16px;margin-bottom:8px}
.ec-export-icon{width:34px;height:34px;border-radius:8px;background:#1a1a1a;
  display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0}
.ec-export-name{font-size:0.85rem;font-weight:600;color:#e8e8e8}
.ec-export-desc{font-size:0.72rem;color:#6b7280;margin-top:2px}
.ec-soon{font-size:0.68rem;color:#374151;background:#111;border:1px solid #1e1e1e;
  padding:2px 8px;border-radius:20px;margin-left:auto;flex-shrink:0;white-space:nowrap}
</style>""", unsafe_allow_html=True)

    pid = ensure_product_id()
    gen = st.session_state.get("generated", {})
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "product")
    lang = st.session_state.get("lang", "ja")
    is_ja = (lang == "ja")

    # ── Header ────────────────────────────────────────────────────────────────
    hcol_title, hcol_btn = st.columns([5, 1])
    with hcol_title:
        title = "生成＆エクスポートセンター" if is_ja else "Centro de Geração & Exportação"
        sub = ("各形式で生成されたコンテンツを確認・調整し、ワンクリックでエクスポートできます。"
               if is_ja else
               "Confirme, ajuste e exporte conteúdo gerado com um clique.")
        st.markdown(f'<div class="section-header">⚡ {title}</div>'
                    f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)
    with hcol_btn:
        new_label = "✨ 新規生成を開始" if is_ja else "✨ Nova Geração"
        if st.button(new_label, type="primary", use_container_width=True, key="ec_new_gen"):
            st.session_state["page"] = "product_input"
            st.rerun()

    # ── Page navigator mapping (used in multiple places) ─────────────────────
    CT_PAGE = {
        "product_page":          "product_page",
        "shopify_custom_liquid": "product_page",
        "image_prompt":          "image_prompt",
        "video_script":          "video_script",
        "ads_sns":               "ads_sns",
    }

    # ── Content tabs ─────────────────────────────────────────────────────────
    if is_ja:
        TAB_DEFS = [
            ("📄 商品ページ文",   "product_page",          "product_page"),
            ("</> Shopifyコード", "shopify_custom_liquid",  "shopify_custom_liquid"),
            ("🖼️ 画像プロンプト", "image_prompt",           "image_prompt"),
            ("🎬 動画台本",       "video_script",           "video_script"),
            ("📣 広告SNS",        "ads_sns",                "ads_sns"),
        ]
    else:
        TAB_DEFS = [
            ("📄 Página do Produto",  "product_page",         "product_page"),
            ("</> Código Shopify",    "shopify_custom_liquid", "shopify_custom_liquid"),
            ("🖼️ Prompts de Imagem",  "image_prompt",          "image_prompt"),
            ("🎬 Roteiro de Vídeo",   "video_script",          "video_script"),
            ("📣 Anúncios/SNS",       "ads_sns",               "ads_sns"),
        ]

    tabs = st.tabs([d[0] for d in TAB_DEFS])

    for tab_widget, (tab_label, gen_key, ct) in zip(tabs, TAB_DEFS):
        with tab_widget:
            content = gen.get(gen_key, "")

            # Header row + language toggle
            row_a, row_b = st.columns([3, 1])
            with row_a:
                short_label = tab_label.split(" ", 1)[-1]
                st.markdown(
                    f'<div style="margin:4px 0 12px">'
                    f'<span style="font-weight:700;color:#e8e8e8;font-size:0.9rem">{short_label}</span></div>',
                    unsafe_allow_html=True,
                )
            with row_b:
                cur_lang = st.session_state.get(f"ec_lang_{ct}", "ja")
                lc1, lc2 = st.columns(2)
                with lc1:
                    if st.button("JA", key=f"ec_ja_{ct}",
                                 type="primary" if cur_lang == "ja" else "secondary",
                                 use_container_width=True):
                        st.session_state[f"ec_lang_{ct}"] = "ja"
                        st.rerun()
                with lc2:
                    if st.button("PT", key=f"ec_pt_{ct}",
                                 type="primary" if cur_lang == "pt" else "secondary",
                                 use_container_width=True):
                        st.session_state[f"ec_lang_{ct}"] = "pt"
                        st.rerun()

            if content:
                # Content preview (first 500 chars)
                preview = content[:500] + ("\n…" if len(content) > 500 else "")
                st.markdown(f'<div class="ec-preview-box">{preview}</div>',
                            unsafe_allow_html=True)
                st.markdown("")

                # Action buttons
                a1, a2, a3 = st.columns(3)
                with a1:
                    copy_label = "📋 コピー" if is_ja else "📋 Copiar"
                    if st.button(copy_label, key=f"ec_copy_{ct}", use_container_width=True):
                        st.session_state[f"ec_show_copy_{ct}"] = not st.session_state.get(f"ec_show_copy_{ct}", False)
                        st.rerun()
                with a2:
                    st.download_button(
                        "⬇️ DL",
                        data=content.encode("utf-8"),
                        file_name=f"{ct}_{product_name}.txt",
                        mime="text/plain",
                        key=f"ec_dl_{ct}",
                        use_container_width=True,
                    )
                with a3:
                    edit_label = "✏️ 編集" if is_ja else "✏️ Editar"
                    if st.button(edit_label, key=f"ec_edit_{ct}", use_container_width=True):
                        st.session_state["page"] = CT_PAGE.get(ct, "product_page")
                        st.rerun()
                # Toggle copy area (st.code has built-in copy button)
                if st.session_state.get(f"ec_show_copy_{ct}"):
                    st.code(content, language="text")
                    close_label = "閉じる" if is_ja else "Fechar"
                    if st.button(close_label, key=f"ec_close_copy_{ct}"):
                        st.session_state[f"ec_show_copy_{ct}"] = False
                        st.rerun()
            else:
                empty_msg = "まだ生成されていません。各生成ページでコンテンツを生成してください。" if is_ja else "Ainda não gerado. Gere o conteúdo na página correspondente."
                st.markdown(f'<div class="ec-empty-card">⚡ {empty_msg}</div>',
                            unsafe_allow_html=True)
                st.markdown("")
                gen_nav_label = (f"🚀 {short_label}を生成する"
                                 if is_ja else f"🚀 Gerar {short_label}")
                if st.button(gen_nav_label, key=f"ec_goto_{ct}", type="primary"):
                    st.session_state["page"] = CT_PAGE.get(ct, "product_page")
                    st.rerun()

    # ── Bottom: saved projects + export ──────────────────────────────────────
    st.markdown("---")
    bot_l, bot_r = st.columns([3, 2])

    with bot_l:
        proj_title = "保存済みプロジェクト" if is_ja else "Projetos Salvos"
        st.markdown(f'<div class="ec-section-title">💾 {proj_title}</div>',
                    unsafe_allow_html=True)
        try:
            projects = svc["storage"].list_products()
        except Exception:
            projects = []

        if projects:
            rows_html = ""
            for p in list(reversed(projects))[:5]:
                badge_html = '<span class="badge badge-draft">保存済み</span>'
                rows_html += (
                    f'<tr>'
                    f'<td><div class="ec-proj-name">{p.get("name", p["id"])}</div>'
                    f'<div class="ec-proj-sub">{p.get("category", "")}</div></td>'
                    f'<td style="color:#6b7280;font-size:0.75rem">{p.get("updated_at", "")}</td>'
                    f'<td>{badge_html}</td>'
                    f'</tr>'
                )
            th_name = "プロジェクト名" if is_ja else "Projeto"
            th_updated = "最終更新" if is_ja else "Atualizado"
            th_status = "ステータス" if is_ja else "Status"
            st.markdown(
                f'<table class="ec-proj-table">'
                f'<thead><tr><th>{th_name}</th><th>{th_updated}</th><th>{th_status}</th></tr></thead>'
                f'<tbody>{rows_html}</tbody>'
                f'</table>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            see_all = "すべてのプロジェクトを見る →" if is_ja else "Ver todos os projetos →"
            if st.button(see_all, key="ec_all_projects"):
                st.session_state["page"] = "saved_data"
                st.rerun()
        else:
            no_proj = "保存済みプロジェクトがありません" if is_ja else "Nenhum projeto salvo"
            st.markdown(f'<div class="ec-empty-card">{no_proj}</div>',
                        unsafe_allow_html=True)

    with bot_r:
        exp_title = "エクスポート＆連携" if is_ja else "Exportação & Integração"
        st.markdown(f'<div class="ec-section-title">📤 {exp_title}</div>',
                    unsafe_allow_html=True)

        _SHOPIFY_KEYS_EC = [
            "shopify_common_css", "shopify_hero_section_code", "shopify_about_section_code",
            "shopify_problem_section_code", "shopify_features_section_code",
            "shopify_usage_scene_section_code", "shopify_comparison_section_code",
            "shopify_faq_section_code", "shopify_cta_section_code",
        ]
        export_items = {k: v for k, v in gen.items()
                        if v and isinstance(v, str) and not k.startswith("_")}
        all_text = "\n\n---\n\n".join(f"# {k}\n\n{v}" for k, v in export_items.items())
        shopify_code = "\n\n".join(gen[k] for k in _SHOPIFY_KEYS_EC if gen.get(k))

        # Build ZIP bundle
        def _build_zip() -> bytes:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                core_t = st.session_state.get("core_text", "")
                if core_t:
                    zf.writestr("core.txt", core_t)
                for key, text in export_items.items():
                    safe = key.replace("/", "_").replace(" ", "_")
                    ext = "html" if "shopify" in key.lower() else "txt"
                    zf.writestr(f"{safe}.{ext}", text)
                if shopify_code:
                    zf.writestr(f"shopify_{product_name}.html", shopify_code)
            buf.seek(0)
            return buf.read()

        has_content = bool(all_text or st.session_state.get("core_text"))

        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            st.download_button(
                "⬇️ " + ("一括TXT" if is_ja else "Tudo TXT"),
                data=(all_text or " ").encode("utf-8"),
                file_name=f"task_destroyer_{product_name}.txt",
                mime="text/plain",
                key="ec_bulk_dl",
                use_container_width=True,
                disabled=not all_text,
            )
        with dl2:
            st.download_button(
                "</> Shopify",
                data=(shopify_code or " ").encode("utf-8"),
                file_name=f"shopify_{product_name}.html",
                mime="text/html",
                key="ec_shopify_dl",
                use_container_width=True,
                disabled=not shopify_code,
            )
        with dl3:
            zip_bytes = _build_zip() if has_content else b""
            st.download_button(
                "📦 ZIP",
                data=zip_bytes if zip_bytes else b" ",
                file_name=f"task_destroyer_{product_name}.zip",
                mime="application/zip",
                key="ec_zip_dl",
                use_container_width=True,
                disabled=not has_content,
            )

        st.markdown("")

        INTEGRATIONS = [
            ("🟢", ("Googleドライブに保存" if is_ja else "Salvar no Google Drive"),
                   ("Google Drive連携"    if is_ja else "Integração Google Drive")),
            ("📘", ("Word / Docsに出力"  if is_ja else "Exportar Word/Docs"),
                   ("文書エクスポート"    if is_ja else "Exportação de documentos")),
            ("📅", ("SNS投稿を予約"      if is_ja else "Agendar posts SNS"),
                   ("SNS連携"            if is_ja else "Integração SNS")),
            ("📧", ("メールで送信"       if is_ja else "Enviar por e-mail"),
                   ("メール送信"         if is_ja else "Envio por e-mail")),
        ]
        soon = "近日公開" if is_ja else "Em breve"
        for icon, name, desc in INTEGRATIONS:
            st.markdown(
                f'<div class="ec-export-tile">'
                f'<div class="ec-export-icon">{icon}</div>'
                f'<div><div class="ec-export-name">{name}</div>'
                f'<div class="ec-export-desc">{desc}</div></div>'
                f'<span class="ec-soon">{soon}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        manage_label = "🔗 連携サービスを管理" if is_ja else "🔗 Gerenciar integrações"
        if st.button(manage_label, key="ec_manage_int", use_container_width=True):
            st.session_state["page"] = "instruction_sheet"
            st.rerun()


# ── Page: Saved Data → moved to modules/saved_data_page.py ───────────────────


# ── Page: New Dashboard → moved to modules/dashboard_page.py ─────────────────


# ── Page: Custom Mode ──────────────────────────────────────────────────────────

def page_custom_mode():
    is_ja = st.session_state.get("lang", "ja") == "ja"
    st.markdown('<div class="section-header">⚙️ Custom Mode</div>', unsafe_allow_html=True)
    st.markdown('<div class="cs-info">💡 ' + ("Custom Modeは将来拡張用の自由入力モードです。" if is_ja else "Custom Mode é para uso futuro de entrada livre.") + '</div>',
                unsafe_allow_html=True)

    user_input = st.text_area(
        "自由入力（任意のコンテンツ生成）" if is_ja else "Entrada livre (geração de conteúdo livre)",
        height=300,
        placeholder="コンテンツの概要、目的、ターゲットなどを自由に入力してください" if is_ja else "Insira o resumo, objetivo, público-alvo etc. livremente",
    )

    if st.button("✨ " + ("生成" if is_ja else "Gerar"), type="primary"):
        if user_input.strip():
            from modes.custom.custom_core import CustomCore
            cc = CustomCore(svc["llm"])
            with st.spinner("生成中..." if is_ja else "Gerando..."):
                result = cc.generate(user_input)
                st.session_state["custom_result"] = result
                st.rerun()

    if st.session_state.get("custom_result"):
        st.markdown("**" + ("生成結果" if is_ja else "Resultado") + "**")
        edited = st.text_area("編集可能" if is_ja else "Editável", value=st.session_state["custom_result"], height=400)
        if st.button("💾 " + ("保存" if is_ja else "Salvar"), type="primary"):
            st.session_state["custom_result"] = edited
            st.success("保存しました" if is_ja else "Salvo")


# ── Main router ───────────────────────────────────────────────────────────────

def main():
    render_sidebar()
    render_breadcrumb()

    # API key warning
    if not svc["llm"].is_available:
        st.markdown(
            '<div class="cs-warning">⚠️ ANTHROPIC_API_KEY が設定されていません。'
            '.env ファイルに API キーを設定してください。</div>',
            unsafe_allow_html=True,
        )

    page = st.session_state.get("page", "mode_selection")
    mode = st.session_state.get("mode", "commerce")

    if mode == "custom":
        page_custom_mode()
        return

    page_map = {
        "dashboard": lambda: _page_new_dashboard(svc),
        "mode_selection": page_mode_selection,
        "product_input": page_product_input,
        "external_core": page_external_core,
        "core_generation": page_core_generation,
        "product_page": page_product_page,
        "image_prompt": page_image_prompt,
        "video_script": page_video_script,
        "ads_sns": page_ads_sns,
        "bulk_pack": page_bulk_pack,
        "refinement": page_refinement,
        "check": page_check,
        "output": page_output,
        "saved_data": lambda: _page_saved_data(svc),
        "export_center": page_export_center,
        "instruction_sheet": page_instruction_sheet,
    }

    render_fn = page_map.get(page, page_mode_selection)
    render_fn()


if __name__ == "__main__":
    main()
