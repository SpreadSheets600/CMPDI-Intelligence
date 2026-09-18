"""Asset / Mine Intelligence: unified profile per mine, region or project.

Read-only assembly over the existing knowledge layer — no new extraction,
no schema changes. Every figure carries its receipt (doc_id, page_no /
sheet_no, chunk_id) so the UI can deep-link into the Source Viewer.

An asset is any entity typed mine, coalfield, block or location. Values are
scale-normalized to MT with the same unit table and reporting window as the
Insight Dashboard and Conflict Radar, so a tonnes-vs-MT pair is never a
trend. Per-period values are medians of reported values (labeled as such);
related entities are shared-document co-occurrences (labeled as such).
"""

from __future__ import annotations

from statistics import median

from backend.core.reporting.content import _MAX_PERIOD, _MIN_PERIOD, _UNIT_TO_MT
from backend.db import database as db

ASSET_TYPES = ("mine", "coalfield", "block", "location")

_MAX_ASSETS = 200
_MAX_DOCS = 50
_MAX_EVIDENCE = 60
_MAX_RELATED = 8
_MAX_TREND_ATTRS = 12


def _scale(unit: str | None) -> float | None:
    u = (unit or "").strip().lower()
    return _UNIT_TO_MT.get(u, 1.0 if not u else None)


def list_assets(kind: str | None = None, q: str | None = None) -> list[dict]:
    """Assets with their library footprint, most-reported first."""
    types: tuple[str, ...] = ASSET_TYPES
    if kind == "mine":
        types = ("mine",)
    elif kind == "region":
        types = ("coalfield", "block", "location")
    where = [f"e.type IN ({','.join('?' * len(types))})"]
    params: list = list(types)
    if q:
        where.append("e.canonical_name LIKE ?")
        params.append(f"%{q}%")
    rows = db.q(
        f"""SELECT e.id, e.canonical_name, e.type,
                   COUNT(DISTINCT c.doc_id) AS n_docs,
                   COUNT(f.id) AS n_facts,
                   COUNT(DISTINCT f.attribute) AS n_metrics,
                   MAX(f.period_norm) AS latest_period
            FROM entities e
            LEFT JOIN facts f ON f.entity_id = e.id
            LEFT JOIN chunks c ON c.id = f.chunk_id
            WHERE {" AND ".join(where)}
            GROUP BY e.id HAVING n_facts > 0 ORDER BY n_facts DESC LIMIT ?""",
        (*params, _MAX_ASSETS),
    )
    return [dict(r) for r in rows]


def _fact_rows(entity_id: int) -> list[dict]:
    """Scale-normalized facts in the reporting window, current versions only."""
    rows = db.q(
        """SELECT f.attribute, f.period_norm AS period, f.unit, f.value_norm, f.value_raw,
                  f.flags, d.id AS doc_id, d.display_name, d.filename,
                  c.page_no, c.sheet_no, c.id AS chunk_id
           FROM facts f
           JOIN chunks c ON c.id = f.chunk_id
           JOIN documents d ON d.id = c.doc_id
           WHERE f.entity_id = ? AND f.value_norm IS NOT NULL
             AND f.attribute != 'quantity'
             AND d.status = 'completed' AND d.is_current_version = 1
             AND f.period_norm IS NOT NULL
             AND f.period_norm >= ? AND f.period_norm <= ?
           ORDER BY f.period_norm""",
        (entity_id, _MIN_PERIOD, _MAX_PERIOD),
    )
    out = []
    for r in rows:
        scale = _scale(r["unit"])
        if not scale:
            continue
        out.append({**dict(r), "value_mt": r["value_norm"] * scale})
    return out


def _key_figures(rows: list[dict]) -> list[dict]:
    """Latest reported value per metric (median when several sources agree)."""
    by_attr: dict[str, list[dict]] = {}
    for r in rows:
        by_attr.setdefault(r["attribute"], []).append(r)
    figures = []
    for attr, vals in by_attr.items():
        latest = max(v["period"] for v in vals)
        at_latest = [v for v in vals if v["period"] == latest]
        rec = at_latest[0]
        figures.append(
            {
                "attribute": attr,
                "period": latest,
                "value_mt": round(median([v["value_mt"] for v in at_latest]), 3),
                "value_raw": rec["value_raw"],
                "unit": rec["unit"],
                "n_sources": len({v["doc_id"] for v in at_latest}),
                "doc_id": rec["doc_id"],
                "filename": rec["display_name"] or rec["filename"],
                "page_no": rec["page_no"],
                "sheet_no": rec["sheet_no"],
                "chunk_id": rec["chunk_id"],
            }
        )
    figures.sort(key=lambda f: f["attribute"])
    return figures


