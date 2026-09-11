"""Ingestion pipeline: classify -> parse -> normalize -> chunk -> embed ->
index -> facts/conflicts. A single worker thread consumes the jobs table so
the UI stays responsive during ingestion. Document id = content SHA-256."""

import json
import logging
import threading
import traceback
import uuid
from pathlib import Path

import numpy as np

from backend.core import config
from backend.db import database as db
from backend import storage
from backend.core.pipeline import parsers
from backend.core.pipeline.chunker import build_chunks
from backend.core.pipeline.embedder import embed_texts, model_info

log = logging.getLogger("cmpdi.pipeline")

STAGES = ["uploaded", "classifying", "extracting", "ocr", "normalizing",
          "chunking", "embedding", "indexing", "completed"]


def ingest_file(path) -> dict:
    """Register a file. Returns {'doc_id', 'duplicate'}; duplicates point at
    the existing document and are not re-processed."""
    path = path if isinstance(path, Path) else Path(path)
    sha = storage.sha256_of(path)
    existing = db.q1("SELECT id FROM documents WHERE sha256=?", (sha,))
    if existing:
        return {"doc_id": existing["id"], "duplicate": True}
    db.execute(
        "INSERT INTO documents (id, sha256, filename, doc_type, status) VALUES (?,?,?,?,?)",
        (sha, sha, path.name, "unknown", "uploaded"))
    db.execute("INSERT INTO jobs (doc_id, stage, status) VALUES (?, 'uploaded', 'pending')", (sha,))
    storage.store_original(path, sha)
    return {"doc_id": sha, "duplicate": False}


def _stage(doc_id: str, stage: str, status: str, error: str | None = None, stats: dict | None = None):
    job = db.q1("SELECT id, stats_json FROM jobs WHERE doc_id=? ORDER BY id DESC LIMIT 1", (doc_id,))
    stats_json = job["stats_json"] if job and job["stats_json"] else "{}"
    if stats:
        merged = json.loads(stats_json)
        merged.update(stats)
        stats_json = json.dumps(merged)
    db.execute(
        "UPDATE jobs SET stage=?, status=?, error=?, stats_json=?, updated_ts=datetime('now') WHERE id=?",
        (stage, status, error, stats_json, job["id"]))
    db.execute("UPDATE documents SET status=? WHERE id=?", (stage if status != "failed" else "failed", doc_id))


def process_document(doc_id: str):
    path = storage.original_path(doc_id)
    if path is None:
        _stage(doc_id, "classifying", "failed", "Original File Missing In Store")
        return
    try:
        _stage(doc_id, "classifying", "running")
        doc_type = parsers.classify(path)
        if doc_type == "unknown":
            raise ValueError("Unrecognized File Type")

        _stage(doc_id, "extracting", "running")
        cdoc = parsers.parse(path)
        stats = {"pages": len(cdoc.pages), "sheets": len(cdoc.sheets),
                 "elements": len(cdoc.elements), "tables": len(cdoc.tables),
                 "ocr_pages": sum(1 for p in cdoc.pages if p.ocr_used)}
        _stage(doc_id, "ocr", "running", stats=stats)
        _stage(doc_id, "normalizing", "running")

        cdoc.meta.pop("_section_stack", None)
        cdoc.meta.pop("_section_timeline", None)
        _persist_document(doc_id, doc_type, cdoc)
        _persist_pages(doc_id, cdoc)
        _persist_elements(doc_id, cdoc)
        table_ids = _persist_tables(doc_id, cdoc)

        _stage(doc_id, "chunking", "running")
        chunks = build_chunks(cdoc)

        # keywords double as tags and enrich every chunk embedding so vector
        # search matches on document-level topics as well as inner content
        keywords, keyword_source = _extract_keywords(doc_id, cdoc)

        _stage(doc_id, "embedding", "running")
        model_name, _dim = model_info()
        if chunks:
            prefix = _embedding_prefix(doc_type, cdoc, keywords)
            vectors = embed_texts([prefix + c["text"] for c in chunks])
        else:
            vectors = []

        _stage(doc_id, "indexing", "running")
        chunk_db_ids = _persist_chunks(doc_id, chunks, vectors, model_name)
        from backend.core.pipeline import vector_store
        vector_store.add(chunk_db_ids, vectors)
        _link_chunk_tables(chunks, chunk_db_ids, table_ids)
        from backend.core import facts
        facts.extract_for_doc(doc_id)
        facts.detect_conflicts()
        _assign_version_group(doc_id)

        _stage(doc_id, "completed", "completed",
               stats={"chunks": len(chunks), "embedding_model": model_name,
                      "keywords": keywords, "keyword_source": keyword_source})
        log.info("Document %s Processed: %s", doc_id[:12], stats)
    except Exception as e:
        log.exception("Pipeline Failed For %s", doc_id)
        _stage(doc_id, "failed", "failed", error=f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}")


