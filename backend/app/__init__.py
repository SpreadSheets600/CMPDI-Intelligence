"""Flask application factory. Serves the frontend templates plus the JSON
API from one process; the ingestion worker thread starts with the app and
SQLite WAL lets reads run while it writes.

The factory is deliberately thin: route blueprints come from the registry in
``backend.api.routes``, template globals live in ``template_globals`` and the
icon loader in ``icons``.
"""

import hashlib

from flask import Flask

from backend.api.routes import ALL_BLUEPRINTS
from backend.app import template_globals
from backend.core import appsettings, config, facts
from backend.core.pipeline import pipeline
from backend.db import database

FRONTEND = config.FRONTEND_DIR


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

    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    template_globals.register(app)

    @app.context_processor
    def inject_globals():
        row = database.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")
        return {"library_size": row["c"] if row else 0,
                "settings_retrieval_k": appsettings.get("retrieval_k")}

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
