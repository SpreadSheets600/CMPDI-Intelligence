"""Compare Documents: turn the version-chain machinery into a visible
feature. Given two documents, report what changed between them: numerical
facts (entity x attribute x period with old -> new values), sections added
and removed, and the headline deltas. Values are scale-normalized like the
Conflict Radar so a tonnes-vs-MT pair is not reported as a change."""

import pandas as pd

from backend.core.reporting.content import _UNIT_TO_MT
from backend.db import database as db


def _doc(doc_id: str):
    return db.q1("SELECT * FROM documents WHERE id = ?", (doc_id,))


def version_pair(doc_id: str) -> dict | None:
    """Suggested comparison partner: the previous document in the same
    version group, or None when the document has no siblings."""
    doc = _doc(doc_id)
    if not doc or not doc["version_group_id"]:
        return None
    rows = db.q("""
        SELECT id, filename, display_name, doc_date_norm, upload_ts
        FROM documents WHERE version_group_id = ? AND id != ?
        ORDER BY doc_date_norm, upload_ts
    """, (doc["version_group_id"], doc_id))
    return dict(rows[-1]) if rows else None


def _facts_frame(doc_id: str) -> pd.DataFrame:
    rows = [dict(r) for r in db.q("""
        SELECT COALESCE(e.canonical_name, f.entity_text) AS entity,
               f.attribute, f.period_norm, f.unit, f.value_norm, f.conf,
               c.page_no, c.sheet_no
        FROM facts f
        LEFT JOIN entities e ON e.id = f.entity_id
        JOIN chunks c ON c.id = f.chunk_id
        WHERE c.doc_id = ?
          AND f.value_norm IS NOT NULL
    """, (doc_id,))]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    scales = []
    for _, r in df.iterrows():
        u = "" if pd.isna(r["unit"]) else str(r["unit"]).strip().lower()
        scales.append(_UNIT_TO_MT.get(u, 1.0 if not u else None))
    df["scale"] = scales
    df = df[df["scale"].notna()]
    df = df[df["entity"].notna() & (df["entity"] != "")]
    # 'quantity' is the raw per-cell bucket of the statistics sheets; the
    # comparison targets named metrics just like the Conflict Radar
    df = df[df["attribute"] != "quantity"]
    df["value_mt"] = df["value_norm"] * df["scale"]
    # one value per key: keep the most confident
    return (df.sort_values("conf", ascending=False)
              .drop_duplicates(subset=["entity", "attribute", "period_norm"],
                               keep="first"))


def _sections(doc_id: str) -> dict[str, str]:
    """Section path -> first meaningful paragraph, for added/removed diffs."""
    out: dict[str, str] = {}
    for r in db.q("""
        SELECT section_path, MIN(text) AS text FROM elements
        WHERE doc_id = ? AND section_path != '' AND length(text) > 40
        GROUP BY section_path
    """, (doc_id,)):
        out[r["section_path"]] = (r["text"] or "")[:160]
    return out


def compare(doc_a: str, doc_b: str) -> dict:
    a, b = _facts_frame(doc_a), _facts_frame(doc_b)
    da, db_ = _doc(doc_a), _doc(doc_b)

    fact_changes, added, removed = [], [], []
    if not a.empty and not b.empty:
        merged = a.merge(b, on=["entity", "attribute", "period_norm"],
                         how="outer", suffixes=("_a", "_b"), indicator=True)
        for _, r in merged.iterrows():
            key = {"entity": r["entity"], "attribute": r["attribute"],
                   "period": r["period_norm"]}
            if r["_merge"] == "left_only":
                removed.append({**key, "old": float(r["value_mt_a"])})
            elif r["_merge"] == "right_only":
                added.append({**key, "new": float(r["value_mt_b"])})
            else:
                old, new = float(r["value_mt_a"]), float(r["value_mt_b"])
                if old and abs(new - old) / abs(old) > 0.01:
                    fact_changes.append({**key, "old": old, "new": new,
                                         "delta_pct": round((new - old) / abs(old) * 100, 1)})
        fact_changes.sort(key=lambda x: -abs(x["delta_pct"]))

    sec_a, sec_b = _sections(doc_a), _sections(doc_b)
    new_sections = [{"path": p, "excerpt": sec_b[p]} for p in sec_b if p not in sec_a]
    removed_sections = [{"path": p, "excerpt": sec_a[p]} for p in sec_a if p not in sec_b]

    return {
        "a": {"id": doc_a, "filename": da["filename"], "name": da["display_name"],
              "date": da["doc_date_raw"], "facts": int(len(a)),
              "sections": len(sec_a)},
        "b": {"id": doc_b, "filename": db_["filename"], "name": db_["display_name"],
              "date": db_["doc_date_raw"], "facts": int(len(b)),
              "sections": len(sec_b)},
        "fact_changes": fact_changes[:30],
        "added_facts": added[:15], "removed_facts": removed[:15],
        "new_sections": new_sections[:15], "removed_sections": removed_sections[:15],
        "summary": {"changed": len(fact_changes), "added": len(added),
                    "removed": len(removed), "new_sections": len(new_sections),
                    "removed_sections": len(removed_sections)},
    }
