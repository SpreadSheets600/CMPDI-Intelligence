"""Central tool registry. Every capability the LLM may invoke — retrieval,
deterministic analysis, evidence, workspace I/O — is a typed Tool registered
here. The ReAct agent (core/llm/agent.py) and the report director consume
the same catalog, so chat and reports share one runtime instead of two
disconnected agent systems.

A Tool is pure Python: the model sees name/description/args only, the host
owns the data. Numbers returned by analytical tools carry their formula and
inputs (the numerical truth layer); prose tools never compute.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

log = logging.getLogger("cmpdi.tools")


@dataclass
class Tool:
    name: str
    description: str
    args_schema: dict                      # {arg: "human type hint"}
    fn: object = field(repr=False)         # (args: dict) -> dict (JSON-safe)
    readonly: bool = True

    def run(self, args: dict) -> dict:
        try:
            out = self.fn(args or {})
            if not isinstance(out, dict):
                out = {"result": out}
            return {"ok": True, "tool": self.name, **out}
        except Exception as e:
            log.warning("Tool %s Failed: %s: %s", self.name,
                        type(e).__name__, e)
            return {"ok": False, "tool": self.name,
                    "error": f"{type(e).__name__}: {e}"}


_REGISTRY: dict[str, Tool] = {}


def register(tool: Tool) -> Tool:
    _REGISTRY[tool.name] = tool
    return tool


def get(name: str) -> Tool | None:
    return _REGISTRY.get(name)


def catalog() -> list[dict]:
    """Model-facing listing: name, description, args. No implementation."""
    return [{"name": t.name, "description": t.description,
             "args": t.args_schema} for t in _REGISTRY.values()]


def describe_for_prompt() -> str:
    lines = []
    for t in _REGISTRY.values():
        args = ", ".join(f"{k}: {v}" for k, v in t.args_schema.items())
        lines.append(f"- {t.name}  args: {{{args}}}\n  {t.description}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Deterministic analytical tools over the fact index. All arithmetic happens
# here in Python; every result records formula + inputs + source refs so the
# auditor can re-derive it without trusting prose.


def _calc(metric: str, value: float | None, unit: str, formula: str,
          inputs: dict, sources: list[dict]) -> dict:
    return {"calc": {"metric": metric, "value": value, "unit": unit,
                     "formula": formula, "inputs": inputs,
                     "sources": sources}}


def _fact_sources(df, limit: int = 4) -> list[dict]:
    out = []
    for _, r in df.head(limit).iterrows():
        try:
            pg = r.get("page_no")
            page_no = None if pg is None or pg != pg else int(pg)
        except Exception:
            page_no = None
        out.append({"doc_id": r.get("doc_id"), "filename": r.get("filename"),
                    "page_no": page_no,
                    "sheet_no": r.get("sheet_no"),
                    "value_raw": str(r.get("value_raw", "")),
                    "unit": r.get("unit")})
    return out


def _series(attribute: str, entity: str | None):
    from backend.core.reporting import content as rc
    df = rc.normalize_units(rc.fact_series(attribute, fiscal_only=True))
    if df.empty:
        return None
    df = rc.dedupe_series(df)
    df = df[df["entity"].notna() & (df["entity"] != "")]
    if df.empty:
        return None
    if entity:
        df = df[df["entity"] == entity]
    return df


def tool_calculate_growth(args: dict) -> dict:
    """YoY growth between the two latest fiscal periods, from data."""
    from backend.core.reporting import content as rc
    df = _series(args.get("attribute") or "production",
                 args.get("entity"))
    if df is None or df.empty or "fiscal" not in df:
        return {"error": "no data for this entity/metric"}
    piv = rc.pivot_by_year(df, last_n=6)
    cols = list(piv.columns)
    target = args.get("entity") or (cols[0] if cols else None)
    if not target or target not in piv.columns:
        return {"error": f"no series for {args.get('entity')}"}
    s = piv[target].dropna()
    if len(s) < 2:
        return {"error": "need two periods to compute growth"}
    cur, prev = float(s.iloc[-1]), float(s.iloc[-2])
    growth = (cur - prev) / prev * 100 if prev else None
    return _calc(
        "growth", round(growth, 2) if growth is not None else None, "%",
        f"({cur} - {prev}) / {prev} * 100",
        {"current": cur, "previous": prev,
         "current_period": str(s.index[-1]), "previous_period": str(s.index[-2]),
         "entity": target, "attribute": args.get("attribute") or "production"},
        _fact_sources(df[df["entity"] == target]))


def tool_compare_periods(args: dict) -> dict:
    """Entity values for two fiscal labels (e.g. 'FY2023-24'), with deltas."""
    from backend.core.reporting import content as rc
    df = _series(args.get("attribute") or "production", None)
    if df is None or df.empty:
        return {"error": "no data for this metric"}
    pa, pb = args.get("period_a"), args.get("period_b")
    if not pa or not pb:
        return {"error": "period_a and period_b are required (FY labels)"}
    da = df[df["fiscal"] == pa].set_index("entity")["value_norm"]
    dbb = df[df["fiscal"] == pb].set_index("entity")["value_norm"]
    rows = []
    for ent in sorted(set(da.index) | set(dbb.index)):
        a = float(da[ent]) if ent in da.index else None
        b = float(dbb[ent]) if ent in dbb.index else None
        delta = ((b - a) / a * 100) if (a and b) else None
        rows.append({"entity": ent, "period_a": a, "period_b": b,
                     "delta_pct": round(delta, 2) if delta is not None else None})
    return {"comparison": {"period_a": pa, "period_b": pb, "rows": rows},
            "formula": "(period_b - period_a) / period_a * 100",
            "sources": _fact_sources(df, 6)}


def tool_rank_entities(args: dict) -> dict:
    """Top/bottom N entities by metric in one fiscal period."""
    df = _series(args.get("attribute") or "production", None)
    if df is None or df.empty:
        return {"error": "no data for this metric"}
    period = args.get("period")
    if not period:
        period = sorted(df["fiscal"].unique())[-1]
    n = min(int(args.get("n") or 5), 20)
    sub = df[df["fiscal"] == period].sort_values("value_norm",
                                                 ascending=False)
    rows = [{"entity": r["entity"], "value": float(r["value_norm"])}
            for _, r in sub.head(n).iterrows()]
    return {"ranking": {"period": period, "order": "desc", "rows": rows},
            "sources": _fact_sources(sub)}


def tool_get_evidence(args: dict) -> dict:
    """Receipts for one entity/metric/period: exact chunks, no similarity."""
    from backend.db import database as db
    sql = ("SELECT f.value_raw, f.value_norm, f.unit, f.period_norm, "
           "d.filename, c.doc_id, c.page_no, c.sheet_no, c.id AS chunk_id "
           "FROM facts f JOIN chunks c ON c.id = f.chunk_id "
           "JOIN documents d ON d.id = c.doc_id "
           "LEFT JOIN entities e ON e.id = f.entity_id "
           "WHERE COALESCE(e.canonical_name, f.entity_text) = ? "
           "AND f.attribute = ?")
    params = [args.get("entity") or "", args.get("attribute") or ""]
    if args.get("period"):
        sql += " AND f.period_norm LIKE ?"
        params.append(f"%{args['period'][:4]}%")
    rows = [dict(r) for r in db.q(sql + " LIMIT 12", tuple(params))]
    return {"evidence": rows}


def tool_entity_summary(args: dict) -> dict:
    """Scope card for the working context: entities, periods, counts."""
    from backend.db import database as db
    q = (args.get("query") or "").strip()
    if q:
        ents = db.q("SELECT canonical_name FROM entities WHERE canonical_name "
                    "LIKE ? ORDER BY canonical_name LIMIT 25", (f"%{q}%",))
    else:
        ents = db.q("SELECT canonical_name FROM entities ORDER BY "
                    "canonical_name LIMIT 25")
    attrs = [r["attribute"] for r in db.q(
        "SELECT DISTINCT attribute FROM facts ORDER BY attribute")]
    periods = [r["period_norm"] for r in db.q(
        "SELECT DISTINCT period_norm FROM facts WHERE period_norm IS NOT NULL "
        "ORDER BY period_norm DESC LIMIT 12")]
    docs = db.q1("SELECT COUNT(*) c FROM documents WHERE status='completed'")
    return {"entities": [e["canonical_name"] for e in ents],
            "attributes": attrs, "periods": periods,
            "documents": docs["c"] if docs else 0}


register(Tool("calculate_growth",
              "Year-over-year growth for one entity+metric from the fact index. "
              "Returns value, formula and source receipts.",
              {"entity": "string", "attribute": "string, e.g. production"},
              tool_calculate_growth))
register(Tool("compare_periods",
              "Per-entity values and deltas between two fiscal labels "
              "(FY2023-24 style) for one metric.",
              {"attribute": "string", "period_a": "FY label",
               "period_b": "FY label"},
              tool_compare_periods))
register(Tool("rank_entities",
              "Top/bottom N entities by metric in one fiscal period.",
              {"attribute": "string", "period": "FY label, latest if empty",
               "n": "int"},
              tool_rank_entities))
register(Tool("get_evidence",
              "Exact receipts (document/page/chunk) for an entity+metric, "
              "optionally one period. No semantic guessing.",
              {"entity": "string", "attribute": "string",
               "period": "optional year"},
              tool_get_evidence))
register(Tool("entity_summary",
              "Scope card: known entities, metrics, periods, library size. "
              "Use it to ground the working context before planning.",
              {"query": "optional entity substring"},
              tool_entity_summary))
