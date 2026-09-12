"""Content extraction for reports. Pulls the most meaningful material out
of the library: clean narrative paragraphs from the section structure, the
best-matching extracted tables as row matrices, and cleaned fact series from
the numeric index. Everything a report needs, gathered in one place."""

import re
from datetime import date

import pandas as pd

from backend.db import database as db

# reporting window: anything outside is a parse artifact (year typos,
# long-range targets); the cap also excludes future plan targets
_MIN_PERIOD = "1995-04-01"
_MAX_PERIOD = f"{date.today().year + 1}-04-01"

# unit -> multiplier to million tonnes (MT). Values without a unit inherit
# the sheet context, which the Coal Directory states as "Qty. in MT".
_UNIT_TO_MT = {
    "mt": 1.0, "million tonnes": 1.0, "million tonne": 1.0,
    "lakh tonnes": 0.1, "lakh tonne": 0.1,
    "tonnes": 1e-6, "tonne": 1e-6, "t": 1e-6,
    "million cubic metres": None, "mt": 1.0,
}
# units that are not production quantities at all
_NON_QUANTITY = {"percent", "%", "tonnes/annum", "mtpa", "per cent"}


# ---------------------------------------------------------------- narrative

_JUNK = re.compile(
    r"^\s*[\d\s.,()%-]+$|^\s*\(?\d+\)?\s*$|^page\s+\d+|^\s*$|^[A-Z]\s*:")
_MIN_PARA = 70


def clean_paragraphs(limit: int = 400) -> list[dict]:
    """Deduplicated, meaningful prose blocks in document order. Skips number
    grids, page artifacts and fragments; keeps heading/paragraph/list text."""
    rows = db.q("""
        SELECT e.element_type, e.section_path, e.text,
               e.doc_id, e.page_no, e.sheet_no
        FROM elements e JOIN documents d ON d.id = e.doc_id
        WHERE e.text != '' ORDER BY d.upload_ts, e.order_idx
    """)
    out, seen = [], set()
    for r in rows:
        text = " ".join((r["text"] or "").split())
        if len(text) < _MIN_PARA or _JUNK.search(text[:60]):
            continue
        if text in seen:
            continue
        seen.add(text)
        out.append({
            "type": r["element_type"], "section": r["section_path"],
            "text": text, "doc_id": r["doc_id"],
            "page_no": r["page_no"], "sheet_no": r["sheet_no"],
        })
        if len(out) >= limit:
            break
    return out


def narrative_candidates(topic: str, k: int = 6) -> list[dict]:
    """Prose blocks most relevant to a topic, scored on keyword coverage."""
    from backend.core.retrieval import _tokens
    terms = [t for t in _tokens(topic) if len(t) > 3]
    scored = []
    for block in clean_paragraphs():
        low = block["text"].lower()
        hits = sum(1 for t in terms if t in low)
        # prefer complete sentences that explain, not fragments
        score = hits * 10 + min(len(block["text"]) / 200, 6)
        if hits:
            scored.append((score, block))
    scored.sort(key=lambda x: -x[0])
    picked, section_use = [], {}
    for _, b in scored:
        key = (b["doc_id"], b["section"])
        # avoid five paragraphs from one section crowding out the rest
        if section_use.get(key, 0) >= 2:
            continue
        section_use[key] = section_use.get(key, 0) + 1
        picked.append(b)
        if len(picked) >= k:
            break
    return picked


# ---------------------------------------------------------------- tables

