"""Hybrid retrieval: SQLite FTS5 BM25 (lexical) + FAISS cosine (semantic),
fused with weighted scoring. Weights follow contribution to relevance:
vector 0.45, BM25 0.25, title 0.15, keyword/tag 0.10, recency 0.05. Results
are not the source of truth; each one carries its provenance chain (chunk,
element, page, document, file)."""

import json
import math
import re
from datetime import date

from backend.core import appsettings, config
from backend.core.llm import get_backend
from backend.core.pipeline import vector_store
from backend.core.pipeline.embedder import embed_texts
from backend.db import database as db

_TOKEN_RE = re.compile(r"[\w']+")

# fusion weights
W_VECTOR = 0.45
W_BM25 = 0.25
W_TITLE = 0.15
W_KEYWORD = 0.10
W_RECENCY = 0.05


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _fts_query(query: str, extra_terms: list[str] | None = None) -> str:
    tokens = _tokens(query)
    for phrase in extra_terms or []:
        tokens.extend(_tokens(phrase))
    tokens = list(dict.fromkeys(tokens))
    if not tokens:
        return '""'
    return " OR ".join(f'"{t}"' for t in tokens)


def expand_query(query: str) -> list[str]:
    """Alternative phrasings via the LLM backend; empty when unavailable
    (BM25 and vector search still run on the original query)."""
    if len(query.split()) > 12:
        return []
    backend = get_backend()
    raw = backend.generate(
        "You expand search queries. Reply with the comma-separated list only.",
        f"Give up to 3 alternative phrasings for this mining/geological search "
        f"query, each 1 to 4 words, comma-separated. No numbering.\n\nQuery: {query}",
    )
    if not raw:
        return []
    phrases = [p.strip().lower() for p in re.split(r"[,\n]", raw)]
    return [p for p in phrases if 1 <= len(p.split()) <= 4 and p != query.lower()][:3]


def _filter_sql(filters: dict | None) -> tuple[str, list]:
    where, params = ["1=1"], []
    if not filters:
        return " AND ".join(where), params
    if filters.get("subsidiary"):
        where.append("d.subsidiary = ?")
        params.append(filters["subsidiary"])
    if filters.get("doc_type"):
        where.append("d.doc_type = ?")
        params.append(filters["doc_type"])
    if filters.get("doc_types"):
        marks = ",".join("?" * filters["doc_types"])
        where.append(f"d.doc_type IN ({marks})")
        params.extend(filters["doc_types"])
    if filters.get("doc_ids"):
        marks = ",".join("?" * len(filters["doc_ids"]))
        where.append(f"d.id IN ({marks})")
        params.extend(filters["doc_ids"])
    if filters.get("content_type"):
        marks = ",".join("?" * len(filters["content_type"]))
        where.append(f"c.content_type IN ({marks})")
        params.extend(filters["content_type"])
    if filters.get("tag"):
        where.append("d.id IN (SELECT doc_id FROM doc_keywords WHERE keyword = ?)")
        params.append(filters["tag"])
    if filters.get("doc_from"):
        where.append("d.doc_date_norm IS NOT NULL AND d.doc_date_norm >= ?")
        params.append(filters["doc_from"])
    if filters.get("doc_to"):
        where.append("d.doc_date_norm IS NOT NULL AND d.doc_date_norm <= ?")
        params.append(filters["doc_to"])
    if filters.get("current_only", True):
        where.append("d.is_current_version = 1")
    return " AND ".join(where), params


def _evidence(row) -> dict:
    return {
        "chunk_id": row["id"], "doc_id": row["doc_id"], "filename": row["filename"],
        "doc_title": row["filename"], "doc_type": row["doc_type"],
        "subsidiary": row["subsidiary"], "content_type": row["content_type"],
        "section_path": row["section_path"], "page_no": row["page_no"],
        "sheet_no": row["sheet_no"], "text": row["text"],
        "element_ids": json.loads(row["element_ids_json"] or "[]"),
        "bm25": None, "vec": None, "score": None,
        "title_hit": None, "keyword_hit": None, "recency": None, "tags": [],
    }


_BASE_SQL = """
    SELECT c.id, c.doc_id, d.filename, d.doc_type, d.subsidiary, d.sha256,
           c.content_type, c.section_path, c.page_no, c.sheet_no, c.text, c.element_ids_json
    FROM chunks c JOIN documents d ON d.id = c.doc_id
"""


def bm25_search(query: str, k: int | None = None, filters: dict | None = None,
                extra_terms: list[str] | None = None) -> list[dict]:
    k = k or appsettings.get("retrieval_k")
    where, params = _filter_sql(filters)
    rows = db.q(
        f"""SELECT sub.*, bm25(chunks_fts) AS score
            FROM chunks_fts
            JOIN (
                {_BASE_SQL} WHERE {where}
            ) sub ON sub.id = chunks_fts.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY score LIMIT ?""",
        (*params, _fts_query(query, extra_terms), k))
    return [_evidence(r) for r in rows]


