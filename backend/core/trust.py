"""Evidence trust layer. Grades the evidence behind every answer with
checkable facts (source count, independent documents, conflicts, OCR
provenance, exact fact match) instead of a made-up confidence percentage,
and records the reasoning trail for the "Why this answer?" panel."""

from backend.db import database as db

_ocr_docs: set[str] | None = None


def _ocr_set() -> set[str]:
    global _ocr_docs
    if _ocr_docs is None:
        _ocr_docs = {r["id"] for r in db.q(
            "SELECT id FROM documents WHERE ocr_pages > 0")}
    return _ocr_docs


def reset_cache():
    global _ocr_docs
    _ocr_docs = None


def grade(fact: dict | None, citations: list[dict],
          alternatives: list | None, abstained: bool = False) -> dict:
    """Evidence Quality for an answer: HIGH / MEDIUM / LOW with the check
    list that justifies it. No invented percentages."""
    n_sources = len(citations)
    n_docs = len({c["doc_id"] for c in citations if c.get("doc_id")})
    ocr_used = [c for c in citations if c.get("doc_id") in _ocr_set()]
    n_conflicts = len(alternatives or [])
    if fact:
        n_conflicts += len(fact.get("alternatives", []))
    exact = fact is not None

    checks: list[tuple[str, str]] = []
    checks.append((
        "ok" if n_sources >= 2 else ("warn" if n_sources == 1 else "bad"),
        f"{n_sources} supporting source{'s' if n_sources != 1 else ''}"))
    checks.append((
        "ok" if n_docs >= 2 else "warn",
        f"{n_docs} independent document{'s' if n_docs != 1 else ''}"))
    checks.append((
        "ok" if n_conflicts == 0 else "warn",
        "no conflicting values" if n_conflicts == 0
        else f"{n_conflicts} conflicting value{'s' if n_conflicts != 1 else ''} reported elsewhere"))
    checks.append((
        "warn" if ocr_used else "ok",
        f"{len(ocr_used)} source{'s' if len(ocr_used) != 1 else ''} OCR-derived"
        if ocr_used else "no OCR-derived sources"))
    checks.append((
        "ok" if exact else "warn",
        "exact fact-index match" if exact else "semantic match only"))

    if abstained or n_sources == 0:
        level = "LOW"
    elif exact and n_conflicts == 0 and n_sources >= 2 and not ocr_used:
        level = "HIGH"
    elif exact or (n_sources >= 2 and n_conflicts == 0):
        level = "MEDIUM"
    else:
        level = "LOW"
    return {"level": level, "checks": checks, "exact_match": exact,
            "conflicts": n_conflicts, "sources": n_sources, "documents": n_docs}


def coverage(citations: list[dict], evidence_count: int) -> dict:
    """Source Coverage: how much of the retrieved pool the answer actually
    stands on, and how many documents confirm it independently."""
    used_docs = {c["doc_id"] for c in citations if c.get("doc_id")}
    n = len(used_docs)
    level = "HIGH" if n >= 3 else "MEDIUM" if n == 2 else "LOW" if n == 1 else "NONE"
    return {"evidence_retrieved": evidence_count, "sources_used": len(citations),
            "independent_documents": n, "level": level}


def why(route: str, fact: dict | None, evidence: list, citations: list[dict],
        alternatives: list | None, backend_name: str,
        generation: str) -> dict:
    """The reasoning trail for 'Why did you answer this?'."""
    return {
        "route": route,
        "chunks_retrieved": len(evidence),
        "documents_represented": len({e["doc_id"] for e in evidence}),
        "facts_matched": len(fact["all"]) if fact else 0,
        "sources_cited": len(citations),
        "conflicts": (len(alternatives or []) + (len(fact.get("alternatives", [])) if fact else 0)),
        "llm": backend_name,
        "generation": generation,
    }
