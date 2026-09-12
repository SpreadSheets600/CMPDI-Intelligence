"""Document library, source viewer and deletion endpoints."""

import json

from flask import Blueprint, abort, redirect, render_template, request, send_file, send_from_directory, url_for

from backend import storage
from backend.core import config, retrieval
from backend.core.pipeline import pipeline
from backend.core.summary import generate_summary
from backend.db import database as db

bp = Blueprint("documents", __name__)


@bp.route("/documents")
def documents():
    subs = db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")
    types = db.q("SELECT DISTINCT doc_type FROM documents ORDER BY doc_type")
    sel_sub = request.args.get("subsidiary") or ""
    sel_type = request.args.get("type") or ""
    q = (request.args.get("q") or "").strip()
    where, params = [], []
    if sel_sub:
        where.append("subsidiary=?")
        params.append(sel_sub)
    if sel_type:
        where.append("doc_type=?")
        params.append(sel_type)
    if q:
        where.append("(display_name LIKE ? OR filename LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    sql = "SELECT * FROM documents" + (" WHERE " + " AND ".join(where) if where else "") + \
        " ORDER BY upload_ts DESC"
    rows = db.q(sql, tuple(params))
    tag_filter = request.args.get("tag") or None
    if tag_filter:
        rows = [r for r in rows if tag_filter in
                [x["keyword"] for x in db.q(
                    "SELECT keyword FROM doc_keywords WHERE doc_id=?", (r["id"],))]]
    kw_map = {}
    for r in rows:
        kw_map[r["id"]] = [x["keyword"] for x in db.q(
            "SELECT keyword FROM doc_keywords WHERE doc_id=? ORDER BY keyword", (r["id"],))]
    counts = {r["doc_type"]: r["n"] for r in db.q(
        "SELECT doc_type, COUNT(*) n FROM documents GROUP BY doc_type")}
    return render_template("pages/documents.html", docs=rows, subsidiaries=subs,
                           doc_types=types, type_counts=counts, sel_sub=sel_sub,
                           sel_type=sel_type, q=q, kw_map=kw_map, tag=tag_filter,
                           tags=retrieval.top_tags(30))


@bp.route("/doc/<doc_id>")
def viewer(doc_id):
    doc = db.q1("SELECT * FROM documents WHERE id=?", (doc_id,))
    if not doc:
        abort(404)
    pages = db.q(
        "SELECT page_no, ocr_used, avg_confidence, image_path FROM pages WHERE doc_id=? ORDER BY page_no",
        (doc_id,))
    sheets = db.q(
        "SELECT DISTINCT sheet_no FROM elements WHERE doc_id=? AND sheet_no IS NOT NULL ORDER BY sheet_no",
        (doc_id,))
    page_no = request.args.get("page", type=int)
    sheet_no = request.args.get("sheet", type=int)
    is_pdf = doc["doc_type"] in ("pdf", "digital_pdf", "mixed_pdf", "scanned_pdf")
    is_sheet = doc["doc_type"] in ("xlsx", "csv")
    elements, tables, reading_elements = [], [], []
    if page_no and is_pdf:
        elements = [dict(r) for r in db.q(
            "SELECT * FROM elements WHERE doc_id=? AND page_no=? ORDER BY order_idx",
            (doc_id, page_no))]
    elif sheet_no and is_sheet:
        tables = [dict(r) for r in db.q(
            "SELECT * FROM tables WHERE doc_id=? AND sheet_no=? ORDER BY table_idx", (doc_id, sheet_no))]
        for t in tables:
            t["headers"] = json.loads(t["headers_json"])
            t["rows"] = [dict(r) for r in db.q(
                "SELECT * FROM table_cells WHERE table_id=? ORDER BY row_idx, col_idx", (t["id"],))]
    elif not is_pdf and not is_sheet:
        # DOCX / image / misc: a linear reading view over everything extracted
        reading_elements = [dict(r) for r in db.q(
            "SELECT * FROM elements WHERE doc_id=? AND text != '' ORDER BY order_idx LIMIT 400",
            (doc_id,))]
    kw_list = [r["keyword"] for r in db.q(
        "SELECT keyword FROM doc_keywords WHERE doc_id=? ORDER BY keyword", (doc_id,))]
    return render_template("pages/viewer.html", doc=doc, pages=pages, sheets=sheets,
                           page_no=page_no, sheet_no=sheet_no, elements=elements,
                           tables=tables, reading_elements=reading_elements, kw_list=kw_list)


@bp.route("/documents/<doc_id>/delete", methods=["POST"])
def delete(doc_id):
    if not pipeline.delete_document(doc_id):
        abort(404)
    return redirect(url_for("documents.documents"))


@bp.route("/documents/<doc_id>/rename", methods=["POST"])
def rename(doc_id):
    name = (request.form.get("display_name") or "").strip()
    if not db.q1("SELECT id FROM documents WHERE id=?", (doc_id,)):
        abort(404)
    # empty value resets to the original filename
    db.execute("UPDATE documents SET display_name=? WHERE id=?",
               (name or None, doc_id))
    return redirect(url_for("documents.viewer", doc_id=doc_id))


@bp.route("/documents/<doc_id>/summarize", methods=["POST"])
def summarize(doc_id):
    if not db.q1("SELECT id FROM documents WHERE id=?", (doc_id,)):
        abort(404)
    generate_summary(doc_id, regenerate=True)
    return redirect(url_for("documents.viewer", doc_id=doc_id))


@bp.route("/documents/<doc_id>/original")
def original(doc_id):
    """Serves the untouched original so the browser can render native
    previews (PDF viewer) and users can download the source of truth."""
    path = storage.original_path(doc_id)
    if path is None:
        abort(404)
    return send_file(path, download_name=path.name)


@bp.route("/page_image/<doc_id>/<path:rel>")
def page_image(doc_id, rel):
    return send_from_directory(config.FILES_DIR, f"{doc_id}/{rel}")
