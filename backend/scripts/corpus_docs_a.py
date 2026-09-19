"""Corpus part A: the original fifteen documents, deepened to six pages each.
Planted Conflict Radar pairs keep byte-exact values; subsidiary totals were
aligned to Ministry of Coal tables so the new real-data documents corroborate
instead of contradicting them."""

from backend.scripts.corpus_data import (
    COKING_OUT,
    COKING_YEARS,
    KORBA_TRIO,
    MCL_PROD,
    MCL_YEARS,
    NCL_OFFTAKE,
    NCL_PROD,
    NCL_YEARS,
    WASHERIES_NEW,
)
from backend.scripts.corpus_flow import FlowDoc


def _s(mapping, years):
    return [[m] + [str(v) for v in vals] for m, vals in mapping.items()]


# ------------------------------------------------------------------ 1/2 SECL

def make_annual_report(revised=False):
    f = FlowDoc()
    f.h1("SECL Annual Report FY2021-22" + (" (Revised)" if revised else ""))
    f.h2("1. Overview")
    f.para(
        "South Eastern Coalfields Limited (SECL), the largest coal producing subsidiary of "
        "Coal India Limited, recorded total coal production of 142.51 MT during FY2021-22, "
        "against 146.20 MT in the previous year. The dip reflects prolonged monsoon flooding "
        "in the Korba coalfield during Q2 and a planned dragline outage at Kusmunda OCP in Q3. "
        "Kusmunda Mine is an underground mine in the Korba coalfield with established geological "
        "reserves of 412.60 MT. The mine achieved an average GCV of 5,800 kcal/kg with ash "
        "content of 22.4 percent. Dipka, Gevra and Kusmunda mega opencast projects together "
        "contributed over two thirds of SECL output during the year.")
    f.para(
        "Coal offtake for the year stood at 144.20 MT, of which 118.60 MT moved by rail and "
        "25.60 MT by road and MGR. Average rake loading improved to 18.4 rakes per day in Q4 "
        "after the commissioning of the rapid loading silo at Dipka. E-auction realisation "
        "averaged 118 percent of the notified price across grades G11 to G13.")
    f.h2("2. Production Performance")
    f.para(
        "Mine-wise production for the last three financial years is presented below. Values are "
        "in million tonnes (MT). The Korba trio of Gevra, Kusmunda and Dipka remains the backbone "
        "of SECL, while underground mines such as Kusunda contribute high-grade coal for linkage "
        "consumers in the power and steel sectors.")
    if revised:
        f.table(["Mine (production, MT)", "2020-21", "2021-22", "2022-23"],
                [["Gevra OCP", "40.10", "41.46", "52.50"],
                 ["Kusmunda OCP", "36.20", "38.90", "44.80"],
                 ["Dipka OCP", "31.40", "33.80", "37.60"],
                 ["Kusunda Mine", "4.10", "4.85", "5.32"]],
                col_w=[150, 90, 90, 90])
    else:
        f.table(["Mine (production, MT)", "2019-20", "2020-21", "2021-22"],
                [["Gevra OCP", "38.20", "40.10", "41.46"],
                 ["Kusmunda OCP", "34.50", "36.20", "38.90"],
                 ["Dipka OCP", "30.10", "31.40", "33.80"],
                 ["Kusunda Mine", "3.95", "4.10", "4.85"]],
                col_w=[150, 90, 90, 90])
    f.h2("3. Reserves")
    reserves = "818.90" if revised else "812.45"
    f.para(
        f"Total extractable reserves of SECL as on 1 April 2022 stand at {reserves} MT. "
        "Geological reserves of Chirimiri Mine are 289.15 MT with stripping ratio of 2.45 cu.m "
        "per tonne. Proved reserves increased by 41.20 MT during the year after CMPDI submitted "
        "four geological reports covering the Hasdeo-Arand coalfield.")
    f.table(["Block", "Proved (MT)", "Indicated (MT)", "Stripping ratio"],
            [["Chirimiri UG", "289.15", "96.40", "2.45"],
             ["Hasdeo-Arand OC", "512.80", "188.30", "3.10"],
             ["Korba West", "344.60", "121.70", "2.85"]],
            col_w=[150, 100, 100, 100])
    f.h2("4. Quality and Manpower")
    f.para(
        "The company employed 82,415 persons as on 31 March 2022, of whom 61,208 were posted in "
        "revenue mines. Operating profit before tax for the year was Rs 4,285.60 crore. Grade-wise "
        "coal despatch is monitored monthly through third-party sampling at 42 loading points. The "
        "average grade of coal despatched improved to G12 after the commissioning of two feeder "
        "breaker-crusher circuits at Gevra.")
    f.table(["Mine", "GCV (kcal/kg)", "Ash (%)", "Depth (m)"],
            [["Kusunda Mine", "5800", "22.4", "310"],
             ["Dipka OCP", "5100", "28.1", "95"],
             ["Gevra Area", "4950", "30.6", "110"]])
    f.h2("5. Evacuation and First Mile Connectivity")
    f.para(
        "SECL operated 9 rapid loading systems during the year, evacuating 61.40 MT through "
        "mechanised first-mile connectivity. The Dipka-Kusmunda-Gevra rail corridor handled "
        "11,240 rakes, and wagon turnaround at the Korba complex improved to 31 hours. Two new "
        "silos of 4 MTPA each at Gevra and Kusmunda are under construction and will add 8 MTPA "
        "of mechanised evacuation by FY2023-24.")
    f.table(["Corridor", "Rakes loaded", "Qty (MT)", "Turnaround (hrs)"],
            [["Korba complex", "11240", "44.20", "31"],
             ["Chirimiri branch", "2180", "8.60", "38"],
             ["Hasdeo siding", "1640", "6.40", "42"]],
            col_w=[150, 100, 100, 110])
    f.h2("6. Safety and Outlook")
    f.para(
        "Four fatal accidents were recorded during 2021, against seven in the previous year, and "
        "the fatality rate per million tonnes improved to 0.05. strata control audits covered all "
        "11 underground mines, and 2,140 executives completed simulator-based HEMM refresher "
        "training. For FY2022-23 the company targets 167 MT of production with Gevra crossing "
        "the 50 MT milestone, the first Indian mine to do so.")
    f.bullets([
        "Target FY2022-23: 167 MT production, 165 MT offtake.",
        "Gevra expansion environmental clearance for 70 MTPA under examination.",
        "Zero-discharge mine-water utilisation at 68 percent across OCPs.",
    ])
    f.h2("7. Quarterly performance")
    f.para(
        "Production accelerated through the year as monsoon effects faded: Q1 managed 32.40 MT "
        "against flood-hit faces, Q2 recovered to 34.10 MT, Q3 reached 37.20 MT on the new "
        "Kusmunda shovel, and Q4 closed at 38.81 MT with Gevra alone loading 14.20 MT. Offtake "
        "tracked production with a quarter-end stock drawdown of 2.10 MT in March.")
    f.table(["Quarter", "Production (MT)", "Offtake (MT)", "OBR (Mcum)"],
            [["Q1", "32.40", "31.80", "52.40"],
             ["Q2", "34.10", "34.60", "48.20"],
             ["Q3", "37.20", "37.40", "58.60"],
             ["Q4", "38.81", "40.40", "64.20"]],
            col_w=[100, 120, 110, 100])
    f.para(
        "Overburden peaked in Q4 ahead of the monsoon, exposing 41 MT of coal across the Korba "
        "trio. Dragline availability averaged 86 percent for the year, with the Kusmunda 24/96 "
        "dragline logging 7,120 working hours.")
    f.h2("8. Grade-wise despatch")
    f.para(
        "Despatch concentrated in mid grades for power linkage, with washed and direct-feed "
        "superior grades serving steel and cement. Grade conformity penalties fell to Rs 42 "
        "crore from Rs 68 crore as third-party sampling expanded to every loading point.")
    f.table(["Grade", "Despatch (MT)", "GCV band", "Price (Rs/t)"],
            [["G11", "48.20", "5801-6100", "2140"],
             ["G12", "52.60", "5501-5800", "1980"],
             ["G13", "31.40", "5201-5500", "1820"],
             ["Steel-II", "2.10", "6200+", "4860"]],
            col_w=[100, 110, 110, 100])
    f.para(
        "Surface miners at Gevra and Dipka produce sized coal directly, cutting crusher load by "
        "38 percent and improving G12 consistency. Feeder-breaker circuits added at Kusmunda "
        "lifted sized-coal share to 64 percent of despatch.")
    f.h2("9. Project pipeline")
    f.para(
        "Eleven projects hold 96 MTPA of pipeline capacity. The Gevra 70 MTPA expansion awaits "
        "forest clearance Stage-II over 1,240 hectares, Kusmunda adds a 20 cu.m shovel in Q2, "
        "and Dipka commissions its second silo in Q4. Chirimiri underground modernization puts "
        "two continuous miner panels on stream by March.")
    f.table(["Project", "Capacity (MTPA)", "Capex (Rs cr)", "Completion"],
            [["Gevra expansion", "70.0", "4860", "FY2024-25"],
             ["Kusmunda HEMM", "4.0", "620", "Q2 FY2022-23"],
             ["Dipka silo II", "4.0", "540", "Q4 FY2022-23"],
             ["Chirimiri UG mod", "2.4", "480", "Mar 2023"]],
            col_w=[140, 100, 100, 110])
    f.h2("10. Financial summary")
    f.para(
        "Revenue from operations grew 18.4 percent to Rs 32,640 crore on higher e-auction "
        "premiums and 117 percent materialisation of power linkage. Profit after tax of Rs "
        "6,840 crore funded Rs 3,420 crore of capex and a Rs 2,180 crore dividend to CIL. "
        "Trade receivables from state gencos closed at Rs 4,120 crore, down Rs 640 crore after "
        "the late-payment surcharge rules took effect.")
    f.table(["Head (Rs cr)", "2020-21", "2021-22"],
            [["Revenue", "27560", "32640"],
             ["PAT", "5420", "6840"],
             ["Capex", "2840", "3420"],
             ["Dividend", "1640", "2180"]],
            col_w=[140, 110, 110])
    f.h2("11. Overburden and stripping annex")
    f.para(
        "Overburden removal of 223.40 million cu.m held the stripping ratio at 1.56 cu.m per "
        "tonne, the lowest among CIL opencast subsidiaries. Contractor HEMM moved 58 percent "
        "of overburden while departmental draglines and shovels covered the prime cuts at "
        "Gevra and Kusmunda.")
    f.table(["Mine", "OBR (Mcum)", "Stripping ratio"],
            [["Gevra OCP", "96.40", "2.32"],
             ["Kusmunda OCP", "72.80", "1.87"],
             ["Dipka OCP", "48.60", "1.44"],
             ["Others", "5.60", "1.10"]],
            col_w=[140, 110, 120])
    f.table(["Year", "OBR (Mcum)", "Stripping ratio"],
            [["2019-20", "198.20", "1.68"],
             ["2020-21", "206.40", "1.62"],
             ["2021-22", "223.40", "1.56"]],
            col_w=[140, 110, 120])
    f.h2("12. Rake loading annex")
    f.para(
        "Rake loading averaged 30.8 per day for the year with March peaking at 36 rakes. "
        "Demurrage of Rs 18.40 crore was the lowest in five years after the rapid loading "
        "silos at Dipka and Gevra cut siding detention to 4.1 hours per rake.")
    f.table(["Siding", "Rakes/day", "Qty (MT)"],
            [["Gevra silo", "9.2", "14.20"],
             ["Dipka silo", "7.8", "11.60"],
             ["Kusmunda siding", "6.4", "9.80"],
             ["Chirimiri", "3.1", "4.60"],
             ["Hasdeo", "2.4", "3.40"],
             ["Others", "1.9", "2.80"]],
            col_w=[140, 100, 100])
    f.table(["Year", "Rakes/day", "Demurrage (Rs cr)"],
            [["2019-20", "27.40", "32.60"],
             ["2020-21", "28.10", "26.40"],
             ["2021-22", "30.80", "18.40"]],
            col_w=[140, 110, 120])
    return f


