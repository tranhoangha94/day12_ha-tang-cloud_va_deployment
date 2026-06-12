"""Shared Redis connection — state lưu trong Redis, không trong memory."""
import redis

from app.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL is not configured")
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def ping_redis() -> bool:
    try:
        return get_redis().ping()
    except Exception:
        return False
