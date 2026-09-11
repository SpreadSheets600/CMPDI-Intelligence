"""Generate a synthetic demo corpus that exercises every pipeline path:
digital PDF (headings, tables, figures), scanned PDF (image-only), mixed PDF,
multi-sheet XLSX with merged cells, CSV, parliamentary DOCX, a revised
version of the annual report, a duplicate, and a corrupt file. One planted
data conflict: two documents disagree about Kusunda Mine's FY2021-22 output."""

import sys
from pathlib import Path

import numpy as np
import pymupdf

OUT = Path(__file__).resolve().parents[2] / "data" / "demo_corpus"

MINES = ["Kusunda Mine", "Dipka OCP", "Gevra Area", "Barpali Mine"]


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


def make_annual_report(revised=False):
    doc = pymupdf.open()
    page = doc.new_page()  # A4
    add_heading(page, 90, "SECL Annual Report FY2021-22", 17)
    add_heading(page, 120, "1. Overview", 13)
    y = add_para(page, 138,
        "South Eastern Coalfields Limited (SECL) recorded total coal production of "
        "157.30 MT during FY2021-22, against 143.85 MT in the previous year. "
        "Kusunda Mine is an underground mine in the Korba coalfield with "
        "established geological reserves of 412.60 MT. The mine achieved an "
        "average GCV of 5,800 kcal/kg with ash content of 22.4 percent. "
        "Dipka OCP and Gevra Area are the largest open cast projects of the company.")
    add_heading(page, y + 10, "2. Production Performance", 13)
    y2 = add_para(page, y + 28,
        "Mine-wise production for the last three financial years is presented below. "
        "Values are in million tonnes (MT).")
    prod_rows = [
        ["Kusunda Mine", "4.10", "4.85", "5.32"],
        ["Dipka OCP", "12.60", "13.75", "14.90"],
        ["Gevra Area", "35.20", "37.40", "39.10"],
        ["Barpali Mine", "6.30", "6.85", "7.20"],
    ]
    add_table(page, 72, y2, ["Mine", "2020-21", "2021-22", "2022-23"], prod_rows)
    y3 = y2 + 6 * 22 + 30
    add_heading(page, y3, "3. Reserves", 13)
    reserves = "812.45" if not revised else "818.90"
    add_para(page, y3 + 18,
        f"Total extractable reserves of the company as on 1 April 2022 stand at "
        f"{reserves} MT. Geological reserves of Barpali Mine are 289.15 MT with "
        "stripping ratio of 2.45 cu.m per tonne.")

    page2 = doc.new_page()
    add_heading(page2, 90, "4. Quality and Manpower", 13)
    add_para(page2, 118,
        "The company employed 82,415 persons as on 31 March 2022. Operating profit "
        "before tax (OB folder) for the year was Rs 4,285.60 crore. Grade-wise coal "
        "despatch is monitored monthly. The average grade of coal despatched improved to G12.")
    add_table(page2, 72, 200, ["Mine", "GCV (kcal/kg)", "Ash (%)", "Depth (m)"],
              [["Kusunda Mine", "5800", "22.4", "310"],
               ["Dipka OCP", "5100", "28.1", "95"],
               ["Gevra Area", "4950", "30.6", "110"]])
    out = OUT / ("annual_report_revised.pdf" if revised else "annual_report.pdf")
    doc.save(str(out))
    doc.close()
    return out


def render_text_image(text_lines, out_png, rotate=0.9, quality=75):
    """Render text to a noisy, slightly rotated JPEG that forces the OCR path."""
    import io
    from PIL import Image, ImageFilter
    import matplotlib
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
            fig.text(0.08, y, line[2:], fontsize=17, fontweight="bold")
            y -= 0.045
        elif line.startswith("## "):
            fig.text(0.08, y, line[3:], fontsize=13, fontweight="bold")
            y -= 0.038
        else:
            fig.text(0.08, y, line, fontsize=10.5, wrap=True)
            y -= 0.030
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("L")
    img = img.rotate(rotate, expand=False, fillcolor=255, resample=Image.BICUBIC)
    arr = np.array(img).astype(np.int16)
    noise = np.random.default_rng(42).integers(-8, 8, arr.shape, dtype=np.int16)
    img = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(0.25))
    img.convert("RGB").save(out_png, "JPEG", quality=quality)
    return out_png


def make_scanned_geological_report():
    """Image-only PDF with the planted conflicting production figure."""
    pages = [
        ["# Geological Report: Korba Coalfield",
         "## Exploration Summary",
         "The Korba coalfield of SECL comprises the Kusunda Mine, Dipka OCP and",
         "Gevra Area workings within the Chhattisgarh state. This report",
         "consolidates exploration results for the period 2021-22.",
         "",
         "## Seam Details",
         "The Korba seam occurs at a depth of 105 m to 310 m with an average",
         "thickness of 12.8 m. GCV of the Korba seam averages 5,650 kcal/kg.",
         "The seam dips at 1 in 5.5 towards the south-east."],
        ["# Production Reconciliation 2021-22",
         "## Mine-wise Production",
         "As per the reconciliation exercise, Kusunda Mine produced 4.35 MT",
         "during FY2021-22. Dipka OCP produced 13.75 MT and Gevra Area",
         "recorded offtake of 36.90 MT during the same period.",
         "",
         "## geological reserves",
         "Extractable reserves of Kusunda Mine are estimated at 405.20 MT as",
         "on April 2022, with ash content of 23.1 percent."],
    ]
    doc = pymupdf.open()
    for i, lines in enumerate(pages):
        png = OUT / f"_scan_page_{i}.jpg"
        render_text_image(lines, png)
        img = open(png, "rb").read()
        page = doc.new_page(width=595, height=842)
        page.insert_image(pymupdf.Rect(0, 0, 595, 842), stream=img)
        png.unlink()
    out = OUT / "geological_report_scan.pdf"
    doc.save(str(out))
    doc.close()
    return out


