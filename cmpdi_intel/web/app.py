"""Flask app: light, minimal UI + JSON API in one process. The ingestion
worker thread starts with the app; SQLite WAL lets reads run during writes."""

import json

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from .. import config, db, facts, query, reports, retrieval, topics
from ..pipeline import pipeline

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024

db.init_db()
facts.ensure_subsidiary_entities()
pipeline.start_worker()


@app.template_filter("fromjson")
def fromjson(seq, i):
    return json.loads(seq)[i]


@app.template_filter("loads")
def loads(s):
    return json.loads(s)


@app.context_processor
def inject_globals():
    row = db.q1("SELECT COUNT(*) c FROM conflicts WHERE status='open'")
    return {"open_conflicts": row["c"] if row else 0}


# ---------------------------------------------------------------- dashboard


@app.route("/")
def index():
    stats = {
        "documents": db.q1("SELECT COUNT(*) c FROM documents")["c"],
        "chunks": db.q1("SELECT COUNT(*) c FROM chunks")["c"],
        "facts": db.q1("SELECT COUNT(*) c FROM facts")["c"],
        "conflicts": db.q1("SELECT COUNT(*) c FROM conflicts WHERE status='open'")["c"],
    }
    jobs = db.q("""SELECT j.*, d.filename, d.doc_type FROM jobs j
                   LEFT JOIN documents d ON d.id=j.doc_id ORDER BY j.id DESC LIMIT 12""")
    return render_template("index.html", stats=stats, jobs=jobs, stages=pipeline.STAGES)


@app.route("/api/jobs")
def api_jobs():
    jobs = db.q("""SELECT j.id, j.stage, j.status, j.stats_json, j.error, d.filename
                   FROM jobs j LEFT JOIN documents d ON d.id=j.doc_id
                   ORDER BY j.id DESC LIMIT 12""")
    return jsonify([dict(j) for j in jobs])


@app.route("/ingest", methods=["POST"])
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
            r = pipeline.ingest_file(tmp)
            results.append(r | {"filename": f.filename})
        except Exception as e:
            results.append({"filename": f.filename, "error": str(e)})
    pipeline.notify_worker()
    return render_template("ingested.html", results=results)


# ---------------------------------------------------------------- documents


@app.route("/documents")
def documents():
    subs = db.q(
        "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"
    )
    sel_sub = request.args.get("subsidiary") or ""
    rows = db.q(
        "SELECT * FROM documents WHERE ?='' OR subsidiary=? ORDER BY upload_ts DESC",
        (sel_sub, sel_sub),
    )
    return render_template(
        "documents.html", docs=rows, subsidiaries=subs, sel_sub=sel_sub
    )


@app.route("/doc/<doc_id>")
def viewer(doc_id):
    doc = db.q1("SELECT * FROM documents WHERE id=?", (doc_id,))
    if not doc:
        abort(404)
    pages = db.q(
        "SELECT page_no, ocr_used, avg_confidence, image_path FROM pages WHERE doc_id=? ORDER BY page_no",
        (doc_id,),
    )
    sheets = db.q(
        "SELECT DISTINCT sheet_no FROM elements WHERE doc_id=? AND sheet_no IS NOT NULL ORDER BY sheet_no",
        (doc_id,),
    )
    page_no = request.args.get("page", type=int)
    sheet_no = request.args.get("sheet", type=int)
    elements, tables = [], []
    if page_no:
        elements = [
            dict(r)
            for r in db.q(
                "SELECT * FROM elements WHERE doc_id=? AND page_no=? ORDER BY order_idx",
                (doc_id, page_no),
            )
        ]
    elif sheet_no:
        tables = [
            dict(r)
            for r in db.q(
                "SELECT * FROM tables WHERE doc_id=? AND sheet_no=? ORDER BY table_idx",
                (doc_id, sheet_no),
            )
        ]
        for t in tables:
            t["headers"] = json.loads(t["headers_json"])
            t["rows"] = [
                dict(r)
                for r in db.q(
                    "SELECT * FROM table_cells WHERE table_id=? ORDER BY row_idx, col_idx",
                    (t["id"],),
                )
            ]
    return render_template(
        "viewer.html",
        doc=doc,
        pages=pages,
        sheets=sheets,
        page_no=page_no,
        sheet_no=sheet_no,
        elements=elements,
        tables=tables,
    )


@app.route("/page_image/<doc_id>/<path:rel>")
def page_image(doc_id, rel):
    return send_from_directory(config.FILES_DIR, f"{doc_id}/{rel}")


# ---------------------------------------------------------------- search


