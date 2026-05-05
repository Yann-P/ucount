import os
import json
from typing import Any, cast

_mem: dict = {}
_redis = None


def _r():
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL")
        if url:
            import redis

            _redis = redis.from_url(url)
    return _redis


def get(key: str) -> Any:
    r = _r()
    if r:
        val = cast(bytes | None, r.get(key))
        return json.loads(val) if val else None
    return _mem.get(key)


def set(key: str, value: Any) -> None:
    r = _r()
    if r:
        r.set(key, json.dumps(value))
    else:
        _mem[key] = value
