"""The analytical agent. A model-agnostic ReAct loop: the LLM proposes one
JSON action per turn (search_documents, get_facts, run_python, finish), the
host executes it and feeds the observation back. Anything computational goes
through the sandboxed Python tool so numbers are computed, never hallucinated.
Without a generation backend the agent degrades to direct retrieval answers."""

import json
import logging
import re
import uuid
from pathlib import Path

from backend.core import config, retrieval
from backend.core.llm import get_backend
from backend.db import database as db

log = logging.getLogger("cmpdi.agent")

MAX_STEPS = 8

SYSTEM_PROMPT = """You are CMPDI Intelligence Agent, an analytical agent over an offline \
coal-industry document corpus (PDFs, Word, Excel, CSV). You reason step by step and use tools.

Each turn you output EXACTLY ONE JSON object, no other text:
{"thought": "brief reasoning", "tool": "<name>", "args": { ... }}

Tools:
- search_documents  args: {"query": string, "tag": optional, "subsidiary": optional}
  Hybrid semantic+keyword search; returns chunks with document, page and score.
- get_facts         args: {"entity": optional, "attribute": optional, "period": optional}
  Numeric fact index (production, offtake, reserves, gcv, ash_pct...) with receipts.
- run_python        args: {"code": string}
  Sandboxed pandas/numpy/matplotlib. Preloaded: pd, np, plt, load_table(doc_id, sheet_no=None),
  load_facts(entity=None, attribute=None). Save NO files; every plt figure is captured
  automatically. Print or leave a final expression to return a value.
- finish            args: {"answer": string}
  The final answer in markdown. Cite evidence inline as [E1], [E2] matching the
  numbered evidence entries you received. State computations as derived results and
  document facts as cited facts; if information is missing, say so plainly.

Rules:
- Never invent numbers. Compute with run_python; look up reported values with get_facts.
- Any comparison, share, trend, aggregate or chart MUST go through run_python
  (load_facts()/load_table() give you DataFrames). Do not compute in your head.
- When a question spans several entities, pull all matching facts at once
  (omit the entity filter) and group them in pandas instead of searching pages.
- Compare values across documents before claiming a trend.
- Finish within %d tool calls; make each call count.""" % MAX_STEPS


# ---------------------------------------------------------------- tools

def _tool_search(args: dict) -> tuple[str, list[dict]]:
    hits = retrieval.hybrid_search(
        args.get("query") or "", k=min(int(args.get("k") or 6), 10),
        filters={k: args[k] for k in ("tag", "subsidiary") if args.get(k)})
    if not hits:
        return "No documents matched.", []
    out = []
    for h in hits:
        loc = f"page {h['page_no']}" if h.get("page_no") else f"sheet {h.get('sheet_no')}"
        out.append(f"[score {h['score']:.3f}] {h['filename']} ({loc}): {h['text'][:400]}")
    return "\n---\n".join(out), _evidence_from_search(hits)


def _tool_facts(args: dict) -> str:
    sql = ("SELECT f.entity_text, e.canonical_name, f.attribute, f.period_norm, f.value_raw,"
           " f.value_norm, f.unit, f.flags, c.doc_id, c.page_no, c.sheet_no, d.filename"
           " FROM facts f LEFT JOIN entities e ON e.id=f.entity_id"
           " LEFT JOIN chunks c ON c.id=f.chunk_id LEFT JOIN documents d ON d.id=c.doc_id"
           " WHERE 1=1")
    params = []
    for col, key in [("e.canonical_name", "entity"), ("f.attribute", "attribute"),
                     ("f.period_norm", "period")]:
        if args.get(key):
            sql += f" AND {col} LIKE ?"
            params.append(f"%{args[key]}%")
    rows = [dict(r) for r in db.q(sql + " ORDER BY f.period_norm LIMIT 60", tuple(params))]
    if not rows:
        return "No facts matched; try search_documents to find the table instead."
    for r in rows:
        r["entity"] = r.pop("canonical_name") or r.pop("entity_text")
    return json.dumps(rows, default=str)


def _tool_python(args: dict, run_dir: Path) -> tuple[str, list[str]]:
    import os
    import subprocess
    import sys
    env = {**os.environ,
           "CMPDI_DB_PATH": str(config.DB_PATH),
           "CMPDI_RUN_DIR": str(run_dir)}
    try:
        proc = subprocess.run(
            # -E keeps PYTHON* env out; the runner applies its own import
            # blacklist because -I would also hide the venv's site-packages
            [sys.executable, "-E", str(Path(__file__).parent / "agent_runner.py")],
            input=args.get("code") or "", capture_output=True, text=True,
            timeout=60, cwd=run_dir, env=env)
    except subprocess.TimeoutExpired:
        return "Execution Timed Out (60s)", []
    if proc.returncode != 0 or not proc.stdout.strip():
        tail = (proc.stderr or "")[-1500:]
        return f"Runner Error: {tail or proc.returncode}", []
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        return f"Runner Error: unreadable output {proc.stdout[-300:]}", []
    parts = []
    if data["stdout"]:
        parts.append(f"stdout:\n{data['stdout']}")
    if data["error"]:
        parts.append(f"error: {data['error']}")
    if data["result"] is not None:
        parts.append(f"result: {data['result']}")
    return ("\n".join(parts) or "Completed with no output."), data["figures"]


