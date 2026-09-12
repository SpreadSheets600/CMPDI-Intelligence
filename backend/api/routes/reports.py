"""Report Studio endpoints: generate, download, approve, receipt deep-links."""

from pathlib import Path

from flask import (Blueprint, abort, redirect, render_template, request,
                   send_from_directory, url_for)

from backend.core import conflicts as conflicts_mod
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


@bp.route("/reports/<int:rid>/review")
def review(rid):
    row = db.q1("SELECT * FROM reports WHERE id=?", (rid,))
    if not row:
        abort(404)
    import json
    prov = json.loads(row["provenance_json"] or "{}")
    slots = prov.get("slots", {})
    sources = []
    for ref, slot in slots.items():
        doc = db.q1("SELECT filename, display_name, is_current_version, ocr_pages"
                    " FROM documents WHERE id=?", (slot.get("doc_id") or "",))
        if not doc:
            continue
        sources.append({
            "ref": ref, "filename": doc["display_name"] or doc["filename"],
            "doc_id": slot.get("doc_id"),
            "page_no": slot.get("page_no"), "sheet_no": slot.get("sheet_no"),
            "current_version": bool(doc["is_current_version"]),
            "ocr": bool(doc["ocr_pages"]),
        })
    stats = prov.get("stats")
    open_conflicts = conflicts_mod.status_counts()
    return render_template("pages/review.html", report=row, sources=sources,
                           stats=stats, conflict_counts=open_conflicts)


@bp.route("/reports/<int:rid>/review", methods=["POST"])
def review_action(rid):
    status = request.form.get("status")
    note = (request.form.get("note") or "").strip() or None
    if status not in ("approved", "returned"):
        abort(400)
    db.execute("UPDATE reports SET review_status=?, review_note=?, human_approved=?"
               " WHERE id=?", (status, note, 1 if status == "approved" else 0, rid))
    return redirect(url_for("reports.review", rid=rid))


@bp.route("/reports/parliamentary", methods=["POST"])
def parliamentary():
    question = (request.form.get("question") or "").strip()
    if question:
        reports.generate_parliamentary(question)
    return redirect(url_for("reports.reports_page"))
