"""Insights: the fact index made visible. Fact explorer (any metric across
documents and fiscal years, every value with its receipt), corpus analytics,
and per-document data quality."""

from flask import Blueprint, jsonify, render_template, request

from backend.core import retrieval
from backend.db import database as db

bp = Blueprint("insights", __name__)


@bp.route("/insights")
def insights():
    subs = db.q("SELECT DISTINCT subsidiary FROM documents WHERE subsidiary IS NOT NULL")
    entities = db.q("""SELECT e.canonical_name, COUNT(f.id) n FROM entities e
                       JOIN facts f ON f.entity_id = e.id
                       WHERE f.attribute != 'quantity' AND f.value_norm IS NOT NULL
                       GROUP BY e.id ORDER BY n DESC LIMIT 20""")
    attributes = db.q("""SELECT DISTINCT attribute FROM facts
                         WHERE attribute != 'quantity' ORDER BY attribute""")
    return render_template("pages/insights.html", subs=subs, entities=entities,
                           attributes=attributes,
                           tags=retrieval.top_tags(20))


@bp.route("/api/facts")
def facts_data():
    entity = request.args.get("entity", "")
    attribute = request.args.get("attribute", "")
    if not entity or not attribute:
        return jsonify({"series": [], "documents": {}})
    rows = db.q("""SELECT f.id, f.period_norm, f.value_raw, f.value_norm, f.unit, f.flags,
                          c.doc_id, c.page_no, c.sheet_no, d.filename, d.is_current_version,
                          e.canonical_name
                   FROM facts f
                   JOIN entities e ON e.id = f.entity_id
                   JOIN chunks c ON c.id = f.chunk_id
                   JOIN documents d ON d.id = c.doc_id
                   WHERE e.canonical_name = ? AND f.attribute = ?
                     AND f.value_norm IS NOT NULL
                   ORDER BY f.period_norm, d.is_current_version DESC""",
                (entity, attribute))
    series, docs = [], {}
    for r in rows:
        series.append(dict(r))
        docs[r["doc_id"]] = r["filename"]
    return jsonify({"series": series, "documents": docs,
                    "entity": entity, "attribute": attribute})


@bp.route("/api/insights/summary")
def summary():
    doc_quality = [dict(r) for r in db.q("""
        SELECT d.filename, d.doc_type, d.subsidiary, d.page_count,
               (SELECT COUNT(*) FROM chunks c WHERE c.doc_id = d.id) chunks,
               (SELECT COUNT(*) FROM facts f JOIN chunks c ON c.id = f.chunk_id
                WHERE c.doc_id = d.id AND f.value_norm IS NOT NULL) facts,
               (SELECT COUNT(*) FROM doc_keywords k WHERE k.doc_id = d.id) tags,
               (SELECT COUNT(*) FROM pages p WHERE p.doc_id = d.id AND p.ocr_used) ocr_pages
        FROM documents d WHERE d.is_current_version = 1 AND d.status = 'completed'
        ORDER BY facts DESC""")]
    return jsonify({"doc_quality": doc_quality})
