"""Organizational insight dashboard signals.

Deterministic aggregation over the current knowledge layer — no LLM, no new
extraction, no forecasting. Every signal reuses an existing convention:

* scale normalization (``_UNIT_TO_MT``) and the reporting window from
  ``reporting.content``, so a tonnes-vs-MT pair is never a trend;
* current versions only for trends/anomalies (superseded revisions are shown
  under changes, never as the present);
* the ``quantity`` per-cell bucket excluded, like the Conflict Radar and
  Compare, so the dashboard tracks named metrics.

Provenance is preserved by carrying ``doc_id`` (and page/sheet where a
single point is shown) on every trend and anomaly; the UI links back to the
fact explorer, Conflict Radar and Compare screens for receipts.
"""

import logging
from datetime import UTC, datetime
from statistics import median

logger = logging.getLogger("cmpdi.insights")

from backend.core.reporting.content import _MAX_PERIOD, _MIN_PERIOD, _UNIT_TO_MT

_PCT_DIGITS = 1

# A two-point wiggle is noise; trends need at least this many periods.
_MIN_TREND_PERIODS = 2
# |YoY| at or above this on a 3+ point series is worth an officer's look.
_SHARP_MOVE_PCT = 30.0
# Last value this far from the prior median reads as an outlier, not growth.
_OUTLIER_VS_MEDIAN_PCT = 50.0
# Quarantined-share at or above this means the metric leans on shaky digits.
_LOW_CONF_SHARE = 0.25
# Caps keep the payload small on large libraries.
_MAX_FACT_ROWS = 20000
_MAX_TRENDS = 8
_MAX_ANOMALIES = 8
_MAX_CONFLICTS = 5
_MAX_GROUPS = 5
_MAX_DIFFS = 3


def _scale(unit: str | None) -> float | None:
    u = (unit or "").strip().lower()
    return _UNIT_TO_MT.get(u, 1.0 if not u else None)


