"""AI query and response engine. Routes each question to the right retrieval
strategy (numeric fact lookup, hybrid semantic, or listing), assembles
evidence, and produces grounded answers with citations. Extractive mode works
with no LLM installed; when evidence is weak the engine abstains instead of
guessing."""

import json
import logging
import re

from backend.core import retrieval
from backend.db import database as db
from backend.core.llm import get_backend
from backend.core.quality import trust
from backend.core.normalize import detect_attribute, fy_label, normalize_period
from backend.core.pipeline.embedder import model_info

log = logging.getLogger("cmpdi.query")

SYSTEM_PROMPT = """You are a geological and mining reporting assistant for CMPDI/CIL.
Rules:
- Answer ONLY from the numbered evidence excerpts provided.
- Cite evidence ids in square brackets, e.g. [E2], after every claim you make.
- If the evidence is insufficient, reply exactly: "Insufficient evidence in the indexed documents."
- Never merge or average conflicting numbers; report each value with its source.
- Be concise and factual. No speculation."""


def classify_query(query: str) -> str:
    low = query.lower()
    if re.match(r"^\s*(list|enumerate|name)\b", low) or low.startswith("how many"):
        return "LISTING"
    if detect_attribute(query) or re.search(r"\bFY\s*\d{2,4}\b|\b(19|20)\d{2}\s*[-–]\s*\d{2,4}\b", query, re.I):
        return "NUMERIC_FACT"
    return "SEMANTIC"


def _fuzzy_entity(query: str) -> tuple[int | None, str | None]:
    from rapidfuzz import fuzz
    ents = db.q("SELECT id, canonical_name, aliases_json FROM entities")
    best_id, best_name, best_score = None, None, 0
    for e in ents:
        names = [e["canonical_name"]] + json.loads(e["aliases_json"] or "[]")
        for name in names:
            if name.isupper() and len(name) <= 6:
                # abbreviations need a word boundary so "ECL" never matches
                # inside "SECL"
                score = 100 if re.search(rf"\b{re.escape(name)}\b", query) else 0
            else:
                score = fuzz.partial_ratio(name.lower(), query.lower())
                score = score if score >= 90 else 0
            if score > best_score:
                best_id, best_name, best_score = e["id"], name, score
    if best_score >= 90:
        return best_id, best_name
    return None, None


def fact_lookup(query: str) -> dict | None:
    """Exact numeric answer from the fact index, with receipts and conflicts."""
    entity_id, entity_name = _fuzzy_entity(query)
    attr = detect_attribute(query)
    period = normalize_period(query)
    if not attr and not entity_id:
        return None
    where, params = ["1=1"], []
    if entity_id:
        where.append("f.entity_id = ?")
        params.append(entity_id)
    if attr:
        where.append("f.attribute = ?")
        params.append(attr)
    if period:
        where.append("f.period_norm = ?")
        params.append(period)
    where.append("f.value_norm IS NOT NULL")
    rows = db.q(f"""
        SELECT f.*, e.canonical_name, c.doc_id, c.page_no, c.sheet_no, c.section_path,
               c.element_ids_json, d.filename, d.is_current_version
        FROM facts f
        JOIN entities e ON e.id = f.entity_id
        JOIN chunks c ON c.id = f.chunk_id
        JOIN documents d ON d.id = c.doc_id
        WHERE {" AND ".join(where)}
        ORDER BY d.is_current_version DESC, f.conf DESC, c.rowid DESC
        LIMIT 12
    """, params)
    if not rows:
        return None
    current = [r for r in rows if r["is_current_version"]] or rows
    top = current[0]
    # every distinct reported value for the same (entity, attribute, period),
    # kept with its receipt; differing sources are shown, never averaged
    seen_values = {round(top["value_norm"], 6)}
    alternatives = []
    for r in current[1:]:
        v = round(r["value_norm"], 6)
        if v not in seen_values:
            seen_values.add(v)
            alternatives.append(dict(r))
    return {"top": dict(top), "all": [dict(r) for r in current],
            "entity": entity_name, "attribute": top["attribute"],
            "period": fy_label(top["period_norm"]), "alternatives": alternatives}


def condense_question(query: str, history: list[dict] | None) -> str:
    """Rewrite a follow-up question ('which document says that?') into a
    standalone query using the chat history. Falls back to appending the
    previous user message when no LLM is available."""
    if not history:
        return query
    backend = get_backend()
    turns = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in history[-6:])
    raw = backend.generate(
        "You rewrite follow-up questions as standalone search queries. Reply "
        "with the rewritten query only.",
        f"Rewrite the last question as a standalone search query that keeps "
        f"the entities it refers to from the earlier conversation.\n\n"
        f"Conversation:\n{turns}\n\nLast question: {query}",
    )
    if raw and 2 < len(raw.strip()) < 300:
        return raw.strip()
    prior_user = next((m["content"] for m in reversed(history)
                       if m["role"] == "user"), "")
    return f"{prior_user} {query}".strip()


