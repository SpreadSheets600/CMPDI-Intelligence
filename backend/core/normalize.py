"""Normalization engine: Indian number formats, unit dictionary, fiscal years.
Raw strings are always preserved by callers; this module only derives
normalized counterparts. All comparisons downstream happen in normalized space."""

import re
from datetime import date

MULTIPLIERS = {
    "thousand": 1e3, "'000": 1e3,
    "lakh": 1e5, "lac": 1e5, "lakhs": 1e5, "lacs": 1e5,
    "million": 1e6, "mn": 1e6,
    "crore": 1e7, "crores": 1e7, "cr": 1e7,
    "billion": 1e9, "bn": 1e9,
}

# unit phrase -> (canonical name, factor to absolute value; mass units -> tonnes)
TONNES_UNITS = {
    "t": ("tonnes", 1.0), "tonne": ("tonnes", 1.0), "tonnes": ("tonnes", 1.0),
    "ton": ("tonnes", 1.0), "tons": ("tonnes", 1.0),
    "mt": ("tonnes", 1e6), "mnt": ("tonnes", 1e6),
    "million tonnes": ("tonnes", 1e6), "million tonne": ("tonnes", 1e6),
    "lt": ("tonnes", 1e5), "lakh tonnes": ("tonnes", 1e5), "lakh tonne": ("tonnes", 1e5),
    "kt": ("tonnes", 1e3), "'000 tonnes": ("tonnes", 1e3), "thousand tonnes": ("tonnes", 1e3),
    "'000 t": ("tonnes", 1e3),
}

OTHER_UNITS = {
    "%": ("percent", 1.0), "percent": ("percent", 1.0), "pct": ("percent", 1.0),
    "kcal/kg": ("kcal/kg", 1.0), "kcal per kg": ("kcal/kg", 1.0),
    "cu.m": ("cubic metres", 1.0), "cum": ("cubic metres", 1.0),
    "cubic metre": ("cubic metres", 1.0), "cubic metres": ("cubic metres", 1.0),
    "cubic meters": ("cubic metres", 1.0), "m3": ("cubic metres", 1.0),
    "mcm": ("million cubic metres", 1e6),
    "ha": ("hectares", 1.0), "hectare": ("hectares", 1.0), "hectares": ("hectares", 1.0),
    "sq km": ("sq km", 1.0), "km2": ("sq km", 1.0), "km": ("km", 1.0),
    "m": ("metres", 1.0), "metres": ("metres", 1.0), "meters": ("metres", 1.0),
    "mt/day": ("tonnes/day", 1e6), "tpa": ("tonnes/annum", 1.0),
    "mtpa": ("tonnes/annum", 1e6),
    "rs": ("rupees", 1.0), "rs.": ("rupees", 1.0), "inr": ("rupees", 1.0),
}

MULT_WORD = r"(?:thousand|lakh|lac|lakhs|lacs|million|mn|crore|crores|cr|billion|bn|'000)"
NUM_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")

# A number, optional multiplier word, optional unit phrase (longest-first match).
# Alphabetic units get their own \b so "31 March" cannot match unit "m" inside
# "March". A global \b would break '%' and '/' units, which are non-word chars.
# The lookbehind stops "2021-22" yielding "-22" as a quantity.
def _unit_alt(u: str) -> str:
    escaped = re.escape(u)
    return escaped + (r"\b" if u[-1].isalnum() else "")

_UNIT_ALTS = [_unit_alt(u) for u in sorted(
    list(TONNES_UNITS.keys()) + list(OTHER_UNITS.keys()), key=len, reverse=True)]
QTY_RE = re.compile(
    rf"(?<![\w.-])(?P<num>{NUM_RE.pattern})\s*(?P<mult>{MULT_WORD})?\s*(?P<unit>{'|'.join(_UNIT_ALTS)})?",
    re.IGNORECASE,
)

_NUM_CLEAN = re.compile(r"[,\s]")


