"""Agent endpoints: the workspace page, the run API, figure serving, run
history and DOCX report assembly. Runs are synchronous — the UI shows a
working state while the tool loop executes."""

from flask import Blueprint, abort, jsonify, render_template, request, send_from_directory, url_for

from backend.core import agent, reports
from backend.core import config as cfg
from backend.db import database as db

bp = Blueprint("agent", __name__)


@bp.route("/agent")
def agent_page():
    return render_template("pages/agent.html", runs=agent.recent_runs())


@bp.route("/api/agent", methods=["POST"])
def run():
    task = (request.json or {}).get("task", "").strip()
    if not task:
        return jsonify({"error": "Task Is Empty"}), 400
    try:
        result = agent.run_task(task)
        return jsonify(result)
    except Exception as e:
        import logging
        logging.getLogger("cmpdi.agent").exception("Agent Run Failed")
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


@bp.route("/agent/figure/<run_id>/<path:name>")
def figure(run_id, name):
    directory = cfg.DATA_DIR / "agent_runs" / run_id
    if not (directory / name).exists():
        abort(404)
    return send_from_directory(directory, name)


@bp.route("/api/agent/runs/<int:run_id>")
def run_detail(run_id):
    run = agent.get_run(run_id)
    if not run:
        abort(404)
    return jsonify(run)


@bp.route("/api/agent/report", methods=["POST"])
def make_report():
    run_id = (request.json or {}).get("run_id")
    run = agent.get_run(int(run_id)) if run_id else None
    if not run or not run["answer"]:
        abort(404)
    report_id = reports.generate_from_run(run)
    return jsonify({"report_id": report_id,
                    "download": url_for("reports.download", rid=report_id)})
