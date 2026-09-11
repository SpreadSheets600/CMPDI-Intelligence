"""AI Query & Response Engine. Routes each question to the right retrieval
strategy (numeric fact lookup vs hybrid semantic vs listing), assembles
evidence, and produces grounded answers with citations. Extractive mode
works with no LLM at all; abstention is a first-class outcome."""

import json
import logging
import re

from . import db, retrieval
from .llm import get_backend
from .normalize import detect_attribute, fy_label, normalize_period
from .pipeline.embedder import model_info

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
            # the entity name must appear inside the query, not merely share
            # common tokens like "coal"
            score = fuzz.partial_ratio(name.lower(), query.lower())
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
    key = (f"{top['canonical_name']}|{top['attribute']}|{top['period_norm']}|"
           f"{top['unit'] or ''}")
    conflict = db.q1("SELECT * FROM conflicts WHERE fact_key=? AND status='open'", (key,))
    return {"top": dict(top), "all": [dict(r) for r in current],
            "entity": entity_name, "attribute": top["attribute"],
            "period": fy_label(top["period_norm"]), "conflict": dict(conflict) if conflict else None}


def answer(query: str, filters: dict | None = None) -> dict:
    route = classify_query(query)
    backend = get_backend()
    payload = {
        "query": query, "route": route, "backend": backend.name,
        "answer": "", "citations": [], "conflicts": [], "abstained": False,
        "coverage": {},
    }

    fact = None
    if route == "NUMERIC_FACT":
        fact = fact_lookup(query)

    evidence = retrieval.hybrid_search(query, filters=filters)

    # abstention: measure the vector-score distribution — an irrelevant query
    # retrieves a flat, low-scoring pile; a relevant one has a clear top
    import numpy as np
    vres = retrieval.vector_search(query, k=15, filters=filters)
    if vres:
        vscores = np.array([e["vec"] for e in vres])
        weak = vscores[0] < 0.60 or vscores.std() < 0.03
    else:
        weak = evidence and evidence[0]["vec"] is None and not fact
    if weak and not fact:
        closest = evidence[:3]
        payload["abstained"] = True
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

    conflicts = _conflicts_touched(evidence)
    payload["conflicts"] = conflicts

    if fact and not fact["conflict"]:
        t = fact["top"]
        lead = (f"{fact['entity']} — {fact['attribute'].replace('_', ' ')} for {fact['period']}: "
                f"**{t['value_raw']}**{(' (' + str(t['unit']) + ')') if t['unit'] else ''}")
    elif fact and fact["conflict"]:
        vals = json.loads(fact["conflict"]["values_json"])
        parts = [f"**{v['value_raw']}** {v['unit'] or ''} (Document {v['doc_id'][:8]}…, "
                 f"page {v['page_no'] or ('sheet ' + str(v['sheet_no']))})" for v in vals]
        lead = ("Conflicting values found — human verification required: " + " vs ".join(parts))
    else:
        lead = None

    # numbered evidence blocks for the prompt
    blocks, citation_map = [], []
    for i, ev in enumerate(evidence, start=1):
        loc = f"page {ev['page_no']}" if ev["page_no"] else f"sheet {ev['sheet_no']}"
        blocks.append(f"[E{i}] ({ev['doc_title']}, {loc}, {ev['content_type']}) {ev['text'][:1200]}")
        citation_map.append({"eid": f"E{i}", "chunk_id": ev["chunk_id"],
                             "doc_id": ev["doc_id"], "doc_title": ev["doc_title"],
                             "page_no": ev["page_no"], "sheet_no": ev["sheet_no"],
                             "content_type": ev["content_type"], "text": ev["text"]})
    user_prompt = "Evidence:\n" + "\n\n".join(blocks) + f"\n\nQuestion: {query}"
    if lead:
        user_prompt += f"\n\nThe fact index resolved: {lead}. Use it and cite the matching evidence."

    generated = backend.generate(SYSTEM_PROMPT, user_prompt)
    if generated:
        cleaned = _validate_citations(generated, {c["eid"] for c in citation_map})
        payload["answer"] = cleaned
    else:
        # extractive mode: verbatim snippets, fully cited
        lines = []
        if lead:
            lines.append(lead + "\n")
        lines.append("Extractive Mode — supporting evidence from the indexed documents:")
        for c in citation_map[:4]:
            loc = f"page {c['page_no']}" if c["page_no"] else f"sheet {c['sheet_no']}"
            snippet = c["text"][:400] + ("…" if len(c["text"]) > 400 else "")
            lines.append(f"- [{c['eid']}] ({c['doc_title']}, {loc}): {snippet}")
        if conflicts:
            lines.append("Note: conflicting values were detected for some facts in this answer.")
        payload["answer"] = "\n".join(lines)
        payload["backend"] = backend.name if backend.name != "extractive" else "extractive"

    payload["citations"] = citation_map
    return payload


def _conflicts_touched(evidence) -> list[dict]:
    """Conflicts whose source facts come from chunks cited in this answer."""
    chunk_ids = {e["chunk_id"] for e in evidence}
    out = []
    for c in db.q("SELECT * FROM conflicts WHERE status='open'"):
        values = json.loads(c["values_json"])
        chunk_of = {}
        for v in values:
            row = db.q1("SELECT chunk_id FROM facts WHERE id=?", (v["fact_id"],))
            if row:
                chunk_of[v["fact_id"]] = row["chunk_id"]
        if any(cid in chunk_ids for cid in chunk_of.values()):
            out.append({"key": c["fact_key"], "conflict_id": c["id"], "fact_values": values})
    return out


def _validate_citations(text: str, allowed: set[str]) -> str:
    """Strip citations that don't map to provided evidence ids."""
    def repl(m):
        return m.group(0) if m.group(1) in allowed else ""
    return re.sub(r"\[(E\d+)\]", repl, text)
