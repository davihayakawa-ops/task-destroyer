"""FastAPI endpoint for Stripe billing webhooks.

Deploy this separately from the Streamlit UI when selling publicly.
"""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request

from modules.billing import (
    apply_plan_to_workspace,
    extract_price_id_from_subscription,
    plan_for_price,
    stripe_enabled,
)
from modules.config import secret_or_env
from modules.supabase_db import SupabaseRepository

app = FastAPI(title="Task Destroyer Billing Webhook")


@app.get("/health")
def health():
    return {"ok": True, "stripe": stripe_enabled()}


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

