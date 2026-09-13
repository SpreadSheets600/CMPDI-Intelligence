"""Knowledge graph builder. Nodes are documents, keyword tags and resolved
entities; edges connect documents to their tags and entities. The frontend
renders it as a force-directed tree."""

from backend.db import database as db


def build_graph(subsidiary: str | None = None, max_docs: int = 60,
                max_tags: int = 25) -> dict:
    where, params = ["is_current_version=1"], []
    if subsidiary:
        where.append("subsidiary=?")
        params.append(subsidiary)
    docs = db.q(
        f"SELECT id, filename, doc_type, subsidiary FROM documents "
        f"WHERE {' AND '.join(where)} ORDER BY upload_ts DESC LIMIT ?",
        (*params, max_docs))
    doc_ids = [d["id"] for d in docs]
    if not doc_ids:
        return {"nodes": [], "edges": [], "tags": []}

    marks = ",".join("?" * len(doc_ids))
    kw_rows = db.q(
        f"""SELECT doc_id, keyword, COUNT(*) OVER (PARTITION BY keyword) n
            FROM doc_keywords WHERE doc_id IN ({marks})""", doc_ids)
    tag_counts: dict[str, int] = {}
    doc_tags: dict[str, list[str]] = {}
    for r in kw_rows:
        tag_counts[r["keyword"]] = max(tag_counts.get(r["keyword"], 0), r["n"])
        doc_tags.setdefault(r["doc_id"], []).append(r["keyword"])
    top_tags = sorted(tag_counts, key=lambda k: -tag_counts[k])[:max_tags]

    ent_rows = db.q(
        f"""SELECT DISTINCT f.entity_id, e.canonical_name, f.chunk_id
            FROM facts f JOIN entities e ON e.id = f.entity_id
            JOIN chunks c ON c.id = f.chunk_id
            WHERE c.doc_id IN ({marks})""", doc_ids)
    chunk_doc = {r["id"]: r["doc_id"] for r in db.q(
        f"SELECT id, doc_id FROM chunks WHERE doc_id IN ({marks})", doc_ids)}

    nodes, edges = [], []
    for d in docs:
        nodes.append({"id": f"doc:{d['id']}", "label": d["filename"],
                      "type": "document", "group": d["subsidiary"] or "general",
                      "ref": d["id"]})
    for kw in top_tags:
        nodes.append({"id": f"kw:{kw}", "label": kw, "type": "tag",
                      "group": "tag", "count": tag_counts[kw]})
    seen_entities = set()
    seen_edges = set()
    for r in ent_rows:
        doc_id = chunk_doc.get(r["chunk_id"])
        if not doc_id:
            continue
        ent_key = f"ent:{r['entity_id']}"
        if ent_key not in seen_entities:
            seen_entities.add(ent_key)
            nodes.append({"id": ent_key, "label": r["canonical_name"],
                          "type": "entity", "group": "entity"})
        edge = (f"doc:{doc_id}", ent_key)
        if edge not in seen_edges:
            seen_edges.add(edge)
            edges.append({"source": edge[0], "target": edge[1]})
    for d in docs:
        for kw in doc_tags.get(d["id"], []):
            if kw in top_tags:
                edge = (f"doc:{d['id']}", f"kw:{kw}")
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    edges.append({"source": edge[0], "target": edge[1]})

    nodes = [n for n in nodes if n["type"] != "tag"
             or any(e["target"] == n["id"] for e in edges)]
    tags = [{"keyword": k, "count": tag_counts[k]} for k in top_tags]
    return {"nodes": nodes, "edges": edges, "tags": tags}
