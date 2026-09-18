"""Temporal Intelligence endpoints: historical metric timelines."""

from flask import Blueprint, jsonify, request

from backend.core import temporal

bp = Blueprint("temporal", __name__)


@bp.get("/api/temporal/options")
def api_temporal_options():
    return jsonify(temporal.list_options())


@bp.get("/api/temporal/timeline")
def api_temporal_timeline():
    entity = (request.args.get("entity") or "").strip()
    attribute = (request.args.get("attribute") or "").strip()
    if not entity or not attribute:
        return jsonify({"error": "entity and attribute are required"}), 400
    include_superseded = (request.args.get("superseded") or "").lower() in (
        "1",
        "true",
        "yes",
    )
    result = temporal.timeline(entity, attribute, include_superseded)
    if result is None:
        return jsonify({"error": "entity and attribute are required"}), 400
    return jsonify(result)
