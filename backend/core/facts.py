"""Fact extraction and conflict detection. Facts are (entity, attribute,
period) tuples with normalized values and provenance down to table cells.
Conflict resolution is left to the human review workflow in the UI."""

import json
import re

from backend.core import config
from backend.db import database as db
from backend.core.normalize import (QTY_RE, context_unit, detect_attribute,
                                    in_range, normalize_period, parse_number,
                                    parse_quantity)

_MINE_RE = re.compile(
    r"\b([A-Z][A-Za-z&]+(?:\s+[A-Z][A-Za-z&]+){0,2})\s+"
    r"(Mine|Colliery|Coalfield|Area|OCP|OC Patch|Project|Washery)\b")

# values that are years/grades rather than measurements
_YEAR_LIKE = re.compile(r"^(19|20)\d{2}$")


def ensure_subsidiary_entities():
    for abbr, full in config.SUBSIDIARIES.items():
        if not db.q1("SELECT id FROM entities WHERE canonical_name=?", (abbr,)):
            db.execute("INSERT INTO entities (canonical_name, type, aliases_json) VALUES (?,?,?)",
                       (abbr, "subsidiary", json.dumps([full])))


def load_patterns() -> list[tuple[re.Pattern, int]]:
    """(compiled pattern, entity_id) for canonical names + aliases."""
    ensure_subsidiary_entities()
    patterns = []
    for e in db.q("SELECT id, canonical_name, aliases_json, type FROM entities"):
        names = [e["canonical_name"]] + json.loads(e["aliases_json"] or "[]")
        for name in names:
            if name.isupper() and len(name) <= 6:
                pat = re.compile(rf"\b{re.escape(name)}\b")          # abbreviations: case-sensitive
            else:
                pat = re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
            patterns.append((pat, e["id"]))
    return patterns


def mine_mine_names(doc_text: str):
    """Discover mine/coalfield names used in this document and register them."""
    for m in _MINE_RE.finditer(doc_text):
        name = f"{m.group(1)} {m.group(2)}"
        etype = "coalfield" if m.group(2) == "Coalfield" else "mine"
        if not db.q1("SELECT id FROM entities WHERE canonical_name=?", (name,)):
            db.execute("INSERT INTO entities (canonical_name, type) VALUES (?,?)", (name, etype))


def match_entities(text: str, patterns) -> list[int]:
    seen = []
    for pat, eid in patterns:
        if pat.search(text) and eid not in seen:
            seen.append(eid)
    return seen


def resolve_entity_text(text: str, patterns) -> int | None:
    """Pick the entity with the longest total matched text, so
    'South Eastern Coalfields Limited (SECL)' resolves to SECL and not to ECL
    (whose alias 'Eastern Coalfields Limited' is a substring of it)."""
    scores = {}
    for pat, eid in patterns:
        for m in pat.finditer(text):
            scores[eid] = scores.get(eid, 0) + len(m.group())
    if not scores:
        return None
    return max(scores, key=scores.get)


def extract_for_doc(doc_id: str):
    patterns = load_patterns()
    doc = db.q1("SELECT * FROM documents WHERE id=?", (doc_id,))
    doc_period = doc["doc_date_norm"]

    doc_text = "\n".join(r["text"] for r in db.q("SELECT text FROM pages WHERE doc_id=?", (doc_id,)))
    mine_mine_names(doc_text)
    patterns = load_patterns()

    conn = db.connect()
    conn.execute("DELETE FROM facts WHERE chunk_id IN (SELECT id FROM chunks WHERE doc_id=?)", (doc_id,))
    conn.commit()

    for chunk in db.q("SELECT * FROM chunks WHERE doc_id=?", (doc_id,)):
        refs = json.loads(chunk["element_ids_json"] or "[]")
        period = normalize_period(chunk["text"]) or normalize_period(chunk["section_path"]) or doc_period
        ocr_low = False
        if chunk["page_no"]:
            page = db.q1("SELECT avg_confidence FROM pages WHERE doc_id=? AND page_no=?",
                         (doc_id, chunk["page_no"]))
            ocr_low = bool(page and page["avg_confidence"] is not None
                           and page["avg_confidence"] < config.OCR_MIN_CONF)

        if chunk["content_type"] in ("TABLE", "TABLE_ROW"):
            _facts_from_table_chunk(chunk, refs, period, patterns, ocr_low)
        else:
            _facts_from_text_chunk(chunk, period, patterns, ocr_low)


