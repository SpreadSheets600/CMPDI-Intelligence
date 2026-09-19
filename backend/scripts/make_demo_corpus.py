"""Generate a synthetic demo corpus that exercises every pipeline path:
digital PDFs (headings, tables), scanned PDF (image-only), mixed PDF,
multi-sheet XLSX workbooks with merged cells, CSVs, parliamentary and safety
DOCX memos, revised versions of reports, a duplicate, and a corrupt file.

Planted conflicts (each pair disagrees on one entity x metric x period):
 1. Kusunda Mine production FY2021-22: 4.85 MT (annual report) vs 4.35 MT (scan).
 2. Jayant OCP offtake FY2022-23: 195.4 lakh tonnes (NCL workbook) vs
    197.9 lakh tonnes (NCL ops note).
Corroborated pairs (same value twice, no conflict):
 - Nigahi OCP production FY2023-24: 208.6 lakh tonnes (workbook + ops note).
Hand-checkable series for timelines and forecasting:
 - Lakhanpur OCP production (MT): 18.20, 19.45, 20.10, 21.65, 22.80
   across FY2019-20..FY2023-24 (MCL report).
 - CCL OMS (tonnes): 3.18, 3.31, 3.42 across FY2021-22..FY2023-24 (safety memo)."""

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


MCL_PROD = {  # mine -> FY2019-20..FY2023-24 production in MT
    "Lakhanpur OCP": ["18.20", "19.45", "20.10", "21.65", "22.80"],
    "Ananta OCP": ["12.40", "12.85", "13.60", "13.15", "14.20"],
    "Lingaraj OCP": ["15.00", "15.90", "16.40", "17.20", "17.85"],
}
MCL_YEARS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]


def make_mcl_report(revised=False):
    """MCL Annual Report FY2023-24: five-year mine-wise series (timelines and
    forecasting), offtake, reserves, quality table and manpower."""
    doc = pymupdf.open()
    page = doc.new_page()
    add_heading(page, 90, "MCL Annual Report 2023-24", 17)
    add_heading(page, 120, "1. Overview", 13)
    y = add_para(page, 138,
        "Mahanadi Coalfields Limited (MCL) recorded total coal production of "
        "201.45 MT during FY2023-24, against 193.80 MT in FY2022-23. The three "
        "featured opencast projects of MCL — Lakhanpur OCP, Ananta OCP and "
        "Lingaraj OCP — together produced 54.85 MT during FY2023-24. MCL "
        "remains the largest producing subsidiary of Coal India Limited.")
    add_heading(page, y + 10, "2. Production Performance", 13)
    y2 = add_para(page, y + 28,
        "Mine-wise production of MCL for the last five financial years is "
        "presented below. Values are in million tonnes (MT).")
    rows = [[m] + vals for m, vals in MCL_PROD.items()]
    if revised:
        rows[2][-1] = "18.30"  # Lingaraj OCP FY2023-24 revised figure
    add_table(page, 72, y2, ["Mine"] + MCL_YEARS, rows,
              col_w=[130, 64, 64, 64, 64, 64])

    page2 = doc.new_page()
    add_heading(page2, 90, "3. Offtake, Reserves and Manpower", 13)
    reserves = "1131.20" if revised else "1124.60"
    add_para(page2, 118,
        "MCL recorded coal offtake of 178.20 MT during FY2023-24, with grade-wise "
        "despatch monitored monthly by MCL. Total extractable reserves of MCL as "
        f"on 1 April 2024 stand at {reserves} MT. MCL employed 21,346 persons "
        "as on 31 March 2024.")

    page3 = doc.new_page()
    add_heading(page3, 90, "4. Coal Quality", 13)
    y3 = add_para(page3, 118,
        "Average quality parameters of MCL coal despatched during FY2023-24 are "
        "tabulated below. MCL washeries monitor ash and moisture continuously.")
    add_table(page3, 72, y3, ["Mine", "GCV (kcal/kg)", "Ash (%)"],
              [["Lakhanpur OCP", "4850", "34.2"],
               ["Ananta OCP", "4620", "36.8"],
               ["Lingaraj OCP", "4950", "33.1"]])
    out = OUT / ("mcl_annual_report_2024_revised.pdf" if revised
                 else "mcl_annual_report_2024.pdf")
    doc.save(str(out))
    doc.close()
    return out


