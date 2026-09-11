"""Automated report generation. docxtpl templates (officer-editable DOCX)
filled from the fact index and hybrid retrieval; every generated figure
carries provenance and lands in a Sources appendix. Conflicting facts are
flagged inline, never silently resolved. Low-confidence OCR numbers require
human approval via the conflict workflow before they may appear."""

import json
import time

from docxtpl import DocxTemplate

from . import config, db, facts, retrieval
from .normalize import fy_label

TEMPLATES_DIR = config.ROOT / "cmpdi_intel" / "reports_templates"

TEMPLATES = {
    "production_summary": {
        "title": "Production Summary",
        "body": [
            "Production Summary — {{ entity }}",
            "Period: {{ period }}",
            "",
            "1. Production",
            "{% for r in fact_rows %}{{ r.label }}: {{ r.value }}{% if r.conflict %} [CONFLICT — VERIFY: {{ r.conflict }}]{% endif %} [{{ r.ref }}]",
            "{% endfor %}",
            "2. Narrative Overview",
            "{% for p in narrative %}{{ p }}", "{% endfor %}",
        ],
    },
    "comparative_analysis": {
        "title": "Comparative Analysis",
        "body": [
            "Comparative Analysis — {{ entity }}",
            "Period: {{ period }}",
            "",
            "{% for r in fact_rows %}{{ r.label }}: {{ r.value }}{% if r.conflict %} [CONFLICT — VERIFY: {{ r.conflict }}]{% endif %} [{{ r.ref }}]",
            "{% endfor %}",
            "",
            "{% for p in narrative %}{{ p }}", "{% endfor %}",
        ],
    },
    "parliamentary_reply": {
        "title": "Draft Reply for Parliamentary Question",
        "body": [
            "DRAFT REPLY — prepared for review by competent authority",
            "Question: {{ question }}",
            "",
            "Reply:",
            "{% for p in narrative %}{{ p }}", "{% endfor %}",
            "",
            "Key figures cited: {% for r in fact_rows %}{{ r.label }}: {{ r.value }} [{{ r.ref }}]; {% endfor %}",
            "{% if conflicts_pending %}NOTE: {{ conflicts_pending }} unresolved data conflict(s) detected — see annex.", "{% endif %}",
        ],
    },
}


def ensure_templates():
    TEMPLATES_DIR.mkdir(exist_ok=True)
    from docx import Document
    from docx.shared import Pt
    for name, spec in TEMPLATES.items():
        path = TEMPLATES_DIR / f"{name}.docx"
        if path.exists():
            continue
        doc = Document()
        doc.add_heading(spec["title"], level=0)
        for line in spec["body"]:
            p = doc.add_paragraph()
            run = p.add_run(line)
            run.font.size = Pt(11)
        doc.save(path)


def generate(template: str, params: dict) -> int:
    ensure_templates()
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
    tpl = DocxTemplate(str(TEMPLATES_DIR / f"{template}.docx"))
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
    from .normalize import normalize_period
    if period:
        period_norm = normalize_period(period)

    where, params = ["f.value_norm IS NOT NULL"], []
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
        # unit-agnostic conflict lookup: 4.85 (bare cell) and 4.85 MT are the
        # same fact for the purposes of flagging
        conflict = db.q1(
            "SELECT * FROM conflicts WHERE fact_key LIKE ? AND status='open'",
            (f"{r['canonical_name']}|{r['attribute']}|{r['period_norm']}|%",))
        if conflict:
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
            "conflict": (f"{len(json.loads(conflict['values_json']))} documents disagree"
                         if conflict else ""),
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
