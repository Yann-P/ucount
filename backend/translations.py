import json
from pathlib import Path

_LANGS: dict[str, dict] = {}

for _p in (Path(__file__).parent.parent / "i18n").glob("*.json"):
    _LANGS[_p.stem] = json.loads(_p.read_text())


def get_translations(accept_language: str = "") -> dict:
    for tag in accept_language.split(","):
        lang = tag.strip().split(";")[0].strip()[:2].lower()
        if lang in _LANGS:
            return _LANGS[lang]
    return _LANGS.get("en", {})
