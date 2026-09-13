"""Deterministic structural inspection for PDFs. Cheap single pass — no
rendering, no OCR, no model calls — producing a per-page profile:

    chars, fonts, drawings (vector graphics), images (+area share),
    ruled tables, annotations

From the profile every page gets an independent class:

    TEXT_ONLY | IMAGE_ONLY | TEXT_IMAGE | TEXT_TABLE | IMAGE_TABLE
    | COMPLEX_LAYOUT | LOW_CONFIDENCE

and an extraction plan (ordered cascade steps): native, ocr, vision.
The vision step is only *planned*; parsers attempt it through the vision
hook and degrade gracefully when no vision-capable backend answers.
"""

from __future__ import annotations

import hashlib
import logging
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from backend.core import config

if TYPE_CHECKING:
    from backend.models.documents import CanonicalDoc

log = logging.getLogger("cmpdi.inspection")

TEXT_ONLY = "TEXT_ONLY"
IMAGE_ONLY = "IMAGE_ONLY"
TEXT_IMAGE = "TEXT_IMAGE"
TEXT_TABLE = "TEXT_TABLE"
IMAGE_TABLE = "IMAGE_TABLE"
COMPLEX_LAYOUT = "COMPLEX_LAYOUT"
LOW_CONFIDENCE = "LOW_CONFIDENCE"

PAGE_CLASSES = (TEXT_ONLY, IMAGE_ONLY, TEXT_IMAGE, TEXT_TABLE,
                IMAGE_TABLE, COMPLEX_LAYOUT, LOW_CONFIDENCE)

# drawings above this count mean vector-heavy pages (charts, maps, CAD)
_VECTOR_HEAVY = 200
# image area share above this counts as image-bearing (excludes tiny logos)
_IMAGE_AREA_SHARE = 0.05
# short text that still counts as "has text" for classification purposes
_TEXT_CHARS = 20


def _image_infos(page) -> list[dict]:
    try:
        return list(page.get_image_info())
    except Exception:
        try:
            return [{"bbox": page.get_image_bbox(x) if hasattr(page, "get_image_bbox") else None}
                    for x in page.get_images(full=True)]
        except Exception:
            return []


def profile_page(page) -> dict:
    """Deterministic, model-free profile of one PDF page."""
    try:
        text = page.get_text("text") or ""
    except Exception:
        text = ""
    chars = len(text.strip())
    try:
        fonts = sorted({f[3] for f in page.get_fonts()})
    except Exception:
        fonts = []
    try:
        drawings = len(page.get_drawings())
    except Exception:
        drawings = 0
    images = _image_infos(page)
    try:
        rect = page.rect
        page_area = max(1.0, float(rect.width * rect.height))
    except Exception:
        page_area = 1.0
    image_area = 0.0
    for info in images:
        try:
            b = info.get("bbox")
            if b:
                image_area += max(0.0, (b[2] - b[0]) * (b[3] - b[1]))
        except Exception:
            continue
    try:
        tables = len(page.find_tables().tables)
    except Exception:
        tables = 0
    try:
        annots = page.annots()
        annot_count = sum(1 for _ in annots) if annots else 0
    except Exception:
        annot_count = 0
    try:
        metadata = {"rotation": page.rotation}
    except Exception:
        metadata = {}
    return {
        "chars": chars,
        "fonts": fonts[:32],
        "drawings": drawings,
        "images": len(images),
        "image_area_share": round(image_area / page_area, 4),
        "tables": tables,
        "annots": annot_count,
        "meta": metadata,
    }


def classify_page(profile: dict) -> str:
    has_text = profile["chars"] >= _TEXT_CHARS
    has_image = (profile["images"] > 0
                 and profile["image_area_share"] >= _IMAGE_AREA_SHARE)
    has_table = profile["tables"] > 0
    vector_heavy = profile["drawings"] >= _VECTOR_HEAVY
    if vector_heavy or (has_text and has_image and has_table):
        return COMPLEX_LAYOUT
    if has_table:
        if has_image:
            return IMAGE_TABLE
        return TEXT_TABLE if has_text else IMAGE_TABLE
    if has_image:
        return TEXT_IMAGE if has_text else IMAGE_ONLY
    if has_text:
        return TEXT_ONLY
    return LOW_CONFIDENCE


