"""Ask page. The chat itself runs through /api/chat (chat.py)."""

from flask import Blueprint, render_template, request

from backend.db import database as db

bp = Blueprint("ask", __name__)


@bp.route("/ask")
def ask():
    subs = db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")
    doc_ids = [d for d in (request.args.get("doc") or "").split(",") if d]
    doc_ids += [d for d in (request.args.get("docs") or "").split(",") if d]
    scoped = []
    for d in dict.fromkeys(doc_ids):
        row = db.q1("SELECT id, display_name, filename FROM documents WHERE id = ?", (d,))
        if row:
            scoped.append(dict(row))
    return render_template("pages/chat.html", subs=subs, scoped_docs=scoped,
                           seed_q=request.args.get("q") or "")
