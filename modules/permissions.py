import streamlit as st

# Pages accessible to product_researcher role
_RESEARCHER_PAGES: frozenset[str] = frozenset({
    "dashboard",
    "mode_selection",
    "product_input",
    "saved_data",
})

# Dev role switcher options: display label -> (user_name, role)
DEV_ROLE_OPTIONS: dict[str, tuple[str, str]] = {
    "Davi (admin)":               ("davi",  "admin"),
    "Sara (admin)":               ("sara",  "admin"),
    "Iago (product_researcher)":  ("iago",  "product_researcher"),
}


def get_current_role() -> str:
    return st.session_state.get("dev_role", "admin")


def get_current_user() -> str:
    return st.session_state.get("dev_user", "davi")


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
_RESEARCHER_ACTIONS: frozenset[str] = frozenset({
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