NCL_PROD = {  # mine -> FY2018-19..FY2023-24 production in lakh tonnes
    "Jayant OCP": [172.5, 178.0, 184.6, 190.2, 196.8, 201.5],
    "Nigahi OCP": [180.4, 186.1, 191.7, 197.3, 203.0, 208.6],
    "Dudhichua OCP": [142.8, 147.5, 152.9, 158.4, 163.1, 168.7],
    "Amlohri OCP": [96.3, 99.8, 103.2, 106.9, 110.4, 114.0],
}
NCL_YEARS = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]
NCL_OFFTAKE = {  # mine -> [FY2022-23, FY2023-24] offtake in lakh tonnes
    "Jayant OCP": [195.4, 200.1],
    "Nigahi OCP": [201.8, 207.2],
    "Dudhichua OCP": [161.9, 167.5],
    "Amlohri OCP": [109.6, 113.2],
}


def make_ncl_workbook():
    """NCL performance workbook: six-year production, offtake and drilling
    sheets in lakh units, plus a second table region on the Offtake sheet."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Production"
    ws["A1"] = "Production (lakh tonnes)"
    ws["A1"].font = Font(bold=True)
    ws.merge_cells("A1:G1")
    ws.append([])
    ws.append(["Mine"] + NCL_YEARS)
    for mine, vals in NCL_PROD.items():
        ws.append([mine] + vals)
    ws2 = wb.create_sheet("Offtake")
    ws2["A1"] = "Offtake (lakh tonnes)"
    ws2["A1"].font = Font(bold=True)
    ws2.merge_cells("A1:C1")
    ws2.append([])
    ws2.append(["Mine", "2022-23", "2023-24"])
    for mine, vals in NCL_OFFTAKE.items():
        ws2.append([mine] + vals)
    ws2.append([])
    ws2.append([])
    ws2.append(["Project", "Drilling 2023-24", "Unit"])
    ws2.append(["NCL coalfields", 4.61, "lakh metres"])
    out = OUT / "ncl_performance_workbook.xlsx"
    wb.save(out)
    return out


def make_ncl_ops_note():
    """NCL operational note: conflicts with the workbook on Jayant offtake
    FY2022-23 (197.9 vs 195.4) while corroborating Nigahi production."""
    doc = pymupdf.open()
    page = doc.new_page()
    add_heading(page, 90, "NCL Operational Note FY2022-23", 15)
    y = add_para(page, 120,
        "Northern Coalfields Limited (NCL) reviews mine-wise offtake for the "
        "Financial Year 2022-23. As reconciled by NCL, Jayant OCP offtake stood "
        "at 197.9 lakh tonnes during FY2022-23. NCL further notes that Nigahi "
        "OCP produced 208.6 lakh tonnes during FY2023-24, and NCL drilling "
        "achieved 4.61 lakh metres in the same year.")
    add_table(page, 72, y, ["Mine", "Offtake 2022-23 (lakh tonnes)"],
              [["Jayant OCP", "197.9"],
               ["Nigahi OCP", "201.8"],
               ["Dudhichua OCP", "161.9"]], col_w=[220, 220])
    out = OUT / "ncl_ops_note.pdf"
    doc.save(str(out))
    doc.close()
    return out


def make_bccl_exploration_scan():
    """Scanned BCCL exploration report: drilling, seam depth, GCV and ash."""
    pages = [
        ["# BCCL Exploration Report 2023-24",
         "## Drilling Performance",
         "Bharat Coking Coal Limited (BCCL) completed 2.34 lakh metres of",
         "exploratory drilling during FY2023-24 across the Moonidih and",
         "Muraidih blocks of BCCL. Muraidih OCP produced 8.45 MT during",
         "FY2023-24 while Moonidih UG produced 2.18 MT in the same period.",
         "",
         "## Seam Details",
         "The coking coal seam occurs at a depth of 380 m to 420 m with an",
         "average thickness of 6.4 m. GCV of the seam averages 6,100 kcal/kg",
         "with ash content of 19.8 percent."],
        ["# BCCL Reserves Statement",
         "## Extractable Reserves",
         "Extractable reserves of BCCL as on 1 April 2024 stand at 312.75 MT.",
         "Proved reserves of the Moonidih block of BCCL are 148.20 MT with",
         "a stripping ratio of 3.10 cu.m per tonne."],
    ]
    doc = pymupdf.open()
    for i, lines in enumerate(pages):
        png = OUT / f"_bccl_scan_{i}.jpg"
        render_text_image(lines, png)
        img = open(png, "rb").read()
        page = doc.new_page(width=595, height=842)
        page.insert_image(pymupdf.Rect(0, 0, 595, 842), stream=img)
        png.unlink()
    out = OUT / "bccl_exploration_scan.pdf"
    doc.save(str(out))
    doc.close()
    return out


def make_washery_note():
    """Digital washery/quality note: yields, ash reduction, coking grades."""
    doc = pymupdf.open()
    page = doc.new_page()
    add_heading(page, 90, "Coking Coal Washery Performance Note", 15)
    y = add_para(page, 120,
        "This note reviews coking coal washeries of BCCL for FY2023-24. The "
        "Dugda washery produced 4.85 MT of washed coal at a yield of 48.5 "
        "percent, while the Bhojudih washery produced 3.62 MT at a yield of "
        "51.2 percent. Washed coal ash content averaged 17.9 percent against "
        "raw coal ash of 34.5 percent, with moisture at 6.2 percent.")
    page2 = doc.new_page()
    add_heading(page2, 90, "Grade-wise Despatch", 13)
    add_para(page2, 118,
        "Despatch of Steel-II grade coking coal from BCCL washeries totalled "
        "8.4 lakh tonnes during FY2023-24. Washery-III grade despatch was 5.1 "
        "lakh tonnes in the same period.")
    out = OUT / "washery_quality_note.pdf"
    doc.save(str(out))
    doc.close()
    return out


def make_safety_memo():
    """CCL safety and manpower memo (DOCX): OMS series, incidents, training."""
    import docx
    d = docx.Document()
    d.add_heading("CCL Safety and Manpower Memo 2023-24", 0)
    d.add_paragraph("Central Coalfields Limited (CCL) employed 38,214 persons "
                    "as on 31 March 2024. Output per man shift (OMS) of CCL "
                    "reached 3.42 tonnes during FY2023-24. Reportable incidents "
                    "in CCL stood at 0.19 per million tonnes with 12,400 "
                    "persons trained during the year.")
    t = d.add_table(rows=1, cols=2)
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    hdr[0].text, hdr[1].text = "Financial Year", "OMS (tonnes)"
    for year, oms in [("2021-22", "3.18"), ("2022-23", "3.31"), ("2023-24", "3.42")]:
        row = t.add_row().cells
        row[0].text, row[1].text = year, oms
    out = OUT / "ccl_safety_memo.docx"
    d.save(str(out))
    return out


def make_rake_csv():
    """Monthly rake despatch register for FY2023-24 (agent chart demo)."""
    out = OUT / "rake_despatch_fy24.csv"
    rows = ["Date,Rake,Grade,Quantity (tonnes),Destination"]
    dests = ["Korba TPS", "Sipat TPS", "Rihand TPS", "Vindhyachal TPS"]
    grades = ["G11", "G12", "G12", "G13"]
    qty = [3850, 3975, 4120, 3890, 4055, 4180, 3940, 4090, 4215, 3985, 4070, 4150]
    for i in range(12):
        month = f"{(i + 3) % 12 + 1:02d}"
        year = 2023 if i < 9 else 2024
        rows.append(f"{year}-{month}-15,R-{2001 + i},{grades[i % 4]},"
                    f"{qty[i]},{dests[i % 4]}")
    out.write_text("\n".join(rows), encoding="utf-8")
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
        make_mcl_report(revised=False),
        make_mcl_report(revised=True),
        make_ncl_workbook(),
        make_ncl_ops_note(),
        make_bccl_exploration_scan(),
        make_washery_note(),
        make_safety_memo(),
        make_rake_csv(),
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
