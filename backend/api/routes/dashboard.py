"""Dashboard: operational overview of the system: corpus stats, model
status, storage and recent activity. Every number shown comes from the live
database or a real backend probe; nothing decorative."""

from flask import Blueprint, render_template

from backend.core import config, conflicts, llm, quality
from backend.core.pipeline import embedder, vector_store
from backend.db import database as db

bp = Blueprint("dashboard", __name__)


def _dir_size(path) -> int:
    total = 0
    for f in path.rglob("*"):
        try:
            total += f.stat().st_size
        except OSError:
            pass
    return total


@bp.route("/")
def index():
    """Product landing page: what the platform is, in one scroll."""
    stats = {
        "documents": db.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")["c"],
        "facts": db.q1("SELECT COUNT(*) c FROM facts")["c"],
        "chunks": db.q1("SELECT COUNT(*) c FROM chunks")["c"],
    }
    return render_template("pages/landing.html", stats=stats)


@bp.route("/dashboard")
def dashboard():
    """Operational overview: corpus stats, model status, storage, activity."""
    stats = {
        "documents": db.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")["c"],
        "processing": db.q1(
            "SELECT COUNT(*) c FROM jobs WHERE status IN ('pending','running')")["c"],
        "chunks": db.q1("SELECT COUNT(*) c FROM chunks")["c"],
        "facts": db.q1("SELECT COUNT(*) c FROM facts")["c"],
        "tags": db.q1("SELECT COUNT(DISTINCT keyword) c FROM doc_keywords")["c"],
        "failed": db.q1("SELECT COUNT(*) c FROM jobs WHERE status='failed'")["c"],
    }
    emb_name, emb_dim = embedder.model_info()
    vectors = 0
    try:
        index = vector_store.get_index()
        vectors = index.ntotal if index is not None else 0
    except Exception:
        pass

    recent_docs = db.q(
        """SELECT id, filename, display_name, doc_type, content_norm, subsidiary,
                  doc_date_raw, summary IS NOT NULL AND summary != '' AS has_summary
           FROM documents WHERE status='completed' ORDER BY upload_ts DESC LIMIT 5""")
    jobs = db.q(
        """SELECT j.stage, j.status, j.updated_ts, d.filename FROM jobs j
           LEFT JOIN documents d ON d.id = j.doc_id ORDER BY j.id DESC LIMIT 6""")
    eval_metrics = quality._eval_metrics() or {}
    return render_template(
        "pages/dashboard.html", stats=stats, emb_name=emb_name, emb_dim=emb_dim,
        llm_status=llm.status(), vectors=vectors,
        storage_gb=_dir_size(config.DATA_DIR) / 1e9,
        recent_docs=recent_docs, jobs=jobs,
        open_conflicts=_open_conflicts(),
        extraction_accuracy=eval_metrics.get("accuracy"),
        kpi=quality.kpi_stats())


def _open_conflicts() -> int:
    return sum(1 for c in conflicts.detect(limit=500) if c["status"] == "open")
