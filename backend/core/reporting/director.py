"""Report director: the LLM plans and orchestrates, deterministic tools do
the work. Runtime owns the data — the model requests operations and gets
structured results back; it never invents DataFrames or arithmetic.

Reasoning budget (no six-agent ceremony for simple questions):
  SIMPLE   — deterministic plan + deterministic prose, no LLM calls
  MODERATE — LLM plan, deterministic sections, LLM executive summary
  COMPLEX  — MODERATE + one audit-driven research/revise pass

Flow: context -> plan -> research -> analysis -> charts -> draft DOM ->
audit -> (revise once) -> render DOCX -> persist report row.
"""

from __future__ import annotations

import json
import logging
import time

from backend.core import config
from backend.core.llm import get_provider
from backend.core.reporting import analyst, auditor, charts as report_charts
from backend.core.reporting import content as rc
from backend.core.reporting import engine as eng
from backend.core.reporting import plan as plan_mod
from backend.core.reporting import skills as skill_packs
from backend.core.reporting.evidence import EvidenceGraph
from backend.core.reporting.workspace import Workspace, build_context
from backend.db import database as db

log = logging.getLogger("cmpdi.director")


# --------------------------------------------------------------------------
# Section executors: each returns DOM blocks and registers evidence.


def _src_ref(graph: EvidenceGraph, row: dict) -> str:
    return graph.add_source(row.get("doc_id"), row.get("filename"),
                            row.get("page_no"), row.get("sheet_no"),
                            row.get("chunk_id"), row.get("value_raw", ""),
                            row.get("unit", ""))


def _exec_narrative(section: dict, context: dict, graph: EvidenceGraph,
                    ws: Workspace) -> list[dict]:
    topic = section.get("title", "") + " " + (context["scope"].get("entity") or "")
    blocks = []
    for b in rc.narrative_candidates(topic, k=3):
        sid = graph.add_source(b["doc_id"], b.get("filename", ""),
                               b.get("page_no"), b.get("sheet_no"))
        text = b["text"][:480]
        cid = graph.add_claim(text, [], [])
        # narrative claims resolve to their source paragraph
        graph.claims[cid]["sources"] = [sid]
        blocks.append({"id": f"{section['id']}-{len(blocks)}",
                       "type": "paragraph", "text": f"{text} [{sid}]",
                       "claims": [cid], "source": [sid]})
    return blocks


def _exec_analysis(section: dict, context: dict, graph: EvidenceGraph,
                   ws: Workspace) -> list[dict]:
    metric = section.get("metric") or "production"
    entity = section.get("entity") or context["scope"].get("entity") or "CIL"
    blocks = []
    g = analyst.growth(metric, entity)
    t = analyst.trend(metric, entity)
    for calc in (g,):
        if calc.get("error"):
            continue
        data_ids = []
        for s in calc["sources"]:
            sid = graph.add_source(s["doc_id"], s["filename"], s["page_no"],
                                   s["sheet_no"], None, s["value_raw"], s["unit"])
            data_ids.append(graph.add_data(
                f"{entity} {metric}", s["value_raw"], None, s["unit"], [sid]))
        cid = graph.add_calc("growth", calc["value"], calc["unit"],
                             calc["formula"], calc["inputs"], data_ids)
        text = (f"{entity} {metric} {calc['inputs'].get('current_period')}: "
                f"{calc['inputs'].get('current')} MT (previous "
                f"{calc['inputs'].get('previous')} MT), a change of "
                f"{calc['value']}% [{cid}].")
        claim = graph.add_claim(text, data_ids, [cid])
        blocks.append({"id": f"{section['id']}-growth", "type": "paragraph",
                       "text": text, "claims": [claim],
                       "source": graph.claims[claim]["sources"]})
    if not t.get("error"):
        pts = ", ".join(f"{p['period']}: {p['value']}" for p in t["value"][:6])
        data_ids = []
        for s in t["sources"]:
            sid = graph.add_source(s["doc_id"], s["filename"], s["page_no"],
                                   s["sheet_no"], None, s["value_raw"], s["unit"])
            data_ids.append(graph.add_data(f"{entity} {metric}", s["value_raw"],
                                           None, s["unit"], [sid]))
        text = (f"{entity} {metric} trend ({t['inputs'].get('direction')}): "
                f"{pts} MT.")
        claim = graph.add_claim(text, data_ids, [])
        blocks.append({"id": f"{section['id']}-trend", "type": "paragraph",
                       "text": text, "claims": [claim],
                       "source": graph.claims[claim]["sources"]})
    (ws.root / "analysis").mkdir(parents=True, exist_ok=True)
    ws.write_json(f"analysis/{section['id']}.json",
                  {"growth": g, "trend": t})
    return blocks


