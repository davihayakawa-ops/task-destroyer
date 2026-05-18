"""Stripe billing helpers for plan updates."""

from __future__ import annotations

import json
from typing import Any, Optional

from modules.config import secret_or_env
from modules.supabase_db import SupabaseRepository


VALID_PLANS = {"free", "starter", "pro", "team"}

PLAN_DEFAULT_LIMITS = {
    "free": 100,
    "starter": 500,
    "pro": 2000,
    "team": 5000,
}


def _json_dict(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def stripe_enabled() -> bool:
    return bool(secret_or_env("STRIPE_SECRET_KEY") and secret_or_env("STRIPE_WEBHOOK_SECRET"))


def price_plan_map() -> dict[str, str]:
    loaded = _json_dict(secret_or_env("STRIPE_PRICE_PLAN_MAP"))
    return {str(k): str(v).strip().lower() for k, v in loaded.items() if str(v).strip()}


def plan_price_map() -> dict[str, str]:
    raw = secret_or_env("STRIPE_PLAN_PRICE_MAP")
    if raw:
        loaded = _json_dict(raw)
        return {str(k).strip().lower(): str(v) for k, v in loaded.items() if str(v).strip()}

    inverse = {}
    for price_id, plan in price_plan_map().items():
        inverse.setdefault(plan, price_id)
    return inverse


def price_for_plan(plan: str) -> str:
    return plan_price_map().get(str(plan or "").strip().lower(), "")


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


def billing_config_status() -> dict[str, Any]:
    """Return a user-facing Stripe/Billing readiness summary."""
    required = {
        "STRIPE_SECRET_KEY": secret_or_env("STRIPE_SECRET_KEY"),
        "STRIPE_WEBHOOK_SECRET": secret_or_env("STRIPE_WEBHOOK_SECRET"),
        "BILLING_API_KEY": secret_or_env("BILLING_API_KEY"),
        "BILLING_API_BASE_URL": secret_or_env("BILLING_API_BASE_URL"),
    }
    missing = [key for key, value in required.items() if not value]

    plan_to_price = plan_price_map()
    paid_plans = ["starter", "pro", "team"]
    missing_prices = [plan for plan in paid_plans if not plan_to_price.get(plan)]

    raw_price_plan = secret_or_env("STRIPE_PRICE_PLAN_MAP")
    raw_plan_price = secret_or_env("STRIPE_PLAN_PRICE_MAP")
    invalid_json = []
    for key, raw in {
        "STRIPE_PRICE_PLAN_MAP": raw_price_plan,
        "STRIPE_PLAN_PRICE_MAP": raw_plan_price,
        "TASK_DESTROYER_PLAN_LIMITS": secret_or_env("TASK_DESTROYER_PLAN_LIMITS"),
    }.items():
        if raw and not _json_dict(raw):
            invalid_json.append(key)

    invalid_plans = sorted(
        plan for plan in set(price_plan_map().values()) | set(plan_to_price.keys())
        if plan and plan not in VALID_PLANS
    )

    return {
        "ready": not missing and not missing_prices and not invalid_json and not invalid_plans,
        "checkout_ready": not missing and not missing_prices,
        "missing": missing,
        "missing_prices": missing_prices,
        "invalid_json": invalid_json,
        "invalid_plans": invalid_plans,
        "configured_prices": {plan: price for plan, price in plan_to_price.items() if price},
    }


def plan_for_price(price_id: str, fallback: str = "") -> str:
    mapped = price_plan_map().get(str(price_id or ""))
    if mapped:
        return mapped
    fallback = str(fallback or "").strip().lower()
    return fallback if fallback in VALID_PLANS else "free"


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
    if clean_plan not in VALID_PLANS:
        clean_plan = "free"
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
