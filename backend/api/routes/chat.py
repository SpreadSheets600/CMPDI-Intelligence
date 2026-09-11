"""Chat and knowledge-graph endpoints."""

from flask import Blueprint, jsonify, render_template, request

from backend.core import graph, query, retrieval
from backend.db import database as db

bp = Blueprint("chat", __name__)


@bp.route("/api/chat", methods=["POST"])
def chat():
    """Full-chat endpoint: the client sends the conversation, the backend
    retrieves on the latest user message and grounds the reply in evidence."""
    data = request.get_json(force=True)
    messages = [m for m in data.get("messages", [])
                if m.get("role") in ("user", "assistant") and m.get("content")]
    if not messages or messages[-1]["role"] != "user":
        return jsonify({"error": "last message must be from the user"}), 400
    q_text = messages[-1]["content"].strip()
    filters = {}
    if data.get("subsidiary"):
        filters["subsidiary"] = data["subsidiary"]
    payload = query.answer(q_text, filters=filters, history=messages[:-1])
    return jsonify(payload)


@bp.route("/graph")
def graph_page():
    subs = db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")
    return render_template("pages/graph.html", subs=subs,
                           tags=retrieval.top_tags(30))


@bp.route("/api/graph")
def graph_data():
    subsidiary = request.args.get("subsidiary") or None
    return jsonify(graph.build_graph(subsidiary=subsidiary))
