"""P1 knowledge graph: typed relationships between organizations, mines,
locations, geology, documents, metrics and events.

Persisted evidence edges (``kg_edges``, built by ``relations`` at ingestion)
carry OPERATES / LOCATED_IN / BASED_IN / HAS_GEOLOGY / MENTIONS /
OCCURRED_AT / INVOLVES / REPORTED_IN with chunk -> page -> document
provenance. Fact-derived edges (HAS_METRIC / REPORTS_METRIC / MENTIONS for
organizations and mines) and version SUPERSEDES links are built at query
time so this layer never duplicates the fact index. Reference context
(``entity_reference``) never enters the graph — it is context, not evidence.
"""

from __future__ import annotations

from itertools import pairwise

from backend.core.knowledge import relations
from backend.db import database as db

LEGEND = [
    {"kind": "document", "label": "Document"},
    {"kind": "organization", "label": "Organization"},
    {"kind": "mine", "label": "Mine"},
    {"kind": "location", "label": "Location"},
    {"kind": "geology", "label": "Geology"},
    {"kind": "metric", "label": "Metric"},
    {"kind": "event", "label": "Event"},
    {"kind": "tag", "label": "Tag"},
]

_MAX_ENTITIES = 80
_MAX_METRICS = 20
_MAX_EDGES = 800


def _doc_nodes(subsidiary: str | None, max_docs: int) -> list[dict]:
    where, params = ["is_current_version=1"], []
    if subsidiary:
        where.append("subsidiary=?")
        params.append(subsidiary)
    return [
        dict(d)
        for d in db.q(
            "SELECT id, filename, display_name, doc_type, subsidiary"
            " FROM documents"
            f" WHERE {' AND '.join(where)} ORDER BY upload_ts DESC LIMIT ?",
            (*params, max_docs),
        )
    ]


