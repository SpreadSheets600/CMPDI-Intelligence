"""Report file serving and receipt deep-links. Generation, approval and
review decisions are JSON endpoints in backend/api/actions.py."""

from pathlib import Path

from flask import Blueprint, abort, redirect, send_from_directory

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
