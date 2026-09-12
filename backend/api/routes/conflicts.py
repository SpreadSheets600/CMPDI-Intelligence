"""Conflict Radar: page, API and officer decisions (acknowledge/resolve)."""

from flask import Blueprint, jsonify, request

from backend.core import conflicts

bp = Blueprint("conflicts", __name__)


@bp.route("/api/conflicts")
def api_conflicts():
    entity = request.args.get("entity") or None
    attribute = request.args.get("attribute") or None
    return jsonify(conflicts.detect(entity=entity, attribute=attribute))


@bp.route("/api/conflicts/status", methods=["POST"])
def api_status():
    data = request.get_json(force=True)
    ok = conflicts.set_status(data.get("key", ""), data.get("status", ""),
                              data.get("note"))
    return jsonify({"ok": ok}), (200 if ok else 400)


@bp.route("/api/conflicts/summary")
def api_summary():
    from backend.db import database as db
    counts = conflicts.status_counts()
    open_now = len(conflicts.detect(limit=500))
    counts["detected"] = open_now
    return jsonify(counts)
