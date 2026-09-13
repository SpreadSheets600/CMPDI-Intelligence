"""Parsers: route heterogeneous files into the Canonical Document Model.
Digital PDFs use direct extraction; pages with too little text are OCR'd
(mixed PDFs are decided per page). DOCX preserves heading hierarchy,
XLSX/CSV preserve sheet/table/row/cell structure."""

import csv
import io
import re
from collections import Counter
from pathlib import Path

import pymupdf

from backend.models.documents import CanonicalDoc, ElementData, PageData, SheetData, TableData
from backend.core import config
from backend.core.normalize import clean_text, normalize_period, parse_quantity

EXT_TYPES = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".xlsm": "xlsx",
    ".csv": "csv",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".tif": "image",
    ".tiff": "image",
    ".bmp": "image",
}

_ZOOM = config.OCR_DPI / 72.0


# ---------------------------------------------------------------- OCR engines


class OCREngine:
    """Tesseract (word-level confidences) if the binary exists, else RapidOCR.
    Returns list of (text, conf, [x0,y0,x1,y1]) lines in page-pixel space."""

    def __init__(self):
        self._tesseract = None
        self._rapid = None
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            self._tesseract = pytesseract
        except Exception:
            try:
                from rapidocr_onnxruntime import RapidOCR

                self._rapid = RapidOCR()
            except Exception:
                pass

    @property
    def available(self) -> bool:
        return self._tesseract is not None or self._rapid is not None

    def lines(self, pil_image) -> list[tuple[str, float, list]]:
        if self._tesseract is not None:
            return self._tesseract_lines(pil_image)
        return self._rapid_lines(pil_image)

    def _tesseract_lines(self, img):
        import pytesseract

        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        lines = {}
        for i in range(len(data["text"])):
            txt = data["text"][i].strip()
            conf = float(data["conf"][i])
            if not txt or conf < 0:
                continue
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            box = [
                data["left"][i],
                data["top"][i],
                data["left"][i] + data["width"][i],
                data["top"][i] + data["height"][i],
            ]
            if key in lines:
                t, c, b = lines[key]
                n_words = len(t.split()) + 1
                lines[key] = (
                    t + " " + txt,
                    (c * (n_words - 1) + conf) / n_words,
                    [
                        min(b[0], box[0]),
                        min(b[1], box[1]),
                        max(b[2], box[2]),
                        max(b[3], box[3]),
                    ],
                )
            else:
                lines[key] = (txt, conf, box)
        return [(t, c, b) for t, c, b in lines.values()]

    def _rapid_lines(self, pil_image):
        import numpy as np

        result, _ = self._rapid(np.array(pil_image))
        out = []
        if not result:
            return out
        for box, text, conf in result:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            out.append(
                (
                    text.strip(),
                    float(conf) * 100.0,
                    [min(xs), min(ys), max(xs), max(ys)],
                )
            )
        return out


def _mean_conf(t: str, conf: float) -> float:
    return conf


_OCR = None


def ocr_engine() -> OCREngine:
    global _OCR
    if _OCR is None:
        _OCR = OCREngine()
    return _OCR


# ---------------------------------------------------------------- classify


