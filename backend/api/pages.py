"""Page-data API for the React SPA.

The frontend is a single-page React application built into ``frontend/dist``
and served by the catch-all route in the application factory. Every screen
fetches its initial data from here (``/api/pages/*``) and then talks to the
live JSON APIs (``/api/jobs``, ``/api/chat``, ``/api/conflicts`` ...) for
interaction. Each endpoint returns exactly the context the matching screen
needs — the same data the Jinja templates used to receive.
"""

import json

from flask import Blueprint, jsonify, request

from backend.core import config, conflicts, llm, quality, retrieval
from backend.core.normalize import normalize_period
from backend.core.pipeline import embedder, pipeline, vector_store
from backend.core.retrieval import org_search
from backend.db import database as db

bp = Blueprint("pages", __name__, url_prefix="/api/pages")


def _rows(rows):
    return [dict(r) for r in rows]


def _dir_size(path) -> int:
    total = 0
    for f in path.rglob("*"):
        try:
            total += f.stat().st_size
        except OSError:
            pass
    return total


def _open_conflicts() -> int:
    return sum(1 for c in conflicts.detect(limit=500) if c["status"] == "open")


@bp.get("/landing")
def landing():
    stats = {
        "documents": db.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")["c"],
        "facts": db.q1("SELECT COUNT(*) c FROM facts")["c"],
        "chunks": db.q1("SELECT COUNT(*) c FROM chunks")["c"],
        "conflicts": db.q1(
            "SELECT COUNT(*) c FROM conflict_status WHERE status != 'resolved'")["c"],
    }
    return jsonify({"stats": stats})


@bp.get("/dashboard")
def dashboard():
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
    return jsonify({
        "stats": stats,
        "emb_name": emb_name, "emb_dim": emb_dim,
        "llm_status": llm.status(), "vectors": vectors,
        "storage_gb": _dir_size(config.DATA_DIR) / 1e9,
        "recent_docs": _rows(recent_docs), "jobs": _rows(jobs),
        "open_conflicts": _open_conflicts(),
        "extraction_accuracy": eval_metrics.get("accuracy"),
        "kpi": quality.kpi_stats(),
        "subs": _rows(db.q(
            "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")),
    })


@bp.get("/pipeline")
def pipeline_page():
    stats = {
        "documents": db.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")["c"],
        "chunks": db.q1("SELECT COUNT(*) c FROM chunks")["c"],
        "facts": db.q1("SELECT COUNT(*) c FROM facts")["c"],
        "tags": db.q1("SELECT COUNT(DISTINCT keyword) c FROM doc_keywords")["c"],
    }
    return jsonify({"stats": stats, "stages": pipeline.STAGES})


