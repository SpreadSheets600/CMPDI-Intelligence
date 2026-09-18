"""External knowledge layer: public reference context for entities.

Joins organizational entities with curated public information (profiles,
operating geography, dated production and sector statistics) while keeping
reference strictly separate from evidence. Reference rows live in
``entity_reference`` and are served with ``origin: "reference"``; library
roll-ups are served with ``origin: "evidence"``. Nothing here writes to
the fact index, so reference values can never surface as answers, report
figures or conflicts.
"""

from backend.core.knowledge import reference_data
from backend.db import database as db


def seed_reference() -> dict:
    """Idempotent upsert of the curated dataset. Re-running refreshes
    values and sources without duplicating rows or touching evidence."""
    from backend.core.knowledge import facts

    facts.ensure_subsidiary_entities()

    entities = 0
    entries = 0
    for abbr, rows in reference_data.ENTRIES.items():
        ent = db.q1("SELECT id FROM entities WHERE canonical_name=?", (abbr,))
        if not ent:
            continue
        entities += 1
        for r in rows:
            existing = db.q1(
                """SELECT id FROM entity_reference
                   WHERE entity_id=? AND category=? AND label=?""",
                (ent["id"], r["category"], r["label"]),
            )
            if existing:
                db.execute(
                    """UPDATE entity_reference
                       SET value=?, unit=?, as_of=?, source=? WHERE id=?""",
                    (
                        r["value"],
                        r.get("unit"),
                        r.get("as_of"),
                        r["source"],
                        existing["id"],
                    ),
                )
            else:
                db.execute(
                    """INSERT INTO entity_reference
                       (entity_id, category, label, value, unit, as_of, source)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        ent["id"],
                        r["category"],
                        r["label"],
                        r["value"],
                        r.get("unit"),
                        r.get("as_of"),
                        r["source"],
                    ),
                )
            entries += 1
    return {"entities": entities, "entries": entries}


def resolve(name: str) -> dict | None:
    """Resolve a display name to its entity row using the same
    canonical-plus-alias patterns the fact extractor uses."""
    from backend.core.knowledge import facts

    name = (name or "").strip()
    if not name:
        return None
    direct = db.q1("SELECT * FROM entities WHERE canonical_name=?", (name,))
    if direct:
        return dict(direct)
    # Longest-match resolution, not first-match: ECL's alias
    # ("Eastern Coalfields Limited") is a substring of SECL's.
    eid = facts.resolve_entity_text(name, facts.load_patterns())
    if eid is None:
        return None
    row = db.q1("SELECT * FROM entities WHERE id=?", (eid,))
    return dict(row) if row else None


def _library_rollup(entity_id: int) -> dict:
    """Evidence footprint of the entity inside the ingested library."""
    docs = db.q1(
        """SELECT COUNT(DISTINCT c.doc_id) n FROM facts f
           JOIN chunks c ON c.id = f.chunk_id WHERE f.entity_id=?""",
        (entity_id,),
    )["n"]
    n_facts = db.q1("SELECT COUNT(*) n FROM facts WHERE entity_id=?", (entity_id,))["n"]
    attributes = [
        r["attribute"]
        for r in db.q(
            "SELECT DISTINCT attribute FROM facts WHERE entity_id=? ORDER BY attribute",
            (entity_id,),
        )
    ]
    periods = [
        r["period_norm"]
        for r in db.q(
            """SELECT DISTINCT period_norm FROM facts
               WHERE entity_id=? AND period_norm IS NOT NULL ORDER BY period_norm""",
            (entity_id,),
        )
    ]
    return {
        "origin": "evidence",
        "documents": docs,
        "facts": n_facts,
        "attributes": attributes,
        "periods": periods,
    }


def entity_context(name: str) -> dict | None:
    """Reference context plus library footprint for one entity, or None
    when the name resolves to nothing (unknown entity, empty library)."""
    ent = resolve(name)
    if not ent:
        return None
    grouped: dict[str, list[dict]] = {c: [] for c in reference_data.CATEGORIES}
    for r in db.q(
        """SELECT category, label, value, unit, as_of, source FROM entity_reference
           WHERE entity_id=?""",
        (ent["id"],),
    ):
        grouped.setdefault(r["category"], []).append(
            {
                "label": r["label"],
                "value": r["value"],
                "unit": r["unit"],
                "as_of": r["as_of"],
                "source": r["source"],
                "origin": "reference",
            }
        )
    return {
        "entity": ent["canonical_name"],
        "type": ent["type"],
        "reference": grouped,
        "n_reference": sum(len(v) for v in grouped.values()),
        "library": _library_rollup(ent["id"]),
    }


def coverage() -> list[dict]:
    """Which entities carry reference context and how much."""
    return [
        dict(r)
        for r in db.q(
            """SELECT e.canonical_name, e.type, COUNT(r.id) n FROM entities e
               LEFT JOIN entity_reference r ON r.entity_id = e.id
               GROUP BY e.id ORDER BY n DESC, e.canonical_name"""
        )
    ]
