"""Conversation history stored in Redis — stateless agent design."""
import json
from datetime import datetime, timezone

from app.redis_client import get_redis

HISTORY_TTL = 60 * 60 * 24 * 7  # 7 days
MAX_TURNS = 20


def get_history(user_id: str, limit: int = 5) -> list[dict]:
    r = get_redis()
    items = r.lrange(f"conv:{user_id}", -limit, -1)
    return [json.loads(item) for item in items]


def save_turn(user_id: str, question: str, answer: str) -> None:
    r = get_redis()
    key = f"conv:{user_id}"
    payload = json.dumps({
        "question": question,
        "answer": answer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    r.rpush(key, payload)
    r.ltrim(key, -MAX_TURNS, -1)
    r.expire(key, HISTORY_TTL)
