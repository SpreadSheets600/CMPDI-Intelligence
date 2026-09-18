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