def _trends(rows: list[dict]) -> list[dict]:
    """Median-per-period series per metric with a receipt per point."""
    by_attr: dict[str, dict[str, list[dict]]] = {}
    for r in rows:
        by_attr.setdefault(r["attribute"], {}).setdefault(r["period"], []).append(r)
    trends = []
    for attr, per_period in by_attr.items():
        periods = sorted(per_period)
        points = []
        for p in periods:
            vals = per_period[p]
            rec = vals[0]
            points.append(
                {
                    "period": p,
                    "value_mt": round(median([v["value_mt"] for v in vals]), 3),
                    "n_sources": len({v["doc_id"] for v in vals}),
                    "doc_id": rec["doc_id"],
                    "filename": rec["display_name"] or rec["filename"],
                    "page_no": rec["page_no"],
                    "sheet_no": rec["sheet_no"],
                }
            )
        first, last = points[0]["value_mt"], points[-1]["value_mt"]
        delta = round((last - first) / abs(first) * 100, 1) if first else None
        trends.append(
            {
                "attribute": attr,
                "points": points,
                "first": first,
                "last": last,
                "delta_pct": delta,
                "n_periods": len(periods),
            }
        )
    trends.sort(key=lambda t: -(abs(t["delta_pct"] or 0)))
    return trends[:_MAX_TREND_ATTRS]


def _documents(entity_id: int) -> list[dict]:
    rows = db.q(
        """SELECT d.id AS doc_id, d.display_name, d.filename, d.subsidiary,
                  d.doc_type, d.doc_date_raw, d.is_current_version,
                  COUNT(f.id) AS n_facts, MAX(d.upload_ts) AS upload_ts
           FROM facts f
           JOIN chunks c ON c.id = f.chunk_id
           JOIN documents d ON d.id = c.doc_id
           WHERE f.entity_id = ?
           GROUP BY d.id ORDER BY upload_ts DESC LIMIT ?""",
        (entity_id, _MAX_DOCS),
    )
    return [dict(r) for r in rows]


def _related(entity_id: int) -> dict[str, list[dict]]:
    """Entities sharing a document with this asset, grouped by family."""
    rows = db.q(
        """SELECT e.id, e.canonical_name, e.type,
                  COUNT(DISTINCT c.doc_id) AS shared_docs,
                  MIN(d.id) AS doc_id, MIN(d.display_name) AS display_name,
                  MIN(d.filename) AS filename
           FROM facts f1
           JOIN chunks c1 ON c1.id = f1.chunk_id
           JOIN facts f2 ON f2.chunk_id IN (
               SELECT id FROM chunks WHERE doc_id = c1.doc_id)
           JOIN chunks c ON c.id = f2.chunk_id
           JOIN documents d ON d.id = c.doc_id
           JOIN entities e ON e.id = f2.entity_id
           WHERE f1.entity_id = ? AND f2.entity_id != ?
           GROUP BY e.id ORDER BY shared_docs DESC LIMIT 40""",
        (entity_id, entity_id),
    )
    groups: dict[str, list[dict]] = {"operators": [], "places": [], "geology": []}
    for r in rows:
        r = dict(r)
        t = (r["type"] or "").lower()
        if t in ("subsidiary", "organization"):
            bucket = "operators"
        elif t in ("mine", "coalfield", "block", "location"):
            bucket = "places"
        elif t in ("seam", "geology"):
            bucket = "geology"
        else:
            continue
        if len(groups[bucket]) < _MAX_RELATED:
            groups[bucket].append(r)
    return groups


def _evidence(entity_id: int) -> list[dict]:
    rows = db.q(
        """SELECT f.attribute, f.period_norm, f.value_raw, f.value_norm,
                  f.unit, f.flags, f.conf, d.id AS doc_id,
                  d.display_name, d.filename, d.is_current_version,
                  c.page_no, c.sheet_no, c.id AS chunk_id
           FROM facts f
           JOIN chunks c ON c.id = f.chunk_id
           JOIN documents d ON d.id = c.doc_id
           WHERE f.entity_id = ? AND f.value_norm IS NOT NULL
             AND f.attribute != 'quantity'
           ORDER BY f.period_norm DESC LIMIT ?""",
        (entity_id, _MAX_EVIDENCE),
    )
    return [dict(r) for r in rows]


def profile(name: str) -> dict | None:
    """Unified intelligence profile for one asset (or any named entity)."""
    from backend.core import conflicts
    from backend.core.knowledge import reference

    ent = reference.resolve(name)
    if not ent:
        return None
    ctx = reference.entity_context(ent["canonical_name"])
    rows = _fact_rows(ent["id"])
    figures = _key_figures(rows)
    return {
        "entity": ent["canonical_name"],
        "type": ent["type"],
        "reference": ctx["reference"] if ctx else {},
        "n_reference": ctx["n_reference"] if ctx else 0,
        "library": ctx["library"] if ctx else {},
        "key_figures": figures,
        "trends": _trends(rows),
        "documents": _documents(ent["id"]),
        "related": _related(ent["id"]),
        "conflicts": conflicts.detect(entity=ent["canonical_name"], limit=10),
        "evidence": _evidence(ent["id"]),
    }
