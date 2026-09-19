"""Generate the synthetic demo corpus: 30 documents of six pages each covering
every pipeline path (digital PDFs, scanned PDFs, mixed PDF, multi-sheet XLSX
workbooks, CSV registers, DOCX memos), plus a byte-duplicate and a corrupt
file for dedupe/failure demos.

Planted conflicts (each pair disagrees on one entity x metric x period):
 1. Kusunda Mine production FY2021-22: 4.85 MT (annual report) vs 4.35 MT (scan).
 2. Jayant OCP offtake FY2022-23: 195.4 lakh tonnes (NCL workbook) vs
    197.9 lakh tonnes (NCL ops note).
 3. Lingaraj OCP production FY2023-24: 17.85 MT (MCL report) vs 18.30 (revised).
 4. SECL extractable reserves: 812.45 MT (annual) vs 818.90 MT (revised).
Corroborated pairs (same value twice, no conflict):
 - Nigahi OCP production FY2023-24: 208.6 lakh tonnes (workbook + ops note).
Temporal depth: subsidiary/mine/OMS/drilling/safety series span 4-7 periods,
monthly CSV registers span 24-48 months, so timelines and forecasting resolve.
"""

import shutil
import sys
from pathlib import Path

import numpy as np
import pymupdf

from backend.scripts import corpus_docs_a as A
from backend.scripts import corpus_docs_b as B
from backend.scripts.corpus_flow import (
    render_text_image,
    scan_pdf,
    write_csv,
    xlsx_book,
)

OUT = Path(__file__).resolve().parents[2] / "data" / "demo_corpus"


def _pdf(name, flow):
    out = OUT / name
    pages = flow.save(out)
    return out, pages


def main():
    OUT.mkdir(exist_ok=True)
    np.random.seed(42)
    made = []

    made.append(_pdf("annual_report.pdf", A.make_annual_report(revised=False)))
    made.append(_pdf("annual_report_revised.pdf", A.make_annual_report(revised=True)))

    out = OUT / "geological_report_scan.pdf"
    made.append((out, scan_pdf(out, A.make_scanned_geological_report(), "scan")))

    mixed = A.make_mixed_pdf()
    for i, lines in enumerate(A.mixed_scan_pages()):
        png = OUT / f"_mixed_page_{i}.jpg"
        render_text_image(lines, png)
        img = png.read_bytes()
        page = mixed.doc.new_page(width=595, height=842)
        page.insert_image(pymupdf.Rect(0, 0, 595, 842), stream=img)
        png.unlink()
    made.append((OUT / "quarterly_review_mixed.pdf", mixed.save(OUT / "quarterly_review_mixed.pdf")))

    made.append((OUT / "production_workbook.xlsx",
                 xlsx_book(OUT / "production_workbook.xlsx", A.make_xlsx_secl())))
    made.append((OUT / "dispatch_register.csv",
                 (OUT / "dispatch_register.csv",
                  write_csv(OUT / "dispatch_register.csv",
                            "Date,Rake,Grade,Quantity (tonnes),Destination",
                            A.dispatch_rows()))))

    doc = A.make_parliamentary_docx_sections()
    doc.save(str(OUT / "parliamentary_qa.docx"))
    made.append((OUT / "parliamentary_qa.docx", "docx"))

    made.append(_pdf("mcl_annual_report_2024.pdf", A.make_mcl_report(revised=False)))
    made.append(_pdf("mcl_annual_report_2024_revised.pdf", A.make_mcl_report(revised=True)))
    made.append((OUT / "ncl_performance_workbook.xlsx",
                 xlsx_book(OUT / "ncl_performance_workbook.xlsx", A.make_ncl_workbook())))
    made.append(_pdf("ncl_ops_note.pdf", A.make_ncl_ops_note()))

    out = OUT / "bccl_exploration_scan.pdf"
    made.append((out, scan_pdf(out, A.bccl_scan_pages(), "bccl")))
    made.append(_pdf("washery_quality_note.pdf", A.make_washery_note()))

    doc = A.make_ccl_safety_docx_sections()
    doc.save(str(OUT / "ccl_safety_memo.docx"))
    made.append((OUT / "ccl_safety_memo.docx", "docx"))

    made.append((OUT / "rake_despatch_fy24.csv",
                 (OUT / "rake_despatch_fy24.csv",
                  write_csv(OUT / "rake_despatch_fy24.csv",
                            "Date,Rake,Grade,Quantity (tonnes),Destination",
                            A.rake_rows()))))

    made.append(_pdf("cil_consolidated_fy24.pdf", B.make_cil_consolidated()))
    made.append(_pdf("ecl_annual_report.pdf", B.make_ecl_annual()))
    made.append(_pdf("wcl_annual_report.pdf", B.make_wcl_annual()))
    made.append(_pdf("ccl_annual_report.pdf", B.make_ccl_annual()))
    made.append(_pdf("cmpdi_exploration_fy24.pdf", B.make_cmpdi_exploration()))
    made.append(_pdf("fmc_evacuation_status.pdf", B.make_fmc_status()))
    made.append(_pdf("mission_coking_coal.pdf", B.make_mission_coking()))
    made.append(_pdf("cil_safety_annual_2024.pdf", B.make_cil_safety_annual()))
    made.append(_pdf("gevra_expansion_eia.pdf", B.make_gevra_eia()))
    made.append(_pdf("auction_linkage_note.pdf", B.make_auction_note()))
    made.append(_pdf("cil_1bt_roadmap.pdf", B.make_1bt_roadmap()))

    made.append((OUT / "manpower_oms_fy24.xlsx",
                 xlsx_book(OUT / "manpower_oms_fy24.xlsx", B.make_manpower_xlsx())))
    made.append((OUT / "financial_performance_fy24.xlsx",
                 xlsx_book(OUT / "financial_performance_fy24.xlsx", B.make_financial_xlsx())))
    made.append((OUT / "gradewise_despatch.csv",
                 (OUT / "gradewise_despatch.csv",
                  write_csv(OUT / "gradewise_despatch.csv",
                            "Month,Grade,Quantity (tonnes),Mode", B.gradewise_rows()))))
    made.append((OUT / "coal_stock_ledger.csv",
                 (OUT / "coal_stock_ledger.csv",
                  write_csv(OUT / "coal_stock_ledger.csv",
                            "Month,Production (MT),Lifting (MT),Closing stock (MT),Yard",
                            B.stock_rows()))))

    doc = B.make_environment_docx_sections()
    doc.save(str(OUT / "environmental_clearance.docx"))
    made.append((OUT / "environmental_clearance.docx", "docx"))

    # duplicate + corrupt files for dedup / failure demos
    shutil.copy2(OUT / "annual_report.pdf", OUT / "annual_report_copy.pdf")
    (OUT / "corrupt_file.pdf").write_bytes(b"%PDF-1.4 this is not really a pdf \xff\xfe garbage")
    print("Demo Corpus Written To", OUT)
    for m in made:
        print(" -", Path(m[0]).name, m[1])


if __name__ == "__main__":
    sys.exit(main())
