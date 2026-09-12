"""Conflict Radar. Groups fact-index values that disagree on the same
(entity, attribute, period) key and explains WHY each conflict was flagged
and what likely caused it, so a reviewing officer can judge instead of
guess. Values are never silently resolved; each keeps its receipt. Officer
decisions (acknowledge/resolve) persist in conflict_status."""

import hashlib

from backend.db import database as db


def _key(entity: str, attribute: str, period_norm: str, unit: str | None) -> str:
    raw = "|".join([entity or "", attribute or "", period_norm or "", unit or ""])
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _causes(values: list[dict]) -> list[str]:
    """Explain the disagreement from what the sources look like."""
    causes = []
    units = {v["unit"] for v in values if v["unit"]}
    if len(units) > 1:
        causes.append("units differ between sources; values may not be on the same scale")
    if any(v["ocr"] for v in values):
        causes.append("one or more sources are OCR-derived; digit confusion is possible")
    if any(v["low_conf"] for v in values):
        causes.append("a low-confidence number was detected in a source")
    if any(v["partial"] for v in values):
        causes.append("a source reports a partial period (advance release), not the full year")
    docs = {(v["doc_id"], v["sheet_no"], v["page_no"]) for v in values}
    if len(docs) == 1:
        causes.append("all values come from one table; some may belong to sibling rows "
                      "of a dense sheet rather than the stated entity")
    elif len(docs) > 1:
        causes.append("different source documents may use different reporting cut-offs")
    if any(v["superseded"] for v in values):
        causes.append("a superseded revision may carry a pre-revision figure")
    return causes or ["sources disagree without an obvious structural cause"]


def detect(entity: str | None = None, attribute: str | None = None,
           limit: int = 50) -> list[dict]:
    """All conflict groups, worst spreads first, with every value's receipt.
    Values are normalized to MT before grouping so a tonnes-vs-sheet-scale
    pair is not mistaken for a disagreement."""
    import pandas as pd

    from backend.core.reporting.content import _UNIT_TO_MT

    rows = [dict(r) for r in db.q("""
        SELECT COALESCE(e.canonical_name, f.entity_text) AS entity,
               f.attribute, f.period_norm, f.unit, f.value_norm, f.value_raw,
               f.flags, f.conf, d.filename, d.id AS doc_id,
               d.is_current_version, d.ocr_pages, c.page_no, c.sheet_no
        FROM facts f
        LEFT JOIN entities e ON e.id = f.entity_id
        JOIN chunks c ON c.id = f.chunk_id
        JOIN documents d ON d.id = c.doc_id
        WHERE f.value_norm IS NOT NULL
          AND COALESCE(e.canonical_name, f.entity_text) != ''
    """)]
    if entity:
        rows = [r for r in rows if r["entity"] == entity]
    if attribute:
        rows = [r for r in rows if r["attribute"] == attribute]
    else:
        # 'quantity' is the raw per-cell bucket of the statistics sheets, not
        # an advertised metric; the radar targets the claimed fact types
        rows = [r for r in rows if r["attribute"] != "quantity"]

    for r in rows:
        u = (r["unit"] or "").strip().lower()
        r["_scale"] = _UNIT_TO_MT.get(u, 1.0 if not u else None)
    rows = [r for r in rows if r["_scale"] and r["period_norm"]]

    df = pd.DataFrame(rows)
    if df.empty:
        return []
    df["value_mt"] = df["value_norm"] * df["_scale"]
    statuses = {r["conflict_key"]: r["status"] for r in
                db.q("SELECT conflict_key, status FROM conflict_status")}

    out = []
    grouped = df.groupby(["entity", "attribute", "period_norm"])
    for (ent, attr, period), g in grouped:
        distinct = g.drop_duplicates(subset=["value_mt"])
        if len(distinct) < 2:
            continue
        shown = distinct.nlargest(8, "value_mt").to_dict("records")
        lo = g["value_mt"].abs().min()
        hi = g["value_mt"].abs().max()
        spread = (hi - lo) / lo * 100 if lo else 100.0
        for v in shown:
            import math
            # pandas turns missing strings (unit) into float NaN; JSON forbids it
            for k, val in list(v.items()):
                if isinstance(val, float) and math.isnan(val):
                    v[k] = None
            v["page_no"] = int(v["page_no"]) if v["page_no"] is not None else None
            v["sheet_no"] = int(v["sheet_no"]) if v["sheet_no"] is not None else None
            v["ocr"] = bool(v["ocr_pages"])
            v["low_conf"] = "low_confidence" in (v["flags"] or "")
            v["superseded"] = not v["is_current_version"]
            v["partial"] = "upto" in (v["filename"] or "").lower() or \
                "advance" in (v["filename"] or "").lower()
        key = _key(ent, attr, period, None)
        out.append({
            "key": key, "entity": ent, "attribute": attr, "period": period,
            "n_values": len(shown), "spread_pct": round(spread, 1),
            "values": shown, "causes": _causes(shown),
            "status": statuses.get(key, "open"),
        })
    out.sort(key=lambda c: (c["status"] != "open", -c["spread_pct"]))
    return out[:limit]


def set_status(key: str, status: str, note: str | None = None) -> bool:
    if status not in ("open", "acknowledged", "resolved"):
        return False
    db.execute("""
        INSERT INTO conflict_status (conflict_key, status, note, updated_ts)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(conflict_key) DO UPDATE SET
            status = excluded.status,
            note = COALESCE(excluded.note, conflict_status.note),
            updated_ts = datetime('now')
    """, (key, status, note))
    return True


def status_counts() -> dict:
    counts = {"open": 0, "acknowledged": 0, "resolved": 0}
    for r in db.q("SELECT status, COUNT(*) n FROM conflict_status GROUP BY status"):
        counts[r["status"]] = r["n"]
    return counts