def parse_number(s: str) -> float | None:
    """'1,23,456.78' -> 123456.78. Returns None when no number is present."""
    m = NUM_RE.search(s)
    if not m:
        return None
    try:
        return float(_NUM_CLEAN.sub("", m.group()))
    except ValueError:
        return None


def parse_quantity(text: str) -> tuple[float | None, str | None]:
    """Extract the first (value, canonical_unit) from text.
    '12.5 lakh tonnes' -> (1250000.0, 'tonnes'); '34.2 %' -> (34.2, 'percent')."""
    m = QTY_RE.search(text)
    if not m:
        return parse_number(text), None
    value = _to_float(m.group("num"))
    if value is None:
        return None, None
    mult = MULTIPLIERS.get((m.group("mult") or "").lower(), 1.0)
    unit_raw = m.group("unit")
    if unit_raw is None:
        return value * mult, None
    key = unit_raw.lower()
    if key in TONNES_UNITS:
        name, factor = TONNES_UNITS[key]
    elif unit_raw in OTHER_UNITS:
        name, factor = OTHER_UNITS[unit_raw]
    elif key in OTHER_UNITS:
        name, factor = OTHER_UNITS[key]
    else:
        name, factor = unit_raw, 1.0
    return value * mult * factor, name


def _to_float(s: str) -> float | None:
    try:
        return float(_NUM_CLEAN.sub("", s))
    except ValueError:
        return None


_FY_PATTERNS = [
    # FY22 / FY 22 / FY2022  (Indian FY: April-March, named by ending year)
    (re.compile(r"\bFY\s*'?(\d{2})\b", re.IGNORECASE), "short"),
    (re.compile(r"\bFY\s*'?(\d{4})\b", re.IGNORECASE), "long"),
    # 2021-22 / 2021–22 / 2021-2022
    (re.compile(r"\b(\d{4})\s*[-–—]\s*(\d{2})\b"), "span_short"),
    (re.compile(r"\b(\d{4})\s*[-–—]\s*(\d{4})\b"), "span_long"),
    # 2021-23 (multi-year span) -> use start year
    (re.compile(r"\b(\d{4})\s*[-–—]\s*(\d{2,4})\b"), "span_generic"),
]


def normalize_period(text: str) -> str | None:
    """Return ISO date of the period start, or None.
    '2021-22'/'FY22' -> 2021-04-01 (Indian fiscal year, April start).
    Bare '2021' -> 2021-01-01 (calendar year).
    'as on 31st March 2022' -> 2021-04-01: a 31-March position marks the END
    of a fiscal year, and coal reporting groups it with that fiscal year."""
    m = re.search(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", text)
    if m:
        d_, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= d_ <= 31 and 1 <= mth <= 12:
            d = date(y, mth, d_)
            if (d.month, d.day) == (3, 31):
                return date(y - 1, 4, 1).isoformat()
            return d.isoformat()
    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{4})", text, re.IGNORECASE)
    if m:
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        mth = months.index(m.group(2)[:3].lower()) + 1
        d = date(int(m.group(3)), mth, int(m.group(1)))
        if (d.month, d.day) == (3, 31):
            return date(d.year - 1, 4, 1).isoformat()
        return d.isoformat()
    # Span form first: '2021-22', 'FY 2021-23' (a bare FY-prefixed span means start year)
    m = re.search(r"(?:FY\s*'?|\b)(\d{4})\s*[-–—]\s*(\d{2,4})\b", text)
    if m:
        return date(int(m.group(1)), 4, 1).isoformat()
    m = re.search(r"\bFY\s*'?(\d{2,4})\b", text, re.IGNORECASE)
    if m:
        end_year = _expand_year(m.group(1))
        return date(end_year - 1, 4, 1).isoformat()
    m = re.search(r"\b(19|20)\d{2}\b", text)
    if m:
        return date(int(m.group()), 1, 1).isoformat()
    return None