def build_graph(
    subsidiary: str | None = None,
    max_docs: int = 60,
    max_tags: int = 25,
    kinds: list[str] | None = None,
    query: str | None = None,
) -> dict:
    """Typed graph slice: documents, tags, entities by kind, metric nodes and
    the relationships between them. ``kinds`` optionally limits node kinds;
    ``query`` optionally substring-filters non-document labels."""
    want = set(kinds) if kinds else set()
    docs = _doc_nodes(subsidiary, max_docs)
    doc_ids = [d["id"] for d in docs]
    if not doc_ids:
        return {"nodes": [], "edges": [], "tags": [], "legend": LEGEND, "counts": {}}
    marks = ",".join("?" * len(doc_ids))
    doc_name = {d["id"]: d["display_name"] or d["filename"] for d in docs}

    q = (query or "").strip().lower()

    def keep(label: str) -> bool:
        return not q or q in (label or "").lower()

    def want_kind(kind: str) -> bool:
        return not want or kind in want or kind == "document"

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    seen_edges: set[tuple] = set()

    def add_node(nid: str, label: str, ntype: str, group: str, **extra):
        if nid not in nodes and keep(label):
            nodes[nid] = {
                "id": nid,
                "label": label,
                "type": ntype,
                "group": group,
                **extra,
            }

    def add_edge(source: str, target: str, relation: str, **extra):
        if source not in nodes or target not in nodes:
            return
        key = (source, target, relation)
        if key in seen_edges:
            return
        if len(edges) >= _MAX_EDGES:
            return
        seen_edges.add(key)
        edges.append(
            {"source": source, "target": target, "relation": relation, **extra}
        )

    for d in docs:
        add_node(
            f"doc:{d['id']}",
            doc_name[d["id"]],
            "document",
            d["subsidiary"] or "general",
            ref=d["id"],
            doc_type=d["doc_type"],
        )

    # Tags (unchanged P0 behavior, now labelled TAGGED)
    kw_rows = db.q(
        f"""SELECT doc_id, keyword, COUNT(*) OVER (PARTITION BY keyword) n
            FROM doc_keywords WHERE doc_id IN ({marks})""",
        doc_ids,
    )
    tag_counts: dict[str, int] = {}
    doc_tags: dict[str, list[str]] = {}
    for r in kw_rows:
        tag_counts[r["keyword"]] = max(tag_counts.get(r["keyword"], 0), r["n"])
        doc_tags.setdefault(r["doc_id"], []).append(r["keyword"])
    top_tags = sorted(tag_counts, key=lambda k: -tag_counts[k])[:max_tags]
    if want_kind("tag"):
        for kw in top_tags:
            add_node(f"kw:{kw}", kw, "tag", "tag", count=tag_counts[kw])
        for d in docs:
            for kw in doc_tags.get(d["id"], []):
                if kw in top_tags:
                    add_edge(f"doc:{d['id']}", f"kw:{kw}", "TAGGED")

    # Entity nodes mapped to graph kinds
    ent_rows = db.q(
        f"""SELECT DISTINCT f.entity_id, e.canonical_name, e.type
            FROM facts f JOIN entities e ON e.id = f.entity_id
            JOIN chunks c ON c.id = f.chunk_id
            WHERE c.doc_id IN ({marks})""",
        doc_ids,
    )
    kg_entity_ids = {
        r["src_entity_id"]
        for r in db.q(
            f"SELECT DISTINCT src_entity_id FROM kg_edges WHERE doc_id IN ({marks})"
            f" AND src_entity_id IS NOT NULL",
            doc_ids,
        )
    } | {
        r["dst_entity_id"]
        for r in db.q(
            f"SELECT DISTINCT dst_entity_id FROM kg_edges WHERE doc_id IN ({marks})"
            f" AND dst_entity_id IS NOT NULL",
            doc_ids,
        )
    }
    if kg_entity_ids:
        marks_e = ",".join("?" * len(kg_entity_ids))
        for r in db.q(
            f"SELECT id, canonical_name, type FROM entities WHERE id IN ({marks_e})",
            list(kg_entity_ids),
        ):
            ent_rows.append(
                {
                    "entity_id": r["id"],
                    "canonical_name": r["canonical_name"],
                    "type": r["type"],
                }
            )
    seen_ent: dict[int, str] = {}
    for r in ent_rows:
        if r["entity_id"] in seen_ent or len(seen_ent) >= _MAX_ENTITIES:
            continue
        kind = relations.kind_of(r["type"]) or "organization"
        if not want_kind(kind) or not keep(r["canonical_name"]):
            continue
        nid = f"ent:{r['entity_id']}"
        seen_ent[r["entity_id"]] = nid
        add_node(
            nid,
            r["canonical_name"],
            kind,
            kind,
            ref=r["canonical_name"],
            entity_id=r["entity_id"],
            entity_type=r["type"],
        )

    # Metric nodes from the fact index (named metrics only, like Insights)
    metric_rows = db.q(
        f"""SELECT DISTINCT f.attribute FROM facts f
            JOIN chunks c ON c.id = f.chunk_id
            WHERE c.doc_id IN ({marks}) AND f.attribute != 'quantity'""",
        doc_ids,
    )
    metrics = sorted({r["attribute"] for r in metric_rows})[:_MAX_METRICS]
    if want_kind("metric"):
        for m in metrics:
            if keep(m):
                add_node(f"metric:{m}", m.replace("_", " "), "metric", "metric", ref=m)

    # Event nodes with no facts yet still appear via persisted edges
    if want_kind("event"):
        for r in db.q(
            f"""SELECT DISTINCT dst_entity_id, dst_label FROM kg_edges
                    WHERE doc_id IN ({marks}) AND dst_kind='event'
                    AND dst_entity_id IS NOT NULL""",
            doc_ids,
        ):
            if r["dst_entity_id"] not in seen_ent and keep(r["dst_label"]):
                nid = f"ent:{r['dst_entity_id']}"
                seen_ent[r["dst_entity_id"]] = nid
                add_node(
                    nid,
                    r["dst_label"],
                    "event",
                    "event",
                    ref=r["dst_label"],
                    entity_id=r["dst_entity_id"],
                )

    # Persisted typed edges, aggregated per (source, target, relation)
    for r in db.q(
        f"""SELECT src_kind, src_label, src_entity_id, dst_kind, dst_label,
                       dst_entity_id, relation, COUNT(*) n,
                       MIN(chunk_id) chunk_id, MIN(doc_id) doc_id, MIN(page_no) page_no
                FROM kg_edges WHERE doc_id IN ({marks})
                GROUP BY src_kind, src_label, src_entity_id,
                         dst_kind, dst_label, dst_entity_id, relation
                ORDER BY n DESC LIMIT {_MAX_EDGES}""",
        doc_ids,
    ):
        src = (
            f"ent:{r['src_entity_id']}"
            if r["src_entity_id"]
            else f"doc:{r['doc_id']}"
            if r["src_kind"] == "document"
            else None
        )
        dst = (
            f"ent:{r['dst_entity_id']}"
            if r["dst_entity_id"]
            else f"doc:{r['doc_id']}"
            if r["dst_kind"] == "document"
            else None
        )
        if not src or not dst:
            continue
        add_edge(
            src,
            dst,
            r["relation"],
            count=r["n"],
            doc_id=r["doc_id"],
            chunk_id=r["chunk_id"],
            page_no=r["page_no"],
        )

    # Derived MENTIONS for organizations and mines (fact-backed; locations,
    # geology and events already persist MENTIONS above so they are skipped
    # here to avoid double edges)
    chunk_doc = {
        r["id"]: r["doc_id"]
        for r in db.q(
            f"SELECT id, doc_id FROM chunks WHERE doc_id IN ({marks})", doc_ids
        )
    }
    for r in db.q(
        f"""SELECT DISTINCT f.entity_id, e.canonical_name, e.type, f.chunk_id
                FROM facts f JOIN entities e ON e.id = f.entity_id
                JOIN chunks c ON c.id = f.chunk_id
                WHERE c.doc_id IN ({marks})""",
        doc_ids,
    ):
        kind = relations.kind_of(r["type"])
        if kind not in ("organization", "mine"):
            continue
        doc_id = chunk_doc.get(r["chunk_id"])
        nid = seen_ent.get(r["entity_id"])
        if not doc_id or not nid:
            continue
        add_edge(
            f"doc:{doc_id}", nid, "MENTIONS", doc_id=doc_id, chunk_id=r["chunk_id"]
        )

    # Derived metric edges from the fact index
    fact_metric = db.q(
        f"""SELECT f.entity_id, f.attribute, f.chunk_id, c.doc_id,
                   c.page_no, c.sheet_no
            FROM facts f JOIN chunks c ON c.id = f.chunk_id
            WHERE c.doc_id IN ({marks}) AND f.attribute != 'quantity'
              AND f.entity_id IS NOT NULL""",
        doc_ids,
    )
    for r in fact_metric:
        nid = seen_ent.get(r["entity_id"])
        mid = f"metric:{r['attribute']}"
        if nid and mid in nodes:
            add_edge(
                nid,
                mid,
                "HAS_METRIC",
                doc_id=r["doc_id"],
                chunk_id=r["chunk_id"],
                page_no=r["page_no"],
                sheet_no=r["sheet_no"],
            )
            add_edge(
                f"doc:{r['doc_id']}",
                mid,
                "REPORTS_METRIC",
                doc_id=r["doc_id"],
                chunk_id=r["chunk_id"],
            )

    # Version SUPERSEDES links inside this slice
    groups: dict[str, list[dict]] = {}
    for d in db.q(
        f"""SELECT id, version_group_id, doc_date_norm, upload_ts
                FROM documents WHERE id IN ({marks})
                AND version_group_id IS NOT NULL""",
        doc_ids,
    ):
        groups.setdefault(d["version_group_id"], []).append(d)
    for members in groups.values():
        ordered = sorted(
            members, key=lambda r: (r["doc_date_norm"] or "", r["upload_ts"])
        )
        for older, newer in pairwise(ordered):
            add_edge(f"doc:{newer['id']}", f"doc:{older['id']}", "SUPERSEDES")

    node_list = list(nodes.values())
    # Drop isolated tag nodes (P0 behavior kept)
    node_list = [
        n
        for n in node_list
        if n["type"] != "tag" or any(e["target"] == n["id"] for e in edges)
    ]
    tags = [{"keyword": k, "count": tag_counts[k]} for k in top_tags]
    counts = {}
    for n in node_list:
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    counts["edges"] = len(edges)
    return {
        "nodes": node_list,
        "edges": edges,
        "tags": tags,
        "legend": LEGEND,
        "counts": counts,
    }


