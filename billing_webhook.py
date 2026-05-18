"""FastAPI endpoint for Stripe billing webhooks.

Deploy this separately from the Streamlit UI when selling publicly.
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

from modules.billing import (
    apply_plan_to_workspace,
    extract_price_id_from_subscription,
    price_for_plan,
    plan_for_price,
    stripe_enabled,
)
from modules.config import secret_or_env
from modules.supabase_db import SupabaseRepository

app = FastAPI(title="Task Destroyer Billing Webhook")


class CheckoutRequest(BaseModel):
    workspace_id: str
    plan: str
    customer_email: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@app.get("/health")
def health():
    return {"ok": True, "stripe": stripe_enabled()}


def _require_billing_api_key(api_key: str) -> None:
    expected = secret_or_env("BILLING_API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="BILLING_API_KEY is not configured")
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid billing API key")


def _stripe_client():
    try:
        import stripe
    except Exception as exc:
        raise HTTPException(status_code=500, detail="stripe package is not installed") from exc

    stripe.api_key = secret_or_env("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY is not configured")
    return stripe


def _checkout_url(kind: str, override: str = "") -> str:
    if override:
        return override
    configured = secret_or_env(f"STRIPE_{kind.upper()}_URL")
    if configured:
        return configured
    app_base = secret_or_env("APP_BASE_URL")
    if app_base:
        suffix = "billing=success" if kind == "success" else "billing=cancel"
        separator = "&" if "?" in app_base else "?"
        return f"{app_base}{separator}{suffix}"
    raise HTTPException(status_code=500, detail=f"STRIPE_{kind.upper()}_URL or APP_BASE_URL is required")


def _stripe_value(obj, key: str) -> str:
    if hasattr(obj, key):
        return str(getattr(obj, key) or "")
    if isinstance(obj, dict):
        return str(obj.get(key) or "")
    return ""


@app.post("/stripe/checkout-session")
def create_checkout_session(
    request: CheckoutRequest,
    x_billing_api_key: str = Header(default="", alias="X-Billing-Api-Key"),
):
    _require_billing_api_key(x_billing_api_key)

    workspace_id = request.workspace_id.strip()
    plan = request.plan.strip().lower()
    if not workspace_id or not plan:
        raise HTTPException(status_code=400, detail="workspace_id and plan are required")

    repo = SupabaseRepository()
    workspace = repo.load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    price_id = price_for_plan(plan)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"No Stripe price configured for plan: {plan}")

    stripe = _stripe_client()
    metadata = {
        "workspace_id": workspace_id,
        "plan": plan,
        "price_id": price_id,
    }
    session_args = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": _checkout_url("success", request.success_url or ""),
        "cancel_url": _checkout_url("cancel", request.cancel_url or ""),
        "client_reference_id": workspace_id,
        "metadata": metadata,
        "subscription_data": {"metadata": metadata},
    }
    if request.customer_email:
        session_args["customer_email"] = request.customer_email.strip().lower()

    session = stripe.checkout.Session.create(**session_args)
    return {
        "id": _stripe_value(session, "id"),
        "url": _stripe_value(session, "url"),
        "workspace_id": workspace_id,
        "plan": plan,
        "price_id": price_id,
    }


def _stripe_event(payload: bytes, signature: str):
    try:
        import stripe
    except Exception as exc:
        raise HTTPException(status_code=500, detail="stripe package is not installed") from exc

    stripe.api_key = secret_or_env("STRIPE_SECRET_KEY")
    endpoint_secret = secret_or_env("STRIPE_WEBHOOK_SECRET")
    if not stripe.api_key or not endpoint_secret:
        raise HTTPException(status_code=500, detail="Stripe secrets are not configured")

    try:
        return stripe.Webhook.construct_event(payload, signature, endpoint_secret)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe payload") from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature") from exc


def _checkout_completed(session: dict):
    metadata = session.get("metadata") or {}
    workspace_id = str(metadata.get("workspace_id") or session.get("client_reference_id") or "")
    if not workspace_id:
        return {"ignored": True, "reason": "missing_workspace_id"}

    plan = str(metadata.get("plan") or "").strip().lower()
    price_id = str(metadata.get("price_id") or "")
    plan = plan_for_price(price_id, plan)

    apply_plan_to_workspace(
        workspace_id,
        plan,
        customer_id=str(session.get("customer") or ""),
        subscription_id=str(session.get("subscription") or ""),
        subscription_status="active",
    )
    return {"updated": True, "workspace_id": workspace_id, "plan": plan}


def _subscription_changed(subscription: dict):
    customer_id = str(subscription.get("customer") or "")
    subscription_id = str(subscription.get("id") or "")
    repo = SupabaseRepository()
    workspace = repo.load_workspace_by_stripe(customer_id=customer_id, subscription_id=subscription_id)
    if not workspace:
        return {"ignored": True, "reason": "workspace_not_found"}

    status = str(subscription.get("status") or "")
    price_id = extract_price_id_from_subscription(subscription)
    plan = "free" if status in {"canceled", "unpaid", "incomplete_expired"} else plan_for_price(price_id, workspace.get("plan", "free"))

    apply_plan_to_workspace(
        str(workspace["id"]),
        plan,
        customer_id=customer_id,
        subscription_id=subscription_id,
        subscription_status=status,
        repo=repo,
    )
    return {"updated": True, "workspace_id": str(workspace["id"]), "plan": plan, "status": status}


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(default="", alias="Stripe-Signature")):
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    event = _stripe_event(payload, stripe_signature)
    event_type = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}

    if event_type == "checkout.session.completed":
        result = _checkout_completed(obj)
    elif event_type in {"customer.subscription.updated", "customer.subscription.deleted"}:
        result = _subscription_changed(obj)
    else:
        result = {"ignored": True, "type": event_type}

    return {"received": True, **result}
