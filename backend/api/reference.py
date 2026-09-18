"""External knowledge layer endpoints: public reference context for entities."""

from flask import Blueprint, jsonify, request

from backend.core.knowledge import reference

bp = Blueprint("reference", __name__)


@bp.get("/api/reference/entity")
def api_reference_entity():
    name = (request.args.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    ctx = reference.entity_context(name)
    if not ctx:
        return jsonify({"error": "unknown entity"}), 404
    return jsonify(ctx)


@bp.get("/api/reference/coverage")
def api_reference_coverage():
    return jsonify({"coverage": reference.coverage()})
