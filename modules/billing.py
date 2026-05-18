"""Stripe billing helpers for plan updates."""

from __future__ import annotations

import json
from typing import Any, Optional

from modules.config import secret_or_env
from modules.supabase_db import SupabaseRepository


PLAN_DEFAULT_LIMITS = {
    "free": 100,
    "starter": 500,
    "pro": 2000,
    "team": 5000,
}


def stripe_enabled() -> bool:
    return bool(secret_or_env("STRIPE_SECRET_KEY") and secret_or_env("STRIPE_WEBHOOK_SECRET"))


def price_plan_map() -> dict[str, str]:
    raw = secret_or_env("STRIPE_PRICE_PLAN_MAP")
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(loaded, dict):
        return {}
    return {str(k): str(v).strip().lower() for k, v in loaded.items() if str(v).strip()}


def plan_limits() -> dict[str, int]:
    raw = secret_or_env("TASK_DESTROYER_PLAN_LIMITS")
    result = dict(PLAN_DEFAULT_LIMITS)
    if not raw:
        return result
    try:
        loaded = json.loads(raw)
    except Exception:
        return result
    if not isinstance(loaded, dict):
        return result
    for key, value in loaded.items():
        try:
            result[str(key).strip().lower()] = max(int(value), 0)
        except Exception:
            continue
    return result


def limit_for_plan(plan: str) -> int:
    return plan_limits().get(str(plan or "free").lower(), PLAN_DEFAULT_LIMITS["free"])


def plan_for_price(price_id: str, fallback: str = "") -> str:
    mapped = price_plan_map().get(str(price_id or ""))
    if mapped:
        return mapped
    fallback = str(fallback or "").strip().lower()
    return fallback if fallback else "free"


def extract_price_id_from_subscription(subscription: dict[str, Any]) -> str:
    items = (((subscription or {}).get("items") or {}).get("data") or [])
    if not items:
        return ""
    price = (items[0] or {}).get("price") or {}
    return str(price.get("id") or "")


def apply_plan_to_workspace(
    workspace_id: str,
    plan: str,
    *,
    customer_id: str = "",
    subscription_id: str = "",
    subscription_status: str = "",
    repo: Optional[SupabaseRepository] = None,
) -> dict[str, Any]:
    clean_plan = str(plan or "free").strip().lower()
    repository = repo or SupabaseRepository()
    return repository.update_workspace_billing(
        workspace_id,
        {
            "plan": clean_plan,
            "monthly_call_limit": limit_for_plan(clean_plan),
            "stripe_customer_id": customer_id or None,
            "stripe_subscription_id": subscription_id or None,
            "subscription_status": subscription_status or None,
        },
    )

