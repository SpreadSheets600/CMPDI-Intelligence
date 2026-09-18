"""Insight Dashboard endpoint: deterministic organizational signals."""

from flask import Blueprint, jsonify, request

from backend.core import insights

bp = Blueprint("insights", __name__)


@bp.get("/api/insights/dashboard")
def api_insights_dashboard():
    subsidiary = (request.args.get("subsidiary") or "").strip() or None
    return jsonify(insights.dashboard(subsidiary))
