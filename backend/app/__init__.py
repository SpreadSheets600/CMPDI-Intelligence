"""Flask application factory. Serves the frontend templates plus the JSON
API from one process; the ingestion worker thread starts with the app and
SQLite WAL lets reads run while it writes."""

import json
from pathlib import Path

from flask import Flask

from backend.api.routes import ask, chat, conflicts, documents, ingest, reports, search, topics
from backend.core import facts
from backend.core.pipeline import pipeline
from backend.db import database

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(FRONTEND / "templates"),
        static_folder=str(FRONTEND / "static"),
    )
    app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024

    database.init_db()
    facts.ensure_subsidiary_entities()
    pipeline.start_worker()

    app.register_blueprint(ingest.bp)
    app.register_blueprint(documents.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(ask.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(conflicts.bp)
    app.register_blueprint(topics.bp)
    app.register_blueprint(reports.bp)

    @app.template_filter("fromjson")
    def fromjson(seq, i):
        return json.loads(seq)[i]

    @app.template_filter("loads")
    def loads(s):
        return json.loads(s)

    @app.context_processor
    def inject_globals():
        row = database.q1("SELECT COUNT(*) c FROM conflicts WHERE status='open'")
        return {"open_conflicts": row["c"] if row else 0}

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