def neighbourhood(node_id: str, limit: int = 60) -> dict | None:
    """One-hop neighbourhood of a node with evidence receipts per edge."""
    kind, _, raw = node_id.partition(":")
    if kind == "doc":
        doc = db.q1("SELECT * FROM documents WHERE id=?", (raw,))
        if not doc:
            return None
        node = {
            "id": node_id,
            "label": doc["display_name"] or doc["filename"],
            "type": "document",
            "ref": doc["id"],
        }
        edge_rows = db.q(
            """SELECT src_kind, src_label, src_entity_id, dst_kind, dst_label,
                      dst_entity_id, relation, chunk_id, doc_id, page_no, sheet_no
               FROM kg_edges WHERE doc_id=? LIMIT ?""",
            (raw, limit),
        )
        neighbours: dict[str, dict] = {}
        out_edges: list[dict] = []
        for r in edge_rows:
            other_kind = r["dst_kind"] if r["src_kind"] == "document" else r["src_kind"]
            other_label = (
                r["dst_label"] if r["src_kind"] == "document" else r["src_label"]
            )
            other_eid = (
                r["dst_entity_id"]
                if r["src_kind"] == "document"
                else r["src_entity_id"]
            )
            oid = f"ent:{other_eid}" if other_eid else f"{other_kind}:{other_label}"
            neighbours.setdefault(
                oid, {"id": oid, "label": other_label, "type": other_kind}
            )
            out_edges.append(_edge_with_receipt(node_id, oid, r))
        fact_rows = db.q(
            """SELECT e.canonical_name, e.id, f.attribute, f.chunk_id,
                      c.page_no, c.sheet_no FROM facts f
               JOIN entities e ON e.id = f.entity_id
               JOIN chunks c ON c.id = f.chunk_id
               WHERE c.doc_id=? AND f.attribute != 'quantity' LIMIT ?""",
            (raw, limit),
        )
        for r in fact_rows:
            oid = f"ent:{r['id']}"
            neighbours.setdefault(
                oid, {"id": oid, "label": r["canonical_name"], "type": "entity"}
            )
            out_edges.append(
                {
                    "source": node_id,
                    "target": oid,
                    "relation": "MENTIONS",
                    "evidence": _receipt(
                        raw, r["chunk_id"], r["page_no"], r["sheet_no"]
                    ),
                }
            )
            mid = f"metric:{r['attribute']}"
            neighbours.setdefault(
                mid,
                {
                    "id": mid,
                    "label": r["attribute"].replace("_", " "),
                    "type": "metric",
                },
            )
            out_edges.append(
                {
                    "source": node_id,
                    "target": mid,
                    "relation": "REPORTS_METRIC",
                    "evidence": _receipt(
                        raw, r["chunk_id"], r["page_no"], r["sheet_no"]
                    ),
                }
            )
        return {
            "node": node,
            "neighbours": list(neighbours.values()),
            "edges": out_edges[:limit],
        }
    if kind == "ent":
        try:
            eid = int(raw)
        except ValueError:
            return None
        ent = db.q1("SELECT * FROM entities WHERE id=?", (eid,))
        if not ent:
            return None
        ekind = relations.kind_of(ent["type"]) or "entity"
        node = {
            "id": node_id,
            "label": ent["canonical_name"],
            "type": ekind,
            "ref": ent["canonical_name"],
            "entity_id": eid,
        }
        edge_rows = db.q(
            """SELECT src_kind, src_label, src_entity_id, dst_kind, dst_label,
                      dst_entity_id, relation, chunk_id, doc_id, page_no, sheet_no
               FROM kg_edges WHERE src_entity_id=? OR dst_entity_id=?
               LIMIT ?""",
            (eid, eid, limit),
        )
        neighbours: dict[str, dict] = {}
        out_edges: list[dict] = []
        for r in edge_rows:
            if r["src_entity_id"] == eid:
                oid = (
                    f"ent:{r['dst_entity_id']}"
                    if r["dst_entity_id"]
                    else f"doc:{r['doc_id']}"
                )
                olabel = r["dst_label"]
                okind = r["dst_kind"]
                out_edges.append(_edge_with_receipt(node_id, oid, r))
            else:
                oid = (
                    f"ent:{r['src_entity_id']}"
                    if r["src_entity_id"]
                    else f"doc:{r['doc_id']}"
                )
                olabel = r["src_label"]
                okind = r["src_kind"]
                out_edges.append(_edge_with_receipt(oid, node_id, r))
            neighbours.setdefault(oid, {"id": oid, "label": olabel, "type": okind})
        for r in db.q(
            """SELECT f.attribute, c.doc_id, c.page_no, c.sheet_no, f.chunk_id,
                          d.filename, d.display_name FROM facts f
                   JOIN chunks c ON c.id = f.chunk_id
                   JOIN documents d ON d.id = c.doc_id
                   WHERE f.entity_id=? AND f.attribute != 'quantity' LIMIT ?""",
            (eid, limit),
        ):
            mid = f"metric:{r['attribute']}"
            neighbours.setdefault(
                mid,
                {
                    "id": mid,
                    "label": r["attribute"].replace("_", " "),
                    "type": "metric",
                },
            )
            out_edges.append(
                {
                    "source": node_id,
                    "target": mid,
                    "relation": "HAS_METRIC",
                    "evidence": _receipt(
                        r["doc_id"], r["chunk_id"], r["page_no"], r["sheet_no"]
                    ),
                }
            )
            did = f"doc:{r['doc_id']}"
            neighbours.setdefault(
                did,
                {
                    "id": did,
                    "label": r["display_name"] or r["filename"],
                    "type": "document",
                },
            )
            out_edges.append(
                {
                    "source": did,
                    "target": node_id,
                    "relation": "MENTIONS",
                    "evidence": _receipt(
                        r["doc_id"], r["chunk_id"], r["page_no"], r["sheet_no"]
                    ),
                }
            )
        return {
            "node": node,
            "neighbours": list(neighbours.values()),
            "edges": out_edges[:limit],
        }
    if kind == "metric":
        rows = db.q(
            """SELECT e.canonical_name, e.id, c.doc_id, d.filename, d.display_name,
                      c.page_no, f.chunk_id FROM facts f
               JOIN entities e ON e.id = f.entity_id
               JOIN chunks c ON c.id = f.chunk_id
               JOIN documents d ON d.id = c.doc_id
               WHERE f.attribute=? LIMIT ?""",
            (raw, limit),
        )
        if not rows:
            return None
        neighbours: dict[str, dict] = {}
        out_edges: list[dict] = []
        for r in rows:
            oid = f"ent:{r['id']}"
            neighbours.setdefault(
                oid, {"id": oid, "label": r["canonical_name"], "type": "entity"}
            )
            out_edges.append(
                {
                    "source": oid,
                    "target": node_id,
                    "relation": "HAS_METRIC",
                    "evidence": _receipt(
                        r["doc_id"], r["chunk_id"], r["page_no"], None
                    ),
                }
            )
        return {
            "node": {
                "id": node_id,
                "label": raw.replace("_", " "),
                "type": "metric",
                "ref": raw,
            },
            "neighbours": list(neighbours.values()),
            "edges": out_edges[:limit],
        }
    return None


def _receipt(
    doc_id: str | None, chunk_id: int | None, page_no: int | None, sheet_no: int | None
) -> dict:
    doc = (
        db.q1("SELECT filename, display_name FROM documents WHERE id=?", (doc_id,))
        if doc_id
        else None
    )
    snippet = ""
    if chunk_id:
        row = db.q1("SELECT text FROM chunks WHERE id=?", (chunk_id,))
        snippet = row["text"][:280] if row and row["text"] else ""
    return {
        "doc_id": doc_id,
        "filename": (doc["display_name"] or doc["filename"]) if doc else None,
        "chunk_id": chunk_id,
        "page_no": page_no,
        "sheet_no": sheet_no,
        "snippet": snippet,
    }


def _edge_with_receipt(source: str, target: str, row: dict) -> dict:
    return {
        "source": source,
        "target": target,
        "relation": row["relation"],
        "evidence": _receipt(
            row["doc_id"], row["chunk_id"], row["page_no"], row["sheet_no"]
        ),
    }