def classify(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in EXT_TYPES and EXT_TYPES[ext] != "pdf":
        return EXT_TYPES[ext]
    if ext == ".pdf":
        return "pdf"  # refined to digital/scanned/mixed after per-page probe
    try:
        with open(path, "rb") as f:
            magic = f.read(8)
    except OSError:
        return "unknown"
    if magic.startswith(b"%PDF"):
        return "pdf"
    if magic.startswith(b"PK"):
        return "xlsx"
    if (
        magic.startswith(b"\x89PNG")
        or magic[:3] == b"\xff\xd8\xff"
        or magic[:4] == b"II*\x00"
    ):
        return "image"
    return "unknown"


# ---------------------------------------------------------------- PDF


def parse_pdf(path: Path) -> CanonicalDoc:
    """Multi-path cascade: deterministic structural inspection first (no
    rendering, no OCR), then per-page plans. Cheap pages cost one native
    pass; visual pages escalate to OCR and, when a vision-capable backend
    answers, to vision interpretation. Everything is fused into one
    canonical pass so section state stays sequential."""
    from backend.core.pipeline import inspection as insp
    from backend.core.pipeline import vision as vis

    doc = pymupdf.open(path)
    profile = insp.inspect_open_pdf(doc)
    ocr = ocr_engine()
    insp.attach_plans(profile, ocr.available)
    cdoc = CanonicalDoc(
        doc_type="digital_pdf",
        meta={"title": doc.metadata.get("title") or "",
              "inspection": profile, "vision_used": 0, "vision_skipped": 0},
    )
    for pno in range(len(doc)):
        page = doc[pno]
        prof = profile["pages"][pno]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(_ZOOM, _ZOOM))
        img_path = save_page_image(pix, path.stem, pno)
        text = page.get_text("text").strip()
        short = len(text) < config.PAGE_TEXT_FLOOR
        visual = prof["page_class"] in (insp.IMAGE_ONLY, insp.IMAGE_TABLE,
                                        insp.COMPLEX_LAYOUT)
        use_ocr = ("ocr" in prof["plan"] and (short or visual)
                   and ocr.available)
        pd = PageData(
            page_no=pno + 1,
            text=text,
            ocr_used=use_ocr,
            image_path=img_path,
            width=pix.width,
            height=pix.height,
            page_class=prof["page_class"],
            methods=["native"] + (["ocr"] if use_ocr else []),
        )
        if use_ocr:
            from PIL import Image

            img = Image.open(io.BytesIO(pix.tobytes("png")))
            lines = ocr.lines(img)
            pd._ocr_lines = lines
            pd.text = assemble_ocr_text(lines, pd)
        cdoc.pages.append(pd)

        # pass 1: locate ruled tables so their cells are not duplicated as
        # loose text; pass 2 extracts text (headings update sections); pass 3
        # builds the TableData with the now-correct section context; pass 4
        # figures (+vision escalation) with caption linkage
        regions = find_table_regions(page)
        if pd.ocr_used:
            extract_ocr_elements(cdoc, pd)
        else:
            extract_digital_elements(cdoc, page, pd, skip_boxes=regions)
        extract_tables(cdoc, page, pd, regions)
        extract_figures(cdoc, page, pd)
        budget = vis.MAX_FIGURES_PER_DOC - cdoc.meta.get("vision_used", 0)
        if "vision" in prof["plan"] and budget > 0 and vis.available():
            pd.methods.append("vision")
            interpret_figures(cdoc, page, pd, pix, budget)

    flags = [p.ocr_used for p in cdoc.pages]
    if all(flags):
        cdoc.doc_type = "scanned_pdf"
    elif any(flags):
        cdoc.doc_type = "mixed_pdf"

    derive_meta(cdoc)
    return cdoc


def save_page_image(pix, stem: str, pno: int) -> str:
    # page images land in the doc dir after the sha is known; stage in _tmp
    tmp = config.FILES_DIR / "_tmp" / f"{stem}_{pno + 1:04d}.png"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    pix.save(tmp)
    return str(tmp.relative_to(config.FILES_DIR))


def assemble_ocr_text(lines, pd: PageData):
    parts = []
    confs = []
    for text, conf, _ in lines:
        parts.append(text)
        confs.append(conf)
    pd.avg_confidence = sum(confs) / len(confs) if confs else 0.0
    return clean_text("\n".join(parts))


