from datetime import datetime, timezone
from typing import Any

from fastapi import Request

import store


def parse_browser(ua: str) -> str:
    if "OPR/" in ua:
        return "Opera"
    if "Edg/" in ua:
        return "Edge"
    if "Chrome/" in ua:
        return "Chrome"
    if "Firefox/" in ua:
        return "Firefox"
    if "Safari/" in ua:
        return "Safari"
    return ua[:30] if ua else "Unknown"


def get_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return (
        fwd.split(",")[0].strip()
        if fwd
        else (request.client.host if request.client else "unknown")
    )


def log(slug: str, ip: str, browser: str, action: str) -> None:
    key = f"log:{slug}"
    entries: list[Any] = store.get(key) or []
    if not isinstance(entries, list):
        entries = []
    entries.append(
        {
            "dt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "ip": ip,
            "browser": browser,
            "action": action,
        }
    )
    store.set(key, entries[-100:])


def get_log(slug: str) -> list[Any]:
    entries = store.get(f"log:{slug}")
    return entries if isinstance(entries, list) else []
