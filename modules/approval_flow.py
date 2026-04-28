from datetime import datetime
from .storage import Storage

STATUSES = [
    "draft",
    "ai_generated",
    "edited",
    "pending",
    "revision_requested",
    "approved",
    "ready",
    "published",
]

STATUS_FLOW = {
    "draft": ["ai_generated", "pending"],
    "ai_generated": ["edited", "pending"],
    "edited": ["pending"],
    "pending": ["revision_requested", "approved", "hold"],
    "revision_requested": ["edited", "pending"],
    "approved": ["ready"],
    "ready": ["published"],
    "published": [],
}


class ApprovalFlow:
    def __init__(self, storage: Storage):
        self.storage = storage

    def get_status(self, product_id: str, content_type: str) -> dict:
        approval = self.storage.get_approval(product_id, content_type)
        if not approval:
            return {"status": "draft", "comment": "", "updated_at": ""}
        return approval

    def set_pending(self, product_id: str, content_type: str, user: str = "") -> bool:
        self.storage.update_approval(product_id, content_type, "pending")
        self.storage.log_activity(product_id, "確認待ちに変更", content_type, user)
        return True

    def approve(self, product_id: str, content_type: str, comment: str = "", user: str = "") -> bool:
        self.storage.update_approval(product_id, content_type, "approved", comment)
        self.storage.log_activity(product_id, "承認", f"{content_type}: {comment}", user)
        return True

    def request_revision(self, product_id: str, content_type: str, comment: str = "", user: str = "") -> bool:
        self.storage.update_approval(product_id, content_type, "revision_requested", comment)
        self.storage.log_activity(product_id, "修正依頼", f"{content_type}: {comment}", user)
        return True

    def hold(self, product_id: str, content_type: str, comment: str = "", user: str = "") -> bool:
        self.storage.update_approval(product_id, content_type, "hold", comment)
        self.storage.log_activity(product_id, "保留", f"{content_type}: {comment}", user)
        return True

    def mark_ai_generated(self, product_id: str, content_type: str) -> bool:
        self.storage.update_approval(product_id, content_type, "ai_generated")
        return True

    def is_approved(self, product_id: str, content_type: str) -> bool:
        status = self.get_status(product_id, content_type)
        return status.get("status") in ("approved", "ready", "published")
