"""Report file serving and receipt deep-links. Generation, approval and
review decisions are JSON endpoints in backend/api/actions.py."""

import json
from pathlib import Path

from flask import Blueprint, abort, jsonify, redirect, send_from_directory

from backend.core import reports
from backend.db import database as db

bp = Blueprint("reports", __name__)


@bp.route("/reports/<int:rid>/download")
def download(rid):
    row = db.q1("SELECT docx_path FROM reports WHERE id=?", (rid,))
    if not row:
        abort(404)
    p = Path(row["docx_path"])
    return send_from_directory(p.parent, p.name, as_attachment=True)


@bp.route("/reports/<int:rid>/audit")
def audit(rid):
    """Machine-readable audit trail for one report: review history plus the
    full figure-to-source provenance map stored at generation time."""
    row = db.q1("SELECT * FROM reports WHERE id=?", (rid,))
    if not row:
        return jsonify({"error": "report not found"}), 404
    try:
        provenance = json.loads(row["provenance_json"] or "{}")
    except ValueError:
        provenance = {"unparseable": True}
    slots = provenance.get("slots") or {}
    return jsonify({
        "report_id": rid,
        "template": row["template"],
        "params": json.loads(row["params_json"] or "{}"),
        "created_ts": row["created_ts"],
        "review": {"status": row["review_status"], "note": row["review_note"],
                   "by": row["reviewed_by"], "rounds": row["review_rounds"],
                   "approved": bool(row["human_approved"])},
        "figures_traced": len(slots),
        "provenance": provenance,
    })


@bp.route("/receipt/<int:rid>/<ref>")
def receipt(rid, ref):
    """Resolve a report figure reference to its source page or sheet (the
    viewer is a React route)."""
    r = reports.receipt(rid, ref)
    if not r:
        abort(404)
    dest = f"/doc/{r['doc_id']}"
    if r["page_no"]:
        dest += f"?page={r['page_no']}"
    elif r["sheet_no"]:
        dest += f"?sheet={r['sheet_no']}"
    return redirect(dest)