def make_mixed_pdf():
    doc = pymupdf.open()
    page = doc.new_page()
    add_heading(page, 90, "Quarterly Review Note (Digital)", 15)
    add_para(page, 120,
        "This note reviews the Q4 performance of WCL subsidiaries. Coal offtake of "
        "SECL in the fourth quarter was 39.85 MT. Manpower productivity improved "
        "by 4.2 percent year on year.")
    page2 = doc.new_page()
    add_para(page2, 90,
        "Safety statistics remained satisfactory with 0.16 reportable incidents "
        "per thousand manpower. Output per man shift (OMS) at underground mines "
        "reached 2.68 tonnes.")
    # image-only page forces per-page OCR in the mixed flow
    png = OUT / "_mixed_page.jpg"
    render_text_image(["# Annexure: Scanned Circular",
                       "The area manager shall ensure despatch of grade G12 coal",
                       "to the thermal plants as per the linked quantity of",
                       "1.85 lakh tonnes for the month of March 2022."], png)
    img = open(png, "rb").read()
    page3 = doc.new_page()
    page3.insert_image(pymupdf.Rect(0, 0, 595, 842), stream=img)
    png.unlink()
    out = OUT / "quarterly_review_mixed.pdf"
    doc.save(str(out))
    doc.close()
    return out


def make_xlsx():
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Production"
    ws["A1"] = "Production (lakh tonnes)"
    ws["A1"].font = Font(bold=True)
    ws.merge_cells("A1:D1")
    ws.append([])  # blank band separates title from header
    ws.append(["Mine", "2020-21", "2021-22", "2022-23"])
    for mine, vals in zip(MINES, [[41.0, 48.5, 53.2], [126.0, 137.5, 149.0],
                                  [352.0, 374.0, 391.0], [63.0, 68.5, 72.0]]):
        ws.append([mine] + vals)
    ws2 = wb.create_sheet("Offtake")
    ws2["A1"] = "Offtake (lakh tonnes)"
    ws2["A1"].font = Font(bold=True)
    ws2.merge_cells("A1:C1")
    ws2.append([])
    ws2.append(["Mine", "2021-22", "2022-23"])
    ws2.append(["Kusunda Mine", 47.9, 52.6])
    ws2.append(["Dipka OCP", 136.2, 148.1])
    # second table on the same sheet, split by blank rows
    ws2.append([])
    ws2.append([])
    ws2.append(["Subsidiary", "Offtake 2021-22", "Share (%)"])
    ws2.append(["SECL", 1539.8, 24.7])
    ws2.append(["CIL", 6226.4, 100.0])
    out = OUT / "production_workbook.xlsx"
    wb.save(out)
    return out


def make_csv():
    out = OUT / "dispatch_register.csv"
    lines = ["Date,Rake,Grade,Quantity (tonnes),Destination",
             "2022-01-14,R-1201,G12,3850,Korba TPS",
             "2022-02-03,R-1244,G11,4120,Sipat TPS",
             "2022-03-21,R-1290,G12,3975,Korba TPS"]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def make_parliamentary_docx():
    import docx
    d = docx.Document()
    d.add_heading("Parliamentary Questions Extract, Session 2022", 0)
    d.add_heading("Starred Question No. 214", level=1)
    d.add_paragraph("Question: What is the current status of coal production in "
                    "the subsidiaries of Coal India Limited, subsidiary-wise?")
    d.add_paragraph("Reply: The subsidiary-wise raw coal production of Coal India "
                    "Limited (CIL) during FY2021-22 is as under:")
    t = d.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "Subsidiary", "Production (MT)", "Growth (%)"
    for name, prod, growth in [("ECL", "62.10", "5.2"), ("BCCL", "55.30", "7.8"),
                               ("SECL", "157.30", "9.3"), ("MCL", "163.20", "4.9")]:
        row = t.add_row().cells
        row[0].text, row[1].text, row[2].text = name, prod, growth
    d.add_heading("Unstarred Question No. 388", level=1)
    d.add_paragraph("Question: The steps taken to augment evacuation capacity…")
    d.add_paragraph("Reply: The following initiatives were taken:")
    for item in ("Construction of the Tori-Shivpur railway line.",
                 "First Mile Connectivity projects at Dipka OCP and Gevra Area.",
                 "Rapid loading silos commissioned at Barpali Mine."):
        d.add_paragraph(item, style="List Bullet")
    out = OUT / "parliamentary_qa.docx"
    d.save(str(out))
    return out


def main():
    OUT.mkdir(exist_ok=True)
    np.random.seed(42)
    made = [
        make_annual_report(revised=False),
        make_annual_report(revised=True),
        make_scanned_geological_report(),
        make_mixed_pdf(),
        make_xlsx(),
        make_csv(),
        make_parliamentary_docx(),
    ]
    # duplicate + corrupt files for dedup / failure demos
    import shutil
    shutil.copy2(OUT / "annual_report.pdf", OUT / "annual_report_copy.pdf")
    (OUT / "corrupt_file.pdf").write_bytes(b"%PDF-1.4 this is not really a pdf \xff\xfe garbage")
    print("Demo Corpus Written To", OUT)
    for m in made:
        print(" -", Path(m).name)


if __name__ == "__main__":
    sys.exit(main())
