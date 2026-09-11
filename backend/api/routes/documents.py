"""Document library and source viewer endpoints."""

import json

from flask import Blueprint, abort, render_template, request, send_from_directory

from backend.core import config, retrieval
from backend.db import database as db

bp = Blueprint("documents", __name__)


@bp.route("/documents")
def documents():
    subs = db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")
    sel_sub = request.args.get("subsidiary") or ""
    rows = db.q("SELECT * FROM documents WHERE ?='' OR subsidiary=? ORDER BY upload_ts DESC",
                (sel_sub, sel_sub))
    tag_filter = request.args.get("tag") or None
    if tag_filter:
        rows = [r for r in rows if tag_filter in
                [x["keyword"] for x in db.q(
                    "SELECT keyword FROM doc_keywords WHERE doc_id=?", (r["id"],))]]
    kw_map = {}
    for r in rows:
        kw_map[r["id"]] = [x["keyword"] for x in db.q(
            "SELECT keyword FROM doc_keywords WHERE doc_id=? ORDER BY keyword", (r["id"],))]
    return render_template("pages/documents.html", docs=rows, subsidiaries=subs,
                           sel_sub=sel_sub, kw_map=kw_map, tag=tag_filter,
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
    elements, tables = [], []
    if page_no:
        elements = [dict(r) for r in db.q(
            "SELECT * FROM elements WHERE doc_id=? AND page_no=? ORDER BY order_idx",
            (doc_id, page_no))]
    elif sheet_no:
        tables = [dict(r) for r in db.q(
            "SELECT * FROM tables WHERE doc_id=? AND sheet_no=? ORDER BY table_idx", (doc_id, sheet_no))]
        for t in tables:
            t["headers"] = json.loads(t["headers_json"])
            t["rows"] = [dict(r) for r in db.q(
                "SELECT * FROM table_cells WHERE table_id=? ORDER BY row_idx, col_idx", (t["id"],))]
    return render_template("pages/viewer.html", doc=doc, pages=pages, sheets=sheets,
                           page_no=page_no, sheet_no=sheet_no, elements=elements,
                           tables=tables)


@bp.route("/page_image/<doc_id>/<path:rel>")
def page_image(doc_id, rel):
    return send_from_directory(config.FILES_DIR, f"{doc_id}/{rel}")