def _facts_from_table_chunk(chunk, refs, period, patterns, ocr_low):
    tref = next((r for r in refs if "t" in r), None)
    if not tref:
        return
    cells = db.q("SELECT * FROM table_cells WHERE table_id=? ORDER BY row_idx, col_idx",
                 (tref["tid"],))
    headers = json.loads(db.q1("SELECT headers_json FROM tables WHERE id=?", (tref["tid"],))["headers_json"])
    if "r" in tref:
        rows = [dict(c) for c in cells if c["row_idx"] == tref["r"]]
    else:
        # whole-table chunk: extract per row so each fact is row-precise; the
        # sub-context must contain ONLY this row, not sibling rows
        header_line = "TABLE | " + " | ".join(h for h in headers if h)
        row_ids = sorted({c["row_idx"] for c in cells})
        for ridx in row_ids:
            row_cells = [c for c in cells if c["row_idx"] == ridx]
            row_text = " | ".join(c["value_raw"] for c in row_cells if c["value_raw"])
            sub = {
                "id": chunk["id"], "section_path": chunk["section_path"],
                "page_no": chunk["page_no"], "sheet_no": chunk["sheet_no"],
                "text": f"{header_line} || {row_text}",
                "element_ids_json":
                    json.dumps([{"t": tref["t"], "r": ridx, "tid": tref["tid"]}]),
            }
            _facts_from_table_chunk(sub, json.loads(sub["element_ids_json"]),
                                    period, patterns, ocr_low)
        return

    context = f"{chunk['section_path']} {chunk['text'][:300]}"
    # entity comes from THIS row, not the whole table
    row_text = " | ".join(c["value_raw"] for c in rows if c["value_raw"])
    entity_id = resolve_entity_text(row_text, patterns) or resolve_entity_text(context, patterns)
    attr = detect_attribute(context)
    # bare spreadsheet cells inherit the unit from the table title/section
    ctx_unit_name, ctx_unit_factor = context_unit(f"{chunk['section_path']} {headers[0] if headers else ''}")
    for cell in rows:
        if cell["value_norm"] is None or _is_noise(cell["value_raw"]):
            continue
        col_attr = detect_attribute(headers[cell["col_idx"]]) if cell["col_idx"] < len(headers) else None
        cell_period = normalize_period(headers[cell["col_idx"]]) if cell["col_idx"] < len(headers) else None
        _, cell_unit = parse_quantity(cell["value_raw"])
        if cell_unit:
            unit, value = cell_unit, cell["value_norm"]
        elif ctx_unit_name:
            unit, value = ctx_unit_name, cell["value_norm"] * ctx_unit_factor
        else:
            unit, value = None, cell["value_norm"]
        eff_attr = col_attr or attr or "quantity"
        if not in_range(eff_attr, value):
            continue
        flags = "low_confidence_number" if ocr_low else ""
        conn = db.connect()
        conn.execute(
            "INSERT INTO facts (entity_id, entity_text, attribute, period_norm, value_raw,"
            " value_norm, unit, conf, flags, chunk_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (entity_id, None, eff_attr, cell_period or period,
             cell["value_raw"], value, unit,
             0.5 if ocr_low else 1.0, flags, chunk["id"]))
        conn.commit()


_MONTH_NEXT = re.compile(r"\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", re.IGNORECASE)
_DATE_LIKE = re.compile(r"^(?:\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{4}-\d{2}-\d{2})")
_ALPHA_WORDS = re.compile(r"[A-Za-z]{2,}")


def _is_noise(raw: str) -> bool:
    """Statistics sheets are full of computed cells: shares stored as
    fractions, date strings, quarter labels, variation columns. None are
    measurable quantities."""
    raw = raw.strip()
    if not raw or raw.startswith("(") or _YEAR_LIKE.match(raw) or _DATE_LIKE.match(raw):
        return True  # "(9)" is a footnote marker, not a value
    if raw.lower() in ("nil", "na", "n/a", "-", "\u2014"):
        return True
    if re.match(r"^\d+\s*[-\u2013\u2014]\s*\d+$", raw):
        return True  # year spans (2019-20) and ranges (300-600)
    # alphabetic text outside the recognized quantity kills the cell
    # ("3rd Quarter" is noise; "5,800 kcal/kg" is not)
    m = QTY_RE.search(raw)
    rest = raw.replace(m.group(0), "", 1) if m else raw
    if _ALPHA_WORDS.search(rest):
        return True
    v = parse_number(raw)
    if v is None or v < 0:
        return True
    if -1 < v < 1:
        return True  # unitless fractions are computed shares
    # high decimal precision = a computed value, never a reported figure;
    # measure on the bare number, the unit suffix must not count
    num = QTY_RE.search(raw)
    if num:
        whole = num.group(0).split()[0]
        decimals = whole.split(".")
        if len(decimals) == 2 and len(decimals[1].rstrip("0")) > 4:
            return True
    return False


