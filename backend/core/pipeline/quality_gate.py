"""Ingestion quality gate. Runs after facts/versioning, before a document
becomes searchable. Verdicts:

    COMPLETE — index as normal
    WARNING  — index, but record what needs an officer's eye
    FAILED   — do not index; mark the job failed with the reason

Every verdict carries its checks so the pipeline feed can show *why*.
Thresholds follow config (OCR floor, OCR confidence) with local defaults.
"""

from __future__ import annotations

import logging

from backend.core.pipeline.inspection import inspection_for

log = logging.getLogger("cmpdi.quality_gate")

COMPLETE = "COMPLETE"
WARNING = "WARNING"
FAILED = "FAILED"

# fraction of pages allowed to end up content-free before WARNING
_EMPTY_PAGE_WARN = 0.5
# fraction of planned-OCR pages that must actually OCR before WARNING
_OCR_COVERAGE_WARN = 0.8
# mean OCR confidence below this warns (per-page floor lives in config)
_OCR_CONF_WARN = 70.0


def _check(name, status, detail=""):
    return {"name": name, "status": status, "detail": detail}


def evaluate(doc_id: str, cdoc, chunks: list[dict]) -> dict:
    inspection = inspection_for(cdoc)
    checks = []

    # 1. every inspected page produced a PageData
    expected = inspection.get("page_count", 0)
    got = len(cdoc.pages) or len(cdoc.sheets)
    if expected and got < expected:
        checks.append(_check("pages_processed", "fail",
                             f"{got}/{expected} pages produced"))
    else:
        checks.append(_check("pages_processed", "pass",
                             f"{got} page(s)/sheet(s)"))

    # 2. content coverage: pages with text, tables or figures
    fig_pages = {e.page_no for e in cdoc.elements
                 if e.element_type == "FIGURE" and e.page_no}
    content_pages = sum(1 for p in cdoc.pages
                        if (p.text or "").strip()
                        or any(t.page_no == p.page_no for t in cdoc.tables)
                        or p.page_no in fig_pages)
    total_pages = len(cdoc.pages)
    if total_pages:
        empty_share = 1 - content_pages / total_pages
        if empty_share == 1 and not cdoc.tables and not cdoc.sheets:
            checks.append(_check("content_coverage", "fail",
                                 "no text, tables or figures extracted"))
        elif empty_share > _EMPTY_PAGE_WARN:
            checks.append(_check("content_coverage", "warn",
                                 f"{round(empty_share * 100)}% pages empty"))
        else:
            checks.append(_check("content_coverage", "pass",
                                 f"{content_pages}/{total_pages} pages"))
    else:
        checks.append(_check("content_coverage",
                             "pass" if cdoc.sheets else "fail",
                             f"{len(cdoc.sheets)} sheet(s)"))

    # 3. OCR fidelity: planned-OCR pages that actually OCR'd, and confidence
    planned = [p for p in cdoc.pages
               if "ocr" in (getattr(p, "methods", None) or [])]
    done = [p for p in planned if p.ocr_used and (p.text or "").strip()]
    if planned:
        cov = len(done) / len(planned)
        if cov < 1 and not done:
            checks.append(_check("ocr_fidelity", "fail",
                                 f"0/{len(planned)} planned pages OCR'd"))
        elif cov < _OCR_COVERAGE_WARN:
            checks.append(_check("ocr_fidelity", "warn",
                                 f"{len(done)}/{len(planned)} pages OCR'd"))
        else:
            confs = [p.avg_confidence for p in done
                     if p.avg_confidence]
            mean_conf = sum(confs) / len(confs) if confs else None
            if mean_conf is not None and mean_conf < _OCR_CONF_WARN:
                checks.append(_check("ocr_fidelity", "warn",
                                     f"mean OCR confidence {mean_conf:.1f}%"))
            else:
                checks.append(_check("ocr_fidelity", "pass",
                                     f"{len(done)}/{len(planned)} pages"))
    else:
        checks.append(_check("ocr_fidelity", "pass", "no OCR planned"))

    # 4. table parity: inspection-predicted tables vs extracted
    predicted = sum(p.get("tables", 0)
                    for p in inspection.get("pages", []))
    found = len(cdoc.tables)
    if predicted and not found:
        checks.append(_check("table_parity", "warn",
                             f"{predicted} ruled table(s) seen, none extracted"))
    else:
        checks.append(_check("table_parity", "pass",
                             f"{found} table(s)"))

    # 5. provenance: chunks must carry element refs into the canonical model
    if chunks:
        linked = sum(1 for c in chunks if c.get("element_ids"))
        if linked < len(chunks):
            checks.append(_check("provenance", "warn",
                                 f"{linked}/{len(chunks)} chunks linked"))
        else:
            checks.append(_check("provenance", "pass",
                                 f"{len(chunks)} chunks linked"))
    else:
        checks.append(_check("provenance",
                             "warn" if (content_pages or cdoc.tables) else "pass",
                             "no chunks built"))

    # 6. vision ledger (informational only — never fails the gate)
    vision_ok = sum(1 for e in cdoc.elements if e.method == "vision")
    skipped = cdoc.meta.get("vision_skipped", 0)
    checks.append(_check("vision", "pass",
                         f"{vision_ok} interpreted, {skipped} skipped"))

    fails = [c for c in checks if c["status"] == "fail"]
    warns = [c for c in checks if c["status"] == "warn"]
    verdict = FAILED if fails else (WARNING if warns else COMPLETE)
    reason = "; ".join(f"{c['name']}: {c['detail']}" for c in fails)
    log.info("Quality Gate %s For %s: %s", verdict, doc_id[:12], reason or "ok")
    return {"verdict": verdict, "checks": checks, "reason": reason}