def _extract_keywords(doc_id: str, cdoc) -> tuple[list[str], str]:
    from backend.core.keywords import extract_keywords
    parts = [p.text for p in cdoc.pages]
    parts += [el.text for el in cdoc.elements if el.text]
    text = "\n".join(parts)
    keywords, source = extract_keywords(text)
    conn = db.connect()
    conn.execute("DELETE FROM doc_keywords WHERE doc_id=?", (doc_id,))
    for kw in keywords:
        conn.execute("INSERT OR IGNORE INTO doc_keywords (doc_id, keyword, source) VALUES (?,?,?)",
                     (doc_id, kw, source))
    conn.commit()
    return keywords, source


def _embedding_prefix(doc_type: str, cdoc, keywords: list[str]) -> str:
    meta = cdoc.meta
    lines = [
        f"Title: {meta.get('title') or ''}",
        f"Subsidiary: {meta.get('subsidiary') or ''}",
        f"Doc Type: {doc_type}",
        f"Keywords: {', '.join(keywords)}",
    ]
    return "\n".join(lines) + "\n\n"


def _persist_document(doc_id: str, doc_type: str, cdoc):
    db.execute(
        """UPDATE documents SET doc_type=?, subsidiary=?, doc_date_raw=?, doc_date_norm=?,
           page_count=? WHERE id=?""",
        (doc_type, cdoc.meta.get("subsidiary"), cdoc.meta.get("doc_date_raw"),
         cdoc.meta.get("doc_date_norm"), len(cdoc.pages), doc_id))


def _persist_pages(doc_id: str, cdoc):
    conn = db.connect()
    dest_dir = storage.doc_dir(doc_id)
    for p in cdoc.pages:
        image_path = None
        if p.image_path:
            src = config.FILES_DIR / p.image_path
            if src.exists():
                dest = dest_dir / Path(p.image_path).name
                src.rename(dest)
                image_path = f"{doc_id}/{dest.name}"
        conn.execute(
            "INSERT INTO pages (doc_id, page_no, text, ocr_used, avg_confidence, image_path)"
            " VALUES (?,?,?,?,?,?)",
            (doc_id, p.page_no, p.text, int(p.ocr_used), p.avg_confidence, image_path))
    conn.commit()


def _persist_elements(doc_id: str, cdoc) -> list[int]:
    conn = db.connect()
    ids = []
    for el in cdoc.elements:
        cur = conn.execute(
            "INSERT INTO elements (doc_id, page_no, sheet_no, element_type, order_idx,"
            " bbox, text, conf, section_path) VALUES (?,?,?,?,?,?,?,?,?)",
            (doc_id, el.page_no, el.sheet_no, el.element_type, el.order_idx,
             json.dumps(el.bbox) if el.bbox else None, el.text, el.conf, el.section_path))
        ids.append(cur.lastrowid)
    conn.commit()
    return ids


def _persist_tables(doc_id: str, cdoc) -> list[int]:
    conn = db.connect()
    ids = []
    for t in cdoc.tables:
        cur = conn.execute(
            "INSERT INTO tables (doc_id, page_no, sheet_no, table_idx, n_rows, n_cols, headers_json)"
            " VALUES (?,?,?,?,?,?,?)",
            (doc_id, t.page_no, t.sheet_no, t.table_idx, len(t.rows), len(t.headers),
             json.dumps(t.headers)))
        tid = cur.lastrowid
        ids.append(tid)
        for row in t.rows:
            for cell in row:
                conn.execute(
                    "INSERT INTO table_cells (table_id, row_idx, col_idx, value_raw, value_norm, conf)"
                    " VALUES (?,?,?,?,?,?)",
                    (tid, cell["row"], cell["col"], cell["value_raw"],
                     cell["value_norm"], cell["conf"]))
    conn.commit()
    return ids


