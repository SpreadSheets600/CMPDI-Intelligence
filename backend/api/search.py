"""Organization-wide search endpoint: one query across documents, facts,
entities, locations, metrics and external reference context."""

from flask import Blueprint, jsonify, request

from backend.core.normalize import normalize_period
from backend.core.retrieval import org_search

bp = Blueprint("search", __name__)


def _filters(args) -> dict:
    date_from = (args.get("from") or "").strip() or None
    date_to = (args.get("to") or "").strip() or None
    return {
        "tag": args.get("tag") or None,
        "subsidiary": args.get("subsidiary") or None,
        "doc_type": args.get("type") or None,
        "doc_from": normalize_period(date_from) if date_from else None,
        "doc_to": normalize_period(date_to) if date_to else None,
    }


@bp.get("/api/search/organization")
def api_organization_search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "q is required"}), 400
    return jsonify(
        {
            "q": query,
            **org_search.organization_search(query, filters=_filters(request.args)),
        }
    )