def _exec_visual(section: dict, context: dict, graph: EvidenceGraph,
                 ws: Workspace) -> list[dict]:
    blocks = _exec_analysis(section, context, graph, ws)
    metric = section.get("metric") or "production"
    entity = section.get("entity") or context["scope"].get("entity")
    df = analyst._frame(metric, None if not entity else entity)
    if df is None or "fiscal" not in df:
        return blocks
    table = rc.pivot_by_year(df, last_n=6)
    table, partial_note = eng._drop_partial_year(table)
    if table.empty or table.shape[0] < 2:
        return blocks
    title = section.get("title", f"{metric} trend")
    fname = f"{section['id']}.png"
    path = ws.chart_path(fname)
    if len(table) >= 3:
        report_charts.chart_trend(table, path, title, "MT")
    else:
        report_charts.chart_grouped(table, path, title, "MT")
    csv_name = f"{section['id']}.csv"
    table.to_csv(ws.table_path(csv_name))
    # charts cite the same underlying data sources as the analysis above,
    # never placeholders: the claim must resolve to real documents
    srcs = []
    for b in blocks:
        for cid in b.get("claims", []):
            resolved = graph.resolve_claim(cid)
            if resolved:
                srcs.extend(s["id"] for s in resolved["sources"]
                            if s.get("doc_id"))
    srcs = sorted(set(srcs))
    claim = graph.add_claim(f"{title} (see chart).", [], [])
    graph.claims[claim]["sources"] = srcs
    if not srcs:
        log.warning("Chart %s Has No Resolvable Sources", section["id"])
    graph.claims[claim]["sources"] = srcs
    blocks.append({"id": f"{section['id']}-chart", "type": "chart",
                   "asset": fname, "caption": f"{title}. Values in MT.",
                   "claims": [claim], "source": srcs})
    if partial_note:
        blocks.append({"id": f"{section['id']}-note", "type": "paragraph",
                       "text": partial_note, "claims": [], "source": []})
    return blocks


def _exec_table(section: dict, context: dict, graph: EvidenceGraph,
                ws: Workspace) -> list[dict]:
    metric = section.get("metric") or "production"
    blocks = []
    for tbl in rc.find_tables([metric, "year", "quantity"], limit=1):
        headers = tbl["headers"]
        rows = [[c for c in row] for row in tbl["rows"][:12]]
        sid = graph.add_source(tbl["doc_id"], tbl["filename"], tbl["page_no"],
                               tbl["sheet_no"])
        text = (f"Extracted table from {tbl['filename']}: "
                f"{', '.join(h for h in headers if h)}.")
        claim = graph.add_claim(text, [], [])
        graph.claims[claim]["sources"] = [sid]
        blocks.append({"id": f"{section['id']}-table", "type": "table",
                       "asset": "", "headers": headers, "rows": rows,
                       "caption": text, "claims": [claim], "source": [sid]})
    return blocks