def _fact_rows(subsidiary: str | None = None) -> list[dict]:
    """Scale-normalized, in-window facts from current document versions."""
    from backend.db import database as db

    where = [
        "f.value_norm IS NOT NULL",
        "COALESCE(e.canonical_name, f.entity_text) != ''",
        "f.attribute != 'quantity'",
        "d.status = 'completed'",
        "d.is_current_version = 1",
        "f.period_norm IS NOT NULL",
        "f.period_norm >= ?",
        "f.period_norm <= ?",
    ]
    params: list = [_MIN_PERIOD, _MAX_PERIOD]
    if subsidiary:
        where.append("d.subsidiary = ?")
        params.append(subsidiary)
    rows = db.q(
        f"""SELECT COALESCE(e.canonical_name, f.entity_text) AS entity,
                   f.attribute, f.period_norm, f.unit, f.value_norm,
                   f.flags, f.conf, d.id AS doc_id, c.page_no, c.sheet_no
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
                "entity": r["entity"],
                "attribute": r["attribute"],
                "period": r["period_norm"],
                "value_mt": r["value_norm"] * scale,
                "low_conf": "low_confidence" in (r["flags"] or ""),
                "doc_id": r["doc_id"],
            }
        )
    return out


def _series(rows: list[dict]) -> dict[tuple, dict]:
    """(entity, attribute) -> median-per-period series with doc receipts."""
    grouped: dict[tuple, dict[str, list]] = {}
    for r in rows:
        grouped.setdefault((r["entity"], r["attribute"]), {}).setdefault(
            r["period"], []
        ).append(r)
    out = {}
    for key, per_period in grouped.items():
        periods = sorted(per_period)
        values = [median([v["value_mt"] for v in per_period[p]]) for p in periods]
        docs = {v["doc_id"] for vals in per_period.values() for v in vals}
        low = sum(1 for vals in per_period.values() for v in vals if v["low_conf"])
        total = sum(len(vals) for vals in per_period.values())
        out[key] = {
            "periods": periods,
            "values": values,
            "n_docs": len(docs),
            "doc_ids": sorted(docs),
            "low_conf_share": round(low / total, 3) if total else 0.0,
        }
    return out


def _delta_pct(first: float, last: float) -> float | None:
    if not first:
        return None
    return round((last - first) / abs(first) * 100, _PCT_DIGITS)


def _trends(series: dict[tuple, dict]) -> list[dict]:
    trends = []
    for (entity, attribute), s in series.items():
        if len(s["periods"]) < _MIN_TREND_PERIODS:
            continue
        first, last = s["values"][0], s["values"][-1]
        delta = _delta_pct(first, last)
        trends.append(
            {
                "entity": entity,
                "attribute": attribute,
                "periods": s["periods"],
                "values_mt": [round(v, 3) for v in s["values"]],
                "first": round(first, 3),
                "last": round(last, 3),
                "delta_pct": delta,
                "direction": "flat"
                if delta is None or abs(delta) < 1
                else ("up" if delta > 0 else "down"),
                "n_periods": len(s["periods"]),
                "n_docs": s["n_docs"],
                "doc_ids": s["doc_ids"],
            }
        )
    trends.sort(key=lambda t: -(abs(t["delta_pct"] or 0)))
    return trends[:_MAX_TRENDS]


def _anomalies(series: dict[tuple, dict]) -> list[dict]:
    found = []
    for (entity, attribute), s in series.items():
        periods, values = s["periods"], s["values"]
        if len(periods) < _MIN_TREND_PERIODS:
            continue
        last, prev = values[-1], values[-2]
        yoy = _delta_pct(prev, last)
        base = {"entity": entity, "attribute": attribute, "period": periods[-1]}
        if len(periods) >= 3 and yoy is not None and abs(yoy) >= _SHARP_MOVE_PCT:
            found.append(
                {
                    **base,
                    "kind": "sharp_move",
                    "title": f"{entity} {attribute.replace('_', ' ')} "
                    f"{'jumped' if yoy > 0 else 'fell'} {abs(yoy)}% in one year",
                    "detail": f"{round(prev, 3)} to {round(last, 3)} MT "
                    f"between {periods[-2][:4]} and {periods[-1][:4]} "
                    f"across {s['n_docs']} document(s).",
                    "delta_pct": yoy,
                    "severity": "high" if abs(yoy) >= _SHARP_MOVE_PCT * 2 else "watch",
                }
            )
            continue
        if len(periods) >= 3:
            mid = median(values[:-1])
            dev = _delta_pct(mid, last)
            if dev is not None and abs(dev) >= _OUTLIER_VS_MEDIAN_PCT:
                found.append(
                    {
                        **base,
                        "kind": "outlier_vs_history",
                        "title": f"{entity} {attribute.replace('_', ' ')} "
                        f"latest value sits {abs(dev)}% off its history",
                        "detail": f"Latest {round(last, 3)} MT against a prior "
                        f"median of {round(mid, 3)} MT.",
                        "delta_pct": dev,
                        "severity": "watch",
                    }
                )
                continue
        if s["n_docs"] == 1 and len(periods) >= 2:
            found.append(
                {
                    **base,
                    "kind": "thin_evidence",
                    "title": f"{entity} {attribute.replace('_', ' ')} "
                    "rests on a single document",
                    "detail": "Trend spans "
                    f"{len(periods)} period(s) from one source; corroborate "
                    "before citing.",
                    "delta_pct": yoy,
                    "severity": "watch",
                }
            )
        elif s["low_conf_share"] >= _LOW_CONF_SHARE:
            found.append(
                {
                    **base,
                    "kind": "low_confidence",
                    "title": f"{entity} {attribute.replace('_', ' ')} "
                    f"leans on quarantined digits ({s['low_conf_share']:.0%})",
                    "detail": "Low-confidence OCR numbers need human approval "
                    "before reports may use them.",
                    "delta_pct": yoy,
                    "severity": "watch",
                }
            )
    found.sort(key=lambda a: (a["severity"] != "high", -(abs(a["delta_pct"] or 0))))
    return found[:_MAX_ANOMALIES]


def _conflicts_top(subsidiary: str | None = None) -> tuple[list[dict], int]:
    """Worst open conflicts first; subsidiary scope keeps groups touching it."""
    from backend.core import conflicts
    from backend.db import database as db

    groups = conflicts.detect(limit=50)
    if subsidiary:
        doc_sub = {
            r["id"]: r["subsidiary"]
            for r in db.q("SELECT id, subsidiary FROM documents")
        }
        groups = [
            g
            for g in groups
            if subsidiary in {doc_sub.get(v["doc_id"]) for v in g["values"]}
        ]
    open_n = sum(1 for g in groups if g["status"] == "open")
    return groups[:_MAX_CONFLICTS], open_n


def _changes(subsidiary: str | None = None) -> dict:
    from backend.core import compare
    from backend.db import database as db

    group_rows = db.q(
        """SELECT version_group_id, COUNT(*) n, MAX(upload_ts) latest
           FROM documents WHERE version_group_id IS NOT NULL
           GROUP BY version_group_id HAVING n > 1 ORDER BY latest DESC"""
    )
    groups = []
    for g in group_rows:
        docs = [
            dict(r)
            for r in db.q(
                """SELECT id, filename, display_name, doc_date_raw, doc_date_norm,
                          subsidiary, is_current_version, upload_ts
                   FROM documents WHERE version_group_id = ?
                   ORDER BY doc_date_norm, upload_ts""",
                (g["version_group_id"],),
            )
        ]
        if subsidiary and subsidiary not in {d["subsidiary"] for d in docs}:
            continue
        groups.append({"group_id": g["version_group_id"], "docs": docs})
        if len(groups) >= _MAX_GROUPS:
            break

    diffs = []
    for g in groups[:_MAX_DIFFS]:
        docs = g["docs"]
        if len(docs) < 2:
            continue
        try:
            cmp = compare.compare(docs[0]["id"], docs[-1]["id"])
        except Exception:
            logger.warning(
                "Insight version diff failed", extra={"group_id": g["group_id"]}
            )
            continue
        diffs.append(
            {
                "group_id": g["group_id"],
                "a_name": docs[0]["display_name"] or docs[0]["filename"],
                "b_name": docs[-1]["display_name"] or docs[-1]["filename"],
                "summary": cmp["summary"],
                "top_changes": cmp["fact_changes"][:3],
            }
        )

    where = ["status = 'completed'"]
    params: list = []
    if subsidiary:
        where.append("subsidiary = ?")
        params.append(subsidiary)
    recent = [
        dict(r)
        for r in db.q(
            f"""SELECT id, filename, display_name, subsidiary, doc_type,
                       doc_date_raw, upload_ts FROM documents
                WHERE {" AND ".join(where)} ORDER BY upload_ts DESC LIMIT 5""",
            params,
        )
    ]
    failed = [
        dict(r)
        for r in db.q(
            """SELECT j.stage, j.error, j.updated_ts, d.filename FROM jobs j
               LEFT JOIN documents d ON d.id = j.doc_id
               WHERE j.status = 'failed' ORDER BY j.id DESC LIMIT 5"""
        )
    ]
    return {
        "version_groups": groups,
        "version_diffs": diffs,
        "recent_docs": recent,
        "failed_jobs": failed,
    }


def _gaps(
    subsidiary: str | None = None,
    series: dict | None = None,
    changes: dict | None = None,
    open_conflicts: int = 0,
) -> list[dict]:
    from backend.db import database as db

    gaps = []
    where = ["status = 'completed'"]
    params: list = []
    if subsidiary:
        where.append("subsidiary = ?")
        params.append(subsidiary)
    missing = db.q(
        f"""SELECT id, filename, display_name FROM documents
            WHERE {" AND ".join(where)} AND (summary IS NULL OR summary = '')
            ORDER BY upload_ts DESC LIMIT 5""",
        params,
    )
    if missing:
        n = db.q1(
            f"""SELECT COUNT(*) c FROM documents
                WHERE {" AND ".join(where)} AND (summary IS NULL OR summary = '')""",
            params,
        )["c"]
        gaps.append(
            {
                "kind": "missing_summaries",
                "title": f"{n} document(s) have no summary yet",
                "detail": "Example: "
                + ", ".join(d["display_name"] or d["filename"] for d in missing[:3]),
            }
        )
    failed_n = len((changes or {}).get("failed_jobs", []))
    if failed_n:
        gaps.append(
            {
                "kind": "failed_jobs",
                "title": f"{failed_n} recent ingestion failure(s)",
                "detail": "See Pipeline for the per-file reason; no data was "
                "silently dropped.",
            }
        )
    if open_conflicts:
        gaps.append(
            {
                "kind": "open_conflicts",
                "title": f"{open_conflicts} open value conflict(s)",
                "detail": "Same entity, metric and period reported differently; "
                "an officer needs to acknowledge or resolve them.",
            }
        )
    thin = [(key, s) for key, s in (series or {}).items() if s["n_docs"] == 1]
    if thin:
        sample = ", ".join(f"{e} {a.replace('_', ' ')}" for (e, a), _ in thin[:3])
        gaps.append(
            {
                "kind": "single_source",
                "title": f"{len(thin)} metric(s) rest on one document",
                "detail": f"Example: {sample}.",
            }
        )
    return gaps


def _topics(subsidiary: str | None = None) -> dict:
    import json

    from backend.core import retrieval
    from backend.db import database as db

    scope = f"subsidiary:{subsidiary}" if subsidiary else "corpus"
    clusters = []
    for t in db.q(
        "SELECT * FROM doc_topics WHERE scope = ? ORDER BY id DESC LIMIT 4", (scope,)
    ):
        t = dict(t)
        try:
            keywords = json.loads(t["keywords_json"])
            doc_ids = json.loads(t["doc_ids_json"])
        except (ValueError, TypeError):
            continue
        clusters.append(
            {"label": t["label"], "keywords": keywords[:6], "n_docs": len(doc_ids)}
        )
    if not clusters and subsidiary:
        for t in db.q(
            "SELECT * FROM doc_topics WHERE scope = 'corpus' ORDER BY id DESC LIMIT 4"
        ):
            t = dict(t)
            try:
                keywords = json.loads(t["keywords_json"])
                doc_ids = json.loads(t["doc_ids_json"])
            except (ValueError, TypeError):
                continue
            clusters.append(
                {"label": t["label"], "keywords": keywords[:6], "n_docs": len(doc_ids)}
            )
    return {"tags": retrieval.top_tags(12, subsidiary), "clusters": clusters}


def dashboard(subsidiary: str | None = None) -> dict:
    """Full signal payload for the Insight Dashboard screen."""
    from backend.core import quality
    from backend.db import database as db

    subsidiary = (subsidiary or "").strip() or None
    rows = _fact_rows(subsidiary)
    series = _series(rows)
    conflicts_top, open_conflicts = _conflicts_top(subsidiary)
    changes = _changes(subsidiary)
    completed = db.q1(
        "SELECT COUNT(*) c FROM documents WHERE status = 'completed'"
        + (" AND subsidiary = ?" if subsidiary else ""),
        (subsidiary,) if subsidiary else (),
    )["c"]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": subsidiary or "corpus",
        "corpus": {
            "documents": completed,
            "fact_points": len(rows),
            "metrics": len(series),
            "open_conflicts": open_conflicts,
            "version_groups": len(changes["version_groups"]),
        },
        "trends": _trends(series),
        "anomalies": _anomalies(series),
        "conflicts_top": conflicts_top,
        "changes": changes,
        "gaps": _gaps(subsidiary, series, changes, open_conflicts),
        "topics": _topics(subsidiary),
        "quality": quality.quality_stats(),
    }
