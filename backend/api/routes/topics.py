"""Topic analysis endpoints: word clouds and document clusters."""

from flask import Blueprint, redirect, render_template, request, send_from_directory, url_for

from backend.core import config, topics
from backend.db import database as db

bp = Blueprint("topics", __name__)


@bp.route("/topics")
def topics_page():
    scope = request.args.get("scope", "corpus")
    scope_filter = None if scope == "corpus" else scope
    subs = db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")
    clusters = db.q("SELECT * FROM doc_topics WHERE scope IS ? ORDER BY id DESC LIMIT 6",
                    (scope_filter,))
    return render_template("pages/topics.html", scope=scope, clusters=clusters, subs=subs)


@bp.route("/topics/refresh", methods=["POST"])
def refresh():
    scope = request.form.get("scope") or None
    db.execute("DELETE FROM doc_topics WHERE scope IS ?", (scope,))
    topics.cluster_corpus(scope)
    topics.wordcloud_png(scope)
    return redirect(url_for("topics.topics_page", scope=scope or "corpus"))


@bp.route("/cloud/<path:scope>.png")
def cloud_image(scope):
    # clouds are stored under a scope-derived slug; the URL carries the scope
    from backend.core.topics import hashlib_slug
    return send_from_directory(config.CLOUDS_DIR, f"cloud_{hashlib_slug(scope)}.png")
