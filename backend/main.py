from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import audit
import groups
import limiter
import translations as i18n
import spendings
from tmpl import TEMPLATES

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent / "frontend" / "static"),
    name="static",
)
app.include_router(groups.router)
app.include_router(spendings.router)


@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    ip = audit.get_ip(request)
    if limiter.is_rate_limited(ip):
        return JSONResponse(
            {"error": "Too many requests"},
            status_code=429,
            headers={"Retry-After": "60"},
        )
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    t = i18n.get_translations(request.headers.get("accept-language", ""))
    return TEMPLATES.TemplateResponse(request, "index.html", {"t": t})