def answer(query: str, filters: dict | None = None,
           history: list[dict] | None = None) -> dict:
    """Answer a question. `history` carries prior chat turns
    ([{role, content}, ...]); follow-up questions are condensed into
    standalone search queries using that history."""
    backend = get_backend()
    retrieval_query = condense_question(query, history) if history else query
    route = classify_query(retrieval_query)
    payload = {
        "query": query, "route": route, "backend": backend.name,
        "answer": "", "citations": [], "conflicts": [], "abstained": False,
        "coverage": {},
    }

    fact = None
    if route == "NUMERIC_FACT":
        fact = fact_lookup(retrieval_query)

    evidence = retrieval.hybrid_search(retrieval_query, filters=filters)

    # Abstention: measure the vector-score distribution. An irrelevant query
    # retrieves a flat, low-scoring pile; a relevant one has a clear top.
    import numpy as np
    vres = retrieval.vector_search(retrieval_query, k=15, filters=filters)
    if vres:
        vscores = np.array([e["vec"] for e in vres])
        # abstain on a low top score, or on a flat distribution that never
        # rises clearly above the corpus baseline (statistical tables score
        # uniformly ~0.78 even for irrelevant wording, so flatness alone
        # is not evidence of a miss)
        weak = vscores[0] < 0.60 or (vscores.std() < 0.03 and vscores[0] < 0.75)
    else:
        weak = evidence and evidence[0]["vec"] is None and not fact
    if weak and not fact:
        closest = evidence[:3]
        payload["abstained"] = True
        payload["quality"] = trust.grade(None, [], None, abstained=True)
        payload["why"] = trust.why(route, None, evidence, [], None, backend.name,
                                   "abstained")
        payload["answer"] = ("Insufficient evidence in the indexed documents for this question.\n"
                             "Closest matches found (low confidence):")
        payload["citations"] = [
            {"eid": f"E{i}", "chunk_id": ev["chunk_id"], "doc_id": ev["doc_id"],
             "doc_title": ev["doc_title"], "page_no": ev["page_no"],
             "sheet_no": ev["sheet_no"], "content_type": ev["content_type"],
             "text": ev["text"]}
            for i, ev in enumerate(closest, start=1)]
        return payload

    # a fact hit always joins the evidence set with its own chunk
    if fact:
        frow = db.q1("""SELECT c.id, c.doc_id, c.page_no, c.sheet_no, c.content_type,
                        c.section_path, c.text, c.element_ids_json, d.filename, d.doc_type,
                        d.subsidiary FROM chunks c JOIN documents d ON d.id=c.doc_id WHERE c.id=?""",
                     (fact["top"]["chunk_id"],))
        if frow and all(e["chunk_id"] != frow["id"] for e in evidence):
            evidence.insert(0, retrieval._evidence(frow))

    if not evidence:
        payload["abstained"] = True
        payload["answer"] = ("No supporting evidence found in the indexed documents. "
                             "Upload relevant reports and try again.")
        return payload

    model_name, dim = model_info()
    payload["coverage"] = {"evidence_count": len(evidence), "embedding_model": model_name}

    alternatives = _alternatives_for_evidence(evidence)
    payload["alternatives"] = alternatives

    # numbered evidence blocks for the prompt
    blocks, citation_map = [], []
    for i, ev in enumerate(evidence, start=1):
        loc = f"page {ev['page_no']}" if ev["page_no"] else f"sheet {ev['sheet_no']}"
        blocks.append(f"[E{i}] ({ev['doc_title']}, {loc}, {ev['content_type']}) {ev['text'][:1200]}")
        citation_map.append({"eid": f"E{i}", "chunk_id": ev["chunk_id"],
                             "doc_id": ev["doc_id"], "doc_title": ev["doc_title"],
                             "doc_type": ev.get("doc_type"),
                             "page_no": ev["page_no"], "sheet_no": ev["sheet_no"],
                             "content_type": ev["content_type"], "text": ev["text"]})

    # a resolved fact answers deterministically: the value was extracted from
    # a cited cell, so no generation step is allowed to muddy it
    if fact:
        t = fact["top"]
        eid = next((c["eid"] for c in citation_map
                    if c["chunk_id"] == fact["top"]["chunk_id"]), "E1")
        loc = f"page {t['page_no']}" if t["page_no"] else f"sheet {t['sheet_no']}"
        val = t["value_raw"]
        if t["unit"] and not any(ch.isalpha() for ch in val):
            val = f"{val} {t['unit']}"
        t_conf = t.get("conf")
        for c in citation_map:
            if c["chunk_id"] == fact["top"].get("chunk_id") and t_conf is not None:
                c["conf"] = round(float(t_conf) * 100, 1)
        lines = [f"**{val}** — {fact['entity']} {fact['attribute'].replace('_', ' ')} "
                 f"for {fact['period']}, reported in {t['filename']}, {loc} [{eid}]"]
        if fact["alternatives"]:
            alts = ", ".join(
                f"**{a['value_raw']}** ({a['filename']}, "
                f"{'page ' + str(a['page_no']) if a['page_no'] else 'sheet ' + str(a['sheet_no'])})"
                for a in fact["alternatives"][:3])
            lines.append(f"Also reported elsewhere: {alts}.")
        payload["answer"] = "\n".join(lines)
        payload["citations"] = citation_map
        payload["fact"] = fact
        payload["alternatives"] = _alternatives_for_evidence(evidence)
        payload["quality"] = trust.grade(fact, citation_map, payload["alternatives"])
        payload["why"] = trust.why(route, fact, evidence, citation_map,
                                   payload["alternatives"], backend.name,
                                   "deterministic fact resolution")
        return payload

    user_prompt = "Evidence:\n" + "\n\n".join(blocks) + f"\n\nQuestion: {query}"
    if history:
        turns = "\n".join(f"{m['role']}: {m['content'][:300]}"
                          for m in history[-6:] if m.get("content"))
        user_prompt += f"\n\nEarlier conversation (for context only):\n{turns}"

    generated = backend.generate(SYSTEM_PROMPT, user_prompt)
    if generated:
        cleaned = _validate_citations(generated, {c["eid"] for c in citation_map})
        payload["answer"] = cleaned
    else:
        # extractive mode: verbatim snippets, fully cited
        lines = ["Extractive mode: supporting evidence from the indexed documents."]
        for c in citation_map[:4]:
            loc = f"page {c['page_no']}" if c["page_no"] else f"sheet {c['sheet_no']}"
            snippet = c["text"][:400] + ("…" if len(c["text"]) > 400 else "")
            lines.append(f"- [{c['eid']}] ({c['doc_title']}, {loc}): {snippet}")
        if alternatives:
            lines.append("Note: some facts in this answer are reported differently across documents.")
        payload["answer"] = "\n".join(lines)
        payload["backend"] = backend.name if backend.name != "extractive" else "extractive"

    payload["citations"] = citation_map
    payload["quality"] = trust.grade(None, citation_map, alternatives)
    payload["why"] = trust.why(
        route, fact, evidence, citation_map, alternatives, backend.name,
        "extractive evidence" if not generated else "grounded generation")
    return payload