def _expand_year(y: str) -> int:
    y = int(y)
    if y < 100:
        y += 2000
    return y


def fy_label(period_start: str | None) -> str:
    """'2021-04-01' -> 'FY2021-22' for display."""
    if not period_start:
        return "-"
    try:
        d = date.fromisoformat(period_start)
    except ValueError:
        return period_start
    if d.month == 4 and d.day == 1:
        return f"FY{d.year}-{str(d.year + 1)[-2:]}"
    return str(d.year)


def clean_text(s: str) -> str:
    """Whitespace/ligature cleanup, Unicode NFC."""
    import unicodedata
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\u00ad", "")                      # soft hyphen
    s = re.sub(r"(\w)-\n(\w)", r"\1\2", s)           # de-hyphenate line breaks
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


# Attribute vocabulary: attribute -> trigger keywords (lowercased context match)
ATTRIBUTE_KEYWORDS = {
    "production": ["production", "produced", "output"],
    "offtake": ["offtake", "off take", "despatch", "dispatch", "lifted", "supplied"],
    "reserves": ["reserves", "reserve", "geological reserves", "extractable reserve",
                 "mineable reserve", "in-situ"],
    "gcv": ["gcv", "gross calorific", "calorific value", "calorific"],
    "ash_pct": ["ash", "ash content", "% ash"],
    "moisture_pct": ["moisture"],
    "depth": ["depth", "seam thickness", "thickness"],
    "drilling": ["drilling", "drilled", "borehole", "exploration drilling"],
    "stripping_ratio": ["stripping ratio", "ob ratio", "o.b. ratio"],
    "area": ["area", "lease hold", "leasehold", "extent"],
    "manpower": ["manpower", "employees", "workforce", "men on roll"],
    "profit": ["profit", "profit before tax", "pbt", "operating profit", "obf"],
    "revenue": ["revenue", "turnover", "sales value", "income"],
    "grade": ["grade of coal", "coal grade"],
    "growth_pct": ["growth"],
    "share_pct": ["share"],
}


def context_unit(text: str) -> tuple[str | None, float]:
    """Find a unit phrase without requiring a number ('Production (lakh tonnes)'
    -> ('tonnes', 1e5)). Used to attach units to bare spreadsheet cells."""
    for unit in _UNIT_KEYS_BY_LEN:
        m = re.search(rf"(?<![\w.-]){_unit_alt(unit)}", text, re.IGNORECASE)
        if m:
            if unit in TONNES_UNITS:
                name, factor = TONNES_UNITS[unit]
                return name, factor
            if unit in OTHER_UNITS:
                name, factor = OTHER_UNITS[unit]
                return name, factor
    return None, 1.0


_UNIT_KEYS_BY_LEN = sorted(
    list(TONNES_UNITS.keys()) + list(OTHER_UNITS.keys()), key=len, reverse=True)


# Plausibility bands for physical quantities; computed-column junk that
# survives the syntax guards still fails these.
ATTRIBUTE_RANGES = {
    "ash_pct": (0, 100), "moisture_pct": (0, 100), "share_pct": (0, 100),
    "growth_pct": (-100, 500), "gcv": (500, 12000), "stripping_ratio": (0, 20),
    "depth": (0, 3000),
}


def in_range(attribute: str, value: float) -> bool:
    band = ATTRIBUTE_RANGES.get(attribute)
    return band is None or band[0] <= value <= band[1]


def detect_attribute(context: str) -> str | None:
    """Classify what a number measures. The keyword nearest to the number wins
    (callers cut the context at the number), so '... reserves of 412 MT ... GCV
    of 5,800 kcal/kg' attributes 5,800 to GCV, not reserves."""
    low = context.lower()
    best, best_pos = None, -1
    for attr, words in ATTRIBUTE_KEYWORDS.items():
        for w in words:
            pos = low.rfind(w)
            if pos > best_pos:
                best, best_pos = attr, pos
    return best