def find_tables(keywords: list[str], limit: int = 3, min_rows: int = 4) -> list[dict]:
    """The extracted tables most relevant to keywords, as header+row matrices.
    Tables are scored on keyword hits in their cell text and numeric density."""
    kw = [k.lower() for k in keywords]
    rows = db.q("""
        SELECT t.id, t.doc_id, t.sheet_no, t.page_no, t.table_idx, t.n_rows, t.n_cols,
               d.filename
        FROM tables t JOIN documents d ON d.id = t.doc_id
        WHERE t.n_rows >= ? AND t.n_cols BETWEEN 2 AND 12
    """, (min_rows,))
    scored = []
    for t in rows:
        cells = db.q("""
            SELECT row_idx, col_idx, value_raw FROM table_cells
            WHERE table_id=? AND value_raw != '' ORDER BY row_idx, col_idx
        """, (t["id"],))
        if not cells:
            continue
        header_text = " ".join(c["value_raw"] for c in cells if c["row_idx"] == 0).lower()
        body_text = " ".join(c["value_raw"] for c in cells if c["row_idx"] > 0).lower()
        hits = sum(body_text.count(k) + header_text.count(k) * 2 for k in kw)
        numeric = sum(1 for c in cells if re.fullmatch(r"[\d,.\-]+", (c["value_raw"] or "").strip()))
        density = numeric / len(cells)
        if hits == 0:
            continue
        scored.append((hits + density * 5, density, t, cells))
    scored.sort(key=lambda x: -x[0])
    out = []
    for _, _, t, cells in scored[:limit]:
        max_col = max(c["col_idx"] for c in cells)
        matrix: dict[int, dict[int, str]] = {}
        for c in cells:
            matrix.setdefault(c["row_idx"], {})[c["col_idx"]] = (c["value_raw"] or "").strip()
        headers = [matrix.get(0, {}).get(i, f"col{i}") or f"col{i}" for i in range(max_col + 1)]
        body = [[matrix.get(r, {}).get(i, "") for i in range(max_col + 1)]
                for r in sorted(matrix) if r > 0]
        out.append({"doc_id": t["doc_id"], "filename": t["filename"],
                    "sheet_no": t["sheet_no"], "page_no": t["page_no"],
                    "table_idx": t["table_idx"], "headers": headers, "rows": body})
    return out


# ---------------------------------------------------------------- facts

_YEAR = re.compile(r"20\d{2}(-\d{2})?")


def longest_year_series(tbl: dict) -> list[tuple[str, float]]:
    """The longest parseable year -> value column in an extracted table.
    Coal Directory tables carry multi-decade Quantity columns, which make far
    richer trend charts than the fact index alone; share and growth columns
    are excluded by header text."""
    def numeric_cols():
        for i, h in enumerate(tbl["headers"]):
            hl = str(h).lower()
            if "share" in hl or "growth" in hl or "percentage" in hl or "change" in hl:
                continue
            yield i
    candidates: dict[int, list[tuple[str, float]]] = {}
    for row in tbl["rows"]:
        if not row or not _YEAR.fullmatch(str(row[0]).strip()):
            continue
        for i in numeric_cols():
            raw = str(row[i]).strip().replace(",", "") if i < len(row) else ""
            try:
                v = float(raw)
            except ValueError:
                continue
            candidates.setdefault(i, []).append((str(row[0]).strip(), v))
    if not candidates:
        return []
    best = max(candidates.values(), key=len)
    return best


def fact_series(attribute: str, entity: str | None = None,
                require_period: bool = True, fiscal_only: bool = False) -> pd.DataFrame:
    """Cleaned fact series for an attribute: entity resolved (canonical name
    or raw mention), values kept raw; period artifacts and quarantined digits
    dropped. fiscal_only keeps April-1 fiscal starts, which is how Indian coal
    reporting periods normalize. Use normalize_units() for consistent scale."""
    sql = """
        SELECT COALESCE(e.canonical_name, f.entity_text) AS entity, f.attribute,
               f.period_norm, f.value_norm, f.value_raw, f.unit, f.conf, f.flags,
               d.is_current_version, d.filename, c.doc_id, c.page_no, c.sheet_no
        FROM facts f
        LEFT JOIN entities e ON e.id = f.entity_id
        JOIN chunks c ON c.id = f.chunk_id
        JOIN documents d ON d.id = c.doc_id
        WHERE f.attribute = ? AND f.value_norm IS NOT NULL
    """
    params = [attribute]
    if entity:
        sql += " AND COALESCE(e.canonical_name, f.entity_text) = ?"
        params.append(entity)
    if fiscal_only:
        sql += " AND f.period_norm LIKE '%-04-01'"
    con = db.connect()
    df = pd.read_sql_query(sql, con, params=params)
    if df.empty:
        return df
    if require_period:
        df = df[(df["period_norm"] >= _MIN_PERIOD) & (df["period_norm"] <= _MAX_PERIOD)]
    df = df[~df["flags"].fillna("").str.contains("low_confidence")]
    df = df.dropna(subset=["value_norm"])

    def fy(p):
        try:
            d = date.fromisoformat(p)
            return f"FY{d.year}-{str(d.year + 1)[-2:]}" if (d.month, d.day) == (4, 1) else str(d.year)
        except (ValueError, TypeError):
            return None
    df["fiscal"] = df["period_norm"].map(fy) if require_period else None
    return df