def extract_ocr_elements(cdoc: CanonicalDoc, pd: PageData):
    """Group OCR lines into paragraph elements; split on vertical gaps and
    heading-like short lines."""
    # lines were consumed in assemble; re-derive grouping from page text is lossy,
    # so parsers keep the raw lines on the page object
    lines = getattr(pd, "_ocr_lines", None) or []
    order = len(cdoc.elements)
    for text, conf, box in lines:
        cdoc.elements.append(
            ElementData(
                page_no=pd.page_no,
                sheet_no=None,
                element_type="PARAGRAPH",
                order_idx=order,
                text=text,
                bbox=box,
                conf=conf,
                section_path=current_section(cdoc),
                method="ocr",
            )
        )
        order += 1


def extract_digital_elements(cdoc: CanonicalDoc, page, pd: PageData, skip_boxes=None):
    """Blocks -> paragraphs/headings via font-size clustering; reading order
    follows block geometry (top-to-bottom, left column first). Blocks whose
    centre falls inside a detected table region are skipped (already
    represented structurally)."""
    skip_boxes = skip_boxes or []
    sizes = Counter()
    spans_by_block = {}
    d = page.get_text("dict")
    for bno, block in enumerate(d["blocks"]):
        if block.get("type") != 0:
            continue
        if _in_any_box(block["bbox"], skip_boxes):
            continue
        lines = []
        for line in block["lines"]:
            for span in line["spans"]:
                if span["text"].strip():
                    sizes[round(span["size"], 1)] += len(span["text"])
                    lines.append((span["size"], span["text"]))
        if lines:
            spans_by_block[bno] = lines
    body_size = sizes.most_common(1)[0][0] if sizes else 11.0

    blocks = sorted(
        (
            b
            for b in d["blocks"]
            if b.get("type") == 0 and b["number"] in spans_by_block
        ),
        key=lambda b: (round(b["bbox"][1]), b["bbox"][0]),
    )

    # heading levels: distinct sizes above body size, descending
    heading_sizes = sorted(
        {
            s
            for lines in spans_by_block.values()
            for s, _ in lines
            if s >= body_size + 1.5
        },
        reverse=True,
    )

    order = len(cdoc.elements)
    for block in blocks:
        lines = spans_by_block[block["number"]]
        text = clean_text(" ".join(t for _, t in lines))
        if not text:
            continue
        max_size = max(s for s, _ in lines)
        bbox = scale_bbox(block["bbox"])
        if max_size >= body_size + 1.5 and len(text) < 150:
            level = heading_sizes.index(max_size) if max_size in heading_sizes else 0
            push_heading(cdoc, text, level)
            etype = "HEADING"
        else:
            etype = "LIST" if _looks_like_list(text) else "PARAGRAPH"
        cdoc.elements.append(
            ElementData(
                page_no=pd.page_no,
                sheet_no=None,
                element_type=etype,
                order_idx=order,
                text=text,
                bbox=bbox,
                conf=None,
                section_path=current_section(cdoc),
                method="native",
            )
        )
        order += 1
        # timeline of section state by vertical position, so tables (built
        # after text) get the section in effect at their own y-position
        timeline = cdoc.meta.setdefault("_section_timeline", {}).setdefault(pd.page_no, [])
        timeline.append((block["bbox"][3], current_section(cdoc)))


def section_at(cdoc: CanonicalDoc, page_no: int, y: float) -> str:
    timeline = cdoc.meta.get("_section_timeline", {}).get(page_no, [])
    section = ""
    for y_bottom, sec in timeline:
        if y_bottom <= y + 2:
            section = sec
    return section


def _looks_like_list(text: str) -> bool:
    return bool(
        re.match(
            r"^\s*([ivx]+[\).]|\(?[a-z][\).]|[-•*]|\d+[\.\)])\s+\w", text, re.IGNORECASE
        )
    )


def _in_any_box(bbox, boxes) -> bool:
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    for b in boxes:
        if b[0] - 2 <= cx <= b[2] + 2 and b[1] - 2 <= cy <= b[3] + 2:
            return True
    return False


def scale_bbox(bbox) -> list:
    return [round(v * _ZOOM, 1) for v in bbox]


# ---------------------------------------------------------------- sections


