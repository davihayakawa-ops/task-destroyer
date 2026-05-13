"""Permission helpers.

Task Destroyer is currently a single shared workspace, so every user can view
every page and perform every action.
"""


def get_current_role() -> str:
    return "admin"


def get_current_user() -> str:
    return "User"


def can_view_page(page_id: str) -> bool:
    return True


def filter_nav_items(items: list) -> list:
    return items


def can_perform_action(action: str) -> bool:
    return True
