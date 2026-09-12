"""Insights: the fact index made visible. Fact explorer (any metric across
documents and fiscal years, every value with its receipt), corpus analytics,
and per-document data quality."""

from flask import Blueprint, jsonify, render_template, request

from backend.core import retrieval
from backend.core import quality
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
                           quality_stats=quality.quality_stats())