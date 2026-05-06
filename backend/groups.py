import secrets
from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import algorithm
import audit
import translations as i18n
import store

router = APIRouter()
_STATIC = Path(__file__).parent.parent / "frontend" / "static"
TEMPLATES = Jinja2Templates(
    directory=Path(__file__).parent.parent / "frontend" / "templates"
)
TEMPLATES.env.globals["static_v"] = lambda name: int((_STATIC / name).stat().st_mtime)
MAX_MEMBERS = 40


@router.post("/groups")
async def create_group(
    request: Request,
    name: str = Form(..., max_length=400),
    currency: str = Form("EUR", max_length=10),
    members: list[str] = Form(...),
):
    members = [m.strip() for m in members if m.strip()]
    members = [m[:400] for m in members[:MAX_MEMBERS]]
    slug = secrets.token_urlsafe(8)
    store.set(
        f"group:{slug}",
        {
            "slug": slug,
            "name": name,
            "currency": currency,
            "members": members,
            "spendings": [],
        },
    )
    audit.log(
        slug,
        audit.get_ip(request),
        audit.parse_browser(request.headers.get("user-agent", "")),
        "Created group",
    )
    return RedirectResponse(f"/group/{slug}", status_code=303)


@router.get("/group/{slug}")
async def group_page(request: Request, slug: str):
    group = store.get(f"group:{slug}")
    if not group:
        return RedirectResponse("/", status_code=303)
    t = i18n.get_translations(request.headers.get("accept-language", ""))
    stats = algorithm.compute_stats(group)
    balances = {m["name"]: m["balance"] for m in stats["members"]}
    settlements = algorithm.settle(balances)
    graph = {
        "members": group["members"],
        "flows": algorithm.compute_flows(group),
        "settlements": [
            {"from": s["payer"], "to": s["payee"], "amount": s["amount"]}
            for s in settlements
        ],
    }
    return TEMPLATES.TemplateResponse(
        request,
        "group.html",
        {
            "group": group,
            "t": t,
            "settlements": settlements,
            "stats": stats,
            "graph": graph,
            "log": audit.get_log(slug),
        },
    )


@router.get("/api/groups/partial", response_class=HTMLResponse)
async def groups_partial(request: Request, slugs: str = Query(default="")):
    slug_list = [s.strip() for s in slugs.split(",") if s.strip()]
    groups = [g for s in slug_list if (g := store.get(f"group:{s}"))]
    t = i18n.get_translations(request.headers.get("accept-language", ""))
    return TEMPLATES.TemplateResponse(
        request, "my_groups.html", {"groups": groups, "t": t}
    )
