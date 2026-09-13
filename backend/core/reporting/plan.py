"""Report Plan IR. The planner turns (objective, working context) into an
inspectable plan; the director executes it section by section. Plans are
data, not prose, so the UI can show them before generation and the auditor
can check every section got what it required.

Section types: narrative | analysis | visual_analysis | table | verification.
"""

from __future__ import annotations

import logging

log = logging.getLogger("cmpdi.plan")

SECTION_TYPES = ("narrative", "analysis", "visual_analysis", "table",
                 "verification")


def deterministic_plan(objective: str, context: dict) -> dict:
    """Template plan from scope alone. Used when no generative backend is
    available (SIMPLE mode) and as the fallback when planning fails."""
    scope = context.get("scope", {})
    entity = scope.get("entity")
    metrics = [m for m in context.get("metrics", [])
               if m in ("production", "offtake", "dispatch", "reserves")]
    sections = [{"id": "executive_summary", "type": "narrative",
                 "title": "Executive Summary"}]
    for m in metrics[:3]:
        sections.append({"id": f"{m}_trend", "type": "visual_analysis",
                         "title": f"{m.replace('_', ' ').title()} trend",
                         "metric": m, "entity": entity,
                         "analysis": "year_over_year"})
    sections.append({"id": "verification", "type": "verification",
                     "title": "Verification Notes"})
    return {"title": objective[:120] or "Analytical Report",
            "scope": {"entity": entity, "metrics": metrics},
            "sections": sections,
            "required_data": [{"metric": m, "entity": entity} for m in metrics[:3]],
            "required_charts": [s["id"] for s in sections
                                if s["type"] == "visual_analysis"],
            "evidence_requirements": ["every numeric claim has a source ref"],
            "planned_by": "deterministic"}


_PLAN_SCHEMA_HINT = """Reply with JSON only: {"title": str, "sections": \
[{"id": str, "type": one of narrative|analysis|visual_analysis|table|\
verification, "title": str, "metric": optional str, "entity": optional str, \
"analysis": optional str}], "required_data": [{"metric": str, "entity": \
str|null}], "required_charts": [section ids]}. Max 7 sections."""


def plan_with_llm(objective: str, context: dict, provider) -> dict:
    """Ask the orchestrator model for a plan; validate and repair it."""
    import json as _json
    summary = (f"entities: {', '.join(context.get('entities', [])[:20])}; "
               f"metrics: {', '.join(context.get('metrics', [])[:15])}; "
               f"periods: {', '.join(context.get('periods', [])[:8])}; "
               f"documents: {context.get('library', {}).get('documents', 0)}; "
               f"known conflicts: {len(context.get('known_conflicts', []))}")
    parsed, resp = provider.complete_json(
        "You plan analytical coal-industry reports. " + _PLAN_SCHEMA_HINT,
        f"Objective: {objective}\nScope: {_json.dumps(context.get('scope', {}))}\n"
        f"Library: {summary}")
    if not parsed or not isinstance(parsed.get("sections"), list):
        log.info("Plan Fell Back To Deterministic: %s",
                 resp.error.message if resp.error else "bad plan")
        plan = deterministic_plan(objective, context)
        plan["planned_by"] = "deterministic (llm plan invalid)"
        return plan
    sections = []
    for s in parsed["sections"][:7]:
        if not isinstance(s, dict) or s.get("type") not in SECTION_TYPES:
            continue
        sections.append({"id": str(s.get("id") or s.get("title") or "section"),
                         "type": s["type"],
                         "title": str(s.get("title") or s["type"]),
                         "metric": s.get("metric"), "entity": s.get("entity"),
                         "analysis": s.get("analysis")})
    if not sections:
        plan = deterministic_plan(objective, context)
        plan["planned_by"] = "deterministic (llm plan empty)"
        return plan
    metrics = context.get("metrics", [])
    return {"title": str(parsed.get("title") or objective[:120]),
            "scope": context.get("scope", {}),
            "sections": sections,
            "required_data": [{"metric": s.get("metric"),
                               "entity": s.get("entity")}
                              for s in sections if s.get("metric")]
            or [{"metric": m, "entity": context.get("scope", {}).get("entity")}
                for m in metrics[:2]],
            "required_charts": [s["id"] for s in sections
                                if s["type"] == "visual_analysis"],
            "evidence_requirements": ["every numeric claim has a source ref"],
            "planned_by": provider.provider_id}
