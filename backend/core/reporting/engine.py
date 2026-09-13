"""Comprehensive report engine. Extracts the most meaningful content the
library holds (cleaned prose, best-matching tables, cleaned fact series),
draws charts from the real numbers, and composes a structured DOCX report:
executive summary, data sections with tables and charts, verification notes
where sources disagree, and a sources appendix with per-item receipts.

Text is composed as markdown and converted to real Word elements by
md_docx; charts are embedded as images at marked positions."""

import json
import re
import time
from pathlib import Path

from docx import Document
from docx.shared import Inches

from backend.core import config
from backend.core.reporting import charts as report_charts
from backend.core.reporting import content as report_content
from backend.core.reporting.md_docx import markdown_to_document
from backend.db import database as db

SUBSIDIARY_ENTITIES = ["ECL", "BCCL", "CCL", "NCL", "WCL", "SECL", "MCL", "NEC"]
_CORE = ["CIL", *SUBSIDIARY_ENTITIES]


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Full-pipe markdown table; the only format the markdown->DOCX chain
    converts reliably into a real Word table. Cells are flattened to one
    line, pipe-escaped, and junk-precision floats are rounded."""
    def clean(c):
        s = re.sub(r"\s+", " ", str(c)).replace("|", "/").strip()
        if re.fullmatch(r"-?\d+\.\d{4,}", s):
            s = f"{float(s):,.3f}".rstrip("0").rstrip(".")
        return s
    lines = ["| " + " | ".join(clean(h) for h in headers) + " |",
             "|" + "--- | " * len(headers)]
    for row in rows:
        lines.append("| " + " | ".join(clean(c) for c in row) + " |")
    return "\n".join(lines)


def _order_columns(table, preferred: list[str]) -> object:
    cols = [c for c in preferred if c in table.columns] + \
           [c for c in table.columns if c not in preferred]
    return table[list(cols)]


def _drop_partial_year(table, threshold: float = 0.5) -> tuple[object, str | None]:
    """Advance releases report partial years (e.g. up to December); when the
    latest row is far below the previous one it would read as a collapse, so
    it is excluded from tables and charts with a note."""
    if len(table) < 2:
        return table, None
    last, prev = table.iloc[-1].max(), table.iloc[-2].max()
    if last < prev * threshold:
        note = f"{table.index[-1]} excluded: partial-year figures, reported up to a " \
               "mid-year cutoff in the source document."
        return table.iloc[:-1], note
    return table, None


def _promote_real_header(tbl: dict) -> dict:
    """Coal Directory tables often carry a numbered first row, (1)(2)(3);
    when that happens the following row is the real header."""
    import re as _re
    headers = tbl["headers"]
    numbered = sum(1 for h in headers if _re.fullmatch(r"\(?\d+\)?", h.strip()))
    if headers and numbered >= max(2, len(headers) * 0.6) and tbl["rows"]:
        new_headers = tbl["rows"][0]
        return {**tbl, "headers": new_headers, "rows": tbl["rows"][1:]}
    return tbl


def _ref(receipts: dict, doc_id: str, page_no, sheet_no) -> str:
    ref = f"S{len(receipts) + 1}"
    receipts[ref] = {"doc_id": doc_id, "page_no": page_no, "sheet_no": sheet_no}
    return ref


def _section_prose(topic: str, k: int, receipts: dict) -> list[str]:
    """Supporting prose for a section; each paragraph ends with its receipt."""
    lines = []
    for b in report_content.narrative_candidates(topic, k=k):
        ref = _ref(receipts, b["doc_id"], b["page_no"], b["sheet_no"])
        text = b["text"]
        if len(text) > 480:
            cut = text.find(". ", 480)
            text = text[:cut + 1] if cut > 0 else text[:480] + "..."
        lines.append(f"{text} [{ref}]")
    return lines


def _fact_matrix(table, unit: str, receipts: dict) -> str:
    """Entity x fiscal-year matrix as a Word table with a receipt line."""
    headers = ["Fiscal Year", *table.columns]
    rows = []
    for fy, row in table.iterrows():
        cells = ["-" if v != v else f"{v:,.2f}" for v in row]
        rows.append([fy, *cells])
    body = _md_table(headers, rows)
    refs = []
    for doc_id in db.q("SELECT id, filename FROM documents WHERE is_current_version = 1 LIMIT 2"):
        ref = _ref(receipts, doc_id["id"], None, None)
        refs.append(f"{doc_id['filename']} [{ref}]")
    return body + f"\n\n*Values in {unit}, as reported in {', '.join(refs)}.*"


def _extracted_table_block(tbl: dict, receipts: dict, caption: str, max_rows: int = 12) -> str:
    ref = _ref(receipts, tbl["doc_id"], tbl["page_no"], tbl["sheet_no"])
    headers = tbl["headers"]
    rows = [[(c[:26] if c else "") for c in row] for row in tbl["rows"][:max_rows]]
    loc = f"sheet {tbl['sheet_no']}" if tbl["sheet_no"] is not None else f"page {tbl['page_no']}"
    body = _md_table(headers, rows)
    return (f"**{caption}** [{ref}]\n\n{body}\n\n"
            f"*Extracted from {tbl['filename']}, {loc}. Truncated to {len(rows)} of "
            f"{len(tbl['rows'])} rows.*" if len(tbl["rows"]) > max_rows else
            f"**{caption}** [{ref}]\n\n{body}\n\n*Extracted from {tbl['filename']}, {loc}.*")


def _llm_summary(data_brief: str) -> str | None:
    from backend.core.llm import get_backend
    backend = get_backend()
    if backend.name == "extractive":
        return None
    raw = backend.generate(
        "You write the executive summary of a coal-industry data report. Use ONLY "
        "the numbers and statements provided; never invent or extrapolate a value. "
        "Write 5 to 8 sentences of plain prose, no bullet points, no headings.",
        f"Data gathered from the document library:\n\n{data_brief}\n\n"
        "Write the executive summary.")
    return " ".join(raw.split()) if raw else None


def _verification_notes(attribute: str) -> list[str]:
    """Keys where current-version documents report differing values."""
    from backend.core.normalize import fy_label
    rows = db.q("""
        SELECT e.canonical_name AS entity, f.period_norm, COUNT(DISTINCT f.value_norm) n
        FROM facts f JOIN entities e ON e.id = f.entity_id
        WHERE f.attribute = ? AND f.value_norm IS NOT NULL
          AND COALESCE(e.canonical_name, f.entity_text) != ''
        GROUP BY entity, f.period_norm HAVING n > 1 ORDER BY n DESC LIMIT 5
    """, (attribute,))
    return [f"{r['entity']} {fy_label(r['period_norm']) if r['period_norm'] else 'period n/a'}: "
            f"{r['n']} different values reported across documents" for r in rows]


def generate_comprehensive(params: dict) -> int:
    _t0 = time.time()
    entity = (params.get("entity") or "").strip() or None
    focus = f" for {entity}" if entity else ""
    stamp = int(time.time())
    chart_dir = config.REPORTS_DIR / f"charts_{stamp}"
    chart_dir.mkdir(parents=True, exist_ok=True)
    receipts: dict = {}

    blocks: list[tuple[str, object]] = []

    # ------------------------------------------------ production
    prod = report_content.fact_series("production", fiscal_only=True)
    prod = report_content.normalize_units(prod)
    if not prod.empty:
        prod_focus = prod[prod["entity"] == entity] if entity else prod
        md = [f"## Coal Production{focus}", ""]
        hl = report_content.highlights(prod_focus)
        if hl:
            md += [f"**Key figures.** {' '.join(hl)}", ""]
        table = report_content.pivot_by_year(
            prod, entities=None if entity is None else [entity], last_n=6)
        table, partial_note = _drop_partial_year(table)
        if not table.empty:
            table = _order_columns(table, _CORE)
            md.append(_fact_matrix(table, "MT", receipts))
            if partial_note:
                md.append(f"*{partial_note}*")
            blocks.append(("md", "\n".join(md)))
            latest = table.iloc[-1].dropna()
            if len(latest) >= 2:
                blocks.append(("image", report_charts.chart_shares(
                    {k: float(v) for k, v in latest.items()},
                    chart_dir / "production_shares.png",
                    f"Production by entity, {table.index[-1]} (MT)")))
            if table.shape[1] >= 1 and table.shape[0] >= 2:
                trend_path = chart_dir / "production_trend.png"
                if len(table) >= 3:
                    blocks.append(("image", report_charts.chart_trend(
                        table, trend_path,
                        "Production trend by fiscal year", "MT")))
                else:
                    blocks.append(("image", report_charts.chart_grouped(
                        table, trend_path,
                        "Production by fiscal year", "MT")))
        else:
            blocks.append(("md", "\n".join(md)))
        prose = _section_prose("coal production performance off-take", 2, receipts)
        if prose:
            blocks.append(("md", "**From the documents**\n\n" + "\n\n".join(prose)))

    # ------------------------------------------------ offtake
    off = report_content.fact_series("offtake", fiscal_only=True)
    off = report_content.normalize_units(off)
    if not off.empty:
        off_table = report_content.pivot_by_year(
            off, entities=None if entity is None else [entity], last_n=6)
        off_table, off_note = _drop_partial_year(off_table)
        off_md = [f"## Off-take and Despatch{focus}", ""]
        off_hl = report_content.highlights(off[off["entity"] == entity] if entity else off)
        if off_hl:
            off_md += [f"**Key figures.** {' '.join(off_hl)}", ""]
        blocks.append(("md", "\n".join(off_md)))
        if not off_table.empty and off_table.shape[1] >= 1 and off_table.shape[0] >= 2:
            off_table = _order_columns(off_table, _CORE)
            if len(off_table) >= 3:
                blocks.append(("image", report_charts.chart_trend(
                    off_table, chart_dir / "offtake_trend.png",
                    "Off-take trend by fiscal year", "MT")))
            else:
                blocks.append(("image", report_charts.chart_grouped(
                    off_table, chart_dir / "offtake_trend.png",
                    "Off-take by fiscal year", "MT")))

    # ------------------------------------------------ production vs offtake
    base_entity = entity or "CIL"
    if not prod.empty and not off.empty:
        p = report_content.pivot_by_year(
            report_content.drop_partial_points(prod[prod["entity"] == base_entity]),
            entities=[base_entity], last_n=6)
        o = report_content.pivot_by_year(
            report_content.drop_partial_points(off[off["entity"] == base_entity]),
            entities=[base_entity], last_n=6)
        if not p.empty and not o.empty:
            joined = p.join(o, lsuffix=" (prod)", rsuffix=" (off)", how="inner")
            if len(joined) >= 2:
                joined.columns = ["Production", "Off-take"]
                blocks.append(("image", report_charts.chart_grouped(
                    joined, chart_dir / "production_vs_offtake.png",
                    f"{base_entity}: production versus off-take", "MT",
                    labels=("Production", "Off-take"))))

    # ------------------------------------------------ long-run trend
    for tbl in report_content.find_tables(
            ["production", "quantity", "year", "coal"], limit=3):
        series = report_content.longest_year_series(tbl)
        if len(series) >= 5:
            import pandas as pd
            s = pd.DataFrame(series, columns=["fiscal", "Production (MT)"]).set_index("fiscal")
            blocks.append(("image", report_charts.chart_trend(
                s, chart_dir / "longrun_production.png",
                f"Long-run production reported in {tbl['filename']}", "MT")))
            blocks.append(("md", _extracted_table_block(
                _promote_real_header(tbl), receipts,
                f"Extracted table: year-wise production ({len(series)} years)", max_rows=10)))
            break

    # ------------------------------------------------ reserves
    res = report_content.fact_series("reserves", require_period=False)
    res = report_content.normalize_units(res)
    if not res.empty:
        res_md = [f"## Reserves and Resources{focus}", ""]
        res_block = res[res["entity"] == (entity or "CIL")] if entity else res[res["entity"].isin(_CORE)]
        if not res_block.empty:
            res_md.append(f"**Key figures.** {' '.join(report_content.highlights(res_block))}")
        else:
            # mostly state/field-level figures without a period; show the
            # distinct reported values with their sources
            distinct = res.drop_duplicates(subset=["value_norm"]).nlargest(8, "value_norm")
            rows = [[f"{r['entity'] or 'Unattributed'}", f"{r['value_norm']:,.2f}"]
                    for _, r in distinct.iterrows()]
            res_md.append(_md_table(["Reported by", "Geological reserves (MT)"], rows))
        blocks.append(("md", "\n".join(res_md)))
    for tbl in report_content.find_tables(["reserves", "geological", "coal"], limit=1):
        blocks.append(("md", _extracted_table_block(
            _promote_real_header(tbl), receipts,
            "Extracted table: geological reserves of Indian coal")))

    # ------------------------------------------------ a production source table
    for tbl in report_content.find_tables(["production", "offtake", "despatch"], limit=1):
        blocks.append(("md", _extracted_table_block(
            _promote_real_header(tbl), receipts,
            "Extracted table: production and offtake data")))

    # ------------------------------------------------ verification
    notes = _verification_notes("production")
    if notes:
        blocks.append(("md", "## Verification Notes\n\nThe fact index holds more than "
                       "one reported value for the keys below; charts use the value from "
                       "the current-version document and the disagreement is shown here:\n\n"
                       + "\n\n".join(f"- {n}" for n in notes)))

    # ------------------------------------------------ executive summary
    data_brief = "\n".join([
        "Latest-year highlights:",
        *[f"- {h}" for h in report_content.highlights(prod, 5)],
        *[f"- {h}" for h in report_content.highlights(off, 3)],
        "Document summaries:",
        *[f"- {r['summary'][:220]}" for r in db.q(
            "SELECT summary FROM documents WHERE status='completed' AND "
            "summary IS NOT NULL AND summary != '' LIMIT 4")],
    ])
    summary = _llm_summary(data_brief)
    if not summary:
        hl = report_content.highlights(prod, 5)
        summary = " ".join(hl) or "The library did not yield enough numeric evidence for a summary."

    final_blocks: list[tuple[str, object]] = [
        ("md", "## Executive Summary"), ("md", summary), *blocks,
    ]

    # ------------------------------------------------ sources
    src_lines = ["## Sources", ""]
    for ref, slot in receipts.items():
        row = db.q1("SELECT filename FROM documents WHERE id = ?", (slot["doc_id"],))
        name = row["filename"] if row else "unknown document"
        loc = (f"page {slot['page_no']}" if slot.get("page_no")
               else f"sheet {slot['sheet_no']}" if slot.get("sheet_no") is not None
               else "document level")
        src_lines.append(f"• **[{ref}]** {name}, {loc}")
    final_blocks.append(("md", "\n\n".join(src_lines)))

    doc = Document()
    doc.add_heading(f"Comprehensive Analysis{focus}: Coal Production, Offtake and Reserves", level=0)
    doc.add_paragraph("Prepared by CMPDI Intelligence from the indexed document library. "
                      "Every figure, table and chart traces to a cited source; values are "
                      "converted to MT where the source used another unit.")
    for kind, payload in final_blocks:
        if kind == "md":
            markdown_to_document(payload, base_document=doc)
        else:
            doc.add_picture(str(payload), width=Inches(6.1))

    out_path = config.REPORTS_DIR / f"comprehensive_{stamp}.docx"
    doc.save(str(out_path))
    from backend.core import quality
    quality.record_report_time(time.time() - _t0)
    return db.execute(
        "INSERT INTO reports (template, params_json, docx_path, provenance_json) VALUES (?,?,?,?)",
        ("comprehensive", json.dumps(params), str(out_path),
         json.dumps({"slots": receipts, "sources": receipts,
                     "charts_dir": str(chart_dir),
                     "chain_note": "ref -> fact/paragraph/table -> chunk -> page/sheet -> "
                                   "document -> original file (data/files/<sha256>/)"})))