@bp.get("/documents")
def documents():
    sel_sub = request.args.get("subsidiary") or ""
    sel_type = request.args.get("type") or ""
    q = (request.args.get("q") or "").strip()
    tag_filter = request.args.get("tag") or None
    where, params = [], []
    if sel_sub:
        where.append("subsidiary=?")
        params.append(sel_sub)
    if sel_type:
        where.append("doc_type=?")
        params.append(sel_type)
    if q:
        where.append("(display_name LIKE ? OR filename LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    sql = "SELECT * FROM documents" + (" WHERE " + " AND ".join(where) if where else "") + \
        " ORDER BY upload_ts DESC"
    rows = _rows(db.q(sql, tuple(params)))
    if tag_filter:
        keep = {x["doc_id"] for x in db.q("SELECT doc_id FROM doc_keywords WHERE keyword=?",
                                          (tag_filter,))}
        rows = [r for r in rows if r["id"] in keep]
    kw_map = {r["id"]: [x["keyword"] for x in db.q(
        "SELECT keyword FROM doc_keywords WHERE doc_id=? ORDER BY keyword", (r["id"],))]
        for r in rows}
    counts = {r["doc_type"]: r["n"] for r in db.q(
        "SELECT doc_type, COUNT(*) n FROM documents GROUP BY doc_type")}
    return jsonify({
        "docs": rows, "kw_map": kw_map, "type_counts": counts,
        "subsidiaries": _rows(db.q(
            "SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")),
        "doc_types": _rows(db.q("SELECT DISTINCT doc_type FROM documents ORDER BY doc_type")),
        "tags": retrieval.top_tags(30),
        "filters": {"q": q, "subsidiary": sel_sub, "type": sel_type, "tag": tag_filter},
    })


@bp.get("/doc/<doc_id>")
def viewer(doc_id):
    doc = db.q1("SELECT * FROM documents WHERE id=?", (doc_id,))
    if not doc:
        return jsonify({"error": "document not found"}), 404
    doc = dict(doc)
    pages = _rows(db.q(
        "SELECT page_no, ocr_used, avg_confidence, image_path, page_class, summary FROM pages WHERE doc_id=? ORDER BY page_no",
        (doc_id,)))
    sheets = _rows(db.q(
        "SELECT DISTINCT sheet_no FROM elements WHERE doc_id=? AND sheet_no IS NOT NULL ORDER BY sheet_no",
        (doc_id,)))
    page_no = request.args.get("page", type=int)
    sheet_no = request.args.get("sheet", type=int)
    is_pdf = doc["doc_type"] in ("pdf", "digital_pdf", "mixed_pdf", "scanned_pdf")
    is_sheet = doc["doc_type"] in ("xlsx", "csv")
    elements, tables, reading_elements = [], [], []
    if page_no and is_pdf:
        elements = _rows(db.q(
            "SELECT * FROM elements WHERE doc_id=? AND page_no=? ORDER BY order_idx",
            (doc_id, page_no)))
    elif sheet_no and is_sheet:
        for t in db.q(
                "SELECT * FROM tables WHERE doc_id=? AND sheet_no=? ORDER BY table_idx",
                (doc_id, sheet_no)):
            t = dict(t)
            t["headers"] = json.loads(t["headers_json"])
            t["rows"] = _rows(db.q(
                "SELECT * FROM table_cells WHERE table_id=? ORDER BY row_idx, col_idx",
                (t["id"],)))
            tables.append(t)
    elif not is_pdf and not is_sheet:
        reading_elements = _rows(db.q(
            "SELECT * FROM elements WHERE doc_id=? AND text != '' ORDER BY order_idx LIMIT 400",
            (doc_id,)))
    kw_list = [r["keyword"] for r in db.q(
        "SELECT keyword FROM doc_keywords WHERE doc_id=? ORDER BY keyword", (doc_id,))]
    return jsonify({
        "doc": doc, "pages": pages, "sheets": sheets,
        "page_no": page_no, "sheet_no": sheet_no,
        "elements": elements, "tables": tables,
        "reading_elements": reading_elements, "kw_list": kw_list,
    })


@bp.get("/search")
def search():
    q_text = request.args.get("q", "").strip()
    tag = request.args.get("tag") or None
    subsidiary = request.args.get("subsidiary") or None
    doc_type = request.args.get("type") or None
    date_from = (request.args.get("from") or "").strip() or None
    date_to = (request.args.get("to") or "").strip() or None
    doc_from = normalize_period(date_from) if date_from else None
    doc_to = normalize_period(date_to) if date_to else None
    filters = {"tag": tag, "subsidiary": subsidiary, "doc_type": doc_type,
               "doc_from": doc_from, "doc_to": doc_to}
    results = retrieval.hybrid_search(q_text, filters=filters) if q_text else []
    if q_text:
        for ev in results:
            ev["tags"] = retrieval.doc_keywords_map([ev["doc_id"]]).get(ev["doc_id"], [])
    if q_text:
        org = {
            "facts": org_search.search_facts(q_text, filters=filters),
            "entities": org_search.search_entities(q_text),
            "locations": org_search.search_entities(q_text, entity_types=org_search.LOCATION_TYPES),
            "metrics": org_search.search_metrics(q_text),
            "reference": org_search.search_reference(q_text),
        }
    else:
        org = {"facts": [], "entities": [], "locations": [], "metrics": [], "reference": []}
    org["counts"] = {k: len(v) for k, v in org.items() if k != "counts"}
    return jsonify({
        "q": q_text, "results": results, **org,
        "filters": {"tag": tag or "", "subsidiary": subsidiary or "",
                    "type": doc_type or "", "from": date_from or "", "to": date_to or ""},
        "subs": _rows(db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")),
        "doc_types": _rows(db.q("SELECT DISTINCT doc_type FROM documents ORDER BY doc_type")),
        "tags": retrieval.top_tags(30),
    })


@bp.get("/ask")
def ask():
    subs = _rows(db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL"))
    doc_ids = [d for d in (request.args.get("doc") or "").split(",") if d]
    doc_ids += [d for d in (request.args.get("docs") or "").split(",") if d]
    scoped = []
    for d in dict.fromkeys(doc_ids):
        row = db.q1("SELECT id, display_name, filename FROM documents WHERE id = ?", (d,))
        if row:
            scoped.append(dict(row))
    return jsonify({"subs": subs, "scoped_docs": scoped,
                    "seed_q": request.args.get("q") or ""})


@bp.get("/graph")
def graph_page():
    return jsonify({
        "subs": _rows(db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")),
        "tags": retrieval.top_tags(30),
    })


@bp.get("/insights")
def insights():
    return jsonify({
        "subs": _rows(db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")),
        "entities": _rows(db.q("""SELECT e.canonical_name, COUNT(f.id) n FROM entities e
                       JOIN facts f ON f.entity_id = e.id
                       WHERE f.attribute != 'quantity' AND f.value_norm IS NOT NULL
                       GROUP BY e.id ORDER BY n DESC LIMIT 20""")),
        "attributes": _rows(db.q("""SELECT DISTINCT attribute FROM facts
                         WHERE attribute != 'quantity' ORDER BY attribute""")),
        "quality_stats": quality.quality_stats(),
    })


@bp.get("/topics")
def topics():
    scope = request.args.get("scope", "corpus")
    scope_filter = None if scope == "corpus" else scope
    clusters = []
    for t in db.q("SELECT * FROM doc_topics WHERE scope IS ? ORDER BY id DESC LIMIT 6",
                  (scope_filter,)):
        t = dict(t)
        t["keywords"] = json.loads(t["keywords_json"])
        t["doc_ids"] = json.loads(t["doc_ids_json"])
        clusters.append(t)
    return jsonify({
        "scope": scope,
        "clusters": clusters,
        "subs": _rows(db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")),
    })


@bp.get("/reports")
def reports():
    from backend.core import reports as reports_mod
    return jsonify({
        "reports": _rows(db.q("SELECT * FROM reports ORDER BY id DESC")),
        "templates": list(reports_mod.TEMPLATES),
        "entities": _rows(db.q("SELECT canonical_name FROM entities ORDER BY canonical_name")),
    })


@bp.get("/review/<int:rid>")
def review(rid):
    from backend.core import conflicts as conflicts_mod
    from backend.db import database as _db
    row = _db.q1("SELECT * FROM reports WHERE id=?", (rid,))
    if not row:
        return jsonify({"error": "report not found"}), 404
    row = dict(row)
    prov = json.loads(row["provenance_json"] or "{}")
    sources = []
    for ref, slot in prov.get("slots", {}).items():
        doc = _db.q1("SELECT filename, display_name, is_current_version, ocr_pages"
                     " FROM documents WHERE id=?", (slot.get("doc_id") or "",))
        if not doc:
            continue
        sources.append({
            "ref": ref, "filename": doc["display_name"] or doc["filename"],
            "doc_id": slot.get("doc_id"),
            "page_no": slot.get("page_no"), "sheet_no": slot.get("sheet_no"),
            "current_version": bool(doc["is_current_version"]),
            "ocr": bool(doc["ocr_pages"]),
        })
    return jsonify({
        "report": row, "sources": sources, "stats": prov.get("stats"),
        "conflict_counts": conflicts_mod.status_counts(),
    })


@bp.get("/compare")
def compare():
    from backend.core import compare as compare_mod
    doc_id = request.args.get("doc") or None
    suggested = compare_mod.version_pair(doc_id) if doc_id else None
    return jsonify({
        "docs": _rows(db.q("""SELECT id, filename, display_name, doc_date_raw
                     FROM documents WHERE status='completed' ORDER BY upload_ts DESC""")),
        "suggested": suggested, "sel_doc": doc_id or "",
    })


@bp.get("/conflicts-filters")
def conflicts_filters():
    entities = db.q("""SELECT DISTINCT COALESCE(e.canonical_name, f.entity_text) n
                   FROM facts f LEFT JOIN entities e ON e.id = f.entity_id
                   WHERE COALESCE(e.canonical_name, f.entity_text) != ''
                   ORDER BY n""")
    attributes = db.q("SELECT DISTINCT attribute FROM facts ORDER BY attribute")
    return jsonify({"entities": _rows(entities), "attributes": _rows(attributes)})


@bp.get("/settings")
def settings():
    from backend.core import appsettings
    from backend.core.knowledge.summary import has_summaries
    done, total = has_summaries()
    emb_name, emb_dim = embedder.model_info()
    return jsonify({
        "settings": appsettings.all_settings(),
        "llm_status": llm.status(),
        "emb_name": emb_name, "emb_dim": emb_dim,
        "summaries_done": done, "summaries_total": total,
        "doc_count": db.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")["c"],
    })