def extraction_plan(page_class: str, chars: int, ocr_available: bool) -> list[str]:
    """Ordered cascade steps. 'native' is always first (cheap); 'ocr' needs
    an engine; 'vision' is attempted through the vision hook and skipped
    when no vision-capable backend answers."""
    short = chars < config.PAGE_TEXT_FLOOR
    if page_class == TEXT_ONLY:
        return ["native"]
    if page_class == TEXT_TABLE:
        return ["native"]
    if page_class == TEXT_IMAGE:
        return ["native"] + (["ocr"] if short and ocr_available else [])
    if page_class == IMAGE_ONLY:
        steps = ["native"]
        if ocr_available:
            steps.append("ocr")
        steps.append("vision")
        return steps
    if page_class == IMAGE_TABLE:
        steps = ["native"]
        if ocr_available:
            steps.append("ocr")
        steps.append("vision")
        return steps
    if page_class == COMPLEX_LAYOUT:
        steps = ["native"]
        if ocr_available:
            steps.append("ocr")
        steps.append("vision")
        return steps
    # LOW_CONFIDENCE: try everything cheap before giving up
    steps = ["native"]
    if ocr_available:
        steps.append("ocr")
    return steps


def fingerprint(text: str, page_count: int) -> str:
    """Deterministic near-duplicate signal: top terms + page count. Stored
    in the inspection profile; version grouping uses it as a cheap exact
    pre-filter before embedding comparison."""
    toks = [t.lower() for t in text.split() if len(t) > 2]
    top = sorted(Counter(toks).items(), key=lambda kv: (-kv[1], kv[0]))[:30]
    basis = f"{page_count}|" + "|".join(f"{t}:{c}" for t, c in top)
    return hashlib.sha1(basis.encode("utf-8", "ignore")).hexdigest()[:16]


def inspect_pdf(path: Path) -> dict:
    """Full-document structural inspection. Opens the PDF a second time is
    wasteful, so parsers call this once and pass the live document in."""
    import pymupdf

    doc = pymupdf.open(path)
    return inspect_open_pdf(doc)


def inspect_open_pdf(doc) -> dict:
    pages = []
    full_text_parts = []
    for pno in range(len(doc)):
        page = doc[pno]
        prof = profile_page(page)
        try:
            full_text_parts.append(page.get_text("text") or "")
        except Exception:
            pass
        prof["page_class"] = classify_page(prof)
        pages.append(prof)
    try:
        metadata = {k: v for k, v in (doc.metadata or {}).items() if v}
    except Exception:
        metadata = {}
    full_text = "\n".join(full_text_parts)
    counts = Counter(p["page_class"] for p in pages)
    return {
        "page_count": len(pages),
        "metadata": metadata,
        "pages": pages,
        "class_counts": dict(counts),
        "table_pages": sum(1 for p in pages if p["tables"] > 0),
        "image_pages": sum(1 for p in pages if p["images"] > 0),
        "fonts": sorted({f for p in pages for f in p["fonts"]})[:64],
        "fingerprint": fingerprint(full_text, len(pages)),
    }


def attach_plans(inspection: dict, ocr_available: bool) -> None:
    for prof in inspection["pages"]:
        prof["plan"] = extraction_plan(prof["page_class"], prof["chars"],
                                       ocr_available)


def inspection_for(cdoc: "CanonicalDoc") -> dict:
    """Uniform inspection view for non-PDF canonical docs (and any PDF that
    predates inspection): synthesize a deterministic profile from content."""
    if cdoc.meta.get("inspection"):
        return cdoc.meta["inspection"]
    if cdoc.doc_type in ("xlsx", "csv"):
        page_class = TEXT_TABLE
    elif cdoc.doc_type == "image":
        page_class = IMAGE_ONLY
    else:
        page_class = TEXT_ONLY
    n = max(len(cdoc.pages), len(cdoc.sheets), 1)
    pages = [{"chars": 0, "fonts": [], "drawings": 0, "images": 0,
              "image_area_share": 0.0, "tables": len(cdoc.tables),
              "annots": 0, "meta": {},
              "page_class": page_class, "plan": ["native"]} for _ in range(n)]
    return {
        "page_count": n,
        "metadata": {},
        "pages": pages,
        "class_counts": {page_class: n},
        "table_pages": 1 if cdoc.tables else 0,
        "image_pages": 0,
        "fonts": [],
        "fingerprint": fingerprint(
            "\n".join(p.text for p in cdoc.pages
                      if isinstance(getattr(p, "text", ""), str)), n),
        "synthetic": True,
    }
