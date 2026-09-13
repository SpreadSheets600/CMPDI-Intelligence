"""Pipeline status feed. Upload and demo-corpus mutations live in
backend/api/actions.py; the SPA polls this feed for live job status."""

from flask import Blueprint, jsonify

from backend.db import database as db

bp = Blueprint("ingest", __name__)


@bp.route("/api/jobs")
def api_jobs():
    jobs = db.q(
        """SELECT j.id, j.stage, j.status, j.stats_json, j.error, d.filename
           FROM jobs j LEFT JOIN documents d ON d.id = j.doc_id
           ORDER BY j.id DESC LIMIT 12""")
    return jsonify([dict(j) for j in jobs])
