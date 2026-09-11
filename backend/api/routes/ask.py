"""Grounded Q&A endpoint (HTML form and JSON API)."""

from flask import Blueprint, render_template, request

from backend.core import query
from backend.db import database as db

bp = Blueprint("ask", __name__)


@bp.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        q_text = request.form.get("q", "").strip() or request.json.get("q", "")
        filters = {}
        if request.form.get("subsidiary"):
            filters["subsidiary"] = request.form["subsidiary"]
        payload = query.answer(q_text, filters=filters)
        if request.is_json:
            return payload
        return render_template("pages/ask.html", payload=payload, q=q_text, subs=db.q(
            "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"))
    return render_template("pages/ask.html", payload=None, q="", subs=db.q(
        "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"))
