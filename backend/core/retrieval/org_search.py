"""Organization-wide search: one query across documents, facts, entities,
locations, metrics and external reference context.

Read-only assembly over the existing knowledge layer — no new extraction,
no schema changes. Document search reuses hybrid retrieval; every fact
keeps its chunk -> page -> document receipt; reference rows are served
with ``origin: "reference"`` and are context, never evidence.
"""

from __future__ import annotations

from backend.core.knowledge import relations
from backend.core.normalize import (
    ATTRIBUTE_KEYWORDS,
    detect_attribute,
    fy_label,
    normalize_period,
)
from backend.db import database as db

LOCATION_TYPES = ("location", "coalfield", "block")

_MAX_FACTS = 12
_MAX_ENTITIES = 12
_MAX_REFERENCE = 12


def _like(text: str) -> str:
    return f"%{text.strip()}%"


def search_facts(query: str, filters: dict | None = None) -> list[dict]:
    """Numeric facts matching the query's entity, attribute or period."""
    query = (query or "").strip()
    if not query:
        return []
    entity_ids = _matching_entity_ids(query)
    attr = detect_attribute(query)
    period = normalize_period(query)
    if not entity_ids and not attr and not period:
        return []
    where, params = ["f.value_norm IS NOT NULL"], []
    clauses = []
    if entity_ids:
        marks = ",".join("?" * len(entity_ids))
        clauses.append(f"f.entity_id IN ({marks})")
        params.extend(entity_ids)
    if attr:
        clauses.append("f.attribute = ?")
        params.append(attr)
    if period:
        clauses.append("f.period_norm = ?")
        params.append(period)
    # fall back to raw-mention match so unresolved names still hit
    clauses.append("f.entity_text LIKE ?")
    params.append(_like(query))
    if attr is None:
        clauses.append("f.attribute LIKE ?")
        params.append(_like(query))
    where.append("(" + " OR ".join(clauses) + ")")
    if filters and filters.get("subsidiary"):
        where.append("d.subsidiary = ?")
        params.append(filters["subsidiary"])
    if filters and filters.get("doc_type"):
        where.append("d.doc_type = ?")
        params.append(filters["doc_type"])
    rows = db.q(
        f"""SELECT f.id, e.canonical_name AS entity, f.entity_text, f.attribute,
                   f.period_norm, f.value_raw, f.value_norm, f.unit, f.flags,
                   f.conf, c.id AS chunk_id, c.page_no, c.sheet_no,
                   d.id AS doc_id, d.filename, d.display_name, d.subsidiary,
                   d.is_current_version
            FROM facts f
            LEFT JOIN entities e ON e.id = f.entity_id
            JOIN chunks c ON c.id = f.chunk_id
            JOIN documents d ON d.id = c.doc_id
            WHERE {" AND ".join(where)}
            ORDER BY d.is_current_version DESC, f.conf DESC, f.id DESC
            LIMIT ?""",
        (*params, _MAX_FACTS),
    )
    out = []
    for r in rows:
        rec = dict(r)
        rec["period_label"] = fy_label(rec["period_norm"])
        rec["filename"] = rec["display_name"] or rec["filename"]
        out.append(rec)
    return out


def _matching_entity_ids(query: str) -> list[int]:
    like = _like(query)
    rows = db.q(
        """SELECT id FROM entities
           WHERE canonical_name LIKE ? OR aliases_json LIKE ? LIMIT 25""",
        (like, like),
    )
    return [r["id"] for r in rows]


def search_entities(
    query: str, entity_types: tuple[str, ...] | None = None
) -> list[dict]:
    """Entities whose name or alias matches, most-reported first."""
    query = (query or "").strip()
    if not query:
        return []
    like = _like(query)
    where = ["(e.canonical_name LIKE ? OR e.aliases_json LIKE ?)"]
    params: list = [like, like]
    if entity_types:
        marks = ",".join("?" * len(entity_types))
        where.append(f"e.type IN ({marks})")
        params.extend(entity_types)
    rows = db.q(
        f"""SELECT e.id, e.canonical_name, e.type,
                   COUNT(f.id) AS n_facts,
                   COUNT(DISTINCT c.doc_id) AS n_docs,
                   COUNT(DISTINCT f.attribute) AS n_metrics,
                   (SELECT COUNT(*) FROM entity_reference r
                     WHERE r.entity_id = e.id) AS n_reference
            FROM entities e
            LEFT JOIN facts f ON f.entity_id = e.id
            LEFT JOIN chunks c ON c.id = f.chunk_id
            WHERE {" AND ".join(where)}
            GROUP BY e.id ORDER BY n_facts DESC, e.canonical_name LIMIT ?""",
        (*params, _MAX_ENTITIES),
    )
    out = []
    for r in rows:
        rec = dict(r)
        rec["kind"] = relations.kind_of(rec["type"]) or "entity"
        out.append(rec)
    return out


