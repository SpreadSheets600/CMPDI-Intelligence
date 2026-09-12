"""Ingestion endpoints: dashboard, file upload, pipeline status feed."""

from flask import Blueprint, jsonify, render_template, request

from backend.core import config
from backend.core.pipeline import pipeline
from backend.db import database as db

bp = Blueprint("ingest", __name__)


@bp.route("/pipeline")
def index():
    stats = {
        "documents": db.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")["c"],
        "chunks": db.q1("SELECT COUNT(*) c FROM chunks")["c"],
        "facts": db.q1("SELECT COUNT(*) c FROM facts")["c"],
        "tags": db.q1("SELECT COUNT(DISTINCT keyword) c FROM doc_keywords")["c"],
    }
    jobs = db.q(
        """SELECT j.*, d.filename, d.doc_type FROM jobs j
           LEFT JOIN documents d ON d.id = j.doc_id ORDER BY j.id DESC LIMIT 12""")
    return render_template("pages/index.html", stats=stats, jobs=jobs, stages=pipeline.STAGES)


@bp.route("/api/jobs")
def api_jobs():
    jobs = db.q(
        """SELECT j.id, j.stage, j.status, j.stats_json, j.error, d.filename
           FROM jobs j LEFT JOIN documents d ON d.id = j.doc_id
           ORDER BY j.id DESC LIMIT 12""")
    return jsonify([dict(j) for j in jobs])


@bp.route("/ingest", methods=["POST"])
def ingest():
    uploaded = request.files.getlist("files")
    results = []
    for f in uploaded:
        if not f.filename:
            continue
        tmp = config.FILES_DIR / "_uploads" / f.filename
        tmp.parent.mkdir(parents=True, exist_ok=True)
        f.save(tmp)
        try:
            results.append(pipeline.ingest_file(tmp) | {"filename": f.filename})
        except Exception as e:
            results.append({"filename": f.filename, "error": str(e)})
    pipeline.notify_worker()
    return render_template("pages/ingested.html", results=results)

@bp.route("/pipeline/demo", methods=["POST"])
def load_demo():
    """One-click demonstration dataset: generates the curated corpus and
    ingests it, so a fresh install shows a working library immediately."""
    import threading

    def _run():
        from backend.scripts import make_demo_corpus
        make_demo_corpus.main()
        corpus = config.DATA_DIR / "demo_corpus"
        if corpus.exists():
            for f in sorted(corpus.iterdir()):
                try:
                    pipeline.ingest_file(f)
                except Exception as e:
                    import logging
                    logging.getLogger("cmpdi.pipeline").warning("Demo ingest failed: %s", e)
            pipeline.notify_worker()

    threading.Thread(target=_run, name="cmpdi-demo", daemon=True).start()
    from flask import flash, redirect, url_for
    flash("Demonstration dataset is being generated and ingested; watch the pipeline below.", "ok")
    return redirect(url_for("ingest.index"))
