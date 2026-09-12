"""Chat and knowledge-graph endpoints. /api/chat is the single Ask
interface: factual and lookup questions answer through the grounded RAG
path, analytical questions (comparisons, shares, trends, charts) route
through the tool-calling agent automatically."""

import re

from flask import Blueprint, jsonify, render_template, request

from backend.core import agent, graph, query, retrieval
from backend.core.llm import get_backend
from backend.db import database as db

bp = Blueprint("chat", __name__)

# analytical intent: any of these trigger the tool-calling agent so the user
# never has to mention Python or "agent"; charts/statistics just happen
_AGENT_INTENT = re.compile(
    r"\b(compare|comparison|share|shares|percentage|percent|growth|trend|"
    r"chart|charts|graph|plot|visuali[sz]e|analysis|analyse|analyze|"
    r"average|correlation|distribution|aggregate|total|rank|ranking|"
    r"highest|lowest|year.over.year|statistics|statistical)\b", re.I)


@bp.route("/api/chat", methods=["POST"])
def chat():
    """The client sends the conversation; the backend routes the latest user
    message down the right path and grounds the reply in evidence."""
    data = request.get_json(force=True)
    messages = [m for m in data.get("messages", [])
                if m.get("role") in ("user", "assistant") and m.get("content")]
    if not messages or messages[-1]["role"] != "user":
        return jsonify({"error": "last message must be from the user"}), 400
    q_text = messages[-1]["content"].strip()
    filters = {}
    if data.get("subsidiary"):
        filters["subsidiary"] = data["subsidiary"]

    if _AGENT_INTENT.search(q_text) and get_backend().name != "extractive":
        try:
            run = agent.run_task(q_text)
        except Exception:
            import logging
            logging.getLogger("cmpdi.chat").exception("Agent Run Failed In Chat")
            run = None
        if run:
            return jsonify({
                "mode": "agent",
                "answer": run["answer"],
                "run_row_id": run.get("row_id"),
                "citations": [{"eid": f"E{i}", "doc_id": e["doc_id"],
                               "doc_title": e["filename"], "page_no": e.get("page_no"),
                               "sheet_no": e.get("sheet_no"), "text": e.get("snippet", ""),
                               "content_type": "EVIDENCE"}
                              for i, e in enumerate(run["evidence"], 1)],
                "charts": [f"/agent/figure/{f['run_id']}/{f['file']}" for f in run["figures"]],
                "trace": [s for s in run["steps"] if s["type"] in ("thought", "tool", "chart")],
                "alternatives": [], "abstained": False, "route": "AGENT",
            })

    payload = query.answer(q_text, filters=filters, history=messages[:-1])
    payload["mode"] = "chat"
    payload["charts"] = []
    payload["trace"] = []
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
