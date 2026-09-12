"""Document summaries. When an LLM backend answers, it writes a purposeful
summary (what the document contains, which entities, which period, notable
data); otherwise a deterministic fallback describes the extraction shape.
The summary is stored on the document AND indexed as its own SUMMARY chunk,
so a query like "documents containing production information" can retrieve a
spreadsheet whose cells never spell out the word production."""

import logging

import numpy as np

from backend.core.llm import get_backend
from backend.core.pipeline.embedder import embed_texts, model_info
from backend.db import database as db

log = logging.getLogger("cmpdi.summary")

_PROMPT_SYSTEM = (
    "You summarize documents for a coal-industry reporting corpus. Write 4 to 6 "
    "sentences: what the document is, which organizations/period it covers, what "
    "kind of data or sections it contains, and anything notable. Plain facts, no "
    "preamble, no bullet points."
)


def _corpus_text(doc_id: str, limit: int = 4000) -> str:
    parts = []
    for row in db.q(
            """SELECT element_type, section_path, text FROM elements
               WHERE doc_id=? AND text != '' ORDER BY order_idx""", (doc_id,)):
        tag = f"[{row['section_path']}] " if row["section_path"] else ""
        parts.append(f"{tag}{row['text']}")
        if sum(len(p) for p in parts) > limit:
            break
    return "\n".join(parts)[:limit]


def _fallback_summary(doc: dict, n_tables: int, n_pages: int) -> str:
    type_desc = {
        "xlsx": "an Excel workbook", "csv": "a CSV dataset",
        "docx": "a Word document", "image": "a scanned image",
        "scanned_pdf": "a scanned PDF (OCR-extracted)",
        "mixed_pdf": "a PDF mixing digital text and scanned pages",
        "digital_pdf": "a digital PDF",
    }.get(doc["doc_type"], doc["doc_type"])
    scope = f" for {doc['subsidiary']}" if doc["subsidiary"] else ""
    period = f", period {doc['doc_date_raw']}" if doc["doc_date_raw"] else ""
    shape = []
    if n_pages:
        shape.append(f"{n_pages} pages")
    if n_tables:
        shape.append(f"{n_tables} tables")
    return (f"{type_desc.capitalize()}{scope}{period}. Extracted "
            + (", ".join(shape) or "no tabular content")
            + ". Content is indexed for semantic search, fact extraction and citation.")


def generate_summary(doc_id: str, regenerate: bool = False) -> str | None:
    """Produce and persist the summary; returns it or None if the document is
    unknown. Creates/replaces the document's SUMMARY chunk and re-embeds it."""
    doc = db.q1("SELECT * FROM documents WHERE id=?", (doc_id,))
    if doc is None:
        return None
    if doc["summary"] and not regenerate:
        return doc["summary"]

    n_tables = db.q1("SELECT COUNT(DISTINCT table_idx) c FROM tables WHERE doc_id=?", (doc_id,))["c"]
    n_pages = doc["page_count"] or 0
    keywords = [r["keyword"] for r in db.q(
        "SELECT keyword FROM doc_keywords WHERE doc_id=? ORDER BY keyword", (doc_id,))]

    summary = None
    backend = get_backend()
    if backend.name != "extractive":
        user = (f"Document: {doc['display_name'] or doc['filename']} ({doc['doc_type']})\n"
                f"Organization: {doc['subsidiary'] or 'unspecified'}\n"
                f"Period: {doc['doc_date_raw'] or 'unspecified'}\n"
                f"Keywords: {', '.join(keywords) or 'none'}\n\n"
                f"Content:\n{_corpus_text(doc_id)}")
        raw = backend.generate(_PROMPT_SYSTEM, user)
        if raw:
            summary = " ".join(raw.split())
    if not summary:
        summary = _fallback_summary(doc, n_tables, n_pages)

    _persist_summary(doc_id, doc, summary, keywords)
    return summary


def _persist_summary(doc_id: str, doc: dict, summary: str, keywords: list[str]):
    # replacing the summary invalidates the old SUMMARY chunk, its embedding
    # row (cascade) and its vector; the FTS row goes with the chunk
    conn = db.connect()
    conn.execute("DELETE FROM chunks WHERE doc_id=? AND content_type='SUMMARY'", (doc_id,))
    conn.commit()
    from backend.core.pipeline import vector_store
    vector_store.sync()

    from backend.core.pipeline import pipeline as pl
    prefix = pl.summary_embedding_prefix(doc, keywords)
    text = f"Document Summary: {summary}"
    cur = conn.execute(
        "INSERT INTO chunks (doc_id, content_type, section_path, page_no, sheet_no,"
        " text, token_count, element_ids_json) VALUES (?, 'SUMMARY', '', NULL, NULL, ?, NULL, '[]')",
        (doc_id, text))
    cid = cur.lastrowid
    conn.execute("INSERT INTO chunks_fts (rowid, text) VALUES (?,?)", (cid, text))
    conn.execute("UPDATE documents SET summary=? WHERE id=?", (summary, doc_id))
    conn.commit()

    vec = embed_texts([prefix + text])
    model_name, _ = model_info()
    conn.execute(
        "INSERT INTO chunk_embeddings (chunk_id, dim, model, blob) VALUES (?,?,?,?)",
        (cid, int(vec.shape[1]), model_name, vec.astype(np.float32).tobytes()))
    conn.commit()
    from backend.core.pipeline import vector_store as vs
    vs.add([cid], vec)


def has_summaries() -> tuple[int, int]:
    row = db.q1(
        """SELECT SUM(CASE WHEN summary IS NOT NULL AND summary != '' THEN 1 ELSE 0 END) done,
                  COUNT(*) total FROM documents WHERE status='completed'""")
    return (row["done"] or 0, row["total"] or 0)