def push_heading(cdoc: CanonicalDoc, text: str, level: int):
    stack = cdoc.meta.setdefault("_section_stack", [])
    del stack[level:]
    stack.append(text)


def current_section(cdoc: CanonicalDoc) -> str:
    stack = cdoc.meta.get("_section_stack", [])
    return " > ".join(stack[-3:]) if stack else ""


# ---------------------------------------------------------------- tables


def find_table_regions(page) -> list[list]:
    try:
        return [list(t.bbox) for t in page.find_tables().tables]
    except Exception:
        return []


def extract_tables(cdoc: CanonicalDoc, page, pd: PageData, regions: list[list]):
    found = (
        {tuple(b): t for b, t in zip(regions, page.find_tables().tables)}
        if regions
        else {}
    )
    for bbox in regions:
        t = found[tuple(bbox)]
        extraction = t.extract()
        if not extraction or len(extraction) < 2:
            continue
        header = [clean_text(str(c)) if c is not None else "" for c in extraction[0]]
        # continuation: page-spanning tables repeat no header and match column count
        if (
            cdoc.tables
            and not any(header)
            and len(header) == len(cdoc.tables[-1].headers)
        ):
            prev = cdoc.tables[-1]
            for r in extraction[1:]:
                prev.rows.append(_cells_from_row(r, len(prev.rows)))
            continue
        rows = [_cells_from_row(r, i) for i, r in enumerate(extraction[1:])]
        cdoc.tables.append(
            TableData(
                page_no=pd.page_no,
                sheet_no=None,
                table_idx=len(cdoc.tables),
                headers=header,
                rows=rows,
                section_path=section_at(cdoc, pd.page_no, bbox[1]) or current_section(cdoc),
            )
        )


def _cells_from_row(row, row_idx: int) -> list[dict]:
    cells = []
    for col, val in enumerate(row):
        raw = clean_text(str(val)) if val is not None else ""
        v, u = parse_quantity(raw) if raw else (None, None)
        cells.append(
            {
                "row": row_idx,
                "col": col,
                "value_raw": raw,
                "value_norm": v,
                "unit": u,
                "conf": None,
            }
        )
    return cells


_CAPTION_RE = re.compile(
    r"^(Figure|Fig\.|Chart|Graph|Exhibit|Table)\s*\d*", re.IGNORECASE)


def extract_figures(cdoc: CanonicalDoc, page, pd: PageData):
    """Figures are first-class elements: bbox + page provenance, caption
    linkage (nearest Figure/Chart caption on the page becomes the figure's
    text so it stays searchable), method recorded for the cascade."""
    order = len(cdoc.elements)
    for info in page.get_image_info():
        bbox = scale_bbox(info["bbox"])
        if (bbox[2] - bbox[0]) < 40 or (bbox[3] - bbox[1]) < 40:
            continue
        cdoc.elements.append(
            ElementData(
                page_no=pd.page_no,
                sheet_no=None,
                element_type="FIGURE",
                order_idx=order,
                text="",
                bbox=bbox,
                conf=None,
                section_path=current_section(cdoc),
                method="native",
            )
        )
        order += 1
    # captions: paragraphs starting with Figure/Fig./Chart near images
    captions = []
    for el in list(cdoc.elements):
        if el.page_no != pd.page_no or el.element_type != "PARAGRAPH":
            continue
        if _CAPTION_RE.match(el.text):
            captions.append(el)
            cdoc.elements.append(
                ElementData(
                    page_no=pd.page_no,
                    sheet_no=None,
                    element_type="CAPTION",
                    order_idx=order,
                    text=el.text,
                    bbox=el.bbox,
                    conf=None,
                    section_path=el.section_path,
                    method=el.method or "native",
                )
            )
            order += 1
    # link each figure to its nearest caption so figures carry text
    if captions:
        figs = [el for el in cdoc.elements
                if el.page_no == pd.page_no and el.element_type == "FIGURE"
                and not el.text]
        for fig in figs:
            cap = min(captions, key=lambda c: abs(c.order_idx - fig.order_idx))
            fig.text = cap.text


