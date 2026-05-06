from pathlib import Path

from fastapi.templating import Jinja2Templates

_STATIC = Path(__file__).parent.parent / "frontend" / "static"
TEMPLATES = Jinja2Templates(
    directory=Path(__file__).parent.parent / "frontend" / "templates"
)
TEMPLATES.env.globals["static_v"] = lambda name: int((_STATIC / name).stat().st_mtime)
