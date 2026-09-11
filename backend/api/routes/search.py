"""Hybrid search endpoint."""

from flask import Blueprint, render_template, request

from backend.core import retrieval
from backend.db import database as db

bp = Blueprint("search", __name__)


@bp.route("/search")
def search():
    q_text = request.args.get("q", "").strip()
    subsidiary = request.args.get("subsidiary") or None
    results = retrieval.hybrid_search(q_text, filters={"subsidiary": subsidiary}) if q_text else []
    return render_template("pages/search.html", q=q_text, results=results, subs=db.q(
        "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"))
