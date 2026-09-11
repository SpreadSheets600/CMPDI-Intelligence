"""Conflict Radar endpoints: listing and human resolution."""

import json

from flask import Blueprint, redirect, render_template, request, url_for

from backend.core import facts
from backend.db import database as db

bp = Blueprint("conflicts", __name__)


@bp.route("/conflicts")
def conflicts():
    rows = db.q("SELECT * FROM conflicts ORDER BY id DESC")
    parsed = []
    for c in rows:
        d = dict(c)
        d["fact_values"] = json.loads(c["values_json"])
        d["docs"] = {}
        for v in d["fact_values"]:
            doc = db.q1("SELECT filename FROM documents WHERE id=?", (v["doc_id"],))
            d["docs"][v["doc_id"]] = doc["filename"] if doc else v["doc_id"]
        parsed.append(d)
    return render_template("pages/conflicts.html", conflicts=parsed)


@bp.route("/conflicts/<int:conflict_id>/resolve", methods=["POST"])
def resolve(conflict_id):
    facts.resolve_conflict(conflict_id,
                           request.form.get("chosen_fact_id", type=int),
                           request.form.get("notes", ""),
                           status=request.form.get("status", "resolved"))
    return redirect(url_for("conflicts.conflicts"))
