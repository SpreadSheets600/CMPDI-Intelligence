"""Flask application factory. Serves the built React SPA (frontend/dist)
plus the JSON API from one process; the ingestion worker thread starts with
the app and SQLite WAL lets reads run while it writes.

The factory is deliberately thin: route blueprints come from the registry in
``backend.api`` and everything below the catch-all is a JSON API.
"""

import hashlib

from flask import Flask, send_from_directory

from backend.api import ALL_BLUEPRINTS
from backend.core import appsettings, config
from backend.core.knowledge import facts, reference
from backend.core.pipeline import pipeline
from backend.db import database

DIST = config.FRONTEND_DIR / "dist"


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024
    # stable per-installation key so flash messages survive redirects
    app.secret_key = hashlib.sha256(str(config.DATA_DIR).encode()).hexdigest()

    database.init_db()
    facts.ensure_subsidiary_entities()
    reference.seed_reference()
    pipeline.start_worker()

    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    @app.context_processor
    def inject_globals():
        row = database.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")
        return {"library_size": row["c"] if row else 0,
                "settings_retrieval_k": appsettings.get("retrieval_k")}

    @app.get("/")
    def spa_index():
        return send_from_directory(DIST, "index.html")

    @app.get("/<path:path>")
    def spa(path):
        """History-API fallback: real build assets are served from dist,
        every client-side route gets index.html."""
        candidate = DIST / path
        if candidate.is_file():
            return send_from_directory(DIST, path)
        return send_from_directory(DIST, "index.html")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
