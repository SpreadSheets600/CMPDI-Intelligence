"""Agent-driven report revision. An officer instruction ("add more charts",
"cover FY2023-24 as well") runs the analytical agent over the current report
plus the evidence layer; the agent returns the complete revised report as
markdown, which is reassembled into a new DOCX with fresh charts and an
extended evidence appendix. The report keeps its id: file, params and
provenance are updated and the review status returns to pending, because
changed content invalidates any prior approval."""

import json
import re
import time

from backend.core import config
from backend.core.llm import agent as agent_mod
from backend.core.llm import get_backend
from backend.db import database as db


class RevisionError(Exception):
    """Base for revision failures surfaced to the officer."""


class NoBackendError(RevisionError):
    """No generative backend is reachable, so the agent cannot revise."""


MAX_INSTRUCTION_CHARS = 2000
MAX_CONTEXT_CHARS = 8000


def _docx_text(path: str | None, limit: int = MAX_CONTEXT_CHARS) -> str:
    """Plain text of the current DOCX for agent context ('' when unreadable)."""
    if not path:
        return ""
    try:
        import zipfile

        from docx import Document

        doc = Document(path)
    except (OSError, ValueError, zipfile.BadZipFile):
        # best-effort context read: a missing/corrupt DOCX just means the
        # agent rebuilds from the evidence layer instead.
        return ""
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text.strip() for c in row.cells if c.text.strip()))
    text = "\n".join(parts)
    return text[:limit] + ("..." if len(text) > limit else "")


def revise_report(report_id: int, instruction: str) -> dict:
    """Apply an officer instruction to a report via the agent. Returns
    {report_id, run_row_id, figures, revisions} for the API layer."""
    instruction = (instruction or "").strip()
    if not instruction:
        raise RevisionError("Instruction is required.")
    if len(instruction) > MAX_INSTRUCTION_CHARS:
        raise RevisionError(f"Instruction is too long (max {MAX_INSTRUCTION_CHARS} chars).")

    row = db.q1("SELECT * FROM reports WHERE id=?", (report_id,))
    if not row:
        raise KeyError(f"Report {report_id} not found.")
    row = dict(row)

    if get_backend().name == "extractive":
        raise NoBackendError(
            "No language backend is reachable (Ollama offline), so the agent "
            "cannot revise this report. Start Ollama and retry.")

    params = json.loads(row["params_json"] or "{}")
    current = _docx_text(row["docx_path"])
    revisions = params.get("revisions") or []

    task = (
        "You are revising an existing intelligence report. The officer's instruction:\n"
        f"{instruction}\n\n"
        f"Report #{report_id} (template: {row['template']}, parameters: "
        f"{json.dumps({k: v for k, v in params.items() if k != 'revisions'})}).\n"
        "Current report content:\n"
        f"{current or '(unreadable; rebuild from the evidence layer instead)'}\n\n"
        "Apply ONLY the instruction; keep every still-valid section, number and "
        "citation ([S#]/[N#]/[E#] markers refer to the report's provenance and "
        "must stay attached to unchanged claims). Any new number, comparison or "
        "chart MUST come from get_facts or run_python (load_facts()/load_table() "
        "give you DataFrames) — never invent values. When the instruction asks "
        "for charts, draw them with matplotlib in run_python; every figure is "
        "captured automatically. End with the finish tool whose answer is the "
        "COMPLETE revised report in markdown (headings, tables, lists), not a "
        "summary of changes.")

    result = agent_mod.run_task(task)
    if not result.get("finished"):
        # Never rewrite the officer's report from a fallback summary: the
        # run is kept for inspection, the report is untouched.
        raise RevisionError(
            f"The agent stopped before producing a revised report (run "
            f"#{result['row_id']} kept for inspection). Nothing was changed — "
            f"check that the language backend answers, then retry.")

    doc = _assemble_revised(row, instruction, result)
    out_path = config.REPORTS_DIR / f"revised_{report_id}_{int(time.time())}.docx"
    doc.save(str(out_path))

    prov = json.loads(row["provenance_json"] or "{}")
    prov.setdefault("slots", {})
    prov.setdefault("sources", {})
    for i, e in enumerate(result["evidence"], 1):
        ref = f"R{i}"
        loc = (f"page {e['page_no']}" if e.get("page_no")
               else f"sheet {e.get('sheet_no')}" if e.get("sheet_no") is not None else "")
        prov["slots"][ref] = {"doc_id": e["doc_id"], "page_no": e.get("page_no"),
                              "sheet_no": e.get("sheet_no"),
                              "revision": len(revisions) + 1}
        prov["sources"][ref] = f"{e['filename']}{', ' + loc if loc else ''}".strip(", ")
    prov["chain_note"] = ("ref -> fact/evidence -> chunk -> page/sheet -> "
                         "document -> original file (data/files/<sha256>/); "
                         "R-refs were added by agent revision.")

    revisions.append({"ts": time.strftime("%Y-%m-%d %H:%M"), "instruction": instruction,
                      "run_row_id": result["row_id"], "file": out_path.name,
                      "figures": len(result["figures"])})
    params["revisions"] = revisions
    db.execute(
        "UPDATE reports SET docx_path=?, params_json=?, provenance_json=?,"
        " review_status='pending', review_note=NULL, human_approved=0 WHERE id=?",
        (str(out_path), json.dumps(params), json.dumps(prov), report_id))

    return {"report_id": report_id, "run_row_id": result["row_id"],
            "figures": len(result["figures"]), "revisions": len(revisions)}


def _assemble_revised(row: dict, instruction: str, result: dict):
    """Revised DOCX: heading, the agent's full revised markdown (with R-refs),
    captured charts, and an appendix of the evidence added in this revision."""
    from docx import Document
    from docx.shared import Inches

    from backend.core.reporting.md_docx import markdown_to_document

    doc = Document()
    doc.add_heading(f"Report #{row['id']} — revised", level=0)
    doc.add_paragraph(
        f"Agent revision {time.strftime('%d %B %Y')}: {instruction} "
        f"(supersedes {((row['docx_path'] or '').rsplit('/', 1) or [''])[-1]}). "
        "Content changed, so this report needs review again before approval.")

    answer = result["answer"] or ""
    # the run's [E#] markers point at this run's evidence; namespace them to
    # R# so they match the merged provenance and never collide with the
    # original report's refs.
    answer = re.sub(r"\[E(\d+)\]", r"[R\1]", answer)
    markdown_to_document(answer.strip(), base_document=doc)

    for fig in result["figures"]:
        path = (config.DATA_DIR / "agent_runs" / fig["run_id"] / fig["file"])
        if path.exists():
            doc.add_picture(str(path), width=Inches(5.8))

    if result["evidence"]:
        doc.add_heading("Evidence added in this revision", level=1)
        md_evidence = []
        for i, e in enumerate(result["evidence"], 1):
            loc = (f"page {e['page_no']}" if e.get("page_no")
                   else f"sheet {e.get('sheet_no')}" if e.get("sheet_no") is not None else "")
            md_evidence.append(
                f"- **[R{i}]** {e['filename']}{', ' + loc if loc else ''}: "
                f"{e['snippet'][:280]}")
        markdown_to_document("\n".join(md_evidence), base_document=doc)
    return doc
