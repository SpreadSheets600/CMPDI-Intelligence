"""Ingestion pipeline: classify -> parse -> normalize -> chunk -> embed ->
index -> facts. A single worker thread consumes the jobs table so
the UI stays responsive during ingestion. Document id = content SHA-256."""

import json
import shutil
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
          "chunking", "embedding", "indexing", "summarizing", "completed"]

# User-facing label for what each file became inside the intelligence layer;
# shown on documents and the dashboard so format differences stay visible.
NORMALIZED_TYPES = {
    "pdf": "Textual Document",
    "digital_pdf": "Textual Document",
    "mixed_pdf": "Textual Document (mixed scans)",
    "scanned_pdf": "Scanned Document (OCR)",
    "docx": "Textual Document",
    "xlsx": "Structured Tabular Document",
    "csv": "Structured Tabular Document",
    "image": "Image Document (OCR)",
    "unknown": "Unrecognized File",
}


def delete_document(doc_id: str) -> bool:
    """Remove a document everywhere it exists: vector index, derived rows
    (cascades), generated files, and the stored original. Remaining members
    of its version group elect a new current."""
    doc = db.q1("SELECT id, version_group_id FROM documents WHERE id=?", (doc_id,))
    if doc is None:
        return False

    # explicit deletes cover tables whose FKs predate the cascade
    conn = db.connect()
    conn.execute("DELETE FROM facts WHERE chunk_id IN (SELECT id FROM chunks WHERE doc_id=?)",
                 (doc_id,))
    conn.execute("DELETE FROM jobs WHERE doc_id=?", (doc_id,))
    conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()

    from backend.core.pipeline import vector_store
    vector_store.sync()

    group = doc["version_group_id"]
    if group:
        members = db.q(
            "SELECT id, doc_date_norm, upload_ts FROM documents WHERE version_group_id=?", (group,))
        ordered = sorted(members, key=lambda r: (r["doc_date_norm"] or "", r["upload_ts"]))
        for i, m in enumerate(ordered):
            db.execute("UPDATE documents SET is_current_version=? WHERE id=?",
                       (1 if i == len(ordered) - 1 else 0, m["id"]))

    shutil.rmtree(config.FILES_DIR / doc_id, ignore_errors=True)
    log.info("Document %s Deleted", doc_id[:12])
    return True


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
    if job is None:
        # self-heal: processing reached here without a job row (duplicate
        # re-run, crashed run, or a concurrent worker). Never crash on it.
        log.warning("No Job Row For %s, Creating One", doc_id[:12])
        db.execute("INSERT INTO jobs (doc_id, stage, status) VALUES (?, 'uploaded', 'pending')", (doc_id,))
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


# in-process guard against double-processing one document (worker thread vs
# inline/CLI runs in the same process); cross-process races are handled by
# warning in scripts/ingest.py — stop the server before CLI ingestion.
_IN_PROGRESS: set = set()


def process_document(doc_id: str):
    # in-process guard: the worker thread and inline/CLI processing must
    # never handle the same document twice (duplicate derived rows).
    if doc_id in _IN_PROGRESS:
        log.warning("Document %s Already Processing, Skipping Duplicate Run", doc_id[:12])
        return
    _IN_PROGRESS.add(doc_id)
    try:
        _process_document_inner(doc_id)
    finally:
        _IN_PROGRESS.discard(doc_id)


def _process_document_inner(doc_id: str):
    path = storage.original_path(doc_id)
    if path is None:
        _stage(doc_id, "classifying", "failed", "Original File Missing In Store")
        return
    kg_stats: dict = {}
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
        # publish the raw OCR/native text per page immediately so the job
        # feed can show page content while the rest of ingestion runs
        try:
            _stage(doc_id, "ocr", "running", stats={
                "page_texts": {str(p.page_no): (p.text or "")[:600] for p in cdoc.pages},
            })
        except Exception:
            pass
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
        from backend.core.knowledge import facts
        facts.extract_for_doc(doc_id)
        from backend.core.knowledge import relations as kg_relations
        kg_stats = kg_relations.extract_for_doc(doc_id)
        _assign_version_group(doc_id)

        from backend.core.pipeline import quality_gate
        gate = quality_gate.evaluate(doc_id, cdoc, chunks)
        if gate["verdict"] == quality_gate.FAILED:
            _stage(doc_id, "failed", "failed",
                   error=f"Quality Gate FAILED: {gate['reason'] or 'empty extraction'}",
                   stats={"quality_verdict": gate["verdict"],
                          "quality_checks": gate["checks"]})
            return

        _stage(doc_id, "summarizing", "running")
        from backend.core.knowledge import summary as summary_mod
        # per-page LLM summaries first (each page -> LLM -> embedded
        # PAGE_SUMMARY chunk); progress streams to the job feed with both the
        # OCR excerpt and the LLM summary for every page as it completes
        _progress_summaries: dict = {}
        _progress_texts: dict = {}
        try:
            _progress_texts = {str(p.page_no): (p.text or "")[:600] for p in cdoc.pages}
        except Exception:
            pass

        def _page_progress(page_no, summary, excerpt, done, total):
            _progress_summaries[str(page_no)] = summary
            if excerpt:
                _progress_texts[str(page_no)] = excerpt
            try:
                _stage(doc_id, "summarizing", "running", stats={
                    "page_summaries": dict(_progress_summaries),
                    "page_texts": dict(_progress_texts),
                    "pages_done": done, "pages_total": total,
                })
            except Exception:
                pass

        summary_mod.generate_page_summaries(doc_id, on_progress=_page_progress)
        summary_mod.generate_summary(doc_id)

        from backend.core.pipeline.inspection import inspection_for
        inspection = inspection_for(cdoc)
        _stage(doc_id, "completed", "completed",
               stats={"chunks": len(chunks), "embedding_model": model_name,
                      "keywords": keywords, "keyword_source": keyword_source,
                      "quality_verdict": gate["verdict"],
                      "quality_checks": gate["checks"],
                      "kg_edges": (kg_stats or {}).get("edges", 0),
                      "page_classes": inspection.get("class_counts", {}),
                      "vision_used": cdoc.meta.get("vision_used", 0),
                      "vision_skipped": cdoc.meta.get("vision_skipped", 0)})
        log.info("Document %s Processed: %s", doc_id[:12], stats)
    except Exception as e:
        log.exception("Pipeline Failed For %s", doc_id)
        _stage(doc_id, "failed", "failed", error=f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}")