def normalize_units(df: pd.DataFrame, target: str = "MT") -> pd.DataFrame:
    """Convert a series to one scale (default MT). Rows in units that cannot
    be converted (percent, capacities) are dropped; unitless rows are assumed
    to be in MT, which the Coal Directory sheets state as 'Qty. in MT'."""
    if df.empty:
        return df
    out = df.copy()
    scales = []
    for _, r in out.iterrows():
        u = "" if pd.isna(r["unit"]) else str(r["unit"]).strip().lower()
        if not u:
            scales.append(1.0)
            continue
        mult = _UNIT_TO_MT.get(u)
        scales.append(mult if mult is not None else None)
    out["_scale"] = scales
    out = out[out["_scale"].notna()]
    out["value_norm"] = out["value_norm"] * out["_scale"]
    out["unit"] = target
    return out.drop(columns=["_scale"])


def dedupe_series(df: pd.DataFrame) -> pd.DataFrame:
    """One value per (entity, fiscal): prefer current-version documents, then
    higher confidence, then the larger value (totals outrank partials)."""
    if df.empty:
        return df
    key = ["entity", "fiscal"] if "fiscal" in df else ["entity"]
    ordered = df.sort_values(["is_current_version", "conf", "value_norm"],
                             ascending=[False, False, False])
    return ordered.drop_duplicates(subset=[k for k in key if k in ordered], keep="first")


def pivot_by_year(df: pd.DataFrame, entities: list[str] | None = None,
                  last_n: int = 6) -> pd.DataFrame:
    """Entity x fiscal-year matrix of deduplicated values."""
    ded = dedupe_series(df)
    if ded.empty:
        return ded
    if entities:
        ded = ded[ded["entity"].isin(entities)]

    def fy_key(label):
        m = re.search(r"(\d{4})", str(label))
        return int(m.group(1)) if m else 0

    table = ded.pivot_table(index="fiscal", columns="entity",
                            values="value_norm", aggfunc="first")
    return table.sort_index(key=lambda idx: idx.map(fy_key)).tail(last_n)


def _fy_key(label):
    m = re.search(r"(\d{4})", str(label))
    return int(m.group(1)) if m else 0


def drop_partial_points(df: pd.DataFrame) -> pd.DataFrame:
    """Per entity, drop a trailing fiscal year whose value collapses against
    the previous one (advance releases report up to a mid-year cutoff; left
    in place they would read as a production collapse)."""
    if df.empty or "fiscal" not in df:
        return df
    keep = []
    for entity, g in df.groupby("entity"):
        g = g.sort_values("fiscal", key=lambda s: s.map(_fy_key))
        if len(g) >= 2 and g["value_norm"].iloc[-1] < 0.5 * g["value_norm"].iloc[-2]:
            g = g.iloc[:-1]
        keep.append(g)
    return pd.concat(keep) if keep else df


def highlights(df: pd.DataFrame, n: int = 4) -> list[str]:
    """Headline numbers from a series: latest-year top values and changes."""
    ded = drop_partial_points(dedupe_series(df))
    if ded.empty or "fiscal" not in ded:
        return []
    ded = ded.dropna(subset=["fiscal"])
    if ded.empty:
        return []
    out = []
    latest = ded["fiscal"].max()
    top = ded[ded["fiscal"] == latest].nlargest(n, "value_norm")
    for _, r in top.iterrows():
        line = f"{r['entity']} reported {r['value_norm']:,.2f} {r['unit'] or 'MT'} in {r['fiscal']}".strip()
        prev = ded[(ded["entity"] == r["entity"]) & (ded["fiscal"] < latest)].sort_values("fiscal")
        if not prev.empty:
            p = prev.iloc[-1]
            if p["value_norm"]:
                delta = (r["value_norm"] - p["value_norm"]) / abs(p["value_norm"]) * 100
                line += f", {delta:+.1f}% versus {p['fiscal']} ({p['value_norm']:,.2f})"
        out.append(line + ".")
    return out
