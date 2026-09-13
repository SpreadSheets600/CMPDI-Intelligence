"""Deterministic analyst. Controlled analytical tools over the fact index —
the model sees compare_periods-style operations, never raw groupby chains.
Every result is a calc record {metric, value, unit, formula, inputs,
sources} that the evidence graph stores and the auditor re-derives.

Underneath: pandas over the normalized fact series (content.py). The
sandboxed run_python tool remains the escape hatch for bespoke analysis.
"""

from __future__ import annotations


def _page(v):
    try:
        return None if v is None or v != v else int(v)  # NaN-safe
    except Exception:
        return None


def _sources(df, limit: int = 4) -> list[dict]:
    out = []
    for _, r in df.head(limit).iterrows():
        out.append({"doc_id": r.get("doc_id"), "filename": r.get("filename"),
                    "page_no": _page(r.get("page_no")),
                    "sheet_no": r.get("sheet_no"),
                    "value_raw": str(r.get("value_raw", "")),
                    "unit": r.get("unit")})
    return out


def _frame(attribute: str, entity: str | None = None):
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
        if df.empty:
            return None
    return df


def _without_partial(s, threshold: float = 0.5):
    """Drop a trailing partial-year point (mid-year cutoff reads as a
    collapse); returns (series, excluded_label_or_None)."""
    if len(s) >= 2 and s.iloc[-1] < s.iloc[-2] * threshold:
        return s.iloc[:-1], str(s.index[-1])
    return s, None


def growth(attribute: str, entity: str) -> dict:
    """Latest YoY growth for one entity+metric."""
    from backend.core.reporting import content as rc
    df = _frame(attribute, entity)
    if df is None or "fiscal" not in df:
        return {"metric": "growth", "value": None, "unit": "%",
                "formula": "n/a", "inputs": {}, "sources": [],
                "error": "no data"}
    piv = rc.pivot_by_year(df, last_n=6)
    if entity not in piv.columns:
        return {"metric": "growth", "value": None, "unit": "%",
                "formula": "n/a", "inputs": {}, "sources": [],
                "error": "no series"}
    s = piv[entity].dropna()
    s, partial = _without_partial(s)
    if len(s) < 2:
        return {"metric": "growth", "value": None, "unit": "%",
                "formula": "n/a",
                "inputs": {"periods": [str(i) for i in s.index]},
                "sources": _sources(df), "error": "need two periods"}
    cur, prev = float(s.iloc[-1]), float(s.iloc[-2])
    val = (cur - prev) / prev * 100 if prev else None
    inputs = {"current": cur, "previous": prev,
              "current_period": str(s.index[-1]),
              "previous_period": str(s.index[-2]),
              "entity": entity, "attribute": attribute}
    if partial:
        inputs["partial_year_excluded"] = partial
    return {"metric": "growth", "value": round(val, 2) if val is not None else None,
            "unit": "%", "formula": f"({cur} - {prev}) / {prev} * 100",
            "inputs": inputs,
            "sources": _sources(df[df["entity"] == entity])}


def achievement(attribute: str, entity: str, target: float,
                period: str) -> dict:
    """Actual vs target for one entity/metric/period."""
    df = _frame(attribute, entity)
    rows = df[df["fiscal"] == period] if df is not None and "fiscal" in df else None
    if rows is None or rows.empty:
        return {"metric": "achievement", "value": None, "unit": "%",
                "formula": "n/a", "inputs": {"target": target},
                "sources": [], "error": "no actuals"}
    actual = float(rows.iloc[0]["value_norm"])
    val = actual / target * 100 if target else None
    return {"metric": "achievement",
            "value": round(val, 2) if val is not None else None, "unit": "%",
            "formula": f"{actual} / {target} * 100",
            "inputs": {"actual": actual, "target": target, "period": period,
                       "entity": entity, "attribute": attribute},
            "sources": _sources(rows)}


def share(attribute: str, period: str) -> dict:
    """Each entity's share of the metric total in one fiscal period."""
    df = _frame(attribute)
    if df is None or "fiscal" not in df:
        return {"metric": "share", "value": None, "unit": "%",
                "formula": "n/a", "inputs": {}, "sources": [],
                "error": "no data"}
    sub = df[df["fiscal"] == period]
    if sub.empty:
        return {"metric": "share", "value": None, "unit": "%",
                "formula": "n/a", "inputs": {"period": period},
                "sources": [], "error": "no data for period"}
    total = float(sub["value_norm"].sum())
    rows = [{"entity": r["entity"],
             "value": float(r["value_norm"]),
             "share_pct": round(float(r["value_norm"]) / total * 100, 2)}
            for _, r in sub.iterrows()] if total else []
    return {"metric": "share", "value": rows, "unit": "%",
            "formula": "entity / total * 100",
            "inputs": {"period": period, "total": total,
                       "attribute": attribute},
            "sources": _sources(sub, 6)}


def trend(attribute: str, entity: str, last_n: int = 5) -> dict:
    """Compact trend table + direction for one entity+metric."""
    from backend.core.reporting import content as rc
    df = _frame(attribute, entity)
    if df is None or "fiscal" not in df:
        return {"metric": "trend", "value": None, "unit": "MT",
                "formula": "n/a", "inputs": {}, "sources": [],
                "error": "no data"}
    piv = rc.pivot_by_year(df, last_n=last_n)
    if entity not in piv.columns:
        return {"metric": "trend", "value": None, "unit": "MT",
                "formula": "n/a", "inputs": {}, "sources": [],
                "error": "no series"}
    s = piv[entity].dropna()
    pts = [{"period": str(i), "value": round(float(v), 2)} for i, v in s.items()]
    direction = ("increase" if len(pts) >= 2 and pts[-1]["value"] > pts[0]["value"]
                 else "decrease" if len(pts) >= 2 and pts[-1]["value"] < pts[0]["value"]
                 else "stable")
    return {"metric": "trend", "value": pts, "unit": "MT",
            "formula": "ordered fiscal values",
            "inputs": {"entity": entity, "attribute": attribute,
                       "direction": direction},
            "sources": _sources(df, 6)}