def vector_search(query: str, k: int | None = None, filters: dict | None = None) -> list[dict]:
    k = k or appsettings.get("retrieval_k")
    where, params = _filter_sql(filters)
    allowed = {r["id"] for r in db.q(f"{_BASE_SQL} WHERE {where}", params)}
    if not allowed:
        return []
    qvec = embed_texts([query], is_query=True)[0]
    hits = vector_store.search(qvec, k=k * 2, allowed_ids=allowed)
    if not hits:
        return []
    id_score = dict(hits)
    marks = ",".join("?" * len(id_score))
    rows = db.q(f"{_BASE_SQL} WHERE c.id IN ({marks})", tuple(id_score))
    out = []
    for r in rows:
        ev = _evidence(r)
        ev["vec"] = id_score[r["id"]]
        out.append(ev)
    out.sort(key=lambda e: -e["vec"])
    return out[:k]


def doc_keywords_map(doc_ids: list[str]) -> dict[str, list[str]]:
    if not doc_ids:
        return {}
    marks = ",".join("?" * len(doc_ids))
    mapping: dict[str, list[str]] = {}
    for r in db.q(f"SELECT doc_id, keyword FROM doc_keywords WHERE doc_id IN ({marks})", doc_ids):
        mapping.setdefault(r["doc_id"], []).append(r["keyword"])
    return mapping


def top_tags(limit: int = 30, subsidiary: str | None = None) -> list[dict]:
    if subsidiary:
        rows = db.q(
            """SELECT dk.keyword, COUNT(*) n FROM doc_keywords dk
               JOIN documents d ON d.id = dk.doc_id AND d.is_current_version = 1
               WHERE d.subsidiary = ?
               GROUP BY dk.keyword ORDER BY n DESC, dk.keyword LIMIT ?""", (subsidiary, limit))
    else:
        rows = db.q(
            """SELECT dk.keyword, COUNT(*) n FROM doc_keywords dk
               JOIN documents d ON d.id = dk.doc_id AND d.is_current_version = 1
               GROUP BY dk.keyword ORDER BY n DESC, dk.keyword LIMIT ?""", (limit,))
    return [dict(r) for r in rows]


def _recency(doc_date_norm: str | None, upload_ts: str) -> float:
    ref = doc_date_norm or (upload_ts[:10] if upload_ts else None)
    if not ref:
        return 0.3
    try:
        days = max(0, (date.today() - date.fromisoformat(ref[:10])).days)
    except ValueError:
        return 0.3
    return math.exp(-days / 365)


def hybrid_search(query: str, k: int | None = None, filters: dict | None = None) -> list[dict]:
    """Weighted fusion over BM25, vector and title/keyword/recency signals."""
    k = k or appsettings.get("retrieval_k")
    expansions = expand_query(query)
    bm = bm25_search(query, k=k * 4, filters=filters, extra_terms=expansions)
    vs = vector_search(query, k=k * 3, filters=filters)

    by_id: dict[int, dict] = {}
    for ev in bm:
        by_id[ev["chunk_id"]] = ev
    for ev in vs:
        if ev["chunk_id"] in by_id:
            by_id[ev["chunk_id"]]["vec"] = ev["vec"]
        else:
            by_id[ev["chunk_id"]] = ev

    if not by_id:
        return []

    bm_max = max((e["bm25"] or 0) for e in by_id.values()) or 1.0
    q_terms = set(_tokens(query)) | {t for p in expansions for t in _tokens(p)}
    kw_map = doc_keywords_map(list({e["doc_id"] for e in by_id.values()}))
    doc_meta = {r["id"]: dict(r) for r in db.q(
        "SELECT id, filename, doc_date_norm, upload_ts FROM documents")}

    for ev in by_id.values():
        d = doc_meta.get(ev["doc_id"], {})
        title_terms = set(_tokens(d.get("filename", "")))
        ev["bm25"] = ev["bm25"] or 0.0
        bm25_norm = ev["bm25"] / bm_max
        ev["title_hit"] = (len(q_terms & title_terms) / len(q_terms)) if q_terms else 0.0
        kw_terms = set()
        for kw in kw_map.get(ev["doc_id"], []):
            kw_terms.update(_tokens(kw))
        ev["keyword_hit"] = (len(q_terms & kw_terms) / len(q_terms)) if q_terms else 0.0
        ev["recency"] = _recency(d.get("doc_date_norm"), d.get("upload_ts", ""))
        ev["tags"] = kw_map.get(ev["doc_id"], [])
        ev["score"] = round(
            W_VECTOR * max(0.0, ev["vec"] or 0.0)
            + W_BM25 * bm25_norm
            + W_TITLE * ev["title_hit"]
            + W_KEYWORD * ev["keyword_hit"]
            + W_RECENCY * ev["recency"], 4)

    return sorted(by_id.values(), key=lambda e: -e["score"])[:k]
