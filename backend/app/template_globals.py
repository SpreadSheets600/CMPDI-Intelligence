"""Jinja template globals and filters shared by every page."""

import json

from markupsafe import Markup

from backend.app.icons import load_icon


def register(app):
    """Attach filters, the ``icon()`` global and context processors."""

    @app.template_filter("fromjson")
    def fromjson(seq, i):
        return json.loads(seq)[i]

    @app.template_filter("loads")
    def loads(s):
        return json.loads(s)

    @app.template_global("icon")
    def icon(name: str, cls: str = "h-[18px] w-[18px]") -> str:
        svg = load_icon(name)
        if not svg:
            return ""
        return Markup(svg.replace("<svg ", f'<svg class="{cls}" ', 1))
