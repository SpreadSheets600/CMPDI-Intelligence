"""Chat and knowledge-graph endpoints. /api/chat is the single Ask
interface: factual and lookup questions answer through the grounded RAG
path, analytical questions (comparisons, shares, trends, charts) route
through the tool-calling agent automatically."""

import re

from flask import Blueprint, jsonify, request

from backend.core import retrieval
from backend.core.knowledge import graph
from backend.core.llm import agent
from backend.core.quality import trust
from backend.core.retrieval import query
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
    doc_ids = [d for d in (data.get("doc_ids") or []) if d]
    if doc_ids:
        filters["doc_ids"] = doc_ids

    # a document scope must be honored exactly, so scoped questions answer
    # through retrieval only rather than the agent's free search
    if (not doc_ids and not data.get("subsidiary")) and \
            _AGENT_INTENT.search(q_text) and get_backend().provider.generative:
        try:
            run = agent.run_task(q_text)
        except Exception:
            import logging
            logging.getLogger("cmpdi.chat").exception("Agent Run Failed In Chat")
            run = None
        if run:
            cites = [{"eid": f"E{i}", "doc_id": e["doc_id"],
                      "doc_title": e["filename"], "page_no": e.get("page_no"),
                      "sheet_no": e.get("sheet_no"), "text": e.get("snippet", ""),
                      "content_type": "EVIDENCE"}
                     for i, e in enumerate(run["evidence"], 1)]
            steps = [s for s in run["steps"] if s["type"] in ("thought", "tool", "chart")]
            n_tools = sum(1 for s in steps if s["type"] == "tool")
            return jsonify({
                "mode": "agent",
                "answer": run["answer"],
                "run_row_id": run.get("row_id"),
                "citations": cites,
                "quality": trust.grade(None, cites, None),
                "why": {"route": "AGENT",
                        "chunks_retrieved": len(run["evidence"]),
                        "documents_represented": len({e["doc_id"] for e in run["evidence"]}),
                        "facts_matched": sum(1 for s in steps if s.get("tool") == "get_facts"),
                        "computations": sum(1 for s in steps if s.get("tool") == "run_python"),
                        "sources_cited": len(cites), "conflicts": 0,
                        "llm": "agent tool loop", "generation": f"{n_tools} tool steps"},
                "charts": [f"/agent/figure/{f['run_id']}/{f['file']}" for f in run["figures"]],
                "trace": steps,
                "charts": [f"/agent/figure/{f['run_id']}/{f['file']}" for f in run["figures"]],
                "trace": [s for s in run["steps"] if s["type"] in ("thought", "tool", "chart")],
                "alternatives": [], "abstained": False, "route": "AGENT",
            })

    payload = query.answer(q_text, filters=filters, history=messages[:-1])
    payload["mode"] = "chat"
    payload["charts"] = []
    payload["trace"] = []
    return jsonify(payload)


@bp.route("/api/graph")
def graph_data():
    subsidiary = request.args.get("subsidiary") or None
    kinds = [k.strip() for k in (request.args.get("kinds") or "").split(",") if k.strip()]
    query = (request.args.get("q") or "").strip() or None
    return jsonify(graph.build_graph(subsidiary=subsidiary,
                                     kinds=kinds or None, query=query))


@bp.route("/api/graph/node")
def graph_node():
    node_id = (request.args.get("id") or "").strip()
    if not node_id:
        return jsonify({"error": "id is required"}), 400
    result = graph.neighbourhood(node_id)
    if not result:
        return jsonify({"error": "unknown node"}), 404
    return jsonify(result)
