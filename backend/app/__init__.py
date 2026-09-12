"""Flask application factory. Serves the frontend templates plus the JSON
API from one process; the ingestion worker thread starts with the app and
SQLite WAL lets reads run while it writes."""

import hashlib
import json
import re
from pathlib import Path

from flask import Flask

from backend.api.routes import (agent, ask, chat, compare, conflicts,
                                dashboard, documents, ingest, insights,
                                reports, search, settings, topics)
from backend.core import appsettings, config, facts
from backend.core.pipeline import pipeline
from backend.db import database

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
ICONS_DIR = FRONTEND / "static" / "icons"

# vendored Lucide SVGs: license comment stripped, class attribute supplied
# per use so icons inherit text color like the rest of the design system
_icon_cache: dict[str, str] = {}


def _load_icon(name: str) -> str:
    if name not in _icon_cache:
        path = ICONS_DIR / f"{name}.svg"
        try:
            raw = path.read_text()
        except OSError:
            return ""
        raw = re.sub(r"<!--.*?-->\s*", "", raw, flags=re.S)
        raw = re.sub(r'\s*class="[^"]*"\s*', " ", raw, count=1)
        raw = re.sub(r"\s+", " ", raw).replace("> <", "><").strip()
        raw = raw.replace("<svg ", '<svg aria-hidden="true" ', 1)
        _icon_cache[name] = raw
    return _icon_cache[name]


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(FRONTEND / "templates"),
        static_folder=str(FRONTEND / "static"),
    )
    app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024
    # stable per-installation key so flash messages survive redirects
    app.secret_key = hashlib.sha256(str(config.DATA_DIR).encode()).hexdigest()

    database.init_db()
    facts.ensure_subsidiary_entities()
    pipeline.start_worker()

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(ingest.bp)
    app.register_blueprint(documents.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(ask.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(insights.bp)
    app.register_blueprint(topics.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(agent.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(conflicts.bp)
    app.register_blueprint(compare.bp)

    @app.template_filter("fromjson")
    def fromjson(seq, i):
        return json.loads(seq)[i]

    @app.template_filter("loads")
    def loads(s):
        return json.loads(s)

    @app.template_global("icon")
    def icon(name: str, cls: str = "h-[18px] w-[18px]") -> str:
        from markupsafe import Markup

        svg = _load_icon(name)
        if not svg:
            return ""
        return Markup(svg.replace("<svg ", f'<svg class="{cls}" ', 1))

    @app.context_processor
    def inject_globals():
        row = database.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")
        return {"library_size": row["c"] if row else 0,
                "settings_retrieval_k": appsettings.get("retrieval_k")}

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
