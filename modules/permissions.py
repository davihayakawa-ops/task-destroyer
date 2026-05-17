"""Permission helpers."""

from modules.auth import current_user


def get_current_role() -> str:
    return current_user().get("role", "member")


def get_current_user() -> str:
    user = current_user()
    return user.get("name") or user.get("email") or "User"


def can_view_page(page_id: str) -> bool:
    return True


def filter_nav_items(items: list) -> list:
    return items


def can_perform_action(action: str) -> bool:
    role = get_current_role()
    if role == "admin":
        return True

    admin_only_actions = {
        "backup",
        "cleanup_empty",
        "delete_project",
        "delete_shop",
        "purge_trash",
        "restore",
    }
    return action not in admin_only_actions