def make_scanned_geological_report():
    pages = [
        ["# Geological Report: Korba Coalfield",
         "## Exploration Summary",
         "The Korba coalfield of SECL comprises the Kusunda Mine, Dipka OCP and",
         "Gevra Area workings within the Chhattisgarh state. This report",
         "consolidates exploration results for the period 2021-22.",
         "A total of 42 boreholes aggregating 18,240 metres were drilled in the",
         "reporting year, of which 31 were coring holes for coal quality.",
         "## Seam Details",
         "The Korba seam occurs at a depth of 105 m to 310 m with an average",
         "thickness of 12.8 m. GCV of the Korba seam averages 5,650 kcal/kg.",
         "The seam dips at 1 in 5.5 towards the south-east."],
        ["# Drilling Performance 2021-22",
         "## Departmental and Outsourced Drilling",
         "Departmental drills completed 6,120 metres against a target of 6,400",
         "metres. Outsourced drilling through MECL achieved 12,120 metres.",
         "Core recovery averaged 91.4 percent across the Barakar formation.",
         "## Laboratory Results",
         "Proximate analysis of 214 samples shows average ash of 30.6 percent",
         "and moisture of 6.8 percent. Phosphorus stays below 0.08 percent,",
         "suitable for thermal linkage consumers in Chhattisgarh."],
        ["# Production Reconciliation 2021-22",
         "## Mine-wise Production",
         "As per the reconciliation exercise, Kusunda Mine produced 4.35 MT",
         "during FY2021-22. Dipka OCP produced 33.80 MT and Gevra Area",
         "recorded offtake of 36.90 MT during the same period.",
         "The reconciliation committee attributes the Kusunda variance to",
         "weighbridge calibration drift at the Kusunda siding in Q3.",
         "## Geological Reserves",
         "Extractable reserves of Kusunda Mine are estimated at 405.20 MT as",
         "on April 2022, with ash content of 23.1 percent."],
        ["# Structure and Faults",
         "## Fault Interpretation",
         "Seismic interpretation identifies three faults with throws between",
         "8 m and 22 m in the Kusunda block. A dyke of 3.2 m width cuts the",
         "seam near borehole KSN-27 and is excluded from reserves.",
         "Mining panels are sequenced to leave a 45 m barrier around the dyke.",
         "## Roof and Floor",
         "Immediate roof is medium-grained sandstone of 6.5 m thickness with",
         "an RQD of 68. Floor heave was observed in two depillaring panels."],
        ["# Groundwater Regime",
         "## Aquifer Summary",
         "Two granular aquifers sit above the Korba seam at 40 m and 85 m.",
         "Pumping tests give transmissivity of 120 sqm per day in the upper",
         "aquifer. Mine inflow averages 2,850 cu.m per day in the monsoon.",
         "Quarterly monitoring at 14 piezometers shows no regional depletion.",
         "## Utilisation",
         "Mine discharge meets 41 percent of the washery and dust-suppression",
         "demand. The balance is supplied to two nearby villages."],
        ["# Recommendations",
         "## Further Work",
         "Infill drilling of 4,000 metres is recommended in the Kusunda east",
         "block to upgrade 28 MT from indicated to proved category.",
         "A revised geological report should be prepared after the Q1",
         "weighbridge recalibration and the dyke-proving holes are complete.",
         "Reserves of 405.20 MT for Kusunda Mine are retained pending review."],
    ]
    return pages


def make_mixed_pdf():
    f = FlowDoc()
    f.h1("Quarterly Review Note (Digital)")
    f.para(
        "This note reviews the Q4 performance of WCL subsidiaries. Coal offtake of "
        "SECL in the fourth quarter was 39.85 MT. Manpower productivity improved "
        "by 4.2 percent year on year.")
    f.h2("Quarterly production")
    f.table(["Company", "Q4 prod (MT)", "Q4 offtake (MT)", "Growth (%)"],
            [["SECL", "44.20", "39.85", "6.4"],
             ["MCL", "52.40", "48.10", "8.1"],
             ["NCL", "34.60", "33.90", "3.2"]],
            col_w=[150, 100, 110, 90])
    f.h2("Safety")
    f.para(
        "Safety statistics remained satisfactory with 0.16 reportable incidents "
        "per thousand manpower. Output per man shift (OMS) at underground mines "
        "reached 2.68 tonnes.")
    f.table(["Indicator", "Q3", "Q4", "Target"],
            [["Reportable incidents / 1000 manshifts", "0.18", "0.16", "0.15"],
             ["UG OMS (tonnes)", "2.61", "2.68", "2.70"],
             ["Near-miss reports", "142", "168", "200"]],
            col_w=[220, 70, 70, 70])
    f.h2("WCL area notes")
    f.para(
        "Umrer Area commissioned its 4 MTPA silo in March 2022 and evacuated 1.85 lakh "
        "tonnes of grade G12 coal to thermal plants in the month. Kamptee Area overburden "
        "removal lagged by 6 percent after a shovel breakdown; a replacement 20 cu.m rope "
        "shovel arrives in Q1.")
    f.h2("Manpower")
    f.para(
        "WCL employed 38,214 persons as on 31 March 2022. Training man-days reached 96,400, "
        "and 1,240 executives completed the leadership pipeline programme. Voluntary retirement "
        "separations stood at 812 for the quarter.")
    f.h2("E-auction performance")
    f.para(
        "Spot e-auction offered 4.20 MT in Q4 and booked 3.90 MT at an average premium of 121 "
        "percent. Special forward auctions for power lifted 2.40 MT, while single-window "
        "agnostic auctions moved 1.80 MT to cement and sponge-iron buyers.")
    f.table(["Auction window", "Offered (MT)", "Booked (MT)", "Premium (%)"],
            [["Spot Q4", "4.20", "3.90", "121"],
             ["Power forward", "2.60", "2.40", "18"],
             ["Agnostic NRS", "2.00", "1.80", "106"]],
            col_w=[130, 100, 100, 100])
    f.h2("First mile connectivity")
    f.para(
        "Mechanised evacuation touched 46.40 MT for CIL in FY2021-22 terms across the "
        "commissioned silos. The Umrer silo loads 8 rakes daily at 3.2 hours per rake, and "
        "the Kamptee CHP upgrade finishes in Q2 with covered conveyors over the full 6 km "
        "lead to the siding.")
    f.table(["Asset", "Capacity (MTPA)", "Rakes/day", "Loading (hrs)"],
            [["Umrer silo", "4.0", "8", "3.2"],
             ["Kamptee CHP", "6.0", "6", "4.1"],
             ["Ballarpur siding", "3.0", "4", "5.0"]],
            col_w=[130, 100, 90, 100])
    f.h2("Project updates")
    f.para(
        "Dinesh expansion at Umrer advances to 8 MTPA with the second shovel fleet arriving in "
        "May. Padmapur deepening studies add 2.40 MT of proved reserves. The Chandrapur "
        "super-thermal linkage of 8.40 MTPA materialised at 96.4 percent for the quarter.")
    f.h2("Outlook for Q1")
    f.para(
        "Q1 FY2022-23 targets 15.20 MT of production with the monsoon plan pre-positioning "
        "pumps at all 12 flood-prone faces. Rake allotment of 11 per day is confirmed by the "
        "railways, and the grade declaration for the new Ghugus seam keeps G12 realisation "
        "steady into the new year.")
    f.bullets([
        "Q1 target: 15.20 MT production, 14.80 MT offtake.",
        "Monsoon pumps pre-positioned at 12 faces.",
        "Ghugus seam declared G12 from April.",
    ])
    return f


def mixed_scan_pages():
    return [
        ["# Annexure: Scanned Circular",
         "The area manager shall ensure despatch of grade G12 coal",
         "to the thermal plants as per the linked quantity of",
         "1.85 lakh tonnes for the month of March 2022.",
         "Rake allotment will follow the monthly loading plan.",
         "Any shortfall must be reported within 24 hours."],
        ["# Annexure: Safety Circular",
         "All underground mines shall conduct a special safety drive",
         "during the first fortnight of April 2022.",
         "Roof bolting density in depillaring panels is raised to",
         "1 bolt per sqm with immediate effect.",
         "Compliance reports are due by 20 April 2022."],
        ["# Annexure: Monsoon Preparedness",
         "All opencast mines shall position dewatering pumps by 15 May 2022.",
         "Vulnerable faces at Ballarpur and Dinesh need standby 2000 gpm sets.",
         "Dump toe drains must be cleared before the first monsoon shower.",
         "Fortnightly flood reviews start from 1 June 2022."],
    ]


