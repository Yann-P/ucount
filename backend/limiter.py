import os
import time
from collections import defaultdict

import store

LIMIT = int(os.getenv("RATE_LIMIT", "120"))  # requests per minute per IP

_mem: dict[str, int] = defaultdict(int)
_mem_window: dict[str, int] = {}


def is_rate_limited(ip: str) -> bool:
    window = int(time.time() // 60)
    key = f"rl:{ip}:{window}"

    r = store._r()
    if r:
        count: int = r.incr(key)  # type: ignore[assignment]
        if count == 1:
            r.expire(key, 60)
        return count > LIMIT

    # in-memory fallback (dev without Redis)
    if _mem_window.get(ip) != window:
        _mem_window[ip] = window
        _mem[ip] = 0
    _mem[ip] += 1
    return _mem[ip] > LIMIT
