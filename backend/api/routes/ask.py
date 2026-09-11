"""Ask page. The chat itself runs through /api/chat (chat.py)."""

from flask import Blueprint, render_template

from backend.db import database as db

bp = Blueprint("ask", __name__)


@bp.route("/ask")
def ask():
    subs = db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")
    return render_template("pages/chat.html", subs=subs)
