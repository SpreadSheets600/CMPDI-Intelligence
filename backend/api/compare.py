"""Compare Documents endpoints."""

from flask import Blueprint, jsonify, request

from backend.core import compare
from backend.db import database as db

bp = Blueprint("compare", __name__)


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