def interpret_figures(cdoc: CanonicalDoc, page, pd: PageData, pix, budget: int):
    """Vision escalation: crop each uninterpreted figure and ask the vision
    model for a structured description. OCR text and the source image are
    always kept; the interpretation is fused into the figure element with
    method='vision' so downstream consumers know its provenance."""
    from backend.core.pipeline import vision as vis

    figs = [el for el in cdoc.elements
            if el.page_no == pd.page_no and el.element_type == "FIGURE"
            and el.method != "vision"]
    try:
        infos = [i for i in page.get_image_info()
                 if (i["bbox"][2] - i["bbox"][0]) >= 40 / _ZOOM
                 and (i["bbox"][3] - i["bbox"][1]) >= 40 / _ZOOM]
    except Exception:
        infos = []
    for fig, info in zip(figs[:budget], infos[:budget]):
        try:
            png = vis.crop_png(pix, list(info["bbox"]), _ZOOM)
        except Exception:
            png = None
        if not png:
            cdoc.meta["vision_skipped"] = cdoc.meta.get("vision_skipped", 0) + 1
            continue
        caption = fig.text or ""
        desc = vis.describe_figure(png, caption=caption)
        if not desc:
            cdoc.meta["vision_skipped"] = cdoc.meta.get("vision_skipped", 0) + 1
            continue
        parts = [f"[Figure: {desc['type']}]"]
        if desc["title"]:
            parts.append(desc["title"])
        if desc["summary"]:
            parts.append(desc["summary"])
        if desc["numbers"]:
            parts.append("Numbers: " + "; ".join(desc["numbers"]))
        if desc["trend"] not in ("", "unclear"):
            parts.append(f"Trend: {desc['trend']}")
        fig.text = (caption + " — " if caption else "") + " ".join(parts)
        fig.method = "vision"
        cdoc.meta["vision_used"] = cdoc.meta.get("vision_used", 0) + 1


# ---------------------------------------------------------------- DOCX


def parse_docx(path: Path) -> CanonicalDoc:
    import docx

    d = docx.Document(path)
    cdoc = CanonicalDoc(
        doc_type="docx",
        meta={
            "title": d.core_properties.title or "",
            "created": str(d.core_properties.created or ""),
        },
    )
    page = PageData(page_no=1)
    cdoc.pages.append(page)
    order = 0
    heading_re = re.compile(r"Heading (\d)")
    from docx.text.paragraph import Paragraph

    for item in d.iter_inner_content():
        if isinstance(
            item, Paragraph
        ):  # Table has .style too, so discriminate by class
            text = clean_text(item.text)
            if not text:
                continue
            m = heading_re.match(item.style.name or "")
            if m:
                push_heading(cdoc, text, int(m.group(1)) - 1)
                cdoc.elements.append(
                    ElementData(
                        page_no=1,
                        sheet_no=None,
                        element_type="HEADING",
                        order_idx=order,
                        text=text,
                        conf=None,
                        section_path=current_section(cdoc),
                        method="native",
                    )
                )
            else:
                etype = "LIST" if "List" in (item.style.name or "") else "PARAGRAPH"
                cdoc.elements.append(
                    ElementData(
                        page_no=1,
                        sheet_no=None,
                        element_type=etype,
                        order_idx=order,
                        text=text,
                        conf=None,
                        section_path=current_section(cdoc),
                        method="native",
                    )
                )
            order += 1
        else:  # Table
            headers = [clean_text(c.text) for c in item.rows[0].cells]
            rows = []
            for ridx, row in enumerate(item.rows[1:]):
                rows.append(_cells_from_row([c.text for c in row.cells], ridx))
            cdoc.tables.append(
                TableData(
                    page_no=1,
                    sheet_no=None,
                    table_idx=len(cdoc.tables),
                    headers=headers,
                    rows=rows,
                    section_path=current_section(cdoc),
                    method="table",
                )
            )
            cdoc.elements.append(
                ElementData(
                    page_no=1,
                    sheet_no=None,
                    element_type="TABLE",
                    order_idx=order,
                    text=f"[Table: {', '.join(h for h in headers if h)}]",
                    conf=None,
                    section_path=current_section(cdoc),
                    method="table",
                )
            )
            order += 1
    extract_docx_images(d, cdoc)
    derive_meta(cdoc)
    return cdoc


