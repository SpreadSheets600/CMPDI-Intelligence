"""P1 knowledge-graph relationship extraction.

Deterministic, offline, no LLM: every edge comes from entities co-occurring
in one chunk (one observation, one receipt) plus document version links.
Reference context (``entity_reference``) never enters here — it is context,
not evidence.

Node kinds: organization | mine | location | geology | document | metric |
event. Metrics stay virtual (derived from the fact index at query time);
everything else is an ``entities`` row or a ``documents`` row.
"""

from __future__ import annotations

import json
import re

from backend.core import config
from backend.db import database as db

ORGANIZATION = "organization"
MINE = "mine"
LOCATION = "location"
GEOLOGY = "geology"
DOCUMENT = "document"
METRIC = "metric"
EVENT = "event"

RELATIONS = (
    "OPERATES",
    "LOCATED_IN",
    "BASED_IN",
    "HAS_GEOLOGY",
    "MENTIONS",
    "HAS_METRIC",
    "REPORTS_METRIC",
    "OCCURRED_AT",
    "INVOLVES",
    "REPORTED_IN",
    "SUPERSEDES",
)

# Persisted per chunk; the fact-derived trio (MENTIONS org/mine, HAS_METRIC,
# REPORTS_METRIC) is built at query time from facts so this table never
# duplicates the fact index.
_PERSISTED = (
    "OPERATES",
    "LOCATED_IN",
    "BASED_IN",
    "HAS_GEOLOGY",
    "MENTIONS",
    "OCCURRED_AT",
    "INVOLVES",
    "REPORTED_IN",
)

_TYPE_TO_KIND = {
    "subsidiary": ORGANIZATION,
    "organization": ORGANIZATION,
    "mine": MINE,
    "coalfield": LOCATION,
    "block": LOCATION,
    "location": LOCATION,
    "seam": GEOLOGY,
    "geology": GEOLOGY,
    "event": EVENT,
}

INDIAN_STATES = (
    "Andhra Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Tamil Nadu",
    "Telangana",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
)

_SEAM_RE = re.compile(r"\b([A-Z][A-Za-z0-9&]*(?:\s+[A-Z][A-Za-z0-9&]*)*)\s+Seam\b")
_FORMATION_RE = re.compile(
    r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\s+Formation\b"
)
_COALFIELD_RE = re.compile(
    r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\s+Coalfield\b"
)

# Trigger word -> canonical event node. Bounded on purpose: one node per
# event type, every occurrence keeps its own receipt on the edge.
EVENT_TRIGGERS: dict[str, str] = {
    "commissioned": "Commissioning",
    "commissioning": "Commissioning",
    "inaugurated": "Commissioning",
    "accident": "Safety Accident",
    "explosion": "Safety Accident",
    "mishap": "Safety Accident",
    "fatal": "Safety Accident",
    "subsidence": "Subsidence",
    "collapse": "Subsidence",
    "expansion": "Expansion",
    "expansion project": "Expansion",
    "clearance": "Statutory Clearance",
    "approval": "Statutory Clearance",
    "approved": "Statutory Clearance",
    "closure": "Mine Closure",
    "closed": "Mine Closure",
    "abandoned": "Mine Closure",
    "strike": "Strike",
}
_EVENT_RES = [
    (re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE), label)
    for t, label in EVENT_TRIGGERS.items()
]


def kind_of(entity_type: str) -> str | None:
    return _TYPE_TO_KIND.get((entity_type or "").lower())


def ensure_event_entities() -> None:
    for label in sorted(set(EVENT_TRIGGERS.values())):
        if not db.q1("SELECT id FROM entities WHERE canonical_name=?", (label,)):
            db.execute(
                "INSERT INTO entities (canonical_name, type, aliases_json)"
                " VALUES (?,?,?)",
                (label, "event", json.dumps([])),
            )


def ensure_geo_entities(text: str) -> None:
    """Register locations and geology mentioned in text (states, coalfields,
    seams, formations). Idempotent; runs per document before extraction."""
    for state in INDIAN_STATES:
        if re.search(rf"\b{re.escape(state)}\b", text, re.IGNORECASE) and not db.q1(
            "SELECT id FROM entities WHERE canonical_name=?", (state,)
        ):
            db.execute(
                "INSERT INTO entities (canonical_name, type) VALUES (?,?)",
                (state, "location"),
            )
    for pattern, etype in (
        (_COALFIELD_RE, "coalfield"),
        (_SEAM_RE, "seam"),
        (_FORMATION_RE, "geology"),
    ):
        for match in pattern.finditer(text):
            name = match.group(0).strip()
            if not db.q1("SELECT id FROM entities WHERE canonical_name=?", (name,)):
                db.execute(
                    "INSERT INTO entities (canonical_name, type) VALUES (?,?)",
                    (name, etype),
                )


