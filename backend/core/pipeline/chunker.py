"""Structure-aware chunking. Chunks never mix sections, never split a table
row, and every row chunk repeats its header so it is self-describing.
element_ids_json holds provenance refs: {"e": <element index>} for text,
{"t": <table index>, "r": <row index>} for table rows."""

from backend.core import config
from backend.models.documents import CanonicalDoc


def _tok(s: str) -> int:
    return len(s.split())


def build_chunks(cdoc: CanonicalDoc) -> list[dict]:
    chunks = []
    buf, buf_refs, buf_page, buf_sheet, buf_sec, buf_type = [], [], None, None, "", "TEXT"

    def flush():
        nonlocal buf, buf_refs
        if not buf:
            return
        text = " ".join(buf).strip()
        if text:
            chunks.append({
                "content_type": buf_type, "section_path": buf_sec,
                "page_no": buf_page, "sheet_no": buf_sheet, "text": text,
                "token_count": _tok(text), "element_ids": buf_refs,
            })
        buf, buf_refs = [], []

    for idx, el in enumerate(cdoc.elements):
        if el.element_type in ("HEADING", "FIGURE"):
            if el.element_type == "FIGURE" and (el.text or "").strip():
                # interpreted figures (caption-linked or vision-described)
                # are first-class retrievable content with page provenance
                chunks.append({
                    "content_type": "FIGURE", "section_path": el.section_path,
                    "page_no": el.page_no, "sheet_no": el.sheet_no,
                    "text": el.text.strip(),
                    "token_count": _tok(el.text), "element_ids": [{"e": idx}],
                })
            continue
        if el.element_type in ("PARAGRAPH", "LIST"):
            if (buf and (buf_page != el.page_no or buf_sheet != el.sheet_no
                         or buf_sec != el.section_path
                         or buf_type != ("LIST" if el.element_type == "LIST" else "TEXT")
                         or _tok(" ".join(buf)) + _tok(el.text) > config.CHUNK_TOKENS)):
                flush()
            if not buf:
                buf_page, buf_sheet, buf_sec = el.page_no, el.sheet_no, el.section_path
                buf_type = "LIST" if el.element_type == "LIST" else "TEXT"
            buf.append(el.text)
            buf_refs.append({"e": idx})
        elif el.element_type == "CAPTION":
            flush()
            chunks.append({
                "content_type": "FIGURE_CAPTION", "section_path": el.section_path,
                "page_no": el.page_no, "sheet_no": el.sheet_no, "text": el.text,
                "token_count": _tok(el.text), "element_ids": [{"e": idx}],
            })
    flush()

    # table chunks: whole table if small, otherwise one row chunk per row
    for tidx, table in enumerate(cdoc.tables):
        header_line = " | ".join(h for h in table.headers if h)
        header_line = f"TABLE | {header_line}" if header_line else "TABLE"
        rows_text = []
        for row in table.rows:
            cells = [c["value_raw"] for c in row if c["value_raw"]]
            if cells:
                rows_text.append(" | ".join(cells))
        whole = "\n".join([header_line] + rows_text)
        sec = table.section_path or (f"Sheet {table.sheet_no}" if table.sheet_no else "")
        if _tok(whole) <= config.CHUNK_TOKENS:
            chunks.append({
                "content_type": "TABLE", "section_path": sec,
                "page_no": table.page_no, "sheet_no": table.sheet_no,
                "text": whole, "token_count": _tok(whole),
                "element_ids": [{"t": tidx}],
            })
        else:
            for row in table.rows:
                cells = [c["value_raw"] for c in row if c["value_raw"]]
                if not cells:
                    continue
                text = f"{header_line} || {' | '.join(cells)}"
                chunks.append({
                    "content_type": "TABLE_ROW", "section_path": sec,
                    "page_no": table.page_no, "sheet_no": table.sheet_no,
                    "text": text, "token_count": _tok(text),
                    "element_ids": [{"t": tidx, "r": row[0]["row"]}],
                })
    return chunks
