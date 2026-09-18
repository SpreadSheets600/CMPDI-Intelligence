"""Temporal Intelligence: historical timelines for production, reserves,
drilling, dispatch (offtake) and other metrics.

Read-only assembly over the fact index — no new extraction, no schema
changes. Every point carries its receipts (doc_id, page_no / sheet_no,
chunk_id) so the UI can deep-link into the Source Viewer.

Conventions reused from the existing layers:

* scale normalization (``_UNIT_TO_MT``) and the reporting window
  (``_MIN_PERIOD`` / ``_MAX_PERIOD``) from ``reporting.content``, so a
  tonnes-vs-MT pair is never a trend;
* current versions only by default (superseded revisions excluded unless
  the caller opts in), like the Insight Dashboard and Asset profiles;
* the ``quantity`` per-cell bucket excluded, like the Conflict Radar and
  Compare, so timelines track named metrics;
* per-period values are medians of reported values (labeled as such);
* conflicts attached via ``conflicts.detect`` for the same entity/metric.
"""

from __future__ import annotations

from statistics import median

from backend.core.normalize import fy_label
from backend.core.reporting.content import _MAX_PERIOD, _MIN_PERIOD, _UNIT_TO_MT
from backend.db import database as db

_MAX_FACT_ROWS = 5000
_MAX_VALUES_PER_PERIOD = 8

# OLS on fewer than 3 periods is a line through noise, not a trend.
_MIN_FORECAST_PERIODS = 3
_DEFAULT_HORIZON = 3
_MAX_HORIZON = 5


def _scale(unit: str | None) -> float | None:
    u = (unit or "").strip().lower()
    return _UNIT_TO_MT.get(u, 1.0 if not u else None)


def list_options() -> dict:
    """Entities and metrics that have timeline-eligible facts."""
    entities = [
        dict(r)
        for r in db.q(
            """SELECT COALESCE(e.canonical_name, f.entity_text) AS name,
                      COUNT(f.id) AS n_facts,
                      COUNT(DISTINCT f.period_norm) AS n_periods
               FROM facts f
               LEFT JOIN entities e ON e.id = f.entity_id
               WHERE f.value_norm IS NOT NULL AND f.period_norm IS NOT NULL
                 AND f.attribute != 'quantity'
                 AND COALESCE(e.canonical_name, f.entity_text) != ''
               GROUP BY name HAVING n_facts > 0
               ORDER BY n_facts DESC LIMIT 200"""
        )
    ]
    attributes = [
        r["attribute"]
        for r in db.q(
            """SELECT DISTINCT attribute FROM facts
               WHERE attribute != 'quantity' ORDER BY attribute"""
        )
    ]
    return {"entities": entities, "attributes": attributes}


def _fact_rows(
    entity: str, attribute: str, include_superseded: bool = False
) -> list[dict]:
    where = [
        "f.value_norm IS NOT NULL",
        "f.period_norm IS NOT NULL",
        "f.attribute = ?",
        "COALESCE(e.canonical_name, f.entity_text) = ?",
        "f.period_norm >= ?",
        "f.period_norm <= ?",
        "d.status = 'completed'",
    ]
    params: list = [attribute, entity, _MIN_PERIOD, _MAX_PERIOD]
    if not include_superseded:
        where.append("d.is_current_version = 1")
    rows = db.q(
        f"""SELECT f.period_norm AS period, f.unit, f.value_norm, f.value_raw,
                   f.flags, f.conf, d.id AS doc_id, d.display_name, d.filename,
                   d.is_current_version, d.ocr_pages,
                   c.page_no, c.sheet_no, c.id AS chunk_id
            FROM facts f
            LEFT JOIN entities e ON e.id = f.entity_id
            JOIN chunks c ON c.id = f.chunk_id
            JOIN documents d ON d.id = c.doc_id
            WHERE {" AND ".join(where)}
            ORDER BY f.period_norm LIMIT ?""",
        (*params, _MAX_FACT_ROWS),
    )
    out = []
    for r in rows:
        scale = _scale(r["unit"])
        if not scale:
            continue
        out.append(
            {
                "period": r["period"],
                "value_mt": r["value_norm"] * scale,
                "value_raw": r["value_raw"],
                "unit": r["unit"],
                "low_conf": "low_confidence" in (r["flags"] or ""),
                "superseded": not r["is_current_version"],
                "ocr": bool(r["ocr_pages"]),
                "doc_id": r["doc_id"],
                "filename": r["display_name"] or r["filename"],
                "page_no": r["page_no"],
                "sheet_no": r["sheet_no"],
                "chunk_id": r["chunk_id"],
            }
        )
    return out


def _yoy_pct(prev: float, cur: float) -> float | None:
    if not prev:
        return None
    return round((cur - prev) / abs(prev) * 100, 1)


def _cagr_pct(first: float, last: float, n_periods: int) -> float | None:
    if n_periods < 2 or not first or first <= 0 or not last or last <= 0:
        return None
    return round(((last / first) ** (1 / (n_periods - 1)) - 1) * 100, 1)


