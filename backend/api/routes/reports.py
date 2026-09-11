"""Report Studio endpoints: generate, download, approve, receipt deep-links."""

from pathlib import Path

from flask import (Blueprint, abort, redirect, render_template, request,
                   send_from_directory, url_for)

from backend.core import reports
from backend.db import database as db

bp = Blueprint("reports", __name__)


@bp.route("/reports")
def reports_page():
    rows = db.q("SELECT * FROM reports ORDER BY id DESC")
    return render_template("pages/reports.html", reports=rows,
                           templates=list(reports.TEMPLATES),
                           entities=db.q("SELECT canonical_name FROM entities ORDER BY canonical_name"))


@bp.route("/reports/generate", methods=["POST"])
def generate():
    reports.generate(request.form["template"], {
        "entity": request.form.get("entity", "").strip(),
        "period": request.form.get("period", "").strip(),
        "question": request.form.get("question", "").strip(),
    })
    return redirect(url_for("reports.reports_page"))


@bp.route("/reports/<int:rid>/download")
def download(rid):
    row = db.q1("SELECT docx_path FROM reports WHERE id=?", (rid,))
    if not row:
        abort(404)
    p = Path(row["docx_path"])
    return send_from_directory(p.parent, p.name, as_attachment=True)


@bp.route("/reports/<int:rid>/approve", methods=["POST"])
def approve(rid):
    db.execute("UPDATE reports SET human_approved=1 WHERE id=?", (rid,))
    return redirect(url_for("reports.reports_page"))


@bp.route("/receipt/<int:rid>/<ref>")
def receipt(rid, ref):
    """Resolve a report figure reference to its source page or sheet."""
    r = reports.receipt(rid, ref)
    if not r:
        abort(404)
    return redirect(url_for("documents.viewer", doc_id=r["doc_id"],
                            **({"page": r["page_no"]} if r["page_no"] else {"sheet": r["sheet_no"]})))
