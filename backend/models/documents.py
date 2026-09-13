"""Canonical document representation. Every parser produces this shape;
chunking, fact extraction and the viewer all consume it."""

from dataclasses import dataclass, field

# Element / chunk content types
HEADING = "HEADING"
PARAGRAPH = "PARAGRAPH"
TABLE = "TABLE"
TABLE_ROW = "TABLE_ROW"
FIGURE = "FIGURE"
CAPTION = "CAPTION"
LIST = "LIST"


@dataclass
class PageData:
    page_no: int
    text: str = ""
    ocr_used: bool = False
    avg_confidence: float | None = None
    image_path: str | None = None
    width: int = 0
    height: int = 0
    # Deterministic structural class from inspection: TEXT_ONLY | IMAGE_ONLY
    # | TEXT_IMAGE | TEXT_TABLE | IMAGE_TABLE | COMPLEX_LAYOUT | LOW_CONFIDENCE
    page_class: str = "TEXT_ONLY"
    methods: list = field(default_factory=list)  # cascade steps executed, in order


@dataclass
class ElementData:
    page_no: int | None
    sheet_no: int | None
    element_type: str
    order_idx: int
    text: str
    bbox: tuple | None = None        # [x0, y0, x1, y1] in rendered page pixels
    conf: float | None = None        # None = digital text (full confidence)
    section_path: str = ""
    method: str = ""                 # native | ocr | table | sheet | vision (+vision = LLM-interpreted)


@dataclass
class TableData:
    page_no: int | None = None
    sheet_no: int | None = None
    table_idx: int = 0
    headers: list[str] = field(default_factory=list)   # flattened header paths
    rows: list[list[dict]] = field(default_factory=list)
    # each cell: {"value_raw": str, "value_norm": str|None, "conf": float|None, "row": int, "col": int}
    section_path: str = ""
    caption: str = ""                # nearest Figure/Table caption on the page, if any
    method: str = "table"            # table | sheet


@dataclass
class SheetData:
    sheet_no: int
    name: str
    grid: list[list[dict]] = field(default_factory=list)  # raw cell grid for viewer


@dataclass
class CanonicalDoc:
    doc_type: str                     # digital_pdf | scanned_pdf | mixed_pdf | docx | xlsx | csv | image
    pages: list[PageData] = field(default_factory=list)
    sheets: list[SheetData] = field(default_factory=list)
    elements: list[ElementData] = field(default_factory=list)
    tables: list[TableData] = field(default_factory=list)
    meta: dict = field(default_factory=dict)   # title, subsidiary, dates, docx headings, etc.