def _missing_years(periods: list[str]) -> list[int]:
    years = sorted(
        {int(p[:4]) for p in periods if p and len(p) >= 4 and p[:4].isdigit()}
    )
    if len(years) < 2:
        return []
    full = set(range(years[0], years[-1] + 1))
    return sorted(full - set(years))


def _period_year(period: str | None) -> int | None:
    if not period or len(period) < 4 or not period[:4].isdigit():
        return None
    return int(period[:4])


def _ols(xs: list[float], ys: list[float]) -> tuple[float, float, float, float]:
    """Ordinary least squares on (x, y): slope, intercept, R-squared,
    residual std. Pure stdlib so forecasting works with no extra deps."""
    n = len(xs)
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    sxx = sum((x - x_mean) ** 2 for x in xs)
    sxy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else 0.0
    intercept = y_mean - slope * x_mean
    fitted = [slope * x + intercept for x in xs]
    ss_res = sum((y - f) ** 2 for y, f in zip(ys, fitted))
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r_squared = 1 - ss_res / ss_tot if ss_tot else 0.0
    resid_std = (ss_res / (n - 2)) ** 0.5 if n > 2 and ss_res else 0.0
    return slope, intercept, r_squared, resid_std


def forecast(
    entity: str,
    attribute: str,
    horizon: int = _DEFAULT_HORIZON,
    include_superseded: bool = False,
) -> dict | None:
    """Estimate future periods from the median-per-period history.

    Input dataset: scale-normalized facts for one entity x metric inside the
    reporting window (same grain and filters as :func:`timeline`).
    Calculation: OLS linear trend on (fiscal start year, median MT), projected
    ``horizon`` years ahead with an approximate 95% band from the residual
    spread. Interpretation: estimates of where the past trend points, never
    reported figures — every forecast links back to the history receipts.
    Returns ``status: "insufficient"`` with an empty forecast when fewer than
    three periods exist.
    """
    entity = (entity or "").strip()
    attribute = (attribute or "").strip()
    if not entity or not attribute:
        return None
    horizon = max(1, min(int(horizon or _DEFAULT_HORIZON), _MAX_HORIZON))

    hist = timeline(entity, attribute, include_superseded)
    if hist is None:
        return None
    points = hist["points"]
    base = {
        "entity": entity,
        "attribute": attribute,
        "horizon": horizon,
        "history": [
            {"period": p["period"], "label": p["label"], "value_mt": p["value_mt"]}
            for p in points
        ],
        "n_periods": hist["n_periods"],
        "n_docs": hist["n_docs"],
        "low_conf_share": hist["low_conf_share"],
        "conflicts": hist["conflicts"],
        "coverage_gaps": hist["coverage_gaps"],
        "include_superseded": include_superseded,
    }
    if len(points) < _MIN_FORECAST_PERIODS:
        return {
            **base,
            "status": "insufficient",
            "reason": (
                f"Need at least {_MIN_FORECAST_PERIODS} reported periods "
                f"to estimate a trend; found {len(points)}."
            ),
            "forecast": [],
        }

    years = [_period_year(p["period"]) for p in points]
    medians = [p["value_mt"] for p in points]
    pairs = [(x, y) for x, y in zip(years, medians) if x is not None]
    if len(pairs) < _MIN_FORECAST_PERIODS:
        return {
            **base,
            "status": "insufficient",
            "reason": "Reported periods lack parseable years; cannot fit a trend.",
            "forecast": [],
        }
    xs = [float(x) for x, _ in pairs]
    ys = [y for _, y in pairs]
    slope, intercept, r_squared, resid_std = _ols(xs, ys)

    n = len(xs)
    x_mean = sum(xs) / n
    sxx = sum((x - x_mean) ** 2 for x in xs)
    non_negative = all(y >= 0 for y in ys)
    last_year = int(max(xs))

    estimates = []
    floored = False
    for k in range(1, horizon + 1):
        year = last_year + k
        raw = slope * year + intercept
        if non_negative and raw < 0:
            raw = 0.0
            floored = True
        if sxx and resid_std:
            se = resid_std * (1 + 1 / n + (year - x_mean) ** 2 / sxx) ** 0.5
            half = 1.96 * se
        else:
            half = 0.0
        lo = max(0.0, raw - half) if non_negative else raw - half
        period = f"{year}-04-01"
        estimates.append(
            {
                "period": period,
                "label": fy_label(period),
                "value_mt": round(raw, 3),
                "low_mt": round(lo, 3),
                "high_mt": round(raw + half, 3),
                "estimated": True,
            }
        )

    open_conflicts = sum(1 for c in hist["conflicts"] if c.get("status") == "open")
    reasons: list[str] = []
    if n >= 5 and r_squared >= 0.7:
        confidence = "high"
        reasons.append(f"{n} periods with R² {r_squared:.2f}")
    elif n >= 4 and r_squared >= 0.4:
        confidence = "medium"
        reasons.append(f"{n} periods with R² {r_squared:.2f}")
    else:
        confidence = "low"
        reasons.append(
            f"only {n} periods" if n < 4 else f"weak fit (R² {r_squared:.2f})"
        )
    if hist["low_conf_share"] >= 0.25:
        confidence = "low"
        reasons.append(
            f"{hist['low_conf_share']:.0%} of history leans on quarantined digits"
        )
    elif hist["low_conf_share"] > 0:
        reasons.append(f"{hist['low_conf_share']:.0%} low-confidence digits in history")
    if open_conflicts:
        if confidence == "high":
            confidence = "medium"
        reasons.append(f"{open_conflicts} open conflict(s) on this series")
    if hist["n_docs"] == 1:
        if confidence == "high":
            confidence = "medium"
        reasons.append("trend rests on a single document")
    if hist["coverage_gaps"]:
        reasons.append(f"history skips {', '.join(map(str, hist['coverage_gaps']))}")

    warnings = [
        "Estimates project the past linear trend; they are not reported figures."
    ]
    if hist["coverage_gaps"]:
        warnings.append(
            "History has coverage gaps; the trend bridges silence, not zeroes."
        )
    if open_conflicts:
        warnings.append(
            "Sources disagree on this series; the trend uses the median, "
            "either side may be right."
        )
    if hist["low_conf_share"] > 0:
        warnings.append("History includes low-confidence OCR digits.")
    if hist["n_docs"] == 1:
        warnings.append("Trend rests on a single document; corroborate before citing.")
    if floored:
        warnings.append("Negative trend values floored at zero (physical quantity).")
    if slope == 0.0 and r_squared == 0.0:
        warnings.append("History is flat; the estimate repeats the last level.")

    return {
        **base,
        "status": "ok",
        "method": "ols_linear",
        "slope_mt_per_year": round(slope, 4),
        "intercept_mt": round(intercept, 3),
        "r_squared": round(r_squared, 3),
        "forecast": estimates,
        "confidence": confidence,
        "confidence_reasons": reasons,
        "warnings": warnings,
    }