def _alternatives_for_evidence(evidence) -> list[dict]:
    """Facts grounded in this answer whose (entity, attribute, period) is
    reported differently in other documents; each alternative keeps its
    receipt so the reader can compare sources directly."""
    chunk_ids = [e["chunk_id"] for e in evidence]
    marks = ",".join("?" * len(chunk_ids))
    cited = db.q(f"""SELECT f.id, f.entity_id, f.attribute, f.period_norm, f.value_norm,
                            e.canonical_name
                     FROM facts f JOIN entities e ON e.id = f.entity_id
                     WHERE f.chunk_id IN ({marks})
                       AND f.entity_id IS NOT NULL AND f.attribute != 'quantity'
                       AND f.value_norm IS NOT NULL AND f.period_norm IS NOT NULL""",
                 chunk_ids)
    out, seen = [], set()
    for f in cited:
        key = (f["entity_id"], f["attribute"], f["period_norm"])
        if key in seen:
            continue
        seen.add(key)
        others = db.q("""SELECT f.*, d.filename FROM facts f
                         JOIN chunks c ON c.id = f.chunk_id
                         JOIN documents d ON d.id = c.doc_id
                         WHERE f.entity_id = ? AND f.attribute = ? AND f.period_norm = ?
                           AND f.value_norm IS NOT NULL
                         ORDER BY d.is_current_version DESC LIMIT 5""",
                      (f["entity_id"], f["attribute"], f["period_norm"]))
        differing = [dict(o) for o in others
                     if abs(o["value_norm"] - f["value_norm"])
                     > max(0.01, 0.01 * abs(f["value_norm"]))]
        if differing:
            out.append({"key": f"{f['canonical_name']}|{f['attribute']}|{f['period_norm']}",
                        "fact_values": differing})
    return out


def _validate_citations(text: str, allowed: set[str]) -> str:
    """Strip citations that don't map to provided evidence ids."""
    def repl(m):
        return m.group(0) if m.group(1) in allowed else ""
    return re.sub(r"\[(E\d+)\]", repl, text)
