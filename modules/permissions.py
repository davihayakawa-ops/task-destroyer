import streamlit as st

# Pages accessible to product_researcher role
_RESEARCHER_PAGES = frozenset({
    "dashboard",
    "mode_selection",
    "product_input",
    "saved_data",
})

# Dev role switcher options: display label -> (user_name, role)
DEV_ROLE_OPTIONS = {
    "Davi (admin)":               ("Davi",  "admin"),
    "Sara (admin)":               ("Sara",  "admin"),
    "Iago (product_researcher)":  ("Iago",  "product_researcher"),
}


def get_current_role() -> str:
    return st.session_state.get("dev_role", "admin")


def get_current_user() -> str:
    return st.session_state.get("dev_user", "Davi")


def can_view_page(page_id: str) -> bool:
    role = get_current_role()
    if role == "admin":
        return True
    if role == "product_researcher":
        return page_id in _RESEARCHER_PAGES
    # viewer or unknown
    return False


def filter_nav_items(items: list) -> list:
    """Filter _NAV_GROUPS items (page_id, lbl_ja, lbl_pt, key_sfx) by current role."""
    role = get_current_role()
    if role == "admin":
        return items
    if role == "product_researcher":
        return [item for item in items if item[0] in _RESEARCHER_PAGES]
    return []


# Actions allowed for product_researcher
_RESEARCHER_ACTIONS = frozenset({
    "save_product",
    "load_project",
    "product_prep_done",
})


def can_perform_action(action: str) -> bool:
    role = get_current_role()
    if role == "admin":
        return True
    if role == "product_researcher":
        return action in _RESEARCHER_ACTIONS
    return False


def can_generate_core(project: dict) -> bool:
    """Return True only when role is admin AND product prep is approved."""
    if get_current_role() != "admin":
        return False
    return (
        project.get("product_prep_approved") is True
        and project.get("product_prep_status") == "approved"
    )
