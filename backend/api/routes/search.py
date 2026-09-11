"""Hybrid search endpoint."""

from flask import Blueprint, render_template, request

from backend.core import retrieval
from backend.db import database as db

bp = Blueprint("search", __name__)


@bp.route("/search")
def search():
    q_text = request.args.get("q", "").strip()
    tag = request.args.get("tag") or None
    subsidiary = request.args.get("subsidiary") or None
    filters = {"tag": tag, "subsidiary": subsidiary}
    results = retrieval.hybrid_search(q_text, filters=filters) if q_text else []
    if q_text:
        for ev in results:
            ev["tags"] = retrieval.doc_keywords_map([ev["doc_id"]]).get(ev["doc_id"], [])
    return render_template("pages/search.html", q=q_text, results=results, tag=tag,
                           subs=db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"),
                           tags=retrieval.top_tags(30))
