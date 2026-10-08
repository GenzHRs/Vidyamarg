"""Compatibility helper for optional synchronous cache use."""
import time
import redis
from contextlib import suppress
from app.core.config import settings

_client = None
_retry_after = 0.0

def get_redis_client():
    global _client, _retry_after
    if not settings.REDIS_URL or time.monotonic() < _retry_after:
        return None
    try:
        if _client is None:
            _client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
        _client.ping()
        return _client
    except Exception:
        if _client is not None:
            with suppress(Exception):
                _client.close()
        _client = None
        _retry_after = time.monotonic() + 30
        return None