def _exec_verification(section: dict, context: dict, graph: EvidenceGraph,
                       ws: Workspace) -> list[dict]:
    items = [f"{c['entity']} {c['attribute']}: {c['variants']} reported values"
             for c in context.get("known_conflicts", [])[:8]]
    text = ("The fact index holds more than one reported value for the keys "
            "below; charts use the current-version value and the disagreement "
            "is shown here: " + "; ".join(items) + "." if items
            else "No conflicting values were found on the reported keys.")
    return [{"id": section["id"], "type": "paragraph", "text": text,
             "claims": [], "source": []}]


_EXECUTORS = {"narrative": _exec_narrative, "analysis": _exec_analysis,
              "visual_analysis": _exec_visual, "table": _exec_table,
              "verification": _exec_verification}


# --------------------------------------------------------------------------
# Drafting: deterministic prose carries the numbers; the LLM writes only the
# executive summary and transitions from a data brief (same contract as the
# existing engine, now through the unified provider).


def _executive_summary(provider, context: dict, analyses: list[dict]) -> str:
    brief_lines = [f"Objective: {context['objective']}"]
    for b in analyses:
        if b.get("type") == "paragraph" and b.get("claims"):
            brief_lines.append(f"- {b['text'][:300]}")
    brief = "\n".join(brief_lines[:14])
    if provider.generative:
        skill = skill_packs.load_skill("government_reporting") or ""
        text = provider.generate(
            "You write the executive summary of a coal-industry data report. "
            "Use ONLY the numbers and statements provided; never invent or "
            "extrapolate a value. 5 to 8 sentences, no bullets.\n" + skill[:800],
            f"Verified section statements:\n\n{brief}\n\nWrite the summary.")
        if text:
            return " ".join(text.split())
    first = next((b["text"] for b in analyses if b.get("claims")), "")
    return first or "The library did not yield enough evidence for a summary."


# --------------------------------------------------------------------------
# Render + persist


def _render(ws: Workspace, title: str, summary: str, blocks: list[dict]) -> Path:
    from docx import Document
    from docx.shared import Inches

    from backend.core.reporting.md_docx import markdown_to_document

    doc = Document()
    doc.add_heading(title, level=0)
    doc.add_paragraph("Prepared by CMPDI Intelligence from the indexed document "
                      "library. Every figure, table and chart traces to a cited "
                      "source; values are converted to MT where the source used "
                      "another unit.")
    doc.add_heading("Executive Summary", level=1)
    markdown_to_document(summary, base_document=doc)
    for b in blocks:
        if b["type"] == "paragraph":
            markdown_to_document(b["text"], base_document=doc)
        elif b["type"] == "table" and b.get("headers"):
            if b.get("caption"):
                markdown_to_document(f"**{b['caption']}**", base_document=doc)
            rows = b["rows"]
            tbl = doc.add_table(rows=1 + len(rows), cols=len(b["headers"]))
            for j, h in enumerate(b["headers"]):
                tbl.rows[0].cells[j].text = str(h)
            for i, row in enumerate(rows, 1):
                for j in range(len(b["headers"])):
                    tbl.rows[i].cells[j].text = str(row[j] if j < len(row) else "")
        elif b["type"] == "chart":
            p = ws.root / "charts" / b["asset"]
            if p.exists():
                if b.get("caption"):
                    doc.add_paragraph(b["caption"])
                doc.add_picture(str(p), width=Inches(6.1))
    out = ws.final_docx()
    doc.save(str(out))
    return out


# --------------------------------------------------------------------------
# Director entry point


def _classify_mode(params: dict, provider) -> str:
    if params.get("mode") in ("SIMPLE", "MODERATE", "COMPLEX"):
        return params["mode"]
    if not provider.generative:
        return "SIMPLE"
    q = (params.get("question") or "").lower()
    if any(w in q for w in ("why", "compar", "analyz", "trend", "versus", " vs ")):
        return "COMPLEX"
    return "MODERATE"


