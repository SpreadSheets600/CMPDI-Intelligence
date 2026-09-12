"""Hybrid search endpoint with library filters: type, subsidiary, tag and
reporting-period range."""

from flask import Blueprint, render_template, request

from backend.core import retrieval
from backend.core.normalize import normalize_period
from backend.db import database as db

bp = Blueprint("search", __name__)


@bp.route("/search")
def search():
    q_text = request.args.get("q", "").strip()
    tag = request.args.get("tag") or None
    subsidiary = request.args.get("subsidiary") or None
    doc_type = request.args.get("type") or None
    date_from = (request.args.get("from") or "").strip() or None
    date_to = (request.args.get("to") or "").strip() or None

    # the reporting-period filter accepts FY labels ("2022-23"), calendar
    # years ("2022") and ISO dates; both ends normalize to ISO start dates
    doc_from = normalize_period(date_from) if date_from else None
    doc_to = normalize_period(date_to) if date_to else None

    filters = {"tag": tag, "subsidiary": subsidiary, "doc_type": doc_type,
               "doc_from": doc_from, "doc_to": doc_to}
    results = retrieval.hybrid_search(q_text, filters=filters) if q_text else []
    if q_text:
        for ev in results:
            ev["tags"] = retrieval.doc_keywords_map([ev["doc_id"]]).get(ev["doc_id"], [])
    return render_template(
        "pages/search.html", q=q_text, results=results, tag=tag or "",
        subsidiary=subsidiary or "", doc_type=doc_type or "",
        date_from=date_from or "", date_to=date_to or "",
        subs=db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"),
        doc_types=db.q("SELECT DISTINCT doc_type FROM documents ORDER BY doc_type"),
        tags=retrieval.top_tags(30))
