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

_PAGE_PROMPT_SYSTEM = (
    "You summarize a single page of a coal-industry document. Write 2 to 3 "
    "sentences: what this page contains, any key figures or tables, and how it "
    "relates to the document. Plain facts, no preamble, no bullet points. "
    "Use ONLY the page content provided; never invent values."
)

# Bound per-document LLM calls so very long PDFs stay tractable; remaining
# pages keep an extractive fallback and are still indexed.
MAX_LLM_PAGES = 40
_PAGE_TEXT_LIMIT = 1500


def _extractive_page_summary(text: str, limit: int = 320) -> str:
    """Deterministic fallback when no generative backend answers: first
    complete sentences of the OCR/native text, truncated."""
    import re
    clean = " ".join((text or "").split())
    if not clean:
        return "No extractable text on this page."
    parts = re.split(r"(?<=[.!?])\s+", clean)
    out = ""
    for p in parts:
        out = f"{out} {p}".strip() if out else p
        if len(out) >= limit:
            break
    out = out[: limit + 200]
    return out if out else clean[:limit]


def summarize_page_text(page_no: int, text: str, doc_label: str = "") -> str:
    """Summarize one page with the configured LLM of choice; falls back to
    an extractive snippet when the backend is extractive or errors."""
    clean = " ".join((text or "").split())
    if not clean:
        return "No extractable text on this page."
    excerpt = clean[:_PAGE_TEXT_LIMIT]
    backend = get_backend()
    if backend.name != "extractive":
        try:
            raw = backend.generate(
                _PAGE_PROMPT_SYSTEM,
                f"Document: {doc_label}\nPage {page_no} content:\n{excerpt}",
            )
            if raw and raw.strip():
                return " ".join(raw.split())
        except Exception:
            log.warning("Page summary LLM failed, using extractive fallback")
    return _extractive_page_summary(clean)


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
    page_lines = [
        f"Page {r['page_no']}: {(r['summary'] or '').strip()}"
        for r in db.q(
            "SELECT page_no, summary FROM pages WHERE doc_id=? AND summary IS NOT NULL"
            " AND summary != '' ORDER BY page_no",
            (doc_id,)) if (r["summary"] or "").strip()
    ]
    if backend.name != "extractive":
        user = (f"Document: {doc['display_name'] or doc['filename']} ({doc['doc_type']})\n"
                f"Organization: {doc['subsidiary'] or 'unspecified'}\n"
                f"Period: {doc['doc_date_raw'] or 'unspecified'}\n"
                f"Keywords: {', '.join(keywords) or 'none'}\n\n"
                + ("\n".join(page_lines[:MAX_LLM_PAGES]) + "\n\n" if page_lines else "")
                + f"Content:\n{_corpus_text(doc_id)}")
        raw = backend.generate(_PROMPT_SYSTEM, user)
        if raw:
            summary = " ".join(raw.split())
    if not summary:
        summary = _fallback_summary(doc, n_tables, n_pages)
    if page_lines:
        # attach the per-page summaries so the main summary carries them
        digest = " ".join(page_lines[:MAX_LLM_PAGES])[:4000]
        if digest and digest not in summary:
            summary = f"{summary} Page details: {digest}"

    _persist_summary(doc_id, doc, summary, keywords)
    return summary


def generate_page_summaries(doc_id: str, pages_text: list[tuple[int, str]] | None = None,
                             on_progress=None) -> dict[int, str]:
    """Summarize every page with the configured LLM, persist to pages.summary,
    and index each summary as its own embedded PAGE_SUMMARY chunk.

    pages_text: optional [(page_no, ocr_or_native_text)]; defaults to the
    persisted pages rows. on_progress(page_no, summary, done, total) is called
    after each page so the pipeline can publish live OCR+summary progress to
    the job feed while ingestion runs.
    Returns {page_no: summary}."""
    doc = db.q1("SELECT * FROM documents WHERE id=?", (doc_id,))
    if doc is None:
        return {}
    if pages_text is None:
        pages_text = [(r["page_no"], r["text"] or "")
                      for r in db.q("SELECT page_no, text FROM pages WHERE doc_id=? ORDER BY page_no",
                                    (doc_id,))]
    if not pages_text:
        return {}
    doc_label = doc["display_name"] or doc["filename"]
    out: dict[int, str] = {}
    total = len(pages_text)
    for i, (page_no, text) in enumerate(pages_text):
        clean = " ".join((text or "").split())
        if i < MAX_LLM_PAGES and clean:
            summary = summarize_page_text(page_no, clean, doc_label)
        elif not clean:
            summary = "No extractable text on this page."
        else:
            summary = _extractive_page_summary(clean)
        out[page_no] = summary
        db.execute("UPDATE pages SET summary=? WHERE doc_id=? AND page_no=?",
                   (summary, doc_id, page_no))
        if on_progress is not None:
            try:
                on_progress(page_no, summary, clean[:600], i + 1, total)
            except Exception:
                pass
    _persist_page_summary_chunks(doc_id, doc, out, pages_text)
    return out


def _persist_page_summary_chunks(doc_id: str, doc: dict, summaries: dict[int, str],
                                 pages_text: list[tuple[int, str]]):
    """Replace the document's PAGE_SUMMARY chunks and embed each summary so
    page-level semantics are searchable alongside content chunks."""
    import json as _json

    conn = db.connect()
    conn.execute("DELETE FROM chunks WHERE doc_id=? AND content_type='PAGE_SUMMARY'", (doc_id,))
    conn.commit()
    from backend.core.pipeline import vector_store
    vector_store.sync()

    from backend.core.pipeline import pipeline as pl
    keywords = [r["keyword"] for r in db.q(
        "SELECT keyword FROM doc_keywords WHERE doc_id=? ORDER BY keyword", (doc_id,))]
    prefix = pl.summary_embedding_prefix(doc, keywords)
    texts = {pno: t for pno, t in pages_text}
    ids, vec_inputs = [], []
    for page_no in sorted(summaries):
        excerpt = " ".join((texts.get(page_no) or "").split())[:500]
        text = f"Page {page_no} summary: {summaries[page_no]}"
        if excerpt:
            text += f"\nPage {page_no} content: {excerpt}"
        cur = conn.execute(
            "INSERT INTO chunks (doc_id, content_type, section_path, page_no, sheet_no,"
            " text, token_count, element_ids_json) VALUES (?, 'PAGE_SUMMARY', '', ?, NULL, ?, NULL, '[]')",
            (doc_id, page_no, text))
        cid = cur.lastrowid
        conn.execute("INSERT INTO chunks_fts (rowid, text) VALUES (?,?)", (cid, text))
        ids.append(cid)
        vec_inputs.append(prefix + text)
    conn.commit()
    if ids:
        vec = embed_texts(vec_inputs)
        model_name, _ = model_info()
        for cid, row in zip(ids, vec):
            conn.execute(
                "INSERT INTO chunk_embeddings (chunk_id, dim, model, blob) VALUES (?,?,?,?)",
                (cid, int(row.shape[0]), model_name, row.astype(np.float32).tobytes()))
        conn.commit()
        from backend.core.pipeline import vector_store as vs
        vs.add(ids, vec)


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