def extract_docx_images(d, cdoc: CanonicalDoc):
    """Embedded visuals become first-class FIGURE elements (bytes go straight
    to the vision hook — no disk staging), with caption linkage against
    Figure/Chart paragraphs like the PDF path."""
    from backend.core.pipeline import vision as vis

    order = len(cdoc.elements)
    try:
        blobs = []
        for rel in d.part.rels.values():
            try:
                if "image" in rel.reltype and hasattr(rel.target_part, "blob"):
                    blobs.append(rel.target_part.blob)
            except Exception:
                continue
    except Exception:
        blobs = []
    captions = [el for el in cdoc.elements
                if el.element_type == "PARAGRAPH" and _CAPTION_RE.match(el.text)]
    budget = vis.MAX_FIGURES_PER_DOC if vis.available() else 0
    for blob in blobs:
        try:
            if len(blob) < 4096:
                continue
        except Exception:
            continue
        cap = min(captions, key=lambda c: abs(c.order_idx - order),
                  default=None) if captions else None
        text, method = (cap.text if cap else ""), "native"
        if budget > 0:
            desc = vis.describe_figure(blob, caption=text)
            if desc:
                parts = [f"[Figure: {desc['type']}]"]
                if desc["title"]:
                    parts.append(desc["title"])
                if desc["summary"]:
                    parts.append(desc["summary"])
                if desc["numbers"]:
                    parts.append("Numbers: " + "; ".join(desc["numbers"]))
                text = (text + " — " if text else "") + " ".join(parts)
                method = "vision"
                budget -= 1
                cdoc.meta["vision_used"] = cdoc.meta.get("vision_used", 0) + 1
            else:
                cdoc.meta["vision_skipped"] = cdoc.meta.get("vision_skipped", 0) + 1
        cdoc.elements.append(
            ElementData(
                page_no=1,
                sheet_no=None,
                element_type="FIGURE",
                order_idx=order,
                text=text,
                conf=None,
                section_path=current_section(cdoc),
                method=method,
            )
        )
        order += 1


# ---------------------------------------------------------------- XLSX / CSV


def parse_xlsx(path: Path) -> CanonicalDoc:
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True)
    cdoc = CanonicalDoc(doc_type="xlsx", meta={"title": path.stem})
    for sno, ws in enumerate(wb.worksheets, start=1):
        sheet = SheetData(sheet_no=sno, name=ws.title)
        grid = build_grid(ws)
        sheet.grid = grid
        cdoc.sheets.append(sheet)
        extract_sheet_regions(cdoc, sheet)
    derive_meta(cdoc)
    return cdoc


def build_grid(ws) -> list[list[dict]]:
    grid = [
        [{"value_raw": "", "merged": False} for _ in range(ws.max_column)]
        for _ in range(ws.max_row)
    ]
    for row in ws.iter_rows():
        for cell in row:
            if cell.value is not None:
                grid[cell.row - 1][cell.column - 1]["value_raw"] = str(cell.value)
    for rng in ws.merged_cells.ranges:
        top = grid[rng.min_row - 1][rng.min_col - 1]["value_raw"]
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                if r == rng.min_row and c == rng.min_col:
                    continue
                grid[r - 1][c - 1]["value_raw"] = top
                grid[r - 1][c - 1]["merged"] = True
    return grid