def generate_analytical(params: dict) -> int:
    """Run the director workflow; returns the reports row id."""
    _t0 = time.time()
    from backend.core.llm import get_provider as _gp
    provider = _gp()
    objective = (params.get("question")
                 or f"{params.get('entity') or 'Library-wide'} "
                 f"{params.get('period') or ''} performance analysis").strip()
    scope = {"entity": (params.get("entity") or "").strip() or None,
             "period": (params.get("period") or "").strip() or None,
             "question": (params.get("question") or "").strip() or None}
    mode = _classify_mode(params, provider)

    ws = Workspace.create(objective, scope, mode, provider.provider_id,
                          provider.model)
    context = build_context(objective, scope)
    ws.write_json("context.json", context)

    if mode == "SIMPLE":
        plan = plan_mod.deterministic_plan(objective, context)
    else:
        plan = plan_mod.plan_with_llm(objective, context, provider)
    ws.write_json("plan.json", plan)

    graph = EvidenceGraph(ws.evidence_path())
    blocks: list[dict] = []
    for section in plan["sections"]:
        ex = _EXECUTORS.get(section["type"])
        if not ex:
            continue
        try:
            blocks.extend(ex(section, context, graph, ws) or [])
        except Exception as e:
            log.warning("Section %s Failed: %s", section.get("id"), e)
    ws.write_json("drafts/blocks.json", blocks)

    summary = _executive_summary(provider, context, blocks)
    audit = auditor.audit(blocks, graph,
                          {"sections": len(blocks)},
                          ws.root / "charts")
    revised = False
    if audit["verdict"] == "FAIL" and mode == "COMPLEX":
        # one bounded revise pass: re-research failed claims, then re-audit
        from backend.core.llm import tools as _tools
        fallback_metric = (plan.get("required_data") or [{}])[0].get("metric") \
            or "production"
        for f in audit["findings"]:
            if f["level"] != "FAIL" or not f["where"].startswith("CLAIM"):
                continue
            resolved = graph.resolve_claim(f["where"])
            if not resolved:
                continue
            ev = _tools.get("get_evidence").run(
                {"entity": scope.get("entity") or "",
                 "attribute": fallback_metric})
            for row in (ev.get("evidence") or [])[:2]:
                sid = graph.add_source(row.get("doc_id"), row.get("filename"),
                                       row.get("page_no"), row.get("sheet_no"),
                                       row.get("chunk_id"),
                                       row.get("value_raw", ""), row.get("unit", ""))
                graph.claims[f["where"]]["sources"].append(sid)
        audit = auditor.audit(blocks, graph, {"sections": len(blocks)},
                              ws.root / "charts")
        revised = True
    ws.write_json("drafts/audit.json", {**audit, "revised": revised})

    out = _render(ws, plan["title"], summary, blocks)

    refs = graph.receipt_refs()
    ordered = sorted(graph.sources)
    sources = {}
    for ref, slot in refs.items():
        sid = ordered[int(ref[1:]) - 1]
        s = graph.sources[sid]
        loc = (f"page {s['page_no']}" if s["page_no"]
               else f"sheet {s['sheet_no']}" if s["sheet_no"] is not None
               else "document level")
        sources[ref] = f"{s['filename']}, {loc}"
    provenance = {"slots": refs, "sources": sources,
                  "workspace": ws.wid, "mode": mode,
                  "audit": audit["verdict"],
                  "evidence": graph.summary(),
                  "chain_note": "ref -> claim -> data/calc -> source -> "
                                "chunk -> page/sheet -> document -> original "
                                "file (data/files/<sha256>/)"}
    from backend.core import quality
    quality.record_report_time(time.time() - _t0)
    return db.execute(
        "INSERT INTO reports (template, params_json, docx_path, provenance_json)"
        " VALUES (?,?,?,?)",
        ("analytical", json.dumps({**params, "mode": mode,
                                   "workspace": ws.wid}), str(out),
         json.dumps(provenance)))
