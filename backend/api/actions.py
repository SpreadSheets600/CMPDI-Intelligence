import json

from flask import Blueprint, jsonify, request

from backend.core import appsettings, llm, reports
from backend.core.config import CLOUDS_DIR
from backend.core.knowledge import topics
from backend.core.knowledge.summary import generate_summary
from backend.core.pipeline import pipeline
from backend.db import database as db

bp = Blueprint("actions", __name__, url_prefix="/api")


@bp.get("/facts")
def facts_series():
    """One metric (entity x attribute) across the whole library, every value
    with its receipt down to document, page and sheet."""
    entity = request.args.get("entity") or ""
    attribute = request.args.get("attribute") or ""
    if not entity or not attribute:
        return jsonify({"error": "entity and attribute are required"}), 400
    rows = db.q(
        """SELECT f.value_raw, f.value_norm, f.unit, f.period_norm, f.flags, f.conf,
                  COALESCE(e.canonical_name, f.entity_text) AS entity, f.attribute,
                  d.id AS doc_id, d.filename, c.page_no, c.sheet_no
           FROM facts f
           LEFT JOIN entities e ON e.id = f.entity_id
           JOIN chunks c ON c.id = f.chunk_id
           JOIN documents d ON d.id = c.doc_id
           WHERE COALESCE(e.canonical_name, f.entity_text) = ? AND f.attribute = ?
             AND f.value_norm IS NOT NULL
           ORDER BY f.period_norm""",
        (entity, attribute),
    )
    series = [dict(r) for r in rows]
    return jsonify({"entity": entity, "attribute": attribute, "series": series})


@bp.get("/insights/summary")
def insights_summary():
    """Per-document extraction footprint for the Insights quality table."""
    rows = db.q(
        """SELECT d.filename, d.doc_type, d.page_count, d.ocr_pages,
                  (SELECT COUNT(*) FROM chunks c WHERE c.doc_id = d.id) AS chunks,
                  (SELECT COUNT(*) FROM facts f JOIN chunks c2 ON c2.id = f.chunk_id
                   WHERE c2.doc_id = d.id) AS facts,
                  (SELECT COUNT(*) FROM doc_keywords k WHERE k.doc_id = d.id) AS tags
           FROM documents d WHERE d.status='completed' ORDER BY d.upload_ts DESC"""
    )
    return jsonify({"doc_quality": [dict(r) for r in rows]})


# ---------- documents ----------


@bp.post("/documents/<doc_id>/delete")
def delete_document(doc_id):
    if not pipeline.delete_document(doc_id):
        return jsonify({"error": "document not found"}), 404
    return jsonify({"ok": True})


@bp.post("/documents/<doc_id>/rename")
def rename_document(doc_id):
    name = ((request.get_json(silent=True) or {}).get("display_name") or "").strip()
    if not db.q1("SELECT id FROM documents WHERE id=?", (doc_id,)):
        return jsonify({"error": "document not found"}), 404
    db.execute("UPDATE documents SET display_name=? WHERE id=?", (name or None, doc_id))
    return jsonify({"ok": True, "display_name": name or None})


@bp.post("/documents/<doc_id>/summarize")
def summarize_document(doc_id):
    if not db.q1("SELECT id FROM documents WHERE id=?", (doc_id,)):
        return jsonify({"error": "document not found"}), 404
    generate_summary(doc_id, regenerate=True)
    summary = db.q1("SELECT summary FROM documents WHERE id=?", (doc_id,))["summary"]
    return jsonify({"ok": True, "summary": summary})


# ---------- ingest ----------


@bp.post("/ingest")
def ingest_files():
    from backend.core.config import FILES_DIR

    uploaded = request.files.getlist("files")
    results = []
    for f in uploaded:
        if not f.filename:
            continue
        tmp = FILES_DIR / "_uploads" / f.filename
        tmp.parent.mkdir(parents=True, exist_ok=True)
        f.save(tmp)
        try:
            results.append(pipeline.ingest_file(tmp) | {"filename": f.filename})
        except Exception as e:
            results.append({"filename": f.filename, "error": str(e)})
    pipeline.notify_worker()
    return jsonify({"results": results})


@bp.post("/pipeline/demo")
def load_demo():
    import threading

    def _run():
        from backend.scripts import make_demo_corpus

        make_demo_corpus.main()
        from backend.core.config import DATA_DIR

        corpus = DATA_DIR / "demo_corpus"
        if corpus.exists():
            for f in sorted(corpus.iterdir()):
                try:
                    pipeline.ingest_file(f)
                except Exception as e:
                    import logging

                    logging.getLogger("cmpdi.pipeline").warning(
                        "Demo ingest failed: %s", e
                    )
            pipeline.notify_worker()

    threading.Thread(target=_run, name="cmpdi-demo", daemon=True).start()
    return jsonify(
        {
            "ok": True,
            "message": "Demonstration dataset is being generated and ingested.",
        }
    )


# ---------- topics ----------


@bp.post("/topics/refresh")
def topics_refresh():
    scope = (request.get_json(silent=True) or {}).get("scope") or None
    db.execute("DELETE FROM doc_topics WHERE scope IS ?", (scope,))
    topics.cluster_corpus(scope)
    topics.wordcloud_png(scope)
    return jsonify({"ok": True, "scope": scope or "corpus"})


# ---------- reports ----------


@bp.post("/reports/generate")
def reports_generate():
    data = request.get_json(silent=True) or {}
    reports.generate(
        data.get("template") or "",
        {
            "entity": (data.get("entity") or "").strip(),
            "period": (data.get("period") or "").strip(),
            "question": (data.get("question") or "").strip(),
        },
    )
    return jsonify({"ok": True})


@bp.post("/reports/<int:rid>/approve")
def reports_approve(rid):
    db.execute("UPDATE reports SET human_approved=1 WHERE id=?", (rid,))
    return jsonify({"ok": True})


@bp.post("/reports/<int:rid>/review")
def reports_review(rid):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    note = (data.get("note") or "").strip() or None
    if status not in ("approved", "returned"):
        return jsonify({"error": "status must be approved or returned"}), 400
    db.execute(
        "UPDATE reports SET review_status=?, review_note=?, human_approved=?"
        " WHERE id=?",
        (status, note, 1 if status == "approved" else 0, rid),
    )
    return jsonify({"ok": True})


@bp.post("/reports/parliamentary")
def reports_parliamentary():
    question = ((request.get_json(silent=True) or {}).get("question") or "").strip()
    if question:
        reports.generate_parliamentary(question)
    return jsonify({"ok": True, "question": question})


@bp.get("/topics/cloud")
def cloud_image():
    scope = request.args.get("scope") or "corpus"
    from flask import send_from_directory

    from backend.core.knowledge.topics import hashlib_slug

    return send_from_directory(CLOUDS_DIR, f"cloud_{hashlib_slug(scope)}.png")


# ---------- settings ----------


@bp.post("/settings")
def settings_save():
    data = request.get_json(silent=True) or {}
    try:
        appsettings.update(data)
        llm.reset_status_cache()
        return jsonify({"ok": True, "message": "Settings saved and applied."})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@bp.post("/settings/summaries")
def settings_summaries():
    rows = db.q("""SELECT id FROM documents WHERE status='completed'
                   AND (summary IS NULL OR summary='')""")
    for r in rows:
        generate_summary(r["id"])
    return jsonify({"ok": True, "generated": len(rows)})
