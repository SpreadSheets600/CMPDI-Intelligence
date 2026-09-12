"""Conflict Radar: page, API and officer decisions (acknowledge/resolve)."""

from flask import Blueprint, jsonify, render_template, request

from backend.core import conflicts

bp = Blueprint("conflicts", __name__)


@bp.route("/conflicts")
def conflicts_page():
    entity = request.args.get("entity") or None
    attribute = request.args.get("attribute") or None
    return render_template(
        "pages/conflicts.html",
        entities=db_entities(), attributes=db_attributes(),
        sel_entity=entity or "", sel_attribute=attribute or "")


def db_entities():
    from backend.db import database as db
    return db.q("""SELECT DISTINCT COALESCE(e.canonical_name, f.entity_text) n
                   FROM facts f LEFT JOIN entities e ON e.id = f.entity_id
                   WHERE COALESCE(e.canonical_name, f.entity_text) != ''
                   ORDER BY n""")


def db_attributes():
    from backend.db import database as db
    return db.q("SELECT DISTINCT attribute FROM facts ORDER BY attribute")


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
