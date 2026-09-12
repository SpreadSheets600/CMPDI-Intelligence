"""Compare Documents endpoints."""

from flask import Blueprint, jsonify, render_template, request

from backend.core import compare
from backend.db import database as db

bp = Blueprint("compare", __name__)


@bp.route("/compare")
def compare_page():
    doc_id = request.args.get("doc") or None
    suggested = compare.version_pair(doc_id) if doc_id else None
    return render_template(
        "pages/compare.html",
        docs=db.q("""SELECT id, filename, display_name, doc_date_raw
                     FROM documents WHERE status='completed' ORDER BY upload_ts DESC"""),
        suggested=suggested, sel_doc=doc_id or "")


@bp.route("/api/compare")
def api_compare():
    a = request.args.get("a") or ""
    b = request.args.get("b") or ""
    if not a or not b or a == b:
        return jsonify({"error": "pick two different documents"}), 400
    from backend.core.compare import _doc
    if not _doc(a) or not _doc(b):
        return jsonify({"error": "unknown document id"}), 404
    return jsonify(compare.compare(a, b))