def extract_value(raw: str) -> tuple[float, str | None] | None:
    """Noise-gated quantity parse: the single entry point for turning a cell
    or phrase into a number. Statistics junk (footnote markers, year spans,
    date strings, computed shares) returns None."""
    if _is_noise(raw):
        return None
    return parse_quantity(raw)


def _facts_from_text_chunk(chunk, period, patterns, ocr_low):
    from backend.core.normalize import QTY_RE
    from datetime import date
    matches = list(QTY_RE.finditer(chunk["text"]))
    seen_spans = set()
    conn = db.connect()
    for i, m in enumerate(matches):
        raw = m.group(0).strip()
        # A period usually sits right after its number, up to the next number.
        # In "...157.30 MT during FY2021-22, against 143.85 MT in the previous
        # year..." the 'previous year' phrase belongs to the second number only.
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(chunk["text"])
        segment_before = chunk["text"][max(0, m.start() - 150):m.start()]
        segment_after = chunk["text"][m.end():next_start]
        fact_period = (normalize_period(segment_after) or normalize_period(segment_before)
                       or period)
        if re.search(r"previous (?:fiscal )?year|prior year", segment_after,
                     re.IGNORECASE) and fact_period:
            d = date.fromisoformat(fact_period)
            fact_period = date(d.year - 1, d.month, d.day).isoformat()
        if _YEAR_LIKE.match(raw.replace(",", "").split()[0]) and not m.group("unit"):
            continue
        if not m.group("unit") and _MONTH_NEXT.match(chunk["text"][m.end():]):
            continue  # "1 April 2022" is a date, not a fact
        if raw in seen_spans:
            continue
        seen_spans.add(raw)
        value, unit = parse_quantity(raw)
        if value is None or (unit is None and -1 < value < 1):
            continue
        # Entity and attribute come from the text before the number only;
        # text after the number belongs to the next fact.
        entity_id = resolve_entity_text(segment_before, patterns)
        local_attr = detect_attribute(segment_before)
        if local_attr is None:
            if unit is None:
                continue  # a bare number with no context and no unit is noise
            local_attr = "quantity"
        if not in_range(local_attr, value):
            continue
        flags = "low_confidence_number" if ocr_low else ""
        conn.execute(
            "INSERT INTO facts (entity_id, entity_text, attribute, period_norm, value_raw,"
            " value_norm, unit, conf, flags, chunk_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (entity_id, None, local_attr, fact_period, raw, value, unit,
             0.5 if ocr_low else 1.0, flags, chunk["id"]))
    conn.commit()


def detect_conflicts():
    """Group resolved facts by (entity, attribute, period); groups with values
    differing beyond tolerance become conflicts. Acknowledged/resolved
    conflicts are left untouched."""
    rows = db.q("""
        SELECT f.id, f.entity_id, f.attribute, f.period_norm, f.value_norm, f.value_raw,
               f.unit, f.flags, f.chunk_id, e.canonical_name,
               c.doc_id, c.page_no, c.sheet_no, c.element_ids_json
        FROM facts f
        JOIN entities e ON e.id = f.entity_id
        JOIN chunks c ON c.id = f.chunk_id
        WHERE f.entity_id IS NOT NULL AND f.attribute != 'quantity'
          AND f.value_norm IS NOT NULL AND f.period_norm IS NOT NULL
    """)
    groups = {}
    for r in rows:
        # unit-aware key: a unitless 4.85 and 4.85 MT are not comparable
        key = f"{r['canonical_name']}|{r['attribute']}|{r['period_norm']}|{r['unit'] or ''}"
        groups.setdefault(key, []).append(r)

    for key, facts in groups.items():
        values = sorted({round(f["value_norm"], 6) for f in facts})
        if len(values) < 2:
            continue
        base = values[0]
        if all(abs(v - base) / max(abs(base), 1e-9) <= config.CONFLICT_TOLERANCE for v in values[1:]):
            continue
        if db.q1("SELECT id FROM conflicts WHERE fact_key=? AND status != 'open'", (key,)):
            continue
        payload = [{
            "fact_id": f["id"], "value_norm": f["value_norm"], "value_raw": f["value_raw"],
            "unit": f["unit"], "flags": f["flags"], "doc_id": f["doc_id"],
            "page_no": f["page_no"], "sheet_no": f["sheet_no"],
            "element_ids_json": f["element_ids_json"],
        } for f in facts]
        db.execute("DELETE FROM conflicts WHERE fact_key=? AND status='open'", (key,))
        db.execute("INSERT INTO conflicts (fact_key, values_json) VALUES (?,?)",
                   (key, json.dumps(payload)))


def resolve_conflict(conflict_id: int, chosen_fact_id: int | None, notes: str, status: str = "resolved"):
    db.execute("UPDATE conflicts SET status=?, chosen_fact_id=?, notes=? WHERE id=?",
               (status, chosen_fact_id, notes, conflict_id))
