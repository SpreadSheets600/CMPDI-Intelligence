"""Hybrid retrieval: SQLite FTS5 BM25 (lexical) + numpy cosine (semantic) +
Reciprocal Rank Fusion. Never a source of truth — results always carry the
full provenance chain (chunk -> element -> page -> document -> file)."""

import json
import re

import numpy as np

from . import config, db
from .pipeline.embedder import embed_texts, vector_matrix

_TOKEN_RE = re.compile(r"[\w']+")


def _fts_query(query: str) -> str:
    tokens = _TOKEN_RE.findall(query)
    if not tokens:
        return '""'
    return " OR ".join(f'"{t}"' for t in tokens)


def _filter_sql(filters: dict | None) -> tuple[str, list]:
    where, params = ["1=1"], []
    if not filters:
        return " ".join(where), params
    if filters.get("subsidiary"):
        where.append("d.subsidiary = ?")
        params.append(filters["subsidiary"])
    if filters.get("doc_type"):
        where.append("d.doc_type = ?")
        params.append(filters["doc_type"])
    if filters.get("doc_ids"):
        marks = ",".join("?" * len(filters["doc_ids"]))
        where.append(f"d.id IN ({marks})")
        params.extend(filters["doc_ids"])
    if filters.get("content_type"):
        marks = ",".join("?" * len(filters["content_type"]))
        where.append(f"c.content_type IN ({marks})")
        params.extend(filters["content_type"])
    if filters.get("current_only", True):
        where.append("d.is_current_version = 1")
    return " AND ".join(where), params


def _evidence(row, bm25_score=None, vec_score=None, rrf=None) -> dict:
    return {
        "chunk_id": row["id"], "doc_id": row["doc_id"], "filename": row["filename"],
        "doc_title": row["filename"], "doc_type": row["doc_type"],
        "subsidiary": row["subsidiary"], "content_type": row["content_type"],
        "section_path": row["section_path"], "page_no": row["page_no"],
        "sheet_no": row["sheet_no"], "text": row["text"],
        "element_ids": json.loads(row["element_ids_json"] or "[]"),
        "bm25": bm25_score, "vec": vec_score, "rrf": rrf,
    }


_BASE_SQL = """
    SELECT c.id, c.doc_id, d.filename, d.doc_type, d.subsidiary, d.sha256,
           c.content_type, c.section_path, c.page_no, c.sheet_no, c.text, c.element_ids_json
    FROM chunks c JOIN documents d ON d.id = c.doc_id
"""


def _doc_title_subquery():
    # titles live in documents.meta only loosely; filename is the honest label
    return None


def bm25_search(query: str, k: int | None = None, filters: dict | None = None) -> list[dict]:
    k = k or config.RETRIEVAL_K
    where, params = _filter_sql(filters)
    rows = db.q(
        f"""SELECT sub.*, bm25(chunks_fts) AS score
            FROM chunks_fts
            JOIN (
                {_BASE_SQL} WHERE {where}
            ) sub ON sub.id = chunks_fts.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY score LIMIT ?""",
        (*params, _fts_query(query), k))
    # bm25(): lower is better
    return [_evidence(r, bm25_score=-r["score"]) for r in rows]


def vector_search(query: str, k: int | None = None, filters: dict | None = None) -> list[dict]:
    k = k or config.RETRIEVAL_K
    where, params = _filter_sql(filters)
    allowed = {r["id"] for r in db.q(f"{_BASE_SQL} WHERE {where}", params)}
    if not allowed:
        return []
    qvec = embed_texts([query], is_query=True)[0]
    ids, matrix = vector_matrix()
    mask = np.isin(ids, list(allowed))
    if not mask.any():
        return []
    sub_ids, sub_matrix = ids[mask], matrix[mask]
    sims = sub_matrix @ qvec
    order = np.argsort(-sims)[:k]
    id_set = {int(sub_ids[i]): float(sims[i]) for i in order}
    marks = ",".join("?" * len(id_set))
    rows = db.q(f"{_BASE_SQL} WHERE c.id IN ({marks})", tuple(id_set))
    out = []
    for r in rows:
        ev = _evidence(r, vec_score=id_set[r["id"]])
        out.append(ev)
    out.sort(key=lambda e: -e["vec"])
    return out


def hybrid_search(query: str, k: int | None = None, filters: dict | None = None) -> list[dict]:
    """Reciprocal Rank Fusion over BM25 + vector rankings."""
    k = k or config.RETRIEVAL_K
    bm = bm25_search(query, k=k * 2, filters=filters)
    vs = vector_search(query, k=k * 2, filters=filters)
    scores: dict[int, float] = {}
    ranks: dict[int, dict] = {}
    for rank, ev in enumerate(bm):
        scores[ev["chunk_id"]] = scores.get(ev["chunk_id"], 0) + 1 / (config.RRF_K + rank + 1)
        ranks.setdefault(ev["chunk_id"], {})["bm25_rank"] = rank + 1
    for rank, ev in enumerate(vs):
        scores[ev["chunk_id"]] = scores.get(ev["chunk_id"], 0) + 1 / (config.RRF_K + rank + 1)
        ranks.setdefault(ev["chunk_id"], {})["vec_rank"] = rank + 1
    by_id = {ev["chunk_id"]: ev for ev in bm}
    for ev in vs:
        by_id.setdefault(ev["chunk_id"], ev)
    for cid, s in scores.items():
        by_id[cid]["rrf"] = s
    fused = sorted(by_id.values(), key=lambda e: -e["rrf"])[:k]
    return fused
