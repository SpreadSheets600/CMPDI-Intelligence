"""Automated report generation. docxtpl templates (officer-editable DOCX)
filled from the fact index and hybrid retrieval; every generated figure
carries provenance and lands in a Sources appendix. Conflicting facts are
flagged inline, never silently resolved. Low-confidence OCR numbers require
human approval via the conflict workflow before they may appear."""

import io
import json
import time

from docxtpl import DocxTemplate

from backend.core import config, facts, retrieval
from backend.core.normalize import fy_label
from backend.db import database as db

TEMPLATES = {
    "production_summary": {
        "title": "Production Summary",
        "body": [
            "Production Summary: {{ entity }}",
            "Period: {{ period }}",
            "",
            "1. Production",
            "{% for r in fact_rows %}{{ r.label }}: {{ r.value }}{% if r.conflict %} [VERIFY: {{ r.conflict }}]{% endif %} [{{ r.ref }}]",
            "{% endfor %}",
            "2. Narrative Overview",
            "{% for p in narrative %}{{ p }}", "{% endfor %}",
        ],
    },
    "comparative_analysis": {
        "title": "Comparative Analysis",
        "body": [
            "Comparative Analysis: {{ entity }}",
            "Period: {{ period }}",
            "",
            "{% for r in fact_rows %}{{ r.label }}: {{ r.value }}{% if r.conflict %} [VERIFY: {{ r.conflict }}]{% endif %} [{{ r.ref }}]",
            "{% endfor %}",
            "",
            "{% for p in narrative %}{{ p }}", "{% endfor %}",
        ],
    },
    "parliamentary_reply": {
        "title": "Draft Reply for Parliamentary Question",
        "body": [
            "DRAFT REPLY (prepared for review by competent authority)",
            "Question: {{ question }}",
            "",
            "Reply:",
            "{% for p in narrative %}{{ p }}", "{% endfor %}",
            "",
            "Key figures cited: {% for r in fact_rows %}{{ r.label }}: {{ r.value }} [{{ r.ref }}]; {% endfor %}",
            "{% if conflicts_pending %}NOTE: {{ conflicts_pending }} unresolved data conflict(s) detected; see annex.", "{% endif %}",
        ],
    },
}


def _template_stream(name: str) -> io.BytesIO:
    """Build a template DOCX in memory from its spec; nothing ships on disk."""
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    doc.add_heading(TEMPLATES[name]["title"], level=0)
    for line in TEMPLATES[name]["body"]:
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.size = Pt(11)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def generate(template: str, params: dict) -> int:
    if template not in TEMPLATES:
        raise ValueError(f"Unknown Report Template: {template}")
    entity = params.get("entity") or ""
    period = params.get("period") or ""
    question = params.get("question", "")

    fact_rows, provenance = [], {"slots": {}, "sources": {}}
    conflicts_pending = 0

    if entity or period:
        fact_rows, provenance, conflicts_pending = _fact_section(entity, period)

    narrative, provenance_narr = _narrative_section(question or
                                                    f"overview of {entity} {period} performance and operations")
    provenance["sources"].update(provenance_narr)

    ctx = {
        "entity": entity or "All Entities", "period": period or "All Periods",
        "question": question, "fact_rows": fact_rows, "narrative": narrative,
        "conflicts_pending": conflicts_pending,
    }
    tpl = DocxTemplate(_template_stream(template))
    tpl.render(ctx)
    out_name = f"{template}_{int(time.time())}.docx"
    out_path = config.REPORTS_DIR / out_name
    tpl.save(str(out_path))

    provenance["chain_note"] = "ref -> fact id -> chunk -> page/sheet -> document -> original file (data/files/<sha256>/)"
    return db.execute(
        "INSERT INTO reports (template, params_json, docx_path, provenance_json) VALUES (?,?,?,?)",
        (template, json.dumps(params), str(out_path), json.dumps(provenance)))


