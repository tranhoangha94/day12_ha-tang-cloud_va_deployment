"""Redis-based monthly cost guard."""
import logging
import time

from fastapi import HTTPException

from app.config import settings
from app.redis_client import get_redis

logger = logging.getLogger(__name__)

PRICE_PER_1K_INPUT = 0.00015
PRICE_PER_1K_OUTPUT = 0.0006


def _month_key(user_id: str) -> str:
    return f"cost:{user_id}:{time.strftime('%Y-%m')}"


def _global_month_key() -> str:
    return f"cost:global:{time.strftime('%Y-%m')}"


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        (input_tokens / 1000) * PRICE_PER_1K_INPUT
        + (output_tokens / 1000) * PRICE_PER_1K_OUTPUT
    )


def check_budget(user_id: str) -> None:
    r = get_redis()
    used = float(r.get(_month_key(user_id)) or 0)
    global_used = float(r.get(_global_month_key()) or 0)

    if global_used >= settings.monthly_budget_usd:
        raise HTTPException(
            status_code=503,
            detail="Service budget exhausted for this month.",
        )

    if used >= settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "used_usd": round(used, 4),
                "budget_usd": settings.monthly_budget_usd,
                "resets_at": "first day of next month",
            },
        )

    if used >= settings.monthly_budget_usd * settings.budget_warn_pct:
        logger.warning(
            "User %s at %.0f%% monthly budget",
            user_id,
            used / settings.monthly_budget_usd * 100,
        )


def record_usage(user_id: str, input_tokens: int, output_tokens: int) -> float:
    cost = _estimate_cost(input_tokens, output_tokens)
    if cost <= 0:
        return 0.0

    r = get_redis()
    pipe = r.pipeline()
    pipe.incrbyfloat(_month_key(user_id), cost)
    pipe.incrbyfloat(_global_month_key(), cost)
    pipe.execute()
    return cost
