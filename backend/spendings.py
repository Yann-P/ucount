import secrets
from datetime import date as date_cls

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import audit
import store

router = APIRouter()

MAX_SPENDINGS = 1000


@router.post("/group/{slug}/spendings")
async def add_spending(
    request: Request,
    slug: str,
    paid_by: str = Form(..., max_length=400),
    amount: float = Form(...),
    description: str = Form(..., max_length=400),
    beneficiaries: list[str] = Form(default=[]),
    date: str = Form(default=""),
):
    group = store.get(f"group:{slug}")
    if not group:
        return HTMLResponse("Group not found", status_code=404)
    members_set = set(group["members"])
    if paid_by not in members_set:
        return HTMLResponse("Invalid paid_by", status_code=400)
    if not beneficiaries:
        beneficiaries = group["members"]
    invalid = [b for b in beneficiaries if b not in members_set]
    if invalid:
        return HTMLResponse("Invalid beneficiaries", status_code=400)
    if amount <= 0:
        return HTMLResponse("Amount must be positive", status_code=400)
    if len(group["spendings"]) >= MAX_SPENDINGS:
        return HTMLResponse("Spending limit reached", status_code=400)
    if not date:
        date = date_cls.today().isoformat()
    spending = {
        "id": secrets.token_urlsafe(6),
        "paid_by": paid_by,
        "amount": amount,
        "description": description,
        "beneficiaries": beneficiaries,
        "date": date,
    }
    group["spendings"].append(spending)
    store.set(f"group:{slug}", group)
    audit.log(
        slug,
        audit.get_ip(request),
        audit.parse_browser(request.headers.get("user-agent", "")),
        f"Added spending: {description} {amount:.2f} {group['currency']} (paid by {paid_by})",
    )
    return RedirectResponse(f"/group/{slug}?added=1", status_code=303)


@router.post("/group/{slug}/spendings/{spending_id}/delete")
async def delete_spending(request: Request, slug: str, spending_id: str):
    group = store.get(f"group:{slug}")
    if not group:
        return HTMLResponse("Group not found", status_code=404)
    spending = next((s for s in group["spendings"] if s["id"] == spending_id), None)
    group["spendings"] = [s for s in group["spendings"] if s["id"] != spending_id]
    store.set(f"group:{slug}", group)
    if spending:
        audit.log(
            slug,
            audit.get_ip(request),
            audit.parse_browser(request.headers.get("user-agent", "")),
            f"Deleted spending: {spending['description']} {spending['amount']:.2f} {group['currency']}",
        )
    return RedirectResponse(f"/group/{slug}", status_code=303)