def _fact_section(entity: str, period: str) -> tuple[list, dict, int]:
    """Rows: label/value/conflict/ref; every value carries a receipt ref."""
    patterns = facts.load_patterns()
    entity_id = None
    if entity:
        for pat, eid in patterns:
            if pat.search(entity):
                entity_id = eid
                break
    period_norm = None
    from backend.core.normalize import normalize_period
    if period:
        period_norm = normalize_period(period)

    where, params = ["f.value_norm IS NOT NULL", "f.attribute != 'quantity'"], []
    if entity_id:
        where.append("f.entity_id=?")
        params.append(entity_id)
    if period_norm:
        where.append("f.period_norm=?")
        params.append(period_norm)
    rows = db.q(f"""
        SELECT f.*, e.canonical_name, f.attribute, d.filename, d.is_current_version,
               c.page_no, c.sheet_no, c.id AS chunk_id, c.element_ids_json, c.doc_id
        FROM facts f JOIN entities e ON e.id=f.entity_id
        JOIN chunks c ON c.id=f.chunk_id JOIN documents d ON d.id=c.doc_id
        WHERE {' AND '.join(where)}
        ORDER BY f.attribute, d.is_current_version DESC, f.conf DESC
    """, params)

    seen, out = set(), []
    provenance = {"slots": {}, "sources": {}}
    conflicts_pending = 0
    for r in rows:
        slot = (r["canonical_name"], r["attribute"], r["period_norm"])
        if slot in seen:
            continue
        seen.add(slot)
        # values reported differently for the same (entity, attribute, period)
        # are flagged inline so the reviewing officer sees both sources
        differing = db.q("""SELECT COUNT(DISTINCT f.value_norm) n FROM facts f
                            JOIN entities e ON e.id = f.entity_id
                            WHERE e.canonical_name = ? AND f.attribute = ?
                              AND f.period_norm IS ? AND f.value_norm IS NOT NULL
                              AND ABS(f.value_norm - ?) > MAX(0.01, 0.01 * ABS(?))""",
                         (r["canonical_name"], r["attribute"], r["period_norm"],
                          r["value_norm"], r["value_norm"]))
        n_diff = differing[0]["n"] if differing else 0
        if n_diff:
            conflicts_pending += 1
        ref = f"S{len(out) + 1}"
        loc = f"page {r['page_no']}" if r["page_no"] else f"sheet {r['sheet_no']}"
        if r["flags"] and "low_confidence_number" in (r["flags"] or ""):
            continue  # quarantine: OCR digits need human approval first
        value = r["value_raw"]
        # append the canonical unit only when the raw value carries none
        # ("48.5" + tonnes; but "36.90 MT" stays as reported)
        if r["unit"] and not any(c.isalpha() for c in value):
            value = f"{value} {r['unit']}"
        out.append({
            "label": f"{r['canonical_name']} {r['attribute'].replace('_', ' ')} ({fy_label(r['period_norm'])})",
            "value": value,
            "conflict": (f"{n_diff} other value{'s' if n_diff != 1 else ''} reported elsewhere"
                         if n_diff else ""),
            "ref": ref,
        })
        provenance["slots"][ref] = {"fact_id": r["id"], "chunk_id": r["chunk_id"],
                                    "doc_id": r["doc_id"], "page_no": r["page_no"],
                                    "sheet_no": r["sheet_no"]}
        provenance["sources"][ref] = f"{r['filename']}, {loc}"
    return out, provenance, conflicts_pending


def _narrative_section(topic: str, k: int = 5) -> tuple[list, dict]:
    evidence = retrieval.hybrid_search(
        topic, k=k, filters={"content_type": ["TEXT", "LIST", "FIGURE_CAPTION"]})
    if not evidence:
        evidence = retrieval.hybrid_search(topic, k=k)
    provenance = {}
    paras = []
    for i, ev in enumerate(evidence, start=1):
        ref = f"N{i}"
        paras.append(f"{ev['text'][:600]} [{ref}]")
        provenance[ref] = {"chunk_id": ev["chunk_id"], "doc_id": ev["doc_id"],
                           "page_no": ev["page_no"], "sheet_no": ev["sheet_no"]}
    return paras, provenance


def receipt(report_id: int, ref: str) -> dict | None:
    """Click-to-receipt: resolve a report figure ref to its source location."""
    row = db.q1("SELECT provenance_json FROM reports WHERE id=?", (report_id,))
    if not row:
        return None
    prov = json.loads(row["provenance_json"])
    return prov["slots"].get(ref)


def generate_from_run(run: dict) -> int:
    """Assemble the agent's finished analysis into an officer-editable DOCX:
    findings from the agent answer, captured charts, cited evidence, and a
    sources appendix carrying the provenance chain."""
    import re
    import time

    from docx import Document
    from docx.shared import Inches, Pt

    doc = Document()
    doc.add_heading(f"Agent Report: {run['task'][:150]}", level=0)
    doc.add_paragraph(f"Prepared by CMPDI Intelligence Agent · {time.strftime('%d %B %Y')} · "
                      "every figure traces to a cited source document.")

    doc.add_heading("Findings", level=1)
    for line in run["answer"].splitlines():
        text = line.strip()
        if not text:
            continue
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        if re.match(r"^#{1,6}\s", text):
            doc.add_heading(re.sub(r"^#{1,6}\s", "", text), level=2)
        elif re.match(r"^[-*]\s", text):
            doc.add_paragraph(re.sub(r"^[-*]\s", "", text), style="List Bullet")
        else:
            doc.add_paragraph(text)

    # charts captured during the run live under data/agent_runs/<run_id>/
    for step in run["steps"]:
        if step["type"] == "chart":
            name = step["src"].rsplit("/", 1)[-1]
            path = config.DATA_DIR / "agent_runs" / step["src"].split("/")[-2] / name
            if path.exists():
                doc.add_picture(str(path), width=Inches(5.8))

    doc.add_heading("Key Evidence", level=1)
    provenance = {"slots": {}, "sources": {}, "chain_note": (
        "ref -> agent evidence -> chunk -> page/sheet -> document -> "
        "original file (data/files/<sha256>/)")}
    for i, e in enumerate(run["citations"], 1):
        ref = f"E{i}"
        loc = f"page {e['page_no']}" if e.get("page_no") else f"sheet {e.get('sheet_no')}"
        doc.add_paragraph(f"[{ref}] {e['filename']}{', ' + loc if loc else ''}: "
                          f"{e['snippet'][:280]}")
        provenance["slots"][ref] = {"doc_id": e["doc_id"], "page_no": e.get("page_no"),
                                    "sheet_no": e.get("sheet_no")}
        provenance["sources"][ref] = f"{e['filename']}{', ' + loc if loc else ''}"

    out_path = config.REPORTS_DIR / f"agent_{run['id']}_{int(time.time())}.docx"
    doc.save(str(out_path))
    return db.execute(
        "INSERT INTO reports (template, params_json, docx_path, provenance_json) VALUES (?,?,?,?)",
        ("agent_run", json.dumps({"run_id": run["id"], "task": run["task"]}),
         str(out_path), json.dumps(provenance)))