def make_xlsx_secl():
    from backend.scripts.corpus_data import FY as _FY
    prod = [["Gevra OCP"] + KORBA_TRIO["Gevra OCP"][:6],
            ["Kusmunda OCP"] + KORBA_TRIO["Kusmunda OCP"][:6],
            ["Dipka OCP"] + KORBA_TRIO["Dipka OCP"][:6],
            ["Kusunda Mine", "3.95", "4.10", "4.10", "4.85", "5.10", "5.32"]]
    sheets = [
        ("Production", "Production (MT)",
         ["Mine"] + _FY, prod),
        ("Offtake", "Offtake (MT)",
         ["Mine", "2021-22", "2022-23"],
         [["Gevra OCP", 40.90, 51.20], ["Kusmunda OCP", 38.10, 43.60],
          ["Dipka OCP", 33.10, 36.90], ["Kusunda Mine", 4.70, 5.10]]),
        ("Quality", "GCV and ash",
         ["Mine", "GCV (kcal/kg)", "Ash (%)"],
         [["Kusunda Mine", 5800, 22.4], ["Dipka OCP", 5100, 28.1],
          ["Gevra Area", 4950, 30.6], ["Kusmunda OCP", 5050, 29.4]]),
        ("Reserves", "Extractable reserves (MT)",
         ["Block", "2021", "2022"],
         [["Chirimiri", 281.40, 289.15], ["Hasdeo-Arand", 498.20, 512.80],
          ["Korba West", 338.90, 344.60]]),
        ("Manpower", "Manpower (numbers)",
         ["Category", "2021", "2022"],
         [["Executives", 2840, 2915], ["Supervisors", 9210, 9340],
          ["Workers", 68410, 70160]]),
        ("Despatch", "Monthly despatch FY22 (MT)",
         ["Month", "Rail", "Road"],
         [[m, r, d] for m, r, d in zip(
             ["Apr", "May", "Jun", "Jul", "Aug", "Sep",
              "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
             [9.8, 10.1, 9.2, 8.6, 8.9, 9.4, 10.2, 10.6, 11.1, 11.4, 11.8, 12.5],
             [2.1, 2.2, 1.9, 1.7, 1.8, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6])]),
    ]
    return sheets


def dispatch_rows():
    rows = []
    dests = ["Korba TPS", "Sipat TPS", "Rihand TPS", "Vindhyachal TPS"]
    grades = ["G11", "G12", "G12", "G13"]
    for yi, y in enumerate([2020, 2021, 2022, 2023]):
        for m in range(1, 13):
            i = (yi * 12 + m) % 12
            qty = 3750 + ((yi * 37 + m * 53) % 500)
            rows.append(f"{y}-{m:02d}-15,R-{1201 + yi * 12 + m},{grades[i % 4]},"
                        f"{qty},{dests[i % 4]}")
    return rows


def make_parliamentary_docx_sections():
    import docx
    d = docx.Document()
    d.add_heading("Parliamentary Questions Extract, Session 2022", 0)
    d.add_heading("Starred Question No. 214", level=1)
    d.add_paragraph("Question: What is the current status of coal production in "
                    "the subsidiaries of Coal India Limited, subsidiary-wise?")
    d.add_paragraph("Reply: The subsidiary-wise raw coal production of Coal India "
                    "Limited (CIL) during FY2021-22 and FY2022-23 is as under:")
    t = d.add_table(rows=1, cols=4)
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = (
        "Subsidiary", "2021-22 (MT)", "2022-23 (MT)", "Growth (%)")
    for name, a, b, g in [("ECL", "32.43", "35.02", "8.0"),
                          ("BCCL", "30.50", "36.18", "18.6"),
                          ("SECL", "142.51", "167.01", "17.2"),
                          ("MCL", "168.17", "193.26", "14.9")]:
        row = t.add_row().cells
        row[0].text, row[1].text, row[2].text, row[3].text = name, a, b, g
    d.add_heading("Unstarred Question No. 388", level=1)
    d.add_paragraph("Question: The steps taken to augment evacuation capacity?")
    d.add_paragraph("Reply: 44 first-mile connectivity projects of 429.5 MTPA capacity "
                    "are operational; 102.5 MT moved through FMC in FY2024-25 against a "
                    "target of 125 MT in FY2025-26. Two rapid loading silos were commissioned "
                    "at Dipka OCP and Gevra Area, and construction of the Tori-Shivpur railway "
                    "line is in advanced stages.")
    for item in ("Construction of the Tori-Shivpur railway line.",
                 "First Mile Connectivity projects at Dipka OCP and Gevra Area.",
                 "Rapid loading silos commissioned at Kusmunda OCP."):
        d.add_paragraph(item, style="List Bullet")
    d.add_heading("Starred Question No. 301", level=1)
    d.add_paragraph("Question: The number of fatal accidents in coal mines during "
                    "2021, 2022 and 2023?")
    d.add_paragraph("Reply: CIL recorded 27, 18 and 26 fatal accidents with 29, 20 and 29 "
                    "fatalities in 2021, 2022 and 2023 respectively. The fatality rate per "
                    "million tonnes improved to 0.04. The 49th Standing Committee on Safety in "
                    "Coal Mines met on 17 December 2024 and launched the National Coal Mines "
                    "Safety Report Portal for real-time monitoring.")
    d.add_heading("Unstarred Question No. 512", level=1)
    d.add_paragraph("Question: Steps to raise domestic coking coal availability for steel plants?")
    d.add_paragraph("Reply: Under Mission Coking Coal, output rose from 44.79 MT in FY2020-21 "
                    "to 60.43 MT in FY2023-24. BCCL commissioned the 5 MTPA New Madhuband washery "
                    "in FY2023-24 and eight new washeries of 21.5 MTPA combined capacity are under "
                    "implementation. NRS coking linkage tenure was extended up to 30 years and a "
                    "Steel-through-WDO sub-sector was created in March 2024.")
    t3 = d.add_table(rows=1, cols=2)
    t3.style = "Table Grid"
    h3 = t3.rows[0].cells
    h3[0].text, h3[1].text = "Year", "Coking output (MT)"
    for y, v in [("2020-21", "44.79"), ("2021-22", "46.60"), ("2022-23", "54.63"),
                 ("2023-24", "60.43"), ("2024-25", "66.47")]:
        r = t3.add_row().cells
        r[0].text, r[1].text = y, v
    d.add_heading("Starred Question No. 620", level=1)
    d.add_paragraph("Question: What is the status of coal evacuation through first-mile "
                    "connectivity projects?")
    d.add_paragraph("Reply: 44 FMC projects of 429.5 MTPA are operational and moved 102.5 MT in "
                    "FY2024-25. Nineteen projects of nearly 150 MTPA commission in FY2025-26 for a "
                    "125 MT target, and 92 CIL projects of 994 MTPA complete by FY2028-29 at a "
                    "capex of Rs 31,367.66 crore.")
    d.add_heading("Unstarred Question No. 701", level=1)
    d.add_paragraph("Question: Details of exploration and the national coal inventory?")
    d.add_paragraph("Reply: CMPDI drilled 4.317 lakh metres departmentally and 4.308 lakh metres "
                    "through outsourcing in FY2023-24, preparing 31 geological reports. Geological "
                    "resources stand at 378.21 billion tonnes as on 1 April 2023: 199.90 BT measured, "
                    "151.68 BT indicated and 26.63 BT inferred, led by Odisha at 94.52 BT.")
    t4 = d.add_table(rows=1, cols=2)
    t4.style = "Table Grid"
    h4 = t4.rows[0].cells
    h4[0].text, h4[1].text = "State", "Resources (BT)"
    for s, v in [("Odisha", "94.52"), ("Jharkhand", "87.84"), ("Chhattisgarh", "80.77"),
                 ("West Bengal", "33.93"), ("Madhya Pradesh", "32.22")]:
        r = t4.add_row().cells
        r[0].text, r[1].text = s, v
    d.add_heading("Starred Question No. 715", level=1)
    d.add_paragraph("Question: What are the subsidiary-wise production targets and achievements "
                    "for FY2023-24?")
    d.add_paragraph("Reply: Against the 780 MT national target for CIL, achievement was 773.65 MT "
                    "at 99.2 percent. MCL exceeded target at 101.0 percent with 206.10 MT, CCL at "
                    "102.4 percent with 86.05 MT, NCL at 102.4 percent with 136.15 MT and WCL at "
                    "103.1 percent with 69.11 MT. SECL achieved 93.7 percent with 187.38 MT and ECL "
                    "93.3 percent with 47.56 MT, both affected by monsoon flooding in Q2.")
    t5 = d.add_table(rows=1, cols=4)
    t5.style = "Table Grid"
    h5 = t5.rows[0].cells
    h5[0].text, h5[1].text, h5[2].text, h5[3].text = (
        "Subsidiary", "Target (MT)", "Actual (MT)", "Achievement (%)")
    for n, t_, a, p in [("ECL", "51.00", "47.56", "93.3"), ("BCCL", "41.00", "41.10", "100.2"),
                        ("CCL", "84.00", "86.05", "102.4"), ("NCL", "133.00", "136.15", "102.4"),
                        ("WCL", "67.00", "69.11", "103.1"), ("SECL", "200.00", "187.38", "93.7"),
                        ("MCL", "204.00", "206.10", "101.0")]:
        r = t5.add_row().cells
        r[0].text, r[1].text, r[2].text, r[3].text = n, t_, a, p
    d.add_heading("Unstarred Question No. 730", level=1)
    d.add_paragraph("Question: What is the government doing about coal imports and the "
                    "one-billion-tonne roadmap?")
    d.add_paragraph("Reply: Non-essential thermal imports of 176 MT cost Rs 2.84 lakh crore in "
                    "FY2023-24. The roadmap takes all-India output to 1,390 MT by FY2029-30 with "
                    "CIL at 1,000 MT, backed by 68 mega projects of 3,780 MT pipeline capacity, 92 "
                    "FMC projects of 994 MTPA and 14 clearances totalling 210 MTPA under appraisal. "
                    "Import substitution at full displacement saves about Rs 2.10 lakh crore yearly.")
    d.add_heading("Starred Question No. 744", level=1)
    d.add_paragraph("Question: What is the status of underground coal production and safety in "
                    "underground mines?")
    d.add_paragraph("Reply: Underground mines produced 25.55 MT in FY2023-24 with OMS at 1.18 "
                    "tonnes, up from 0.86 tonnes in FY2017-18 on 26 continuous miner panels and two "
                    "longwall faces at Moonidih and Jhanjra. ECL runs the largest UG fleet with 60 "
                    "mines producing 10.10 MT, and longwall face II at Jhanjra achieved 4,200 tonnes "
                    "per day in March, a company record for mass-production technology. All 11 SECL "
                    "underground mines completed strata control audits during the year, and depillaring "
                    "panels run 1 bolt per sqm roof support density with tell-tale instrumentation on "
                    "112 panels at ECL alone. Man-riding chairlifts in 22 UG mines cut walking injuries "
                    "by 44 percent, while proximity detection now covers 68 percent of the underground "
                    "HEMM fleet across CIL. Mass-production technology targets 100 MT of UG output by "
                    "FY2029-30 from 26 continuous miner panels and 8 longwalls, with surface miners "
                    "already handling 42 percent of opencast coal without drilling or blasting.")
    d.add_heading("Unstarred Question No. 758", level=1)
    d.add_paragraph("Question: How is the government ensuring coal quality and grade conformity "
                    "for consumers?")
    d.add_paragraph("Reply: Third-party sampling covers 100 percent of rail loading points with "
                    "referee uphold rates of 94 to 97 percent across subsidiaries. Closed FMC handling "
                    "ends contamination from dust, stones and moisture, lifting grade conformity at "
                    "silo sidings 4 points above manual sidings. Surface miners at Gevra and Dipka "
                    "produce sized coal directly, cutting crusher load by 38 percent, while feeder-"
                    "breaker circuits at Kusmunda lifted sized-coal share to 64 percent of despatch. "
                    "The Ghugus washery treated 2.10 MT cutting ash from 38.2 to 33.9 percent for the "
                    "Chandrapur station, and MCL washeries monitor ash and moisture continuously with "
                    "grade slippage incidents down to 11 from 19. Grade conformity penalties fell "
                    "company-wide to Rs 480 crore as sampling expanded, and the new Ghugus seam keeps "
                    "G12 realisation steady for WCL linkage consumers into the new year.")
    d.add_heading("Starred Question No. 771", level=1)
    d.add_paragraph("Question: What employment and rehabilitation provisions exist for "
                    "land-affected families?")
    d.add_paragraph("Reply: Fatal mine accidents draw Rs 15 lakh compensation plus Rs 90,000 "
                    "ex-gratia, Rs 1,25,000 life cover and employment to one dependent. Gevra expansion "
                    "budgets Rs 1,860 crore for 1,240 hectares with Rs 28.40 lakh per acre compensation "
                    "and 1,140 employments, while Rajmahal offers Rs 28.40 lakh per acre with 640 "
                    "employments and ITI seats for 240 oustee youth yearly. The Pali township houses "
                    "420 families with schools enrolling 640 children, and CSR spend of Rs 84.60 crore "
                    "covers 62 villages around Gevra with health vans logging 28,000 consultations. "
                    "Post-retirement medical support covers 2.63 lakh employees up to Rs 25 lakh, and "
                    "skill development through 24 institutes certified 12,400 persons including 3,100 "
                    "HEMM operators and 640 women dumper drivers.")
    t6 = d.add_table(rows=1, cols=3)
    t6.style = "Table Grid"
    h6 = t6.rows[0].cells
    h6[0].text, h6[1].text, h6[2].text = "Project", "R&R budget (Rs cr)", "Employments"
    for p, b, e in [("Gevra expansion", "1860", "1140"), ("Rajmahal expansion", "920", "640"),
                    ("Siarmal", "1240", "820"), ("Lingaraj expansion", "480", "360")]:
        r = t6.add_row().cells
        r[0].text, r[1].text, r[2].text = p, b, e
    d.add_heading("Unstarred Question No. 785", level=1)
    d.add_paragraph("Question: What is the status of manpower productivity and OMS across "
                    "subsidiaries?")
    d.add_paragraph("Reply: CIL overall OMS reached 13.43 tonnes in FY2023-24, rising from 7.44 "
                    "tonnes in FY2017-18, with opencast OMS at 25.43 tonnes and underground at 1.18 "
                    "tonnes. MCL leads at 22.50 tonnes on its opencast fleet, NCL follows at 14.20 "
                    "tonnes, while ECL trails at 4.10 tonnes on its 60-mine underground fleet. CCL "
                    "improved from 3.18 tonnes in FY2021-22 to 3.42 tonnes in FY2023-24 with 38,214 "
                    "employees. Departmental strength of 2.39 lakh is supplemented by 1.02 lakh "
                    "contractor workers moving 58 percent of overburden. Simulator training crossed "
                    "42,000 hours across six centres, cutting HEMM reversing incidents 31 percent, and "
                    "women run 18 percent of the NCL ancillary fleet after in-house driving schools.")
    t7 = d.add_table(rows=1, cols=3)
    t7.style = "Table Grid"
    h7 = t7.rows[0].cells
    h7[0].text, h7[1].text, h7[2].text = "Year", "Overall OMS", "OC OMS"
    for y, o, c in [("2019-20", "8.53", "14.25"), ("2020-21", "9.02", "15.09"),
                    ("2021-22", "9.56", "15.46"), ("2022-23", "12.80", "22.04"),
                    ("2023-24", "13.43", "25.43")]:
        r = t7.add_row().cells
        r[0].text, r[1].text, r[2].text = y, o, c
    d.add_heading("Starred Question No. 792", level=1)
    d.add_paragraph("Question: How does washed coal evacuation perform for the steel sector?")
    d.add_paragraph("Reply: Washed despatch of 10.85 MT moved 94 percent by rail to steel plants at "
                    "Bokaro, Rourkela, Durgapur and Burnpur with 96 percent linkage materialisation at "
                    "SAIL. Dugda produced 4.85 MT at 48.5 percent yield, Bhojudih 3.62 MT at 51.2 "
                    "percent and Madhuband 2.38 MT at 48.6 percent, with washed ash averaging 17.9 "
                    "percent against raw ash of 34.5 percent. Turnaround at washery sidings averaged "
                    "5.2 hours with demurrage of Rs 2.10 crore, the lowest among BCCL loading points. "
                    "Eight new washeries of 21.5 MTPA take domestic washed capacity past 35 MTPA by "
                    "FY2029-30, displacing about 12 MT of coking imports yearly at full rate.")
    t8 = d.add_table(rows=1, cols=4)
    t8.style = "Table Grid"
    h8 = t8.rows[0].cells
    h8[0].text, h8[1].text, h8[2].text, h8[3].text = (
        "Washery", "Feed (MT)", "Washed (MT)", "Yield (%)")
    for w, f_, c, y in [("Dugda", "10.00", "4.85", "48.5"), ("Bhojudih", "7.07", "3.62", "51.2"),
                        ("Madhuband", "4.90", "2.38", "48.6")]:
        r = t8.add_row().cells
        r[0].text, r[1].text, r[2].text, r[3].text = w, f_, c, y
    d.add_heading("Unstarred Question No. 801", level=1)
    d.add_paragraph("Question: What safety record do coal subsidiaries report for 2024, and what "
                    "compensation applies to accident victims?")
    d.add_paragraph("Reply: CIL recorded 22 fatal accidents with 24 fatalities in 2024 up to November "
                    "against 26 and 29 in 2023, holding the fatality rate per million tonnes at 0.04. "
                    "SECL improved from 8 fatal accidents in 2022 to 6 in 2024 while BCCL reached zero, "
                    "and NCL's contractor HEMM mandate followed five Singrauli accidents. Fatal mine "
                    "accidents draw Rs 15 lakh compensation plus Rs 90,000 ex-gratia, Rs 1,25,000 life "
                    "cover and employment to one dependent, with post-retirement medical support for "
                    "2.63 lakh employees up to Rs 25 lakh. The 49th Standing Committee met on 17 "
                    "December 2024 with 20 companies and launched the National Coal Mines Safety Report "
                    "Portal for real-time monitoring with a safety audit module.")
    t9 = d.add_table(rows=1, cols=3)
    t9.style = "Table Grid"
    h9 = t9.rows[0].cells
    h9[0].text, h9[1].text, h9[2].text = "Year", "Fatal accidents", "Fatalities"
    for y, a, t_ in [("2021", "27", "29"), ("2022", "18", "20"),
                     ("2023", "26", "29"), ("2024", "22", "24")]:
        r = t9.add_row().cells
        r[0].text, r[1].text, r[2].text = y, a, t_
    d.add_paragraph("The initiatives above are monitored quarterly by the Ministry, with "
                    "production, evacuation and safety dashboards reviewed in the monthly secretary-level "
                    "meeting. State governments are associated through joint review committees for land, "
                    "rehabilitation and law-and-order support around the Korba, Talcher and Singrauli "
                    "coalfields. Skill development through 24 mining training institutes certified 12,400 "
                    "persons during the year, including 3,100 HEMM operators for the mega opencast projects.")
    return d


def make_mcl_report(revised=False):
    f = FlowDoc()
    f.h1("MCL Annual Report 2023-24" + (" (Revised)" if revised else ""))
    f.h2("1. Overview")
    f.para(
        "Mahanadi Coalfields Limited (MCL) recorded total coal production of "
        "201.45 MT during FY2023-24, against 193.80 MT in FY2022-23. The three "
        "featured opencast projects of MCL, Lakhanpur OCP, Ananta OCP and "
        "Lingaraj OCP, together produced about fifty-five MT during FY2023-24. MCL "
        "remains the largest producing subsidiary of Coal India Limited.")
    f.para(
        "Offtake touched 198.30 MT with rail loading at a record 21.4 rakes per day in March. "
        "Overburden removal of 212.40 million cu.m kept the stripping ratio at 1.05 cu.m per "
        "tonne. The Ib Valley washery treated 8.60 MT of raw coal at a yield of 72.4 percent.")
    f.h2("2. Production Performance")
    f.para(
        "Mine-wise production of MCL for the last five financial years is "
        "presented below. Values are in million tonnes (MT). Lakhanpur shows an "
        "unbroken rising series across all five years, while Ananta dipped in FY2022-23 "
        "after a shovel fire before recovering to 14.20 MT.")
    rows = [[m] + vals for m, vals in MCL_PROD.items()]
    if revised:
        rows[2][-1] = "18.30"  # Lingaraj OCP FY2023-24 revised figure
    f.table(["Mine (production, MT)"] + MCL_YEARS, rows, col_w=[130, 64, 64, 64, 64, 64])
    f.h2("3. Offtake, Reserves and Manpower")
    reserves = "1131.20" if revised else "1124.60"
    f.para(
        "MCL recorded coal offtake of 178.20 MT during FY2023-24, with grade-wise "
        "despatch monitored monthly by MCL. Total extractable reserves of MCL as "
        f"on 1 April 2024 stand at {reserves} MT. MCL manpower stood at 21,346 employees "
        "as on 31 March 2024, and manpower training totalled 118,200 man-days.")
    f.table(["Year", "Offtake (MT)", "Reserves (MT)", "Manpower"],
            [["2021-22", "164.50", "1098.40", "22410"],
             ["2022-23", "171.80", "1112.30", "21890"],
             ["2023-24", "178.20", reserves, "21346"]],
            col_w=[100, 110, 110, 110])
    f.h2("4. Coal Quality")
    f.para(
        "Average quality parameters of MCL coal despatched during FY2023-24 are "
        "tabulated below. MCL washeries monitor ash and moisture continuously, and "
        "grade slippage incidents fell to 11 for the year from 19 previously.")
    f.table(["Mine", "GCV (kcal/kg)", "Ash (%)"],
            [["Lakhanpur OCP", "4850", "34.2"],
             ["Ananta OCP", "4620", "36.8"],
             ["Lingaraj OCP", "4950", "33.1"]])
    f.h2("5. Projects and First Mile Connectivity")
    f.para(
        "The Lingaraj expansion from 16 to 20 MTPA received Stage-II forest clearance in "
        "January 2024, and the 20 MTPA Siarmal project advances toward commissioning. Two "
        "silos of 10 MTPA each at Lakhanpur and Ananta will take mechanised evacuation to "
        "74 MTPA, covering 92 percent of MCL despatch by FY2027-28.")
    f.table(["Project", "Capacity (MTPA)", "Status", "FMC (MTPA)"],
            [["Lingaraj expansion", "20.0", "Stage-II cleared", "12.0"],
             ["Siarmal OCP", "40.0", "Construction", "25.0"],
             ["Lakhanpur silo", "10.0", "Commissioning", "10.0"]],
            col_w=[140, 100, 110, 90])
    f.h2("6. Safety and Environment")
    f.para(
        "Three fatal accidents were recorded in 2024 against six in 2023. The company planted "
        "4.20 lakh saplings over 168 hectares of reclaimed decoaled land, and mine-water supply "
        "to 34 villages covered 41,000 people. PM10 levels at all four continuous monitoring "
        "stations stayed within the national ambient norms on 96 percent of days.")
    f.bullets([
        "Target FY2024-25: 225 MT production with Siarmal first coal in Q3.",
        "Zero-harm goal: simulator training mandatory for all 1,840 HEMM operators.",
        "CSR spend of Rs 212.40 crore across 214 villages in the command area.",
    ])
    f.h2("7. Quarterly momentum")
    f.para(
        "Quarterly production stepped up from 48.20 MT in Q1 to 54.60 MT in Q4 as Siarmal box-cut "
        "widened and Lingaraj hit a 5.20 MT quarter. Offtake lagged production by 3.15 MT on the "
        "year as siding stocks rebuilt ahead of the monsoon.")
    f.table(["Quarter", "Production (MT)", "Offtake (MT)"],
            [["Q1", "48.20", "46.80"], ["Q2", "49.40", "48.20"],
             ["Q3", "51.20", "50.10"], ["Q4", "54.60", "53.20"]],
            col_w=[110, 130, 130])
    f.h2("8. Grade and pricing")
    f.para(
        "E-auction of 8.60 MT fetched 118 percent premium while linkage realisation held at Rs "
        "1,560 per tonne. Grade G12 dominated despatch at 96.40 MT, with G11 power coal at 62.80 "
        "MT and superior grades at 19.00 MT for non-regulated buyers.")
    f.table(["Grade", "Despatch (MT)", "Realisation (Rs/t)"],
            [["G11", "62.80", "1980"], ["G12", "96.40", "1820"],
             ["G13", "24.60", "1640"], ["Superior", "19.00", "4860"]],
            col_w=[110, 120, 130])
    f.h2("9. Manpower productivity")
    f.para(
        "Overall OMS reached 22.50 tonnes on the opencast fleet, among CIL's highest. Contractor "
        "HEMM logged 68 percent of overburden as departmental strength focused on coal faces. "
        "Women operators now run 42 dumpers across Lingaraj and Lakhanpur after the in-house "
        "training school certified its third batch.")
    f.h2("10. Risk register")
    f.para(
        "Monsoon flooding in the Ib valley cost 2.40 MT in August flash floods. Land possession "
        "for Siarmal phase II slipped two quarters on award disputes covering 340 hectares. "
        "Grade slippage penalties of Rs 38 crore were the lowest in five years on tighter "
        "third-party sampling.")
    f.bullets([
        "Siarmal land awards targeted by December for phase II.",
        "Flood pumping capacity raised to 42,000 gpm across Ib valley.",
        "Grade uphold rate 97 percent in referee sampling.",
    ])
    f.h2("11. Overburden and HEMM annex")
    f.para(
        "Overburden of 212.40 million cu.m held stripping at 1.05 cu.m per tonne across the Ib "
        "valley and Talcher fields. Shovel availability averaged 85.2 percent with the two new "
        "20 cu.m units at Lingaraj logging 7,420 hours each.")
    f.table(["Mine", "OBR (Mcum)", "Stripping ratio"],
            [["Lakhanpur OCP", "48.60", "2.13"],
             ["Ananta OCP", "32.40", "2.28"],
             ["Lingaraj OCP", "38.20", "2.15"],
             ["Bharatpur OCP", "28.40", "1.86"],
             ["Others", "64.80", "0.72"]],
            col_w=[140, 100, 110])
    f.table(["Year", "OBR (Mcum)", "Availability (%)"],
            [["2021-22", "188.40", "83.10"],
             ["2022-23", "198.60", "84.20"],
             ["2023-24", "212.40", "85.20"]],
            col_w=[140, 110, 110])
    f.h2("12. Rake and siding annex")
    f.para(
        "Rake loading averaged 21.4 per day in March with the Jharsuguda-Barpali doubling "
        "absorbing the Siarmal surge. Demurrage fell to Rs 6.20 crore as silo loading cut "
        "detention to 3.6 hours per rake.")
    f.table(["Siding", "Rakes/day", "Qty (MT)"],
            [["Lakhanpur silo", "6.20", "9.40"],
             ["Jharsuguda", "5.40", "8.20"],
             ["Talcher", "4.80", "7.10"],
             ["Ib valley", "3.20", "4.60"],
             ["Others", "1.80", "2.50"]],
            col_w=[140, 100, 100])
    f.table(["Year", "Rakes/day", "Demurrage (Rs cr)"],
            [["2021-22", "17.20", "12.40"],
             ["2022-23", "19.10", "8.60"],
             ["2023-24", "21.40", "6.20"]],
            col_w=[140, 110, 110])
    f.h2("13. Financial annex")
    f.para(
        "Revenue of Rs 32,160 crore and PAT of Rs 10,240 crore reflect record offtake and "
        "118 percent e-auction premiums. Capex of Rs 3,120 crore centred on Siarmal box-cut, "
        "Lingaraj expansion and the two 10 MTPA silos.")
    f.table(["Head (Rs cr)", "2021-22", "2022-23", "2023-24"],
            [["Revenue", "24840", "28480", "32160"],
             ["PAT", "6840", "8420", "10240"],
             ["Capex", "2480", "2820", "3120"]],
            col_w=[140, 90, 90, 90])
    f.table(["Channel", "Qty (MT)", "Realisation (Rs/t)"],
            [["Power linkage", "142.40", "1560"],
             ["NRS auction", "28.60", "2980"],
             ["E-auction spot", "8.60", "3420"],
             ["Washery", "8.60", "4860"]],
            col_w=[140, 100, 120])
    return f


def make_ncl_workbook():
    sheets = [
        ("Production", "Production (lakh tonnes)",
         ["Mine"] + NCL_YEARS,
         [[m] + v for m, v in NCL_PROD.items()]),
        ("Offtake", "Offtake (lakh tonnes)",
         ["Mine", "2022-23", "2023-24"],
         [[m] + v for m, v in NCL_OFFTAKE.items()] +
         [[], [], ["Project", "Drilling 2023-24", "Unit"],
          ["NCL coalfields", 4.61, "lakh metres"]]),
        ("Quality", "GCV and ash",
         ["Mine", "GCV (kcal/kg)", "Ash (%)"],
         [["Jayant OCP", 4780, 35.4], ["Nigahi OCP", 4720, 36.1],
          ["Dudhichua OCP", 4650, 37.2], ["Amlohri OCP", 4810, 34.8]]),
        ("Manpower", "Manpower (numbers)",
         ["Category", "2022", "2023", "2024"],
         [["Executives", 1820, 1840, 1865], ["Supervisors", 3210, 3240, 3280],
          ["Workers", 11240, 11180, 11120]]),
        ("Rakes", "Monthly rake loading FY24",
         ["Month", "Rakes", "Qty (lakh tonnes)"],
         [[m, r, q] for m, r, q in zip(
             ["Apr", "May", "Jun", "Jul", "Aug", "Sep",
              "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
             [410, 425, 398, 380, 372, 390, 415, 430, 445, 460, 470, 495],
             [16.2, 16.8, 15.7, 15.0, 14.7, 15.4, 16.4, 17.0, 17.6, 18.2, 18.6, 19.6])]),
        ("Projects", "Ongoing projects",
         ["Project", "Capacity (MTPA)", "Status"],
         [["Jayant expansion", "25.0", "EC stage"],
          ["Nigahi CHP", "15.0", "Construction"],
          ["Khadia FMC silo", "10.0", "Commissioning"]]),
    ]
    return sheets


def make_ncl_ops_note():
    f = FlowDoc()
    f.h1("NCL Operational Note FY2022-23")
    f.h2("1. Offtake review")
    f.para(
        "Northern Coalfields Limited (NCL) reviews mine-wise offtake for the "
        "Financial Year 2022-23. As reconciled by NCL, Jayant OCP offtake stood "
        "at 197.9 lakh tonnes during FY2022-23. NCL further notes that Nigahi "
        "OCP produced 208.6 lakh tonnes during FY2023-24, and NCL drilling "
        "achieved 4.61 lakh metres in the same year.")
    f.table(["Mine", "Offtake 2022-23 (lakh tonnes)"],
            [["Jayant OCP", "197.9"],
             ["Nigahi OCP", "201.8"],
             ["Dudhichua OCP", "161.9"]], col_w=[220, 220])
    f.h2("2. Reconciliation method")
    f.para(
        "Offtake is reconciled from weighbridge, rail-in-motion and siding stock surveys on "
        "the last working day of each month. The 2.5 lakh tonne gap between the workbook "
        "figure of 195.4 and the reconciled 197.9 for Jayant traces to March dispatches "
        "loaded after the workbook freeze date. NCL has moved the freeze to the 5th of the "
        "following month from FY2023-24 to prevent recurrence.")
    f.h2("3. Production context")
    f.para(
        "Jayant produced 196.8 lakh tonnes in FY2022-23 and 201.5 lakh tonnes in FY2023-24, "
        "while Nigahi rose from 203.0 to 208.6 lakh tonnes. Dudhichua added 163.1 lakh tonnes "
        "and Amlohri 114.0 lakh tonnes in FY2023-24. Combined NCL production of 686.8 lakh "
        "tonnes in unit terms converts to 136.15 MT on the company account after custodian "
        "mine adjustments.")
    f.table(["Mine", "2021-22", "2022-23", "2023-24"],
            [["Jayant OCP", "190.2", "196.8", "201.5"],
             ["Nigahi OCP", "197.3", "203.0", "208.6"],
             ["Dudhichua OCP", "158.4", "163.1", "168.7"],
             ["Amlohri OCP", "106.9", "110.4", "114.0"]],
            col_w=[150, 90, 90, 90])
    f.h2("4. Rake loading")
    f.para(
        "Rake loading averaged 14.2 rakes per day in Q4 FY2022-23, peaking at 16.5 in March. "
        "The Khadia rapid loading system cut loading time per rake to 2.8 hours. Demurrage fell "
        "to Rs 4.20 crore for the year from Rs 7.80 crore previously.")
    f.table(["Quarter", "Rakes/day", "Demurrage (Rs cr)"],
            [["Q1", "12.1", "1.80"], ["Q2", "11.6", "1.10"],
             ["Q3", "13.4", "0.80"], ["Q4", "14.2", "0.50"]],
            col_w=[120, 110, 130])
    f.h2("5. Drilling and outlook")
    f.para(
        "Exploratory drilling of 4.61 lakh metres proved 0.42 billion tonnes of additional "
        "resources in the Singrauli coalfield. For FY2023-24 NCL targets 139 MT of production "
        "with Jayant crossing 20 MT for the first time, supported by the new 25 MTPA expansion "
        "environmental clearance currently at appraisal stage.")
    f.bullets([
        "Workbook freeze moved to the 5th of the following month.",
        "Jayant 20 MT milestone targeted for FY2023-24.",
        "Khadia FMC silo commissioning in Q2 FY2023-24.",
    ])
    f.h2("6. Cost and realisation")
    f.para(
        "Cash cost per tonne held at Rs 1,120 despite diesel inflation, as HEMM productivity "
        "gains offset fuel. E-auction premiums averaged 112 percent on 6.40 MT, lifting overall "
        "realisation to Rs 1,980 per tonne against Rs 1,840 the previous year.")
    f.table(["Head", "FY2021-22", "FY2022-23"],
            [["Cash cost (Rs/t)", "1080", "1120"],
             ["E-auction premium (%)", "98", "112"],
             ["Realisation (Rs/t)", "1840", "1980"]],
            col_w=[150, 110, 110])
    f.h2("7. Contractor and HEMM fleet")
    f.para(
        "Contractor dumpers moved 58 percent of overburden under closely monitored rate "
        "contracts. Departmental shovel availability averaged 84.2 percent, and the two new 20 "
        "cu.m shovels at Nigahi cut prime stripping cost by Rs 42 per cu.m.")
    f.h2("8. Environment compliance")
    f.para(
        "All ten mines hold valid consent to operate with PM10 compliance at 94 percent of "
        "station-days. Over 6.40 lakh saplings were planted on 214 hectares of external dumps, "
        "and the Singrauli water supply scheme delivers 12 MLD of treated mine water to townships.")
    f.h2("9. Manpower")
    f.para(
        "NCL employed 14,200 persons with OMS at 14.20 tonnes, CIL's highest for a mixed fleet. "
        "Simulator training covered all 640 dumper operators, and women run 18 percent of the "
        "ancillary fleet after the in-house driving school's fourth batch.")
    f.h2("10. Overburden annex")
    f.para(
        "Overburden of 362.80 million cu.m held stripping at 2.66 cu.m per tonne in the "
        "Singrauli coalfield. Dragline walks totalled 42 km across Jayant and Nigahi, and "
        "contractor share of 58 percent stayed within the costed mine plans.")
    f.table(["Mine", "OBR (Mcum)", "Stripping ratio"],
            [["Jayant OCP", "118.40", "2.84"],
             ["Nigahi OCP", "112.60", "2.71"],
             ["Dudhichua OCP", "78.40", "2.52"],
             ["Amlohri OCP", "53.40", "2.41"]],
            col_w=[140, 110, 110])
    f.table(["Year", "OBR (Mcum)", "Stripping ratio"],
            [["2020-21", "312.40", "2.72"],
             ["2021-22", "338.60", "2.58"],
             ["2022-23", "362.80", "2.66"]],
            col_w=[140, 110, 110])
    f.h2("11. Consumer linkage annex")
    f.para(
        "NTPC Singrauli and Rihand lift 68.40 MTPA under SHAKTI linkage with 97.2 percent "
        "materialisation, while UP Rajya Vidyut takes 22.60 MTPA. E-auction of 6.40 MT at 112 "
        "percent premium serves the non-regulated cluster around Singrauli.")
    f.table(["Consumer", "Linkage (MTPA)", "Lifting (MT)"],
            [["NTPC Singrauli", "38.20", "37.40"],
             ["NTPC Rihand", "30.20", "29.10"],
             ["UPRVUNL", "22.60", "21.80"],
             ["NRS/e-auction", "6.40", "6.10"]],
            col_w=[150, 110, 100])
    f.table(["Year", "Linkage lifting (%)", "E-auction premium (%)"],
            [["2020-21", "94.20", "88"],
             ["2021-22", "96.10", "98"],
             ["2022-23", "97.20", "112"]],
            col_w=[150, 120, 120])
    f.h2("12. Financial annex")
    f.para(
        "Revenue of Rs 20,120 crore and PAT of Rs 5,180 crore reflect full linkage lifting and "
        "record e-auction premiums. Capex of Rs 1,840 crore went to the Khadia silo, Nigahi CHP "
        "and the Jayant expansion approach roads.")
    f.table(["Head (Rs cr)", "2020-21", "2021-22", "2022-23"],
            [["Revenue", "16840", "18420", "20120"],
             ["PAT", "3840", "4420", "5180"],
             ["Capex", "1420", "1640", "1840"]],
            col_w=[140, 90, 90, 90])
    f.h2("13. Safety annex")
    f.para(
        "Three fatal accidents with three fatalities in 2024 up to November compare with two "
        "and two in 2023 across Singrauli. Slope radar on Jayant and Nigahi highwalls, "
        "proximity detection on 68 percent of the HEMM fleet and 168 mock drills anchor the "
        "zero-harm drive for the 25 MTPA Jayant expansion workforce.")
    f.table(["Indicator", "2022", "2023", "2024"],
            [["Fatal accidents", "1", "2", "3"],
             ["Serious accidents", "8", "12", "4"],
             ["Mock drills", "124", "148", "168"]],
            col_w=[140, 90, 90, 90])
    f.table(["Mine", "HEMM with proximity (%)", "Slope radar"],
            [["Jayant OCP", "72", "Yes"],
             ["Nigahi OCP", "68", "Yes"],
             ["Dudhichua OCP", "64", "Partial"],
             ["Amlohri OCP", "61", "Partial"]],
            col_w=[140, 150, 100])
    f.bullets([
        "100 percent proximity coverage targeted by March 2025.",
        "Contractor induction centre certifies 420 crew monthly.",
        "Heat-stress SOPs for 47-degree Singrauli summers in force.",
    ])
    return f


def bccl_scan_pages():
    return [
        ["# BCCL Exploration Report 2023-24",
         "## Drilling Performance",
         "Bharat Coking Coal Limited (BCCL) completed 2.34 lakh metres of",
         "exploratory drilling during FY2023-24 across the Moonidih and",
         "Muraidih blocks of BCCL. Muraidih OCP produced 8.45 MT during",
         "FY2023-24 while Moonidih UG produced 2.18 MT in the same period.",
         "Departmental drills contributed 0.92 lakh metres of the total.",
         "## Seam Details",
         "The coking coal seam occurs at a depth of 380 m to 420 m with an",
         "average thickness of 6.4 m. GCV of the seam averages 6,100 kcal/kg",
         "with ash content of 19.8 percent."],
        ["# BCCL Reserves Statement",
         "## Extractable Reserves",
         "Extractable reserves of BCCL as on 1 April 2024 stand at 312.75 MT.",
         "Proved reserves of the Moonidih block of BCCL are 148.20 MT with",
         "a stripping ratio of 3.10 cu.m per tonne.",
         "Indicated resources of 96.40 MT await infill drilling approval.",
         "## Washery Linkage",
         "Raw coal feed to the Madhuband washery averaged 4.90 MT per year",
         "at 34.5 percent ash. Washed output of 2.38 MT at 19.2 percent ash",
         "moved to steel plants under long-term linkage."],
        ["# Moonidih Block Geology",
         "## Structure",
         "The Moonidih block is split by two faults with throws of 45 m and",
         "28 m. Seam IX (Top) averages 4.1 m thickness across 14 boreholes.",
         "Seam VIII holds 2.8 m with sulphur below 0.6 percent.",
         "Gradient of the seam is 1 in 4 towards the north-west.",
         "## Coal Quality",
         "Coking properties show CSN values between 6 and 8, suitable for",
         "blending at 22 percent in the steel plant burden."],
        ["# Muraidih Production Review",
         "## OCP Performance",
         "Muraidih OCP produced 8.45 MT in FY2023-24 against 7.90 MT in the",
         "previous year. Overburden removal of 24.60 million cu.m kept the",
         "stripping ratio at 2.91 cu.m per tonne.",
         "HEMM availability averaged 82.4 percent across the shovel fleet.",
         "## Dispatch",
         "Rail dispatch of 7.10 MT moved through the Muraidih siding with",
         "a turnaround of 36 hours per rake on average."],
        ["# Safety in BCCL Mines",
         "## Accident Record",
         "No fatal accident was recorded in BCCL during 2024 up to November,",
         "against five fatal accidents in 2023. Serious accidents fell to",
         "three from four in the previous year.",
         "Roof-bolting coverage in underground galleries reached 94 percent.",
         "## Training",
         "Refresher training covered 6,240 workers across the Kusunda and",
         "Bastacola areas during the reporting year."],
        ["# Recommendations",
         "## Further Exploration",
         "Infill drilling of 18,000 metres is recommended in the Muraidih",
         "deep block to convert 42 MT to the proved category.",
         "A washability study on Seam VI will support the New Moonidih",
         "washery design of 2.5 MTPA capacity.",
         "Reserves of 312.75 MT for BCCL are retained pending review."],
    ]


def make_washery_note():
    f = FlowDoc()
    f.h1("Coking Coal Washery Performance Note")
    f.h2("1. Washery output FY2023-24")
    f.para(
        "This note reviews coking coal washeries of BCCL for FY2023-24. The "
        "Dugda washery produced 4.85 MT of washed coal at a yield of 48.5 "
        "percent, while the Bhojudih washery produced 3.62 MT at a yield of "
        "51.2 percent. Washed coal ash content averaged 17.9 percent against "
        "raw coal ash of 34.5 percent, with moisture at 6.2 percent.")
    f.table(["Washery", "Raw feed (MT)", "Washed (MT)", "Yield (%)", "Ash (%)"],
            [["Dugda", "10.00", "4.85", "48.5", "18.1"],
             ["Bhojudih", "7.07", "3.62", "51.2", "17.6"],
             ["Madhuband", "4.90", "2.38", "48.6", "19.2"]],
            col_w=[110, 100, 90, 80, 80])
    f.h2("2. Grade-wise despatch")
    f.para(
        "Despatch of Steel-II grade coking coal from BCCL washeries totalled "
        "8.4 lakh tonnes during FY2023-24. Washery-III grade despatch was 5.1 "
        "lakh tonnes in the same period. Long-term linkage consumers lifted 94 "
        "percent of their allocation, the balance moving through e-auction at an "
        "average premium of 142 percent.")
    f.h2("3. Mission Coking Coal context")
    f.para(
        "All-India coking coal output rose from 44.79 MT in FY2020-21 to 60.43 MT in "
        "FY2023-24. BCCL commissioned the 5 MTPA New Madhuband washery during the year, "
        "and eight new washeries of 21.5 MTPA combined capacity are under implementation, "
        "including Bhojudih expansion of 2.0 MTPA due in FY2025-26.")
    f.table(["Year", "Coking output (MT)"],
            [[y, v] for y, v in zip(COKING_YEARS, COKING_OUT)],
            col_w=[150, 150])
    f.h2("4. New washery pipeline")
    f.table(["Washery", "Capacity (MTPA)", "Due", "Status"],
            [[n, c, d, s] for n, c, d, _st, s in WASHERIES_NEW[:5]],
            col_w=[130, 100, 80, 140])
    f.para(
        "Bhojudih expansion adds heavy-media cyclones and a 240 TPH coarse circuit. "
        "Patherdih II replaces the 1970s Baum jigs with dense-media baths. New Moonidih "
        "is designed around Seam VI washability currently under study at CFRI.")
    f.h2("5. Quality control")
    f.para(
        "Third-party sampling at 18 loading points reported a consistency index of 91.2, "
        "up from 88.4. CSN values on washed Steel-II averaged 7.1, and phosphorus stayed "
        "below 0.09 percent across all grades. Referee samples upheld the declared grade "
        "in 97 of 100 challenged rakes.")
    f.h2("6. Outlook")
    f.para(
        "Washed output target for FY2024-25 is 12.40 MT with Madhuband at full rate. The "
        "NRS linkage tenure extension to 30 years and the Steel-through-WDO sub-sector "
        "created in March 2024 are expected to lift linkage lifting above 96 percent.")
    f.bullets([
        "Target FY2024-25: 12.40 MT washed coal at 18 percent ash.",
        "Bhojudih 2.0 MTPA expansion due FY2025-26.",
        "Referee uphold rate target: 98 percent.",
    ])
    f.h2("7. Raw coal linkage")
    f.para(
        "BCCL feeds 21.90 MT of raw coal to washeries and steel linkages from Moonidih, "
        "Muraidih and Bastacola. E-auction of 1.80 MT of washery middlings to cement plants "
        "fetched 134 percent premium, funding reject-handling upgrades.")
    f.table(["Destination", "Qty (MT)", "Ash spec (%)"],
            [["Washeries", "21.90", "34.5 max"],
             ["Steel direct", "4.20", "22.0 max"],
             ["Cement/middlings", "1.80", "42.0 max"]],
            col_w=[140, 100, 110])
    f.h2("8. Reject management")
    f.para(
        "Washery rejects of 9.40 MT feed three FBC power plants under long-term tie-up, with "
        "ash ponds at Dugda and Bhojudih capped and greened over 42 hectares. Fines below 0.5 "
        "mm go to the Madhuband flotation cells, recovering 0.40 MT of clean coal yearly.")
    f.h2("9. Maintenance")
    f.para(
        "Dense-media circuit availability averaged 91.4 percent across the three washeries. "
        "Magnetite consumption fell to 0.42 kg per tonne of feed after recovery-drum upgrades, "
        "saving Rs 26 crore annually.")
    f.h2("10. Manpower")
    f.para(
        "Washeries employ 1,240 persons with OMS at 8.60 tonnes. Operator certification through "
        "the CFRI-partnered course covered all 320 control-room staff, and women engineers head "
        "quality at Dugda and Madhuband.")
    f.h2("11. Feed and yield annex")
    f.para(
        "Raw feed of 21.97 MT across the three washeries yielded 10.85 MT of clean coal at 48.9 "
        "percent average yield. Middlings of 4.20 MT feed FBC boilers while 6.92 MT of rejects "
        "go to stowing and backfilling under DGMS permission.")
    f.table(["Washery", "Feed (MT)", "Clean (MT)", "Yield (%)"],
            [["Dugda", "10.00", "4.85", "48.5"],
             ["Bhojudih", "7.07", "3.62", "51.2"],
             ["Madhuband", "4.90", "2.38", "48.6"]],
            col_w=[120, 90, 90, 90])
    f.table(["Year", "Feed (MT)", "Clean (MT)"],
            [["2020-21", "18.20", "8.60"],
             ["2021-22", "19.40", "9.30"],
             ["2022-23", "20.80", "10.10"],
             ["2023-24", "21.97", "10.85"]],
            col_w=[120, 100, 100])
    f.h2("12. Dispatch annex")
    f.para(
        "Washed despatch moved 94 percent by rail to steel plants in Bokaro, Rourkela, Durgapur "
        "and Burnpur. Turnaround at washery sidings averaged 5.2 hours with demurrage of Rs 2.10 "
        "crore, the lowest among BCCL loading points.")
    f.table(["Plant", "Linked (lt)", "Lifted (lt)"],
            [["Bokaro Steel", "3.40", "3.20"],
             ["Rourkela Steel", "2.10", "2.00"],
             ["Durgapur Steel", "1.60", "1.50"],
             ["Others", "1.30", "1.20"]],
            col_w=[140, 100, 100])
    f.h2("13. Cost annex")
    f.para(
        "Washing cost averaged Rs 420 per tonne of feed with magnetite at Rs 38 and power at Rs "
        "96. Premium realisation of Rs 6,120 per tonne of Steel-II against Rs 2,840 raw realisation "
        "funds the 21.5 MTPA new-washery pipeline ungauged by budget support.")
    f.table(["Cost head (Rs/t feed)", "2021-22", "2022-23", "2023-24"],
            [["Power", "88", "92", "96"],
             ["Magnetite", "34", "36", "38"],
             ["O&M", "268", "282", "286"]],
            col_w=[150, 90, 90, 90])
    f.h2("14. Customer annex")
    f.para(
        "SAIL lifted 5.20 MT of washed coal at 96 percent materialisation while RINL took 2.10 "
        "MT. Cement plants absorbed the full 4.20 MT middlings offer, and FBC power stations "
        "burned 6.80 MT of rejects under 15-year tie-ups that fund pond capping.")
    f.table(["Customer", "Grade", "Qty (MT)"],
            [["SAIL", "Steel-II", "5.20"],
             ["RINL", "Steel-II", "2.10"],
             ["Cement cluster", "Middlings", "4.20"],
             ["FBC power", "Rejects", "6.80"]],
            col_w=[150, 110, 110])
    f.table(["Year", "SAIL lifting (%)", "Premium (%)"],
            [["2021-22", "92", "128"],
             ["2022-23", "94", "156"],
             ["2023-24", "96", "142"]],
            col_w=[150, 110, 110])
    f.bullets([
        "RINL linkage doubled to 2.10 MT from FY2024-25.",
        "Middlings e-auction premium record 148 percent in Q3.",
        "Reject pond capping completes 2026 across all sites.",
    ])
    return f


def make_ccl_safety_docx_sections():
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
    d.add_heading("Accident record", level=1)
    d.add_paragraph("CCL recorded 1 fatal accident with 1 fatality in 2024 up to November, "
                    "against 4 fatal accidents with 4 fatalities in 2023. Serious accidents fell "
                    "to 1 from none reported the previous year in the comparable window. The "
                    "fatality rate per million tonnes improved to 0.02.")
    t2 = d.add_table(rows=1, cols=3)
    t2.style = "Table Grid"
    h2 = t2.rows[0].cells
    h2[0].text, h2[1].text, h2[2].text = "Year", "Fatal accidents", "Fatalities"
    for y, a, f_ in [("2021", "1", "1"), ("2022", "2", "2"),
                     ("2023", "4", "4"), ("2024", "1", "1")]:
        r = t2.add_row().cells
        r[0].text, r[1].text, r[2].text = y, a, f_
    d.add_heading("Safety management plan", level=1)
    d.add_paragraph("All 38 operating mines run site-specific safety management plans reviewed "
                    "by the General Manager (Safety) each quarter. Strata management cells cover "
                    "the 4 underground mines, and slope stability radar watches the highwalls of "
                    "Ashoka, Piparwar, Magadh and Amrapali OCPs around the clock.")
    d.add_heading("Training and rescue", level=1)
    d.add_paragraph("The Bhurkunda rescue station conducted 214 mock drills and certified 386 "
                    "rescue-trained persons. Simulator training for 420 HEMM operators cut reversing "
                    "incidents by 31 percent. Women executives now head safety in 6 mines, and "
                    "creche coverage reaches all night-shift townships.")
    d.add_heading("Occupational health", level=1)
    d.add_paragraph("Periodical medical examination covered 36,940 employees, detecting 214 cases "
                    "of early pneumoconiosis referred to the Ranchi occupational health centre. Dust "
                    "suppression through 42 fog cannons and 18 km of fixed sprinklers kept PM10 within "
                    "norms on 93 percent of monitored days around the Piparwar complex.")
    d.add_heading("Rescue cover", level=1)
    d.add_paragraph("The Bhurkunda rescue station holds 4 teams with fresh-air bases at Piparwar and "
                    "Ashoka, running 214 mock drills in the year. Response time to the farthest face "
                    "averages 42 minutes against the 60-minute statutory ceiling.")
    d.add_heading("Contractor workforce", level=1)
    d.add_paragraph("Contractor crew of 14,200 handle overburden and transport under CCL safety "
                    "inductions with penalty-linked compliance scores. Contractor fatalities stood at "
                    "1 of the 3 total in 2024, down from 3 of 6 in 2023 on simulator mandates.")
    d.add_heading("Slope monitoring", level=1)
    d.add_paragraph("Radar watches the highwalls of Ashoka, Piparwar, Magadh and Amrapali around "
                    "the clock with 40-minute failure warnings demonstrated in two controlled slides "
                    "during the monsoon. Fortnightly drone surveys certify all 18 active dumps, and "
                    "toe-drain clearance before June prevented any dump failure for the third year.")
    t3 = d.add_table(rows=1, cols=3)
    t3.style = "Table Grid"
    h3 = t3.rows[0].cells
    h3[0].text, h3[1].text, h3[2].text = "Mine", "Dump height (m)", "Factor of safety"
    for m, h_, f_ in [("Ashoka", "90", "1.42"), ("Piparwar", "75", "1.38"),
                      ("Magadh", "80", "1.45"), ("Amrapali", "70", "1.40")]:
        r = t3.add_row().cells
        r[0].text, r[1].text, r[2].text = m, h_, f_
    d.add_heading("Electrical safety", level=1)
    d.add_paragraph("Earth-leakage protection covers 100 percent of the 452 face substations, and "
                    "640 km of trailing cable was replaced in the year. Flame-proof certification "
                    "backlog cleared to zero across the 4 underground mines with quarterly re-tests.")
    d.add_heading("Monsoon action plan", level=1)
    d.add_paragraph("Pre-monsoon audits closed 1,240 of 1,310 points before June, positioning 42,000 "
                    "gpm of pumping at flood-prone faces. The Damodar river watch room coordinates "
                    "with the state irrigation department on hourly dam releases affecting the "
                    "Bokaro and Kargali siding bridges.")
    d.add_heading("Safety budget", level=1)
    d.add_paragraph("Safety capex of Rs 96 crore covered radar, simulators, man-riding upgrades and "
                    "rescue station modernisation. Revenue safety spend of Rs 142 crore includes "
                    "strata instruments, dust suppression and medical surveillance across all mines.")
    t4 = d.add_table(rows=1, cols=3)
    t4.style = "Table Grid"
    h4 = t4.rows[0].cells
    h4[0].text, h4[1].text, h4[2].text = "Head", "2022-23 (Rs cr)", "2023-24 (Rs cr)"
    for h_, a, b in [("Capex", "78", "96"), ("Revenue", "128", "142"),
                     ("Training", "18", "24"), ("R&D trials", "6", "9")]:
        r = t4.add_row().cells
        r[0].text, r[1].text, r[2].text = h_, a, b
    d.add_heading("Strata management", level=1)
    d.add_paragraph("Site-specific strata management plans cover all 38 operating mines with support "
                    "rules framed per seam gradient, depth and extraction ratio. The 4 underground "
                    "mines run instrumented cells that read tell-tales and load cells weekly, and "
                    "depnillaring panels advance only after the assistant manager certifies the 1 bolt "
                    "per sqm density with photographic evidence uploaded to the area control room. In "
                    "2024 the cells flagged 42 panels for support revision across CCL, all complied "
                    "within 90 days, and no roof-fall fatality was recorded for the second year. Highwall "
                    "stability radar at Ashoka, Piparwar, Magadh and Amrapali gives 40-minute warnings "
                    "demonstrated in two controlled monsoon slides, while fortnightly drone surveys "
                    "certify all 18 active dumps with toe-drain clearance verified before June each year.")
    d.add_heading("HEMM safety", level=1)
    d.add_paragraph("Simulator training for 420 HEMM operators cut reversing incidents by 31 percent, "
                    "and proximity detection now covers 68 percent of the 340-machine opencast fleet. "
                    "Dump-edge berms of 3 m with reflective markers are contract conditions carrying "
                    "penalty clauses, and night operations run under lux-metered floodlight audits that "
                    "failed two contractors into suspension last quarter. The Magadh 20 cu.m shovel "
                    "logged 7,680 hours at 89 percent availability without a single lost-time incident, "
                    "a record the area safety committee attributes to the dedicated maintenance window "
                    "every 250 hours and operator fatigue monitoring through cabin cameras.")
    d.add_heading("Health surveillance", level=1)
    d.add_paragraph("Periodical medical examination covered 36,940 employees with chest radiography, "
                    "audiometry and spirometry; 214 early pneumoconiosis cases moved to non-dusty "
                    "postings with wage protection, and 820 noise-induced hearing cases rotate out of "
                    "crusher houses into enclosure programs. The Ranchi occupational health centre "
                    "follows all 214 cases half-yearly with high-resolution CT on indication, while "
                    "dust suppression through 42 fog cannons and 18 km of fixed sprinklers holds PM10 "
                    "within norms on 93 percent of monitored days around Piparwar. Canteen nutrition "
                    "programs cover 12,000 underground workers with haemoglobin tracking that cut "
                    "anaemia prevalence from 18 to 11 percent in two years.")
    d.add_heading("Fire and spontaneous heating", level=1)
    d.add_paragraph("Thermal mapping with drones covers the Jharia-fringe depillaring panels monthly, "
                    "with nitrogen flushing on standby at two panels showing 8-degree rises. The "
                    "Bhurkunda rescue station stocks 240 breathing apparatus sets with a 42-minute "
                    "average response to the farthest face, inside the 60-minute statutory ceiling. "
                    "Sealing records for 14 old galleries were digitised with gas chromatograph "
                    "baselines, and no heating incident progressed beyond the first alarm stage in "
                    "three years.")
    d.add_heading("Blasting controls", level=1)
    d.add_paragraph("Electronic delays hold village vibration below 5 mm/s with 500 m flyrock "
                    "exclusion zones enforced by sirens and guards on every round. Misfire drills run "
                    "quarterly at all four flagship OCPs, and bulk emulsion handling training covered "
                    "640 shotfirers with zero handling injuries in the year.")
    d.add_heading("Dust and noise control", level=1)
    d.add_paragraph("Fixed sprinklers over 18 km of haul roads plus 42 fog cannons hold PM10 within "
                    "norms on 93 percent of monitored days around Piparwar, with continuous stations "
                    "streaming to the area control room. Crusher houses carry acoustic enclosures "
                    "holding boundary noise to 72 dB against the 75 dB daytime norm, and audiometry "
                    "rotates 820 flagged workers out of high-noise postings into enclosure programs "
                    "with wage protection. Water sprinkling consumes 19 MLD of treated mine water, "
                    "closing the loop with zero discharge to the Bokaro river across 48 sampling rounds.")
    t5 = d.add_table(rows=1, cols=3)
    t5.style = "Table Grid"
    h5 = t5.rows[0].cells
    h5[0].text, h5[1].text, h5[2].text = "Station", "PM10 compliance (%)", "Noise (dB)"
    for s, p, n in [("Piparwar gate", "94", "71"), ("Ashoka siding", "93", "72"),
                    ("Bhurkunda colony", "95", "58"), ("Khalari village", "92", "54")]:
        r = t5.add_row().cells
        r[0].text, r[1].text, r[2].text = s, p, n
    d.add_heading("Emergency drills", level=1)
    d.add_paragraph("The Bhurkunda rescue station ran 214 mock drills spanning gallery search under "
                    "smoke, casualty handling and flood evacuation, certifying 386 rescue-trained "
                    "persons across CCL. Inter-area competitions tested 12 teams on breathing apparatus "
                    "endurance with the winning Piparwar team clocking 3 hours 40 minutes in full kit. "
                    "Monsoon flood rehearsals evacuated the three below-drainage galleries at Kargali "
                    "twice, verifying the 42,000 gpm pumping cascade against Damodar release scenarios "
                    "coordinated with the state irrigation department.")
    t6 = d.add_table(rows=1, cols=3)
    t6.style = "Table Grid"
    h6 = t6.rows[0].cells
    h6[0].text, h6[1].text, h6[2].text = "Drill type", "Count", "Persons covered"
    for t_, c, p in [("Gallery search", "48", "1240"), ("Flood evacuation", "36", "860"),
                     ("First aid", "72", "2140"), ("Fire", "58", "1480")]:
        r = t6.add_row().cells
        r[0].text, r[1].text, r[2].text = t_, c, p
    d.add_heading("Safety awards", level=1)
    d.add_paragraph("Piparwar OCP won the all-India mine safety award for the lowest injury frequency "
                    "among mega projects, while Ashoka took the state award for 2 million accident-free "
                    "manshifts. Individual awards honoured 42 safety champions including 6 women "
                    "supervisors, with citations counting toward promotion appraisals. The awards feed "
                    "a virtuous cycle: near-miss reporting rose 22 percent at awarded mines as workers "
                    "trust the non-punitive system.")
    d.add_heading("Illumination standards", level=1)
    d.add_paragraph("Lux-metered floodlight audits cover all faces and dump edges quarterly, with two "
                    "contractors suspended last quarter for failing night illumination norms. LED "
                    "retrofits cut lighting energy 42 percent while raising face illumination to 28 lux "
                    "against the 20 lux statutory minimum. Portable cap lamps with 12-hour backup "
                    "reached all 4,200 underground workers, replacing the older 8-hour units.")
    t7 = d.add_table(rows=1, cols=3)
    t7.style = "Table Grid"
    h7 = t7.rows[0].cells
    h7[0].text, h7[1].text, h7[2].text = "Location", "Illumination (lux)", "Norm (lux)"
    for l_, v, n in [("Coal face", "28", "20"), ("Dump edge", "24", "15"),
                     ("Haul road", "18", "10"), ("Workshop", "220", "200")]:
        r = t7.add_row().cells
        r[0].text, r[1].text, r[2].text = l_, v, n
    d.add_heading("Pit safety committee", level=1)
    d.add_paragraph("Monthly pit safety committees with workmen inspectors review every accident and "
                    "near-miss with action owners and deadlines published on mine notice boards. The "
                    "2024 rounds closed 1,840 of 1,920 actions within 30 days, and overdue actions "
                    "escalate to the General Manager review with stop-work authority on repeat "
                    "defaults.")
    return d


def rake_rows():
    rows = []
    dests = ["Korba TPS", "Sipat TPS", "Rihand TPS", "Vindhyachal TPS"]
    grades = ["G11", "G12", "G12", "G13"]
    qty = [3850, 3975, 4120, 3890, 4055, 4180, 3940, 4090, 4215, 3985, 4070, 4150]
    n = 0
    for y in [2021, 2022, 2023]:
        for m in range(1, 13):
            rows.append(f"{y}-{m:02d}-15,R-{2001 + n},{grades[n % 4]},"
                        f"{qty[n % 12] + (y - 2021) * 40},{dests[n % 4]}")
            n += 1
    return rows