@app.route("/search")
def search():
    q_text = request.args.get("q", "").strip()
    subsidiary = request.args.get("subsidiary") or None
    results = (
        retrieval.hybrid_search(q_text, filters={"subsidiary": subsidiary})
        if q_text
        else []
    )
    return render_template(
        "search.html",
        q=q_text,
        results=results,
        subs=db.q(
            "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"
        ),
    )


# ---------------------------------------------------------------- ask


@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        q_text = request.form.get("q", "").strip() or request.json.get("q", "")
        filters = {}
        if request.form.get("subsidiary"):
            filters["subsidiary"] = request.form["subsidiary"]
        payload = query.answer(q_text, filters=filters)
        if request.is_json:
            return jsonify(payload)
        return render_template(
            "ask.html",
            payload=payload,
            q=q_text,
            subs=db.q(
                "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"
            ),
        )
    return render_template(
        "ask.html",
        payload=None,
        q="",
        subs=db.q(
            "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"
        ),
    )


# ---------------------------------------------------------------- conflicts


@app.route("/conflicts")
def conflicts():
    rows = db.q("SELECT * FROM conflicts ORDER BY id DESC")
    parsed = []
    for c in rows:
        d = dict(c)
        d["fact_values"] = json.loads(c["values_json"])
        d["docs"] = {}
        for v in d["fact_values"]:
            doc = db.q1("SELECT filename FROM documents WHERE id=?", (v["doc_id"],))
            d["docs"][v["doc_id"]] = doc["filename"] if doc else v["doc_id"]
        parsed.append(d)
    return render_template("conflicts.html", conflicts=parsed)


@app.route("/conflicts/<int:conflict_id>/resolve", methods=["POST"])
def resolve_conflict(conflict_id):
    facts.resolve_conflict(
        conflict_id,
        request.form.get("chosen_fact_id", type=int),
        request.form.get("notes", ""),
        status=request.form.get("status", "resolved"),
    )
    return redirect(url_for("conflicts"))


# ---------------------------------------------------------------- topics


@app.route("/topics")
def topics_page():
    cloud = request.args.get("scope", "corpus")
    scope = None if cloud == "corpus" else cloud
    subs = db.q(
        "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"
    )
    clusters = db.q(
        "SELECT * FROM doc_topics WHERE scope IS ? ORDER BY id DESC LIMIT 6", (scope,)
    )
    return render_template("topics.html", scope=cloud, clusters=clusters, subs=subs)


@app.route("/topics/refresh", methods=["POST"])
def topics_refresh():
    scope = request.form.get("scope") or None
    if scope:
        db.execute("DELETE FROM doc_topics WHERE scope=?", (scope,))
    else:
        db.execute("DELETE FROM doc_topics WHERE scope='corpus'")
    topics.cluster_corpus(scope)
    topics.wordcloud_png(scope)
    return redirect(url_for("topics_page", scope=scope or "corpus"))


@app.route("/cloud/<slug>.png")
def cloud_image(slug):
    return send_from_directory(config.CLOUDS_DIR, f"cloud_{slug}.png")


# ---------------------------------------------------------------- reports


@app.route("/reports")
def reports_page():
    rows = db.q("SELECT * FROM reports ORDER BY id DESC")
    return render_template(
        "reports.html",
        reports=rows,
        templates=list(reports.TEMPLATES),
        entities=db.q("SELECT canonical_name FROM entities ORDER BY canonical_name"),
    )


@app.route("/reports/generate", methods=["POST"])
def reports_generate():
    reports.generate(
        request.form["template"],
        {
            "entity": request.form.get("entity", "").strip(),
            "period": request.form.get("period", "").strip(),
            "question": request.form.get("question", "").strip(),
        },
    )
    return redirect(url_for("reports_page"))


@app.route("/reports/<int:rid>/download")
def reports_download(rid):
    row = db.q1("SELECT docx_path FROM reports WHERE id=?", (rid,))
    if not row:
        abort(404)
    from pathlib import Path

    p = Path(row["docx_path"])
    return send_from_directory(p.parent, p.name, as_attachment=True)


@app.route("/reports/<int:rid>/approve", methods=["POST"])
def reports_approve(rid):
    db.execute("UPDATE reports SET human_approved=1 WHERE id=?", (rid,))
    return redirect(url_for("reports_page"))


@app.route("/receipt/<int:rid>/<ref>")
def receipt(rid, ref):
    """Click-to-receipt: a report figure opens its exact source location."""
    r = reports.receipt(rid, ref)
    if not r:
        abort(404)
    return redirect(
        url_for(
            "viewer",
            doc_id=r["doc_id"],
            **({"page": r["page_no"]} if r["page_no"] else {"sheet": r["sheet_no"]}),
        )
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