# ---------------------------------------------------------------- loop

def _extract_json(text: str) -> dict | None:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def _evidence_from_search(hits: list[dict]) -> list[dict]:
    out = []
    for h in hits:
        out.append({"doc_id": h["doc_id"], "filename": h["filename"],
                    "page_no": h.get("page_no"), "sheet_no": h.get("sheet_no"),
                    "snippet": h["text"][:300]})
    return out


def run_task(task: str) -> dict:
    """Runs the full agent loop. Returns {steps, answer, evidence, run_id}.
    Each step: {type: thought|tool|observation|chart, ...} in display order."""
    run_id = uuid.uuid4().hex[:12]
    run_dir = config.DATA_DIR / "agent_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    steps: list[dict] = []
    evidence: list[dict] = []
    figure_refs: list[dict] = []
    transcript = f"Task: {task}\n"
    answer = None
    backend = get_backend()

    if backend.name == "extractive":
        # no generation: fall back to the direct RAG answer path
        from backend.core import query as qmod
        result = qmod.answer(task)
        steps.append({"type": "note",
                      "text": "No language backend is reachable, so the agent answered "
                              "directly from retrieval without multi-step reasoning."})
        return {"run_id": run_id, "steps": steps, "answer": result["answer"],
                "evidence": result.get("evidence", []), "figures": []}

    for step_no in range(MAX_STEPS):
        user = transcript + "\nEvidence so far (cite these):\n" + (
            "\n".join(f"[E{i + 1}] {e['filename']} "
                      f"{'page ' + str(e['page_no']) if e.get('page_no') else 'sheet ' + str(e['sheet_no'])}: "
                      f"{e['snippet'][:150]}"
                      for i, e in enumerate(evidence)) or "(none yet)")
        raw = backend.generate(SYSTEM_PROMPT, user)
        action = _extract_json(raw or "")
        if action is None:
            steps.append({"type": "note", "text": "The model did not return a valid action; "
                                                  "ending the run."})
            break
        steps.append({"type": "thought", "text": action.get("thought", "")})
        tool = action.get("tool")
        args = action.get("args") or {}
        if tool == "finish":
            answer = args.get("answer") or ""
            break
        steps.append({"type": "tool", "tool": tool, "args": args})

        if tool == "search_documents":
            observation, hits_evidence = _tool_search(args)
            evidence.extend(hits_evidence)
        elif tool == "get_facts":
            observation = _tool_facts(args)
            if observation.startswith("["):
                for r in json.loads(observation):
                    evidence.append({"doc_id": r["doc_id"], "filename": r["filename"],
                                     "page_no": r.get("page_no"), "sheet_no": r.get("sheet_no"),
                                     "snippet": f"{r['entity']} {r['attribute']} {r['period_norm']}: "
                                                f"{r['value_raw']} {r['unit'] or ''}".strip()})
        elif tool == "run_python":
            observation, figures = _tool_python(args, run_dir)
            for f in figures:
                figure_refs.append({"run_id": run_id, "file": f})
                steps.append({"type": "chart", "src": f"/agent/figure/{run_id}/{f}"})
        else:
            observation = f"Unknown tool '{tool}'; available: search_documents, get_facts, run_python, finish."
        steps.append({"type": "observation",
                      "tool": tool, "text": observation[:2500]})
        transcript += f"\nAction: {json.dumps(action, default=str)[:600]}\nObservation: {observation[:2500]}\n"

    if answer is None:
        answer = ("I could not complete this task within the step budget. The trace above "
                  "shows what was checked; try narrowing the request.")

    # deduplicate evidence, keep what the answer cites, and renumber the
    # markers so [E#] in the answer matches the returned evidence order
    seen, unique = set(), []
    for e in evidence:
        key = (e["doc_id"], e.get("page_no"), e.get("sheet_no"))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    cited = set(re.findall(r"\[E(\d+)\]", answer))
    filtered = [e for i, e in enumerate(unique, 1) if str(i) in cited]
    if filtered:
        remap = {str(i): str(j) for j, i in
                 enumerate((i for i, e in enumerate(unique, 1) if str(i) in cited), 1)}
        answer = re.sub(r"\[E(\d+)\]",
                        lambda m: f"[E{remap.get(m.group(1), m.group(1))}]", answer)
        evidence = filtered
    else:
        evidence = unique[:8]

    row_id = _persist_run(task, steps, answer, evidence)
    return {"run_id": run_id, "row_id": row_id, "steps": steps, "answer": answer,
            "evidence": evidence, "figures": figure_refs}


def _persist_run(task, steps, answer, evidence) -> int:
    return db.execute(
        "INSERT INTO agent_runs (task, steps_json, answer, citations_json) VALUES (?,?,?,?)",
        (task, json.dumps(steps), answer, json.dumps(evidence)))


def recent_runs(limit: int = 8) -> list[dict]:
    return [dict(r) for r in db.q(
        "SELECT id, task, answer, created_ts FROM agent_runs ORDER BY id DESC LIMIT ?", (limit,))]


def get_run(run_id: int) -> dict | None:
    row = db.q1("SELECT * FROM agent_runs WHERE id=?", (run_id,))
    if not row:
        return None
    return {**dict(row), "steps": json.loads(row["steps_json"]),
            "citations": json.loads(row["citations_json"] or "[]")}
