"""Vendored Lucide icon loading for Jinja templates.

SVGs live in ``frontend/static/icons/``; license comments are stripped and
the class attribute is supplied per use so icons inherit text color like the
rest of the design system. Parsed SVGs are cached for the life of the
process.
"""

import re
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
ICONS_DIR = FRONTEND / "static" / "icons"

_icon_cache: dict[str, str] = {}


def load_icon(name: str) -> str:
    """Return the raw SVG markup for *name*, or an empty string if missing."""
    if name not in _icon_cache:
        path = ICONS_DIR / f"{name}.svg"
        try:
            raw = path.read_text()
        except OSError:
            return ""
        raw = re.sub(r"<!--.*?-->\s*", "", raw, flags=re.S)
        raw = re.sub(r"\s*class=\"[^\"]*\"\s*", " ", raw, count=1)
        raw = re.sub(r"\s+", " ", raw).replace("> <", "><").strip()
        raw = raw.replace("<svg ", '<svg aria-hidden="true" ', 1)
        _icon_cache[name] = raw
    return _icon_cache[name]