def search_metrics(query: str) -> list[dict]:
    """Metric (attribute) matches with corpus counts and a sample receipt."""
    query = (query or "").strip()
    if not query:
        return []
    low = query.lower()
    matched = [
        attr
        for attr, words in ATTRIBUTE_KEYWORDS.items()
        if low in attr or any(low in w or w in low for w in words)
    ]
    like_rows = db.q(
        """SELECT DISTINCT attribute FROM facts
           WHERE attribute LIKE ? AND attribute != 'quantity' LIMIT 12""",
        (_like(query),),
    )
    for r in like_rows:
        if r["attribute"] not in matched:
            matched.append(r["attribute"])
    out = []
    for attr in matched[:_MAX_ENTITIES]:
        stat = db.q1(
            """SELECT COUNT(*) n_facts, COUNT(DISTINCT f.entity_id) n_entities
               FROM facts f WHERE f.attribute = ?""",
            (attr,),
        )
        sample = db.q1(
            """SELECT e.canonical_name AS entity, f.value_raw, f.unit,
                      d.id AS doc_id, d.filename, d.display_name,
                      c.page_no, c.sheet_no, c.id AS chunk_id
               FROM facts f
               LEFT JOIN entities e ON e.id = f.entity_id
               JOIN chunks c ON c.id = f.chunk_id
               JOIN documents d ON d.id = c.doc_id
               WHERE f.attribute = ?
               ORDER BY d.is_current_version DESC LIMIT 1""",
            (attr,),
        )
        rec = {
            "attribute": attr,
            "label": attr.replace("_", " "),
            "n_facts": stat["n_facts"] if stat else 0,
            "n_entities": stat["n_entities"] if stat else 0,
            "sample": dict(sample) if sample else None,
        }
        if rec["sample"]:
            rec["sample"]["filename"] = (
                rec["sample"]["display_name"] or rec["sample"]["filename"]
            )
        out.append(rec)
    return out


def search_reference(query: str) -> list[dict]:
    """External reference context matching the query. Context only —
    rows never enter the fact index, answers or reports."""
    query = (query or "").strip()
    if not query:
        return []
    like = _like(query)
    rows = db.q(
        """SELECT e.canonical_name AS entity, e.type,
                  r.category, r.label, r.value, r.unit, r.as_of, r.source
           FROM entity_reference r
           JOIN entities e ON e.id = r.entity_id
           WHERE r.label LIKE ? OR r.value LIKE ? OR e.canonical_name LIKE ?
           ORDER BY e.canonical_name, r.category LIMIT ?""",
        (like, like, like, _MAX_REFERENCE),
    )
    return [{**dict(r), "origin": "reference"} for r in rows]


def organization_search(query: str, filters: dict | None = None) -> dict:
    """Unified search across all six organization layers.

    ``filters`` (subsidiary, doc_type, tag, doc_from/doc_to) scope the
    document and fact layers; entity, location, metric and reference layers
    are corpus-wide roll-ups with their library footprint attached.
    """
    from backend.core import retrieval as retrieval_mod

    query = (query or "").strip()
    if not query:
        return {
            "documents": [],
            "facts": [],
            "entities": [],
            "locations": [],
            "metrics": [],
            "reference": [],
            "counts": {},
        }
    documents = retrieval_mod.hybrid_search(query, filters=filters)
    facts = search_facts(query, filters=filters)
    entities = search_entities(query)
    locations = search_entities(query, entity_types=LOCATION_TYPES)
    # mine hits stay in entities; locations are strictly places
    # (location | coalfield | block)
    metrics = search_metrics(query)
    reference = search_reference(query)
    counts = {
        "documents": len(documents),
        "facts": len(facts),
        "entities": len(entities),
        "locations": len(locations),
        "metrics": len(metrics),
        "reference": len(reference),
    }
    return {
        "documents": documents,
        "facts": facts,
        "entities": entities,
        "locations": locations,
        "metrics": metrics,
        "reference": reference,
        "counts": counts,
    }
