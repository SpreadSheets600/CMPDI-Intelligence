"""Landing page: what the platform is, in one scroll. The numbers in the
social-proof band are live database counts, not marketing figures."""

from flask import Blueprint, render_template

from backend.db import database as db

bp = Blueprint("landing", __name__)


@bp.route("/")
def index():
    stats = {
        "documents": db.q1(
            "SELECT COUNT(*) c FROM documents WHERE status='completed'")["c"],
        "facts": db.q1("SELECT COUNT(*) c FROM facts")["c"],
        "chunks": db.q1("SELECT COUNT(*) c FROM chunks")["c"],
        "conflicts": db.q1(
            "SELECT COUNT(*) c FROM conflict_status WHERE status != 'resolved'")["c"],
    }
    return render_template("pages/landing.html", stats=stats)