def _entity_kinds() -> dict[int, tuple[str, str]]:
    """entity_id -> (canonical_name, graph kind)."""
    out: dict[int, tuple[str, str]] = {}
    for row in db.q("SELECT id, canonical_name, type FROM entities"):
        kind = kind_of(row["type"])
        if kind:
            out[row["id"]] = (row["canonical_name"], kind)
    return out


def _matched_entities(text: str, patterns) -> list[int]:
    from backend.core.knowledge import facts

    seen: list[int] = []
    for pattern, eid in patterns:
        if pattern.search(text) and eid not in seen:
            seen.append(eid)
    # resolve_entity_text is for single-entity attribution; here every
    # co-occurring entity in the chunk is a relationship endpoint
    _ = facts  # reuse import site for gazetteer consistency
    return seen


def _match_events(text: str) -> list[str]:
    found: list[str] = []
    for rx, label in _EVENT_RES:
        if rx.search(text) and label not in found:
            found.append(label)
    return found


def _event_ids(labels: list[str], kinds: dict[int, tuple[str, str]]) -> list[int]:
    name_to_id = {name: eid for eid, (name, _kind) in kinds.items()}
    return [name_to_id[label] for label in labels if label in name_to_id]


def _insert(
    src_kind: str,
    src_label: str,
    src_id: int | None,
    dst_kind: str,
    dst_label: str,
    dst_id: int | None,
    relation: str,
    chunk_id: int | None,
    doc_id: str,
    page_no: int | None,
    sheet_no: int | None,
    conf: float,
) -> None:
    db.execute(
        """INSERT OR IGNORE INTO kg_edges
           (src_kind, src_label, src_entity_id, dst_kind, dst_label,
            dst_entity_id, relation, chunk_id, doc_id, page_no, sheet_no, conf)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            src_kind,
            src_label,
            src_id,
            dst_kind,
            dst_label,
            dst_id,
            relation,
            chunk_id,
            doc_id,
            page_no,
            sheet_no,
            conf,
        ),
    )


def extract_for_doc(doc_id: str) -> dict:
    """(Re)build the persisted relationship edges for one document.

    Deletes the document's old edges first so re-ingestion never duplicates.
    Returns a small count summary for job stats."""
    from backend.core.knowledge import facts

    doc = db.q1("SELECT id, filename FROM documents WHERE id=?", (doc_id,))
    if not doc:
        return {"edges": 0}

    texts = [
        r["text"] for r in db.q("SELECT text FROM pages WHERE doc_id=?", (doc_id,))
    ]
    texts += [
        r["text"] for r in db.q("SELECT text FROM elements WHERE doc_id=?", (doc_id,))
    ]
    texts += [
        r["text"] for r in db.q("SELECT text FROM chunks WHERE doc_id=?", (doc_id,))
    ]
    ensure_geo_entities("\n".join(t for t in texts if t))
    ensure_event_entities()
    facts.ensure_subsidiary_entities()

    db.execute("DELETE FROM kg_edges WHERE doc_id=?", (doc_id,))
    patterns = facts.load_patterns()
    kinds = _entity_kinds()

    counts: dict[str, int] = {}
    for chunk in db.q("SELECT * FROM chunks WHERE doc_id=?", (doc_id,)):
        text = chunk["text"] or ""
        if len(text) < 8:
            continue
        conf = 1.0
        if chunk["page_no"]:
            page = db.q1(
                "SELECT avg_confidence FROM pages WHERE doc_id=? AND page_no=?",
                (doc_id, chunk["page_no"]),
            )
            if (
                page
                and page["avg_confidence"] is not None
                and page["avg_confidence"] < config.OCR_MIN_CONF
            ):
                conf = 0.5
        eids = _matched_entities(text, patterns)
        by_kind: dict[str, list[int]] = {}
        for eid in eids:
            if eid in kinds:
                by_kind.setdefault(kinds[eid][1], []).append(eid)
        events = _event_ids(_match_events(text), kinds)
        chunk_id = chunk["id"]
        page_no = chunk["page_no"]
        sheet_no = chunk["sheet_no"]

        def emit(relation: str) -> None:
            counts[relation] = counts.get(relation, 0) + 1

        for org in by_kind.get(ORGANIZATION, []):
            for mine in by_kind.get(MINE, []):
                _insert(
                    ORGANIZATION,
                    kinds[org][0],
                    org,
                    MINE,
                    kinds[mine][0],
                    mine,
                    "OPERATES",
                    chunk_id,
                    doc_id,
                    page_no,
                    sheet_no,
                    conf,
                )
                emit("OPERATES")
        for mine in by_kind.get(MINE, []):
            for loc in by_kind.get(LOCATION, []):
                _insert(
                    MINE,
                    kinds[mine][0],
                    mine,
                    LOCATION,
                    kinds[loc][0],
                    loc,
                    "LOCATED_IN",
                    chunk_id,
                    doc_id,
                    page_no,
                    sheet_no,
                    conf,
                )
                emit("LOCATED_IN")
            for geo in by_kind.get(GEOLOGY, []):
                _insert(
                    MINE,
                    kinds[mine][0],
                    mine,
                    GEOLOGY,
                    kinds[geo][0],
                    geo,
                    "HAS_GEOLOGY",
                    chunk_id,
                    doc_id,
                    page_no,
                    sheet_no,
                    conf,
                )
                emit("HAS_GEOLOGY")
        for org in by_kind.get(ORGANIZATION, []):
            for loc in by_kind.get(LOCATION, []):
                _insert(
                    ORGANIZATION,
                    kinds[org][0],
                    org,
                    LOCATION,
                    kinds[loc][0],
                    loc,
                    "BASED_IN",
                    chunk_id,
                    doc_id,
                    page_no,
                    sheet_no,
                    conf,
                )
                emit("BASED_IN")
        for loc in by_kind.get(LOCATION, []):
            _insert(
                DOCUMENT,
                doc["filename"],
                None,
                LOCATION,
                kinds[loc][0],
                loc,
                "MENTIONS",
                chunk_id,
                doc_id,
                page_no,
                sheet_no,
                conf,
            )
            emit("MENTIONS")
        for geo in by_kind.get(GEOLOGY, []):
            _insert(
                DOCUMENT,
                doc["filename"],
                None,
                GEOLOGY,
                kinds[geo][0],
                geo,
                "MENTIONS",
                chunk_id,
                doc_id,
                page_no,
                sheet_no,
                conf,
            )
            emit("MENTIONS")
        for evt in events:
            _insert(
                DOCUMENT,
                doc["filename"],
                None,
                EVENT,
                kinds[evt][0],
                evt,
                "MENTIONS",
                chunk_id,
                doc_id,
                page_no,
                sheet_no,
                conf,
            )
            _insert(
                EVENT,
                kinds[evt][0],
                evt,
                DOCUMENT,
                doc["filename"],
                None,
                "REPORTED_IN",
                chunk_id,
                doc_id,
                page_no,
                sheet_no,
                conf,
            )
            emit("MENTIONS")
            emit("REPORTED_IN")
            for mine in by_kind.get(MINE, []):
                _insert(
                    EVENT,
                    kinds[evt][0],
                    evt,
                    MINE,
                    kinds[mine][0],
                    mine,
                    "OCCURRED_AT",
                    chunk_id,
                    doc_id,
                    page_no,
                    sheet_no,
                    conf,
                )
                emit("OCCURRED_AT")
            for loc in by_kind.get(LOCATION, []):
                _insert(
                    EVENT,
                    kinds[evt][0],
                    evt,
                    LOCATION,
                    kinds[loc][0],
                    loc,
                    "OCCURRED_AT",
                    chunk_id,
                    doc_id,
                    page_no,
                    sheet_no,
                    conf,
                )
                emit("OCCURRED_AT")
            for org in by_kind.get(ORGANIZATION, []):
                _insert(
                    EVENT,
                    kinds[evt][0],
                    evt,
                    ORGANIZATION,
                    kinds[org][0],
                    org,
                    "INVOLVES",
                    chunk_id,
                    doc_id,
                    page_no,
                    sheet_no,
                    conf,
                )
                emit("INVOLVES")
    return {"edges": sum(counts.values()), "by_relation": counts}


def rebuild_all() -> dict:
    """Backfill edges for every completed document (reindex path)."""
    import logging

    logger = logging.getLogger("cmpdi.knowledge")
    total = 0
    docs = 0
    for row in db.q("SELECT id FROM documents WHERE status='completed'"):
        try:
            total += extract_for_doc(row["id"])["edges"]
            docs += 1
        except Exception:
            logger.warning("KG rebuild failed", extra={"doc_id": row["id"]})
            continue
    return {"documents": docs, "edges": total}