def extract_sheet_regions(cdoc: CanonicalDoc, sheet: SheetData):
    """Split a sheet into table regions at blank-row bands; first string-heavy
    row of each region is the header."""
    grid = sheet.grid
    regions, current = [], []
    for ridx, row in enumerate(grid):
        if any(c["value_raw"] for c in row):
            current.append(ridx)
        elif current:
            regions.append(current)
            current = []
    if current:
        regions.append(current)
    order = len(cdoc.elements)
    tidx = len(cdoc.tables)
    pending_title = None
    for region in regions:
        # drop leading uniform rows (merged title bands like "Production (MT)");
        # a title carries to the next region even across blank-row bands
        title = pending_title
        pending_title = None
        while region:
            row_vals = [
                grid[region[0]][c]["value_raw"]
                for c in range(len(grid[region[0]]))
                if grid[region[0]][c]["value_raw"]
            ]
            if len(row_vals) >= 2 and len(set(row_vals)) == 1:
                title = row_vals[0]
                region = region[1:]
            else:
                break
        if not region:
            pending_title = title
            continue
        if len(region) < 2:
            # lone row: keep as paragraph element for searchability
            text = " | ".join(c["value_raw"] for c in grid[region[0]] if c["value_raw"])
            if text:
                cdoc.elements.append(
                    ElementData(
                        page_no=None,
                        sheet_no=sheet.sheet_no,
                        element_type="PARAGRAPH",
                        order_idx=order,
                        text=text,
                        conf=None,
                        section_path=f"{sheet.name}",
                        method="sheet",
                    )
                )
                order += 1
            continue
        sec_base = f"{sheet.name} > {title}" if title else sheet.name
        first = grid[region[0]]
        # header row: has text cells, and the row below is mostly data
        non_numeric = sum(
            1
            for c in first
            if c["value_raw"] and parse_quantity(c["value_raw"])[0] is None
        )
        if len(region) > 1:
            second_numeric = sum(
                1
                for c in grid[region[1]]
                if c["value_raw"] and parse_quantity(c["value_raw"])[0] is not None
            )
        else:
            second_numeric = 0
        header_like = non_numeric >= 2 or (non_numeric >= 1 and second_numeric >= 2)
        if header_like:
            headers = [c["value_raw"] for c in first]
            data_rows = region[1:]
        else:
            headers = [f"Column {i + 1}" for i in range(len(first))]
            data_rows = region
        rows = []
        for ridx in data_rows:
            cells = []
            for cidx, cell in enumerate(grid[ridx]):
                raw = cell["value_raw"]
                v, u = parse_quantity(raw) if raw else (None, None)
                cells.append(
                    {
                        "row": len(rows),
                        "col": cidx,
                        "value_raw": raw,
                        "value_norm": v,
                        "unit": u,
                        "conf": None,
                    }
                )
            rows.append(cells)
        sec = f"{sec_base} > Table {tidx + 1}"
        cdoc.tables.append(
            TableData(
                page_no=None,
                sheet_no=sheet.sheet_no,
                table_idx=tidx,
                headers=headers,
                rows=rows,
                section_path=sec,
                method="sheet",
            )
        )
        cdoc.elements.append(
            ElementData(
                page_no=None,
                sheet_no=sheet.sheet_no,
                element_type="TABLE",
                order_idx=order,
                text=f"[Table: {', '.join(h for h in headers if h)}]",
                conf=None,
                section_path=sec,
                method="sheet",
            )
        )
        order += 1
        tidx += 1


def parse_csv(path: Path) -> CanonicalDoc:
    raw = path.read_bytes()
    text = None
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if text is None:
        raise ValueError("Could Not Decode CSV File")
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample)
        delim = dialect.delimiter
    except csv.Error:
        delim = ";" if sample.count(";") > sample.count(",") else ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    cdoc = CanonicalDoc(doc_type="csv", meta={"title": path.stem})
    sheet = SheetData(sheet_no=1, name=path.stem)
    sheet.grid = [[{"value_raw": v, "merged": False} for v in row] for row in rows]
    width = max((len(r) for r in rows), default=0)
    for r in sheet.grid:
        r.extend([{"value_raw": "", "merged": False}] * (width - len(r)))
    cdoc.sheets.append(sheet)
    extract_sheet_regions(cdoc, sheet)
    derive_meta(cdoc)
    return cdoc