def timeline(
    entity: str, attribute: str, include_superseded: bool = False
) -> dict | None:
    """Historical timeline for one entity x metric, oldest period first."""
    from backend.core import conflicts

    entity = (entity or "").strip()
    attribute = (attribute or "").strip()
    if not entity or not attribute:
        return None
    rows = _fact_rows(entity, attribute, include_superseded)
    if not rows:
        return {
            "entity": entity,
            "attribute": attribute,
            "points": [],
            "n_periods": 0,
            "n_docs": 0,
            "low_conf_share": 0.0,
            "conflicts": conflicts.detect(entity=entity, attribute=attribute, limit=10),
            "coverage_gaps": [],
        }
    by_period: dict[str, list[dict]] = {}
    for r in rows:
        by_period.setdefault(r["period"], []).append(r)
    periods = sorted(by_period)
    points = []
    prev_median: float | None = None
    for p in periods:
        vals = by_period[p]
        med = median([v["value_mt"] for v in vals])
        shown = sorted(vals, key=lambda v: v["value_mt"], reverse=True)[
            :_MAX_VALUES_PER_PERIOD
        ]
        point = {
            "period": p,
            "label": fy_label(p),
            "value_mt": round(med, 3),
            "n_sources": len({v["doc_id"] for v in vals}),
            "n_values": len(vals),
            "low_conf": any(v["low_conf"] for v in vals),
            "yoy_pct": _yoy_pct(prev_median, med) if prev_median is not None else None,
            "values": [
                {
                    "value_mt": round(v["value_mt"], 3),
                    "value_raw": v["value_raw"],
                    "unit": v["unit"],
                    "low_conf": v["low_conf"],
                    "superseded": v["superseded"],
                    "ocr": v["ocr"],
                    "doc_id": v["doc_id"],
                    "filename": v["filename"],
                    "page_no": v["page_no"],
                    "sheet_no": v["sheet_no"],
                    "chunk_id": v["chunk_id"],
                }
                for v in shown
            ],
        }
        points.append(point)
        prev_median = med
    first, last = points[0]["value_mt"], points[-1]["value_mt"]
    return {
        "entity": entity,
        "attribute": attribute,
        "points": points,
        "first": first,
        "last": last,
        "delta_pct": _yoy_pct(first, last),
        "cagr_pct": _cagr_pct(first, last, len(points)),
        "n_periods": len(points),
        "n_docs": len({v["doc_id"] for vals in by_period.values() for v in vals}),
        "low_conf_share": round(
            sum(1 for vals in by_period.values() for v in vals if v["low_conf"])
            / len(rows),
            3,
        ),
        "include_superseded": include_superseded,
        "conflicts": conflicts.detect(entity=entity, attribute=attribute, limit=10),
        "coverage_gaps": _missing_years(periods),
    }
