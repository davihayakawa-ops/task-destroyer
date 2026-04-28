import streamlit as st
import json
import os
import uuid
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
from modules.approval_flow import ApprovalFlow
from modules.exporter import Exporter
from modules.checker import Checker
from modules.bulk_pack_generator import BulkPackGenerator
from modules.mode_registry import list_modes, get_mode

# ── i18n ─────────────────────────────────────────────────────────────────────

@st.cache_data
def load_i18n(lang: str) -> dict:
    path = ROOT / "i18n" / f"{lang}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def t(key_path: str) -> str:
    """Get translation string by dot-separated key path."""
    i18n = st.session_state.get("i18n", {})
    keys = key_path.split(".")
    val = i18n
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, key_path)
        else:
            return key_path
    return val if isinstance(val, str) else key_path


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
    background-color: #0f0f0f;
    color: #e8e8e8;
}
[data-testid="stSidebar"] {
    background-color: #0a0a0a;
    border-right: 1px solid #1e1e1e;
}
[data-testid="stSidebar"] * {
    color: #e8e8e8 !important;
}

/* ── Header bar ── */
.cs-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 0 20px 0;
    border-bottom: 1px solid #1e1e1e;
    margin-bottom: 24px;
}
.cs-logo {
    width: 36px; height: 36px;
    background: radial-gradient(circle at 40% 40%, #22c55e, #15803d);
    border-radius: 50%;
    display: inline-block;
    border: 2px solid #16a34a;
}
.cs-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #f0f0f0;
    letter-spacing: 0.02em;
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
.badge-pending    { background: #451a03; color: #fb923c; border: 1px solid #7c2d12; }
.badge-approved   { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.badge-revision   { background: #450a0a; color: #f87171; border: 1px solid #7f1d1d; }
.badge-draft      { background: #1c1c1c; color: #9ca3af; border: 1px solid #374151; }
.badge-ai         { background: #0c1a2e; color: #60a5fa; border: 1px solid #1e40af; }
.badge-generated  { background: #052e16; color: #4ade80; border: 1px solid #166534; }

/* ── Section header ── */
.section-header {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f0f0f0;
    margin-bottom: 8px;
}
.section-sub {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 24px;
}

/* ── Approval flow steps ── */
.approval-step {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 8px;
    background: #141414;
    border: 1px solid #1e1e1e;
}
.step-icon {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    font-size: 14px;
}
.step-done  { background: #052e16; border: 2px solid #22c55e; color: #22c55e; }
.step-active { background: #1c1917; border: 2px solid #f97316; color: #f97316; }
.step-wait  { background: #1c1c1c; border: 2px solid #374151; color: #6b7280; }
.step-info  h4 { margin: 0 0 4px; font-size: 0.875rem; color: #e8e8e8; }
.step-info  p  { margin: 0; font-size: 0.75rem; color: #6b7280; }

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
    border-color: #1e1e1e;
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
        "approval": {},
        "assignee": "",
        "reviewer": "",
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

@st.cache_resource
def get_services():
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
        "approval": ApprovalFlow(storage),
        "exporter": Exporter(),
        "checker": Checker(llm),
        "bulk": BulkPackGenerator(llm),
    }


svc = get_services()


# ── Helper: ensure product ID ─────────────────────────────────────────────────

def ensure_product_id() -> str:
    if not st.session_state.get("product_id"):
        st.session_state["product_id"] = str(uuid.uuid4())[:8]
    return st.session_state["product_id"]


# ── Status badge HTML ─────────────────────────────────────────────────────────

STATUS_BADGE_CLASS = {
    "draft": "badge-draft",
    "ai_generated": "badge-ai",
    "edited": "badge-ai",
    "pending": "badge-pending",
    "revision_requested": "badge-revision",
    "approved": "badge-approved",
    "ready": "badge-approved",
    "published": "badge-approved",
    "hold": "badge-draft",
}

STATUS_LABEL_JA = {
    "draft": "下書き",
    "ai_generated": "AI生成済み",
    "edited": "編集済み",
    "pending": "確認待ち",
    "revision_requested": "修正依頼",
    "approved": "承認済み",
    "ready": "公開準備OK",
    "published": "公開済み",
    "hold": "保留",
}
STATUS_LABEL_PT = {
    "draft": "Rascunho",
    "ai_generated": "Gerado pela IA",
    "edited": "Editado",
    "pending": "Aguardando revisão",
    "revision_requested": "Revisão solicitada",
    "approved": "Aprovado",
    "ready": "Pronto",
    "published": "Publicado",
    "hold": "Suspenso",
}


def status_badge(status: str) -> str:
    cls = STATUS_BADGE_CLASS.get(status, "badge-draft")
    labels = STATUS_LABEL_PT if st.session_state["lang"] == "pt" else STATUS_LABEL_JA
    label = labels.get(status, status)
    return f'<span class="badge {cls}">{label}</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        # Logo + title
        st.markdown(
            '<div class="cs-header">'
            '<div class="cs-logo"></div>'
            f'<div class="cs-title">Task Destroyer</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Language switcher
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

        # Current mode badge
        mode = get_mode(st.session_state["mode"])
        lang = st.session_state["lang"]
        mode_name = mode["name_ja"] if lang == "ja" else mode["name_pt"]
        st.markdown(f'<div style="font-size:0.75rem;color:#6b7280;margin-bottom:8px;">'
                    f'{mode["icon"]} {mode_name}</div>', unsafe_allow_html=True)

        # Navigation items
        nav_items = [
            ("mode_selection",    "🗂️  " + t("nav.mode_selection")),
            ("product_input",     "📦  " + t("nav.product_input")),
            ("external_core",     "📥  " + t("nav.external_core")),
            ("core_generation",   "✨  " + t("nav.core_generation")),
            ("product_page",      "📄  " + t("nav.product_page")),
            ("image_prompt",      "🖼️  " + t("nav.image_prompt")),
            ("video_script",      "🎬  " + t("nav.video_script")),
            ("ads_sns",           "📣  " + t("nav.ads_sns")),
            ("bulk_pack",         "⚡  " + t("nav.bulk_pack")),
            ("refinement",        "✍️  " + t("nav.refinement")),
            ("check",             "✅  " + t("nav.check")),
            ("approval",          "🔐  " + t("nav.approval")),
            ("output",            "📤  " + t("nav.output")),
            ("saved_data",        "💾  " + t("nav.saved_data")),
        ]

        for page_id, label in nav_items:
            is_active = st.session_state["page"] == page_id
            if st.button(
                label,
                key=f"nav_{page_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["page"] = page_id
                st.rerun()

        # Product info summary in sidebar
        if st.session_state.get("product_info", {}).get("name"):
            st.markdown("---")
            st.markdown(
                f'<div style="font-size:0.75rem;color:#6b7280;">商品</div>'
                f'<div style="font-size:0.875rem;color:#e8e8e8;font-weight:600;">'
                f'{st.session_state["product_info"]["name"]}</div>',
                unsafe_allow_html=True,
            )
        if st.session_state.get("core_text"):
            core_status = st.session_state.get("core_status", "ai_generated")
            st.markdown(
                f'Core: {status_badge(core_status)}',
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

    info = st.session_state.get("product_info", {})

    with st.form("product_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(t("product_input.name"), value=info.get("name", ""))
            category = st.selectbox(
                t("product_input.category"),
                ["美容・スキンケア", "健康・セルフケア", "インテリア・寝具", "時計・アクセサリー",
                 "ガジェット・電子機器", "アパレル・ファッション", "ギフト・プレゼント",
                 "ペット用品", "食品・飲料", "その他"],
                index=0 if not info.get("category") else None,
            )
            price = st.text_input(t("product_input.price"), value=info.get("price", ""))
            target = st.text_input(t("product_input.target"), value=info.get("target", ""))
            gender = st.selectbox(t("product_input.gender"), ["指定なし", "女性向け", "男性向け", "ユニセックス"])
            age = st.text_input(t("product_input.age"), value=info.get("age", ""))

        with col2:
            product_url = st.text_input(t("product_input.product_url"), value=info.get("product_url", ""))
            features = st.text_area(t("product_input.features"), value=info.get("features", ""), height=100)
            weaknesses = st.text_area(t("product_input.weaknesses"), value=info.get("weaknesses", ""), height=80)
            brand_tone = st.text_input(t("product_input.brand_tone"), value=info.get("brand_tone", ""))
            prohibited = st.text_input(t("product_input.prohibited_expressions"), value=info.get("prohibited", ""))

        description = st.text_area(t("product_input.description"), value=info.get("description", ""), height=120)
        use_scenes = st.text_area(t("product_input.use_scenes"), value=info.get("use_scenes", ""), height=80)
        competitor_urls = st.text_area(t("product_input.competitor_urls"), value=info.get("competitor_urls", ""), height=80)
        notes = st.text_area(t("product_input.notes"), value=info.get("notes", ""), height=60)

        col_a, col_b = st.columns(2)
        with col_a:
            assignee = st.text_input(t("product_input.assignee"), value=st.session_state.get("assignee", ""))
        with col_b:
            reviewer = st.text_input(t("product_input.reviewer"), value=st.session_state.get("reviewer", ""))

        submitted = st.form_submit_button(t("product_input.save_btn"), type="primary", use_container_width=True)

    if submitted:
        product_id = ensure_product_id()
        new_info = {
            "name": name, "category": category, "price": price,
            "target": target, "gender": gender, "age": age,
            "product_url": product_url, "features": features,
            "weaknesses": weaknesses, "brand_tone": brand_tone,
            "prohibited": prohibited, "description": description,
            "use_scenes": use_scenes, "competitor_urls": competitor_urls,
            "notes": notes,
        }
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

    product_info = st.session_state.get("product_info", {})
    if not product_info.get("name"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_product_warning") + '</div>',
                    unsafe_allow_html=True)
        return

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
        st.markdown("**📦 商品情報からCore自動生成**")

        info_summary = "\n".join(
            f"- **{k}**: {v}" for k, v in product_info.items() if v
        )
        with st.expander("入力中の商品情報を確認", expanded=False):
            st.markdown(info_summary)

        col_gen, col_regen = st.columns([2, 1])
        with col_gen:
            if st.button("✨ " + t("core.generate_btn"), type="primary", use_container_width=True):
                with st.spinner(t("core.generating_msg")):
                    result = svc["core_engine"].generate_from_product(product_info)
                    st.session_state["core_text"] = result
                    st.session_state["core_status"] = "ai_generated"
                    pid = ensure_product_id()
                    svc["storage"].save_core(pid, {"text": result, "status": "ai_generated"}, "v1 AI初稿")
                    svc["approval"].mark_ai_generated(pid, "core")
                    svc["storage"].log_activity(pid, "Core生成", "auto", st.session_state.get("assignee", ""))
                    st.rerun()

    # ── Reuse saved core ──
    elif method == "reuse":
        pid = ensure_product_id()
        cores = svc["storage"].list_cores(pid)
        if not cores:
            st.markdown('<div class="cs-info">💡 保存済みCoreがありません。まずCoreを生成してください。</div>',
                        unsafe_allow_html=True)
        else:
            options = [f"{c['version_label']} ({c.get('status', '')})" for c in cores]
            sel = st.selectbox("保存済みCoreを選択", options)
            if st.button("このCoreを使用", type="primary"):
                idx = options.index(sel)
                st.session_state["core_text"] = cores[idx]["core"].get("text", "")
                st.session_state["core_status"] = cores[idx].get("status", "ai_generated")
                st.success("Coreを読み込みました")
                st.rerun()

    # ── Core editor ──
    if st.session_state.get("core_text"):
        st.markdown("---")
        st.markdown("#### ✏️ Core編集")

        core_status = st.session_state.get("core_status", "ai_generated")
        st.markdown(
            f'<div style="margin-bottom:12px;">{status_badge(core_status)}</div>',
            unsafe_allow_html=True,
        )

        edited_core = st.text_area(
            "Core（編集可能）",
            value=st.session_state["core_text"],
            height=500,
            key="core_editor",
        )

        # Action buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("💾 " + t("core.save_btn"), type="primary", use_container_width=True):
                st.session_state["core_text"] = edited_core
                st.session_state["core_status"] = "edited"
                pid = ensure_product_id()
                svc["storage"].save_core(pid, {"text": edited_core, "status": "edited"}, "編集済み")
                svc["storage"].log_activity(pid, "Core編集・保存", "", st.session_state.get("assignee", ""))
                st.success(t("core.saved_msg"))

        with col2:
            if st.button("⏳ " + t("core.pending_btn"), use_container_width=True):
                st.session_state["core_text"] = edited_core
                st.session_state["core_status"] = "pending"
                pid = ensure_product_id()
                svc["approval"].set_pending(pid, "core", st.session_state.get("assignee", ""))
                st.success(t("core.pending_msg"))
                st.rerun()

        with col3:
            if st.button("📋 コピー", use_container_width=True):
                st.code(edited_core, language="")

        with col4:
            md_content = svc["exporter"].core_to_markdown(edited_core, product_info.get("name", ""))
            st.download_button(
                "⬇️ MD",
                data=md_content.encode("utf-8"),
                file_name=f"core_{product_info.get('name', 'product')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col5:
            if st.button("🔄 再生成", use_container_width=True):
                with st.spinner(t("core.generating_msg")):
                    result = svc["core_engine"].generate_from_product(product_info)
                    st.session_state["core_text"] = result
                    st.session_state["core_status"] = "ai_generated"
                    st.rerun()
    else:
        if method == "auto":
            st.markdown('<div class="cs-info">💡 「Core生成」ボタンを押してCoreを生成してください。</div>',
                        unsafe_allow_html=True)


# ── Page: External Core Import ────────────────────────────────────────────────

def page_external_core():
    st.markdown('<div class="section-header">📥 ' + t("external_core.title") + '</div>',
                unsafe_allow_html=True)

    lang = st.session_state["lang"]
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
                svc["approval"].mark_ai_generated(pid, "core")
                svc["storage"].log_activity(pid, "外部Core取り込み", source, "")
                st.rerun()

    with col2:
        if st.button("🌐 言語判定のみ", use_container_width=True):
            if external_text.strip():
                detected = svc["core_importer"].detect_language(external_text)
                st.info(f"検出言語: **{detected}**")

    if st.session_state.get("core_text") and "外部取り込み" in str(svc["storage"].list_cores(ensure_product_id())):
        st.markdown("---")
        st.markdown("**✅ 標準化されたCore（編集して保存してください）**")
        edited = st.text_area("Core（編集可能）", value=st.session_state["core_text"], height=400)
        if st.button("💾 このCoreを保存", type="primary"):
            st.session_state["core_text"] = edited
            st.session_state["core_status"] = "edited"
            pid = ensure_product_id()
            svc["storage"].save_core(pid, {"text": edited, "status": "edited"}, "外部取り込み・編集済み")
            st.success(t("core.saved_msg"))

    # Show current core if exists
    if st.session_state.get("core_text"):
        st.markdown("---")
        st.markdown("**現在のCore（確認用）**")
        st.markdown(
            f'<div class="generated-box">{st.session_state["core_text"][:2000]}...</div>'
            if len(st.session_state["core_text"]) > 2000
            else f'<div class="generated-box">{st.session_state["core_text"]}</div>',
            unsafe_allow_html=True,
        )
        if st.button("✏️ Core生成・編集画面へ"):
            st.session_state["page"] = "core_generation"
            st.rerun()


# ── Page: Product Page ────────────────────────────────────────────────────────

def render_generated_page(page_key: str, title: str, generate_fn, icon: str = "📄"):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        if st.button("✨ Core生成画面へ"):
            st.session_state["page"] = "core_generation"
            st.rerun()
        return

    product_info = st.session_state.get("product_info", {})
    core = st.session_state["core_text"]

    # Generate button
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button(f"✨ {t(f'{page_key}.generate_btn')}", type="primary", use_container_width=True):
            with st.spinner(t(f"{page_key}.generating_msg")):
                result = generate_fn(core, product_info)
                st.session_state["generated"][page_key] = result
                pid = ensure_product_id()
                svc["storage"].save_generated(pid, page_key, {"text": result})
                svc["approval"].mark_ai_generated(pid, page_key)
                svc["storage"].log_activity(pid, f"{title}生成", "", st.session_state.get("assignee", ""))
                st.rerun()

    with col2:
        if st.session_state["generated"].get(page_key):
            if st.button("⏳ 確認待ちにする", use_container_width=True):
                pid = ensure_product_id()
                svc["approval"].set_pending(pid, page_key, st.session_state.get("assignee", ""))
                st.success("確認待ちにしました")

    # Approval status
    pid = ensure_product_id()
    approval = svc["approval"].get_status(pid, page_key)
    st.markdown(f'<div style="margin-bottom:12px;">{status_badge(approval["status"])}</div>',
                unsafe_allow_html=True)

    # Content tabs
    if st.session_state["generated"].get(page_key):
        tab1, tab2 = st.tabs(["📄 生成結果", "✏️ 編集・保存"])

        with tab1:
            content = st.session_state["generated"][page_key]
            st.markdown(f'<div class="generated-box">{content}</div>', unsafe_allow_html=True)

        with tab2:
            content = st.session_state["generated"][page_key]
            edited = st.text_area("編集可能テキスト", value=content, height=600, key=f"edit_{page_key}")

            col_s, col_d, col_c = st.columns(3)
            with col_s:
                if st.button("💾 保存", type="primary", key=f"save_{page_key}", use_container_width=True):
                    st.session_state["generated"][page_key] = edited
                    svc["storage"].save_generated(pid, page_key, {"text": edited, "status": "edited"})
                    st.success(t("common.saved"))
            with col_d:
                st.download_button(
                    "⬇️ MD形式",
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
        st.markdown('<div class="cs-info">💡 生成ボタンを押してコンテンツを生成してください。</div>',
                    unsafe_allow_html=True)


def page_product_page():
    def gen(core, info):
        return svc["generator"].generate_product_page(core, info)
    render_generated_page("product_page", t("product_page.title"), gen, "📄")


def page_image_prompt():
    def gen(core, info):
        return svc["generator"].generate_image_prompts(
            core, info.get("name", ""), info.get("category", "")
        )
    render_generated_page("image_prompt", t("image_prompt.title"), gen, "🖼️")


def page_video_script():
    def gen(core, info):
        return svc["generator"].generate_video_scripts(core, info.get("name", ""))
    render_generated_page("video_script", t("video_script.title"), gen, "🎬")


def page_ads_sns():
    def gen(core, info):
        return svc["generator"].generate_sns_content(core, info.get("name", ""))
    render_generated_page("ads_sns", t("ads_sns.title"), gen, "📣")


# ── Page: Bulk Pack ────────────────────────────────────────────────────────────

def page_bulk_pack():
    st.markdown('<div class="section-header">⚡ ' + t("bulk_pack.title") + '</div>',
                unsafe_allow_html=True)

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
    pack_label = dict(packs).get(pack_id, "パック")

    if st.button(f"⚡ {pack_label}を生成", type="primary", use_container_width=False):
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
                edited = st.text_area(f"編集可能（{key}）", value=value, height=400, key=f"bulk_edit_{pack_id}_{key}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 保存", key=f"bulk_save_{pack_id}_{key}", use_container_width=True):
                        result[key] = edited
                        st.session_state["generated"][f"bulk_{pack_id}"] = result
                        st.success(t("common.saved"))
                with col2:
                    st.download_button(
                        "⬇️ ダウンロード",
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
    tab1, tab2, tab3 = st.tabs(["🇯🇵 日本語補正", "🔄 PT→JA", "🔄 JA→PT"])

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
        st.markdown("**ポルトガル語 → 日本語（日本市場向け自然化）**")
        pt_text = st.text_area("ポルトガル語テキスト", height=200, key="pt_input")
        if st.button("🔄 " + t("refinement.pt_to_ja_btn"), type="primary"):
            if pt_text.strip():
                with st.spinner("変換中..."):
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
        st.markdown("**日本語 → ポルトガル語（ブラジル）**")
        ja_text = st.text_area("日本語テキスト", height=200, key="ja_input")
        if st.button("🔄 " + t("refinement.ja_to_pt_btn"), type="primary"):
            if ja_text.strip():
                with st.spinner("翻訳中..."):
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

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        return

    core = st.session_state["core_text"]

    tab1, tab2 = st.tabs(["🔍 整合性チェック", "⚠️ リスク表現チェック"])

    with tab1:
        content_type = st.selectbox("チェック対象", ["product_page", "image_prompt", "video_script", "ads_sns"])
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
            st.markdown('<div class="cs-info">💡 先に対象コンテンツを生成してください。</div>',
                        unsafe_allow_html=True)

    with tab2:
        text_to_check = st.text_area("チェックしたいテキストを入力", height=200)
        if st.button("⚠️ リスク表現をチェック", type="primary"):
            if text_to_check.strip():
                with st.spinner(t("check.checking_msg")):
                    result = svc["checker"].check_risk_expressions(text_to_check)
                    st.session_state["risk_check_result"] = result
                    st.rerun()
        if st.session_state.get("risk_check_result"):
            st.markdown(f'<div class="generated-box">{st.session_state["risk_check_result"]}</div>',
                        unsafe_allow_html=True)


# ── Page: Approval Flow ────────────────────────────────────────────────────────

def page_approval():
    st.markdown('<div class="section-header">🔐 ' + t("approval.title") + '</div>',
                unsafe_allow_html=True)

    pid = ensure_product_id()
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "未設定")

    # Approval flow visual
    st.markdown("### 承認フロー")

    core_status = svc["approval"].get_status(pid, "core").get("status", "draft")

    steps = [
        ("AI生成", t("approval.ai_generated_desc"),
         "step-done" if core_status not in ("draft",) else "step-wait", "✓"),
        ("担当者編集", t("approval.edit_desc"),
         "step-done" if core_status in ("edited", "pending", "approved") else "step-active" if core_status == "ai_generated" else "step-wait", "✓" if core_status in ("edited", "pending", "approved") else "✎"),
        ("確認待ち", t("approval.pending_desc"),
         "step-active" if core_status == "pending" else "step-done" if core_status in ("approved",) else "step-wait", "⏱" if core_status == "pending" else "✓" if core_status == "approved" else "○"),
        ("承認済み", t("approval.approved_desc"),
         "step-done" if core_status == "approved" else "step-wait", "🛡" if core_status == "approved" else "○"),
    ]

    for title, desc, cls, icon in steps:
        st.markdown(
            f'<div class="approval-step">'
            f'<div class="step-icon {cls}">{icon}</div>'
            f'<div class="step-info"><h4>{title}</h4><p>{desc}</p></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Content approval status overview
    st.markdown("### 各コンテンツのステータス")

    content_types = [
        ("core", "Core / 核"),
        ("product_page", "商品ページ"),
        ("image_prompt", "画像プロンプト"),
        ("video_script", "動画台本"),
        ("ads_sns", "広告・SNS"),
    ]

    for ct, label in content_types:
        approval = svc["approval"].get_status(pid, ct)
        status = approval.get("status", "draft")
        comment = approval.get("comment", "")

        col1, col2, col3 = st.columns([3, 2, 3])
        with col1:
            st.markdown(f'**{label}** {status_badge(status)}', unsafe_allow_html=True)
        with col2:
            if status in ("ai_generated", "edited", "revision_requested"):
                if st.button("⏳ 確認待ち", key=f"pend_{ct}", use_container_width=True):
                    svc["approval"].set_pending(pid, ct, st.session_state.get("assignee", ""))
                    st.rerun()
        with col3:
            if status == "pending":
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ 承認", key=f"appr_{ct}", use_container_width=True, type="primary"):
                        svc["approval"].approve(pid, ct, user=st.session_state.get("reviewer", "管理者"))
                        svc["storage"].log_activity(pid, "承認", ct, st.session_state.get("reviewer", ""))
                        st.rerun()
                with col_b:
                    if st.button("🔄 修正依頼", key=f"rev_{ct}", use_container_width=True):
                        svc["approval"].request_revision(pid, ct, comment)
                        st.rerun()

        if comment:
            st.markdown(f'<div class="cs-info" style="margin-top:4px;margin-bottom:8px;">💬 {comment}</div>',
                        unsafe_allow_html=True)

    # Global comment for revision request
    st.markdown("---")
    st.markdown("### 修正依頼コメント")
    ct_select = st.selectbox("対象コンテンツ", [ct for ct, _ in content_types], format_func=lambda x: dict(content_types)[x])
    comment_text = st.text_area("コメント", placeholder="修正してほしい内容を記入してください", height=100)
    if st.button("🔄 修正依頼を送る", type="primary"):
        svc["approval"].request_revision(pid, ct_select, comment_text, st.session_state.get("reviewer", ""))
        st.success(f"修正依頼を送りました: {comment_text}")
        st.rerun()

    # Activity log
    st.markdown("---")
    with st.expander("📋 作業ログを見る"):
        logs = svc["storage"].get_activity_log(pid)
        if logs:
            for log in reversed(logs[-20:]):
                st.markdown(
                    f'<div style="font-size:0.8rem;color:#9ca3af;padding:4px 0;">'
                    f'[{log["timestamp"]}] <span style="color:#e8e8e8;">{log["action"]}</span> '
                    f'<span style="color:#6b7280;">{log.get("detail","")}</span>'
                    f' — {log.get("user","")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("ログがありません")


# ── Page: Output ──────────────────────────────────────────────────────────────

def page_output():
    st.markdown('<div class="section-header">📤 ' + t("output.title") + '</div>',
                unsafe_allow_html=True)

    pid = ensure_product_id()
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "output")

    approved_only = st.checkbox(t("output.approved_only"), value=False)

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

        # Check approval if needed
        if approved_only and content_type:
            is_appr = svc["approval"].is_approved(pid, content_type)
            if not is_appr:
                continue

        export_data[label] = content

        with st.expander(f"📄 {label}", expanded=False):
            if content_type:
                approval = svc["approval"].get_status(pid, content_type)
                st.markdown(f'{status_badge(approval["status"])}', unsafe_allow_html=True)
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
        st.markdown('<div class="cs-info">💡 生成されたコンテンツがありません。各ページでコンテンツを生成してください。</div>',
                    unsafe_allow_html=True)


# ── Page: Saved Data ──────────────────────────────────────────────────────────

def page_saved_data():
    st.markdown('<div class="section-header">💾 ' + t("nav.saved_data") + '</div>',
                unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💼 商品プロジェクト", "📚 Coreライブラリ"])

    with tab1:
        products = svc["storage"].list_products()
        if not products:
            st.markdown("保存済み商品がありません")
        else:
            for p in products:
                with st.expander(f"📦 {p.get('name', '不明')} ({p.get('category', '')})"):
                    st.markdown(f"**価格:** {p.get('price', '-')}")
                    st.markdown(f"**ターゲット:** {p.get('target', '-')}")
                    st.markdown(f"**更新日:** {p.get('updated_at', '-')}")
                    if st.button("このプロジェクトを読み込む", key=f"load_{p['id']}"):
                        st.session_state["product_id"] = p["id"]
                        st.session_state["product_info"] = {k: v for k, v in p.items() if k != "id"}
                        # Load latest core
                        core_entry = svc["storage"].load_latest_core(p["id"])
                        if core_entry:
                            st.session_state["core_text"] = core_entry["core"].get("text", "")
                            st.session_state["core_status"] = core_entry.get("status", "ai_generated")
                        st.success(f"'{p.get('name')}' を読み込みました")
                        st.rerun()

    with tab2:
        pid = ensure_product_id()
        cores = svc["storage"].list_cores(pid)
        if not cores:
            st.markdown("保存済みCoreがありません")
        else:
            for c in reversed(cores):
                with st.expander(f"📝 {c['version_label']} — {c.get('status', '')} ({c['created_at']})"):
                    core_text = c["core"].get("text", "")
                    st.text_area("Core内容", value=core_text[:1000] + "..." if len(core_text) > 1000 else core_text,
                                 height=200, key=f"saved_core_{c['id']}", disabled=True)
                    if st.button("このCoreを使用", key=f"use_core_{c['id']}"):
                        st.session_state["core_text"] = core_text
                        st.session_state["core_status"] = c.get("status", "ai_generated")
                        st.success("Coreを読み込みました")
                        st.rerun()


# ── Page: Custom Mode ──────────────────────────────────────────────────────────

def page_custom_mode():
    st.markdown('<div class="section-header">⚙️ Custom Mode</div>', unsafe_allow_html=True)
    st.markdown('<div class="cs-info">💡 Custom Modeは将来拡張用の自由入力モードです。</div>',
                unsafe_allow_html=True)

    user_input = st.text_area("自由入力（任意のコンテンツ生成）", height=300,
                               placeholder="コンテンツの概要、目的、ターゲットなどを自由に入力してください")

    if st.button("✨ 生成", type="primary"):
        if user_input.strip():
            from modes.custom.custom_core import CustomCore
            cc = CustomCore(svc["llm"])
            with st.spinner("生成中..."):
                result = cc.generate(user_input)
                st.session_state["custom_result"] = result
                st.rerun()

    if st.session_state.get("custom_result"):
        st.markdown("**生成結果**")
        edited = st.text_area("編集可能", value=st.session_state["custom_result"], height=400)
        if st.button("💾 保存", type="primary"):
            st.session_state["custom_result"] = edited
            st.success("保存しました")


# ── Main router ───────────────────────────────────────────────────────────────

def main():
    render_sidebar()

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
        "approval": page_approval,
        "output": page_output,
        "saved_data": page_saved_data,
    }

    render_fn = page_map.get(page, page_mode_selection)
    render_fn()


if __name__ == "__main__":
    main()
