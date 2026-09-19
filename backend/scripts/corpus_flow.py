"""Flowable builders for the demo corpus. FlowDoc lays headings, paragraphs,
bullets and tables across as many A4 pages as needed (every chronological
report lands at six pages); scan/xlsx/csv/docx helpers keep the other format
paths equally deep."""

from pathlib import Path

import pymupdf

PAGE_TOP = 90
PAGE_BOTTOM = 760


def add_heading(page, y, text, size=15):
    page.insert_text((72, y), text, fontsize=size, fontname="hebo", color=(0.1, 0.1, 0.1))


def add_para(page, y, text, size=11, width=450):
    rc = page.insert_textbox(pymupdf.Rect(72, y, 72 + width, y + 200), text,
                             fontsize=size, fontname="helv", color=(0.15, 0.15, 0.15))
    used = 200 - rc
    return y + max(used, size * 1.6) + 8


def add_table(page, x, y, headers, rows, col_w=None):
    col_w = col_w or [150] + [90] * (len(headers) - 1)
    row_h = 22
    w = sum(col_w)
    h = row_h * (len(rows) + 1)
    shape = page.new_shape()
    for i in range(len(rows) + 2):
        shape.draw_line((x, y + i * row_h), (x + w, y + i * row_h))
    cx = x
    for cw in col_w:
        shape.draw_line((cx, y), (cx, y + h))
        cx += cw
    shape.finish(color=(0.2, 0.2, 0.2), width=0.7)
    shape.commit()
    cx = x
    for j, htxt in enumerate(headers):
        page.insert_text((cx + 4, y + 15), str(htxt), fontsize=9.5, fontname="hebo")
        cx += col_w[j]
    for i, row in enumerate(rows):
        cx = x
        for j, val in enumerate(row):
            page.insert_text((cx + 4, y + (i + 1) * row_h + 15), str(val),
                             fontsize=9.5, fontname="helv")
            cx += col_w[j]
    return y + h + 14


class FlowDoc:
    """Append-only A4 document; blocks flow onto fresh pages as needed."""

    def __init__(self):
        self.doc = pymupdf.open()
        self.page = None
        self.y = 0
        self.new_page()

    def new_page(self):
        self.page = self.doc.new_page()
        self.y = PAGE_TOP

    def need(self, h):
        if self.y + h > PAGE_BOTTOM:
            self.new_page()

    def h1(self, text):
        self.need(60)
        add_heading(self.page, self.y, text, 17)
        self.y += 34

    def h2(self, text):
        self.need(50)
        add_heading(self.page, self.y, text, 13)
        self.y += 28

    def para(self, text):
        # conservative estimate so blocks never spill past the margin
        self.need(max(60, len(text) / 85 * 14 + 24))
        self.y = add_para(self.page, self.y, text)

    def bullets(self, items):
        self.need(len(items) * 17 + 30)
        for it in items:
            self.page.insert_text((84, self.y), "•", fontsize=11, fontname="helv")
            self.y = add_para(self.page, self.y, it, width=438) - 4
        self.y += 6

    def table(self, headers, rows, col_w=None):
        self.need((len(rows) + 1) * 22 + 30)
        self.y = add_table(self.page, 72, self.y, headers, rows, col_w)
        self.y += 4

    def save(self, path):
        self.doc.save(str(path))
        n = len(self.doc)
        self.doc.close()
        return n


def render_text_image(text_lines, out_png, rotate=0.4, quality=82):
    """Render text to a lightly-noised JPEG that still forces the OCR path
    (image-only pages) while keeping inter-word gaps wide enough for the
    recogniser to preserve token boundaries."""
    import io

    import matplotlib
    import numpy as np
    from PIL import Image, ImageFilter
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    fig.patch.set_facecolor("white")
    y = 0.95
    for line in text_lines:
        if not line:
            y -= 0.028
            continue
        if line.startswith("# "):
            fig.text(0.08, y, line[2:], fontsize=18, fontweight="bold")
            y -= 0.048
        elif line.startswith("## "):
            fig.text(0.08, y, line[3:], fontsize=14, fontweight="bold")
            y -= 0.040
        else:
            fig.text(0.08, y, line, fontsize=12, wrap=True)
            y -= 0.032
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("L")
    img = img.rotate(rotate, expand=False, fillcolor=255, resample=Image.BICUBIC)
    arr = np.array(img).astype(np.int16)
    noise = np.random.default_rng(42).integers(-5, 5, arr.shape, dtype=np.int16)
    img = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(0.1))
    img.convert("RGB").save(out_png, "JPEG", quality=quality)
    return out_png


def scan_pdf(out: Path, pages: list[list[str]], tmp_prefix: str):
    """Image-only PDF from per-page line lists (six pages per document)."""
    doc = pymupdf.open()
    for i, lines in enumerate(pages):
        png = out.parent / f"_{tmp_prefix}_{i}.jpg"
        render_text_image(lines, png)
        img = png.read_bytes()
        page = doc.new_page(width=595, height=842)
        page.insert_image(pymupdf.Rect(0, 0, 595, 842), stream=img)
        png.unlink()
    doc.save(str(out))
    n = len(doc)
    doc.close()
    return n


def write_csv(out: Path, header: str, rows: list[str]):
    out.write_text("\n".join([header] + rows), encoding="utf-8")
    return len(rows)


def xlsx_book(out: Path, sheets: list[tuple]):
    """Sheets: (name, title, header, rows). Returns (n_sheets, n_rows)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    total = 0
    for i, (name, title, header, rows) in enumerate(sheets):
        ws = wb.active if i == 0 else wb.create_sheet(name)
        ws.title = name
        ws["A1"] = title
        ws["A1"].font = Font(bold=True)
        ws.merge_cells(start_row=1, start_column=1,
                       end_row=1, end_column=len(header))
        ws.append([])
        ws.append(header)
        for r in rows:
            ws.append(list(r))
        total += len(rows)
    wb.save(out)
    return len(sheets), total
