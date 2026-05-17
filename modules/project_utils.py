"""Project utility helpers for Task Destroyer / core_studio.

Extracted from app.py. Contains status constants, status_badge,
ensure_product_id, and project session helpers.
"""

import uuid
import streamlit as st


# ── Status badge HTML ─────────────────────────────────────────────────────────

STATUS_BADGE_CLASS = {
    "draft": "badge-draft",
    "ai_generated": "badge-ai",
    "edited": "badge-ai",
    "published": "badge-success",
    "imported": "badge-ai",
}

STATUS_LABEL_JA = {
    "draft": "下書き",
    "ai_generated": "AI生成済み",
    "edited": "編集済み",
    "published": "公開済み",
    "imported": "取り込み済み",
}

STATUS_LABEL_PT = {
    "draft": "Rascunho",
    "ai_generated": "Gerado pela IA",
    "edited": "Editado",
    "published": "Publicado",
    "imported": "Importado",
}


def status_badge(status: str) -> str:
    cls = STATUS_BADGE_CLASS.get(status, "badge-draft")
    labels = STATUS_LABEL_PT if st.session_state["lang"] == "pt" else STATUS_LABEL_JA
    label = labels.get(status, status)
    return f'<span class="badge {cls}">{label}</span>'


# ── Helper: ensure product ID ─────────────────────────────────────────────────

def ensure_product_id() -> str:
    if not st.session_state.get("product_id"):
        st.session_state["product_id"] = str(uuid.uuid4())[:8]
    return st.session_state["product_id"]


# ── Project session helpers ───────────────────────────────────────────────────

def load_project_session(pid: str, p: dict, svc: dict):
    """Restore a full project into session state.
    Loads product_info, assignee, core, AND all previously generated content.
    Call this whenever a user loads/switches to an existing project."""
    # Clear stale state from previous project
    st.session_state["generated"] = {}
    st.session_state["core_text"] = ""
    st.session_state["core_status"] = "draft"
    st.session_state["external_core_text"] = ""
    for _cat in ("image_prompts", "video_scripts", "ads_sns_items"):
        st.session_state.pop(_cat, None)

    # Project identity
    st.session_state["product_id"] = pid
    st.session_state["product_info"] = {k: v for k, v in p.items()
                                        if k not in ("id", "file_path")}
    st.session_state["assignee"] = p.get("assignee", "")
    st.session_state["reviewer"] = p.get("final_reviewer", "")
    st.session_state["generation_target_market"] = p.get("target_market") or "japan"
    st.session_state["generation_output_language"] = p.get("output_language") or "ja"
    st.session_state["generation_market_note"] = p.get("market_note") or ""
    st.session_state["_market_loaded_for_product"] = pid

    # Core
    try:
        core_entry = svc["storage"].load_latest_core(pid)
        if core_entry:
            st.session_state["core_text"]   = core_entry["core"].get("text", "")
            st.session_state["core_status"] = core_entry.get("status", "ai_generated")
    except Exception:
        pass

    # All generated content (Phase 3: previously missing)
    try:
        all_gen = svc["storage"].load_all_generated(pid)
        st.session_state["generated"].update(all_gen)
    except Exception:
        pass


def is_empty_project_entry(p: dict) -> bool:
    """Return True if the project has no meaningful content (name/url/description all empty)."""
    name = str(p.get("name") or "").strip()
    url = str(p.get("product_url") or "").strip()
    desc = str(p.get("description") or "").strip()
    return not name and not url and not desc


def do_delete_project(pid: str, file_path: str, delete_reason: str) -> dict:
    """Run delete_project via a fresh Storage instance; normalise the result."""
    from modules.storage import Storage as _Storage
    storage = _Storage(st.session_state.get("shop_id", "default"))
    deleted_by = st.session_state.get("assignee", "")
    try:
        result = storage.delete_project(pid, deleted_by, delete_reason, file_path=file_path)
        if isinstance(result, list):
            result = {"success": True, "message": "削除しました", "deleted_paths": result}
    except Exception as e:
        result = {"success": False, "message": str(e), "deleted_paths": []}
    return result