def _extract_keywords(doc_id: str, cdoc) -> tuple[list[str], str]:
    from backend.core.retrieval.keywords import extract_keywords
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


def summary_embedding_prefix(doc, keywords: list[str]) -> str:
    """Same metadata envelope the content chunks use, so the SUMMARY chunk
    lives in the same embedding space as everything else in its document."""
    lines = [
        f"Title: {doc['display_name'] or doc['filename']}",
        f"Subsidiary: {doc['subsidiary'] or ''}",
        f"Doc Type: {doc['doc_type']}",
        f"Keywords: {', '.join(keywords)}",
    ]
    return "\n".join(lines) + "\n\n"


def _persist_document(doc_id: str, doc_type: str, cdoc):
    # the parser refines the coarse classify() result (pdf -> digital/scanned/mixed)
    from backend.core.pipeline.inspection import inspection_for

    refined = cdoc.doc_type or doc_type
    structure = json.dumps(inspection_for(cdoc), default=str)[:200000]
    db.execute(
        """UPDATE documents SET doc_type=?, content_norm=?, subsidiary=?, doc_date_raw=?,
           doc_date_norm=?, page_count=?, structure_json=? WHERE id=?""",
        (refined, NORMALIZED_TYPES.get(refined, refined), cdoc.meta.get("subsidiary"),
         cdoc.meta.get("doc_date_raw"), cdoc.meta.get("doc_date_norm"), len(cdoc.pages),
         structure, doc_id))


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
            "INSERT INTO pages (doc_id, page_no, text, ocr_used, avg_confidence, image_path,"
            " page_class) VALUES (?,?,?,?,?,?,?)",
            (doc_id, p.page_no, p.text, int(p.ocr_used), p.avg_confidence, image_path,
             getattr(p, "page_class", "TEXT_ONLY")))
    conn.commit()


def _persist_elements(doc_id: str, cdoc) -> list[int]:
    conn = db.connect()
    ids = []
    for el in cdoc.elements:
        cur = conn.execute(
            "INSERT INTO elements (doc_id, page_no, sheet_no, element_type, order_idx,"
            " bbox, text, conf, section_path, method) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (doc_id, el.page_no, el.sheet_no, el.element_type, el.order_idx,
             json.dumps(el.bbox) if el.bbox else None, el.text, el.conf, el.section_path,
             getattr(el, "method", "")))
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


def _elect_current(group: str):
    """Latest doc_date_norm (fallback: latest upload) is the current version."""
    members = db.q("SELECT id, doc_date_norm, upload_ts FROM documents WHERE version_group_id=?", (group,))
    ordered = sorted(members, key=lambda r: (r["doc_date_norm"] or "", r["upload_ts"]))
    for i, m in enumerate(ordered):
        db.execute("UPDATE documents SET is_current_version=? WHERE id=?",
                   (1 if i == len(ordered) - 1 else 0, m["id"]))


def _assign_version_group(doc_id: str):
    """Near-duplicate detection via document-mean embedding cosine. Documents
    over 0.95 similarity form a version group; the one with the latest
    doc_date_norm (fallback: latest upload) is the current version."""
    # cheap exact pre-filter: identical content fingerprints join immediately
    # without waiting on embedding comparison
    mine_fp = None
    cur = db.q1("SELECT structure_json FROM documents WHERE id=?", (doc_id,))
    if cur and cur["structure_json"]:
        try:
            mine_fp = json.loads(cur["structure_json"]).get("fingerprint")
        except Exception:
            mine_fp = None
    if mine_fp:
        for r in db.q("SELECT id, version_group_id, structure_json FROM documents"
                      " WHERE id != ? AND status='completed'", (doc_id,)):
            try:
                fp = (json.loads(r["structure_json"] or "{}").get("fingerprint")
                      if r["structure_json"] else None)
            except Exception:
                fp = None
            if fp and fp == mine_fp:
                group = r["version_group_id"] or str(uuid.uuid4())
                if not r["version_group_id"]:
                    db.execute("UPDATE documents SET version_group_id=? WHERE id=?",
                               (group, r["id"]))
                db.execute("UPDATE documents SET version_group_id=? WHERE id=?",
                           (group, doc_id))
                _elect_current(group)
                log.info("Document %s Fingerprint-Matched Into Group", doc_id[:12])
                return
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
        _elect_current(group)


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