def parse_image(path: Path) -> CanonicalDoc:
    from PIL import Image

    from backend.core.pipeline import vision as vis

    cdoc = CanonicalDoc(doc_type="image", meta={"title": path.stem,
                                                "vision_used": 0,
                                                "vision_skipped": 0})
    img = Image.open(path)
    pd = PageData(page_no=1, width=img.width, height=img.height, ocr_used=True,
                  page_class="IMAGE_ONLY", methods=["native"])
    if ocr_engine().available:
        lines = ocr_engine().lines(img)
        pd.text = assemble_ocr_text(lines, pd)
        pd._ocr_lines = lines
        pd.methods.append("ocr")
        extract_ocr_elements(cdoc, pd)
    if vis.available():
        import io as _io

        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        desc = vis.describe_figure(buf.getvalue())
        if desc:
            parts = [f"[Figure: {desc['type']}]"]
            if desc["title"]:
                parts.append(desc["title"])
            if desc["summary"]:
                parts.append(desc["summary"])
            if desc["numbers"]:
                parts.append("Numbers: " + "; ".join(desc["numbers"]))
            cdoc.elements.append(
                ElementData(page_no=1, sheet_no=None, element_type="FIGURE",
                            order_idx=len(cdoc.elements), text=" ".join(parts),
                            conf=None, section_path="", method="vision"))
            pd.methods.append("vision")
            cdoc.meta["vision_used"] = 1
        else:
            cdoc.meta["vision_skipped"] = 1
    cdoc.pages.append(pd)
    derive_meta(cdoc)
    return cdoc


# ---------------------------------------------------------------- meta


def derive_meta(cdoc: CanonicalDoc):
    full_text = "\n".join(p.text for p in cdoc.pages)
    for el in cdoc.elements:
        full_text += "\n" + el.text

    if not cdoc.meta.get("title"):
        for el in cdoc.elements:
            if el.element_type == "HEADING":
                cdoc.meta["title"] = el.text
                break
        else:
            cdoc.meta["title"] = cdoc.meta.get("title") or ""

    from backend.core import config as cfg

    counts = {}
    for abbr, full in cfg.SUBSIDIARIES.items():
        if re.search(rf"\b{abbr}\b", full_text):
            counts[abbr] = counts.get(abbr, 0) + len(
                re.findall(rf"\b{abbr}\b", full_text)
            )
        if re.search(rf"\b{re.escape(full)}\b", full_text, re.IGNORECASE):
            counts[abbr] = counts.get(abbr, 0) + len(
                re.findall(re.escape(full), full_text, re.IGNORECASE)
            )
    if counts:
        cdoc.meta["subsidiary"] = max(counts, key=counts.get)
        cdoc.meta["subsidiary_full"] = cfg.SUBSIDIARIES[max(counts, key=counts.get)]

    m = re.search(
        r"(?:Annual Report|Financial Year|Fiscal Year|Year)[\s:]*([12]\d{3}\s*[-–—]\s*\d{2,4}|[12]\d{3})",
        full_text,
        re.IGNORECASE,
    )
    if m:
        cdoc.meta["doc_date_raw"] = m.group(1)
        cdoc.meta["doc_date_norm"] = normalize_period(m.group(1))


def parse(path: Path) -> CanonicalDoc:
    kind = classify(path)
    if kind == "pdf":
        return parse_pdf(path)
    if kind == "docx":
        return parse_docx(path)
    if kind == "xlsx":
        return parse_xlsx(path)
    if kind == "csv":
        return parse_csv(path)
    if kind == "image":
        return parse_image(path)
    raise ValueError(f"Unsupported File Type: {path.suffix or 'unknown'}")