def _persist_chunks(doc_id: str, chunks, vectors, model_name) -> list[int]:
    conn = db.connect()
    ids = []
    for chunk, vec in zip(chunks, vectors):
        cur = conn.execute(
            "INSERT INTO chunks (doc_id, content_type, section_path, page_no, sheet_no,"
            " text, token_count, element_ids_json) VALUES (?,?,?,?,?,?,?,?)",
            (doc_id, chunk["content_type"], chunk["section_path"], chunk["page_no"],
             chunk["sheet_no"], chunk["text"], chunk["token_count"],
             json.dumps(chunk["element_ids"])))
        cid = cur.lastrowid
        conn.execute("INSERT INTO chunks_fts (rowid, text) VALUES (?,?)", (cid, chunk["text"]))
        conn.execute(
            "INSERT INTO chunk_embeddings (chunk_id, dim, model, blob) VALUES (?,?,?,?)",
            (cid, int(vec.shape[0]), model_name, vec.astype(np.float32).tobytes()))
        ids.append(cid)
    conn.commit()
    return ids


def _link_chunk_tables(chunks, chunk_db_ids, table_ids):
    """Record cell-level provenance by appending table/row refs into the facts
    staging area (facts reads chunks.element_ids_json)."""
    for chunk, cid in zip(chunks, chunk_db_ids):
        for ref in chunk["element_ids"]:
            if "t" in ref:
                ref["tid"] = table_ids[ref["t"]]
        if any("t" in ref for ref in chunk["element_ids"]):
            db.execute("UPDATE chunks SET element_ids_json=? WHERE id=?",
                       (json.dumps(chunk["element_ids"]), cid))


def _assign_version_group(doc_id: str):
    """Near-duplicate detection via document-mean embedding cosine. Documents
    over 0.95 similarity form a version group; the one with the latest
    doc_date_norm (fallback: latest upload) is the current version."""
    rows = db.q("""
        SELECT c.doc_id, e.blob FROM chunk_embeddings e JOIN chunks c ON c.id = e.chunk_id
    """)
    doc_vecs = {}
    for r in rows:
        v = np.frombuffer(r["blob"], dtype=np.float32)
        doc_vecs.setdefault(r["doc_id"], []).append(v)
    means = {d: np.mean(vs, axis=0) for d, vs in doc_vecs.items() if len(vs)}
    if doc_id not in means:
        return
    def norm(v):
        n = np.linalg.norm(v)
        return v / n if n else v
    mine = norm(means[doc_id])
    group = None
    for other, vec in means.items():
        if other == doc_id:
            continue
        if float(np.dot(mine, norm(vec))) > 0.95:
            row = db.q1("SELECT version_group_id FROM documents WHERE id=?", (other,))
            if row and row["version_group_id"]:
                group = row["version_group_id"]
                break
    if group is None:
        for other, vec in means.items():
            if other != doc_id and float(np.dot(mine, norm(vec))) > 0.95:
                group = str(uuid.uuid4())
                db.execute("UPDATE documents SET version_group_id=? WHERE id=?", (group, other))
                break
    if group:
        db.execute("UPDATE documents SET version_group_id=? WHERE id=?", (group, doc_id))
        members = db.q("SELECT id, doc_date_norm, upload_ts FROM documents WHERE version_group_id=?", (group,))
        def sort_key(r):
            return (r["doc_date_norm"] or "", r["upload_ts"])
        ordered = sorted(members, key=sort_key)
        for i, m in enumerate(ordered):
            db.execute("UPDATE documents SET is_current_version=? WHERE id=?",
                       (1 if i == len(ordered) - 1 else 0, m["id"]))


# ---------------------------------------------------------------- worker

_worker_started = False
_wake = threading.Event()


def start_worker():
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    t = threading.Thread(target=_worker_loop, name="cmpdi-worker", daemon=True)
    t.start()


def _worker_loop():
    while True:
        job = db.q1("SELECT id, doc_id FROM jobs WHERE status='pending' ORDER BY id LIMIT 1")
        if job is None:
            _wake.wait(timeout=2.0)
            _wake.clear()
            continue
        db.execute("UPDATE jobs SET status='running', updated_ts=datetime('now') WHERE id=?", (job["id"],))
        process_document(job["doc_id"])


def notify_worker():
    _wake.set()
