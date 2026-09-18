"""Asset / Mine Intelligence endpoints: asset list and unified profiles."""

from flask import Blueprint, jsonify, request

from backend.core.knowledge import assets

bp = Blueprint("assets", __name__)


@bp.get("/api/assets")
def api_assets():
    kind = (request.args.get("kind") or "").strip() or None
    q = (request.args.get("q") or "").strip() or None
    if kind not in (None, "mine", "region"):
        return jsonify({"error": "kind must be mine or region"}), 400
    return jsonify({"assets": assets.list_assets(kind=kind, q=q)})


@bp.get("/api/assets/profile")
def api_assets_profile():
    name = (request.args.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    result = assets.profile(name)
    if not result:
        return jsonify({"error": "unknown asset"}), 404
    return jsonify(result)


@bp.get("/api/pages/assets")
def api_pages_assets():
    return jsonify({"assets": assets.list_assets()})
