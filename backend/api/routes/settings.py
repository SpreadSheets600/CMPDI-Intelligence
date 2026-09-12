"""Settings: only settings with real effect are exposed and persisted. Every
change takes effect immediately; the page shows live backend probes."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from backend.core import appsettings, llm
from backend.core.pipeline import embedder
from backend.core.summary import generate_summary, has_summaries
from backend.db import database as db

bp = Blueprint("settings", __name__)


@bp.route("/settings")
def settings_page():
    done, total = has_summaries()
    emb_name, emb_dim = embedder.model_info()
    return render_template(
        "pages/settings.html", settings=appsettings.all_settings(),
        llm_status=llm.status(), emb_name=emb_name, emb_dim=emb_dim,
        summaries_done=done, summaries_total=total, doc_count=db.q1(
            "SELECT COUNT(*) c FROM documents WHERE status='completed'")["c"])


@bp.route("/settings", methods=["POST"])
def settings_save():
    try:
        appsettings.update(request.form.to_dict())
        llm.reset_status_cache()
        flash("Settings saved and applied.", "ok")
    except ValueError as e:
        flash(str(e), "err")
    return redirect(url_for("settings.settings_page"))


@bp.route("/settings/summaries", methods=["POST"])
def backfill_summaries():
    rows = db.q("""SELECT id FROM documents WHERE status='completed'
                   AND (summary IS NULL OR summary='')""")
    for r in rows:
        generate_summary(r["id"])
    flash(f"Generated {len(rows)} document summary(ies).", "ok")
    return redirect(url_for("settings.settings_page"))
