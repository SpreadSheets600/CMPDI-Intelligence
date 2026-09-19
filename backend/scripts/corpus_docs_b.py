"""Corpus part B: fifteen new documents, six pages each, grounded in the
researched Ministry/CIL figures in corpus_data. Every report carries
multi-year series tables so Temporal timelines and forecasts have depth."""

from backend.scripts.corpus_data import (
    ACC_COMPANY,
    ACC_YEARS,
    COKING_OUT,
    COKING_YEARS,
    FATAL_ACC,
    FATALITIES,
    FMC_ROLLOUT,
    FY,
    OMS_OC,
    OMS_OVERALL,
    OMS_UG,
    OMS_YEARS,
    RESOURCES_STATES,
    SUB_PROD,
    WASHERIES_NEW,
)
from backend.scripts.corpus_flow import FlowDoc


def _s(mapping):
    return [[m] + [str(v) for v in vals] for m, vals in mapping.items()]


def make_cil_consolidated():
    f = FlowDoc()
    f.h1("CIL Consolidated Performance FY2023-24")
    f.h2("1. Production at a glance")
    f.para(
        "Coal India Limited produced 773.65 MT during FY2023-24 against a target of "
        "780.00 MT, a growth of 10.04 percent over the 703.20 MT of FY2022-23. "
        "All-India production touched 997.83 MT, with CIL contributing 77.6 percent, "
        "SCCL 70.02 MT and captive and commercial mines 147.69 MT. The company crossed "
        "its 770 MT milestone for the first time in March 2024.")
    f.table(["Company", "2022-23", "2023-24", "Target 2023-24", "Achievement (%)"],
            [["ECL", "35.02", "47.56", "51.00", "93.3"],
             ["BCCL", "36.18", "41.10", "41.00", "100.2"],
             ["CCL", "76.09", "86.05", "84.00", "102.4"],
             ["NCL", "131.17", "136.15", "133.00", "102.4"],
             ["WCL", "64.28", "69.11", "67.00", "103.1"],
             ["SECL", "167.01", "187.38", "200.00", "93.7"],
             ["MCL", "193.26", "206.10", "204.00", "101.0"],
             ["CIL", "703.20", "773.65", "780.00", "99.2"]],
            col_w=[90, 80, 80, 110, 110])
    f.h2("2. Six-year subsidiary trajectory")
    f.para(
        "The table below tracks subsidiary production across six financial years. MCL "
        "overtook SECL as the largest producer in FY2022-23 and widened the lead to "
        "18.72 MT in FY2023-24. ECL staged the sharpest recovery, from 32.43 MT in "
        "FY2021-22 to 47.56 MT, after the Rajmahal expansion stabilized.")
    f.table(["Subsidiary (production, MT)"] + FY, _s(SUB_PROD), col_w=[90] + [62] * 6)
    f.para(
        "Production reconciliation across sources: Kusunda Mine FY2021-22 stands reconciled "
        "at 4.35 MT pending weighbridge recalibration, against 4.85 MT reported in the SECL "
        "annual report. Dipka OCP reconciles cleanly at 33.80 MT for the same year, and Gevra "
        "Area offtake at 36.90 MT matches the geological reconciliation exercise.")
    f.h2("3. Offtake and despatch")
    f.para(
        "All-India coal supply reached 972.65 MT, up 10.88 percent. CIL offtake grew in "
        "line with production at 753.50 MT, with rail loading at 303 rakes per day in March. "
        "Power-sector linkage accounted for 82 percent of despatch; e-auction volumes of "
        "68.40 MT fetched an average premium of 117 percent over notified prices.")
    f.table(["Mode", "2021-22", "2022-23", "2023-24"],
            [["Rail (MT)", "421.30", "468.20", "512.60"],
             ["Road (MT)", "148.20", "152.40", "158.30"],
             ["MGR (MT)", "62.40", "66.80", "71.20"],
             ["Belt/pipe (MT)", "29.80", "38.90", "46.40"]],
            col_w=[120, 90, 90, 90])
    f.h2("4. Coking versus non-coking")
    f.para(
        "Coking coal output of 60.43 MT formed 7.8 percent of CIL production, feeding the "
        "steel sector under Mission Coking Coal. Non-coking output of 713.21 MT served "
        "power, cement, sponge iron and fertilizer consumers across grades G1 to G17.")
    f.table(["Grade group", "2021-22", "2022-23", "2023-24"],
            [["Coking (MT)", "46.60", "54.63", "60.43"],
             ["Non-coking (MT)", "576.03", "648.58", "713.21"],
             ["Coking share (%)", "7.5", "7.8", "7.8"]],
            col_w=[130, 90, 90, 90])
    f.h2("5. Opencast and underground split")
    f.para(
        "Opencast mines delivered 742.63 MT in FY2025-26 terms against 25.56 MT from "
        "underground mines, a 96.7 percent OC share. Continuous miners now operate in 26 "
        "underground panels, and longwall faces at Moonidih and Jhanjra add 2.40 MTPA of "
        "high-productivity UG capacity.")
    f.table(["Type", "2022-23", "2023-24"],
            [["Opencast (MT)", "678.40", "748.10"],
             ["Underground (MT)", "24.80", "25.55"],
             ["OC share (%)", "96.5", "96.7"]],
            col_w=[130, 110, 110])
    f.h2("6. Road to one billion tonnes")
    f.para(
        "CIL targets 1 billion tonnes in a time-bound manner, backed by 3,780 MT of project "
        "pipeline capacity across 68 mega projects. Meeting the target depends on demand, "
        "environmental clearances for 14 projects totalling 210 MTPA, and rail evacuation "
        "through 92 first-mile connectivity projects of 994 MTPA capacity by FY2028-29.")
    f.bullets([
        "FY2024-25 target: 875 MT with Gevra at 60 MTPA run-rate.",
        "Three new coking washeries add 7.5 MTPA washing capacity by FY2026-27.",
        "Manpower rationalized to 2.39 lakh with 1.02 lakh contractor workers.",
    ])
    f.h2("7. Quarterly delivery")
    f.para(
        "Q4 delivered 226.40 MT, 29.3 percent of the year, as rakes peaked at 312 per day in "
        "March. Q1 monsoon quarter managed 166.20 MT while overburden stripping ran ahead, "
        "exposing 190 MT of coal for the dry months.")
    f.table(["Quarter", "Production (MT)", "Offtake (MT)"],
            [["Q1", "166.20", "162.40"], ["Q2", "182.60", "180.10"],
             ["Q3", "198.45", "196.20"], ["Q4", "226.40", "228.60"]],
            col_w=[110, 130, 130])
    f.h2("8. Subsidiary capex")
    f.para(
        "Capex of Rs 16,840 crore concentrated on HEMM (Rs 6,240 crore), FMC and sidings "
        "(Rs 5,860 crore) and washeries (Rs 1,240 crore). MCL and SECL together absorbed 52 "
        "percent of project spend on the Siarmal, Lingaraj and Gevra expansions.")
    f.table(["Head (Rs cr)", "2022-23", "2023-24"],
            [["HEMM", "5420", "6240"], ["FMC and siding", "4280", "5860"],
             ["Washery", "820", "1240"], ["Safety", "560", "840"]],
            col_w=[150, 110, 110])
    f.h2("9. Dividend and receivables")
    f.para(
        "CIL paid Rs 25.50 per share as dividend totalling Rs 15,740 crore to the exchequer. "
        "Trade receivables from state gencos closed at Rs 18,240 crore after late-payment "
        "surcharge rules released Rs 4,860 crore of overdues during Q4.")
    f.h2("10. Audit qualifications")
    f.para(
        "Statutory audit flagged grade-slippage provisioning of Rs 480 crore and disputed "
        "royalty claims of Rs 1,240 crore in Chhattisgarh and Odisha. Management certified "
        "internal financial controls as operating effectively across all subsidiaries.")
    f.h2("11. Manpower annex")
    f.para(
        "CIL employed 2.39 lakh departmental and 1.02 lakh contractor workers. Retirements of "
        "18,400 were offset by 4,280 management trainees and 22,600 outsourced HEMM crew. Overall "
        "OMS of 13.43 tonnes reflects the mechanised opencast fleet.")
    f.table(["Head", "2021-22", "2022-23", "2023-24"],
            [["Departmental (lakh)", "2.48", "2.43", "2.39"],
             ["Contractor (lakh)", "0.94", "0.98", "1.02"],
             ["Overall OMS", "9.56", "12.80", "13.43"]],
            col_w=[150, 100, 100, 100])
    f.table(["Subsidiary", "Manpower", "OMS"],
            [["ECL", "52080", "4.10"], ["BCCL", "38420", "3.80"],
             ["CCL", "38214", "9.50"], ["NCL", "14200", "14.20"],
             ["WCL", "38420", "7.30"], ["SECL", "82415", "8.20"],
             ["MCL", "21346", "22.50"]],
            col_w=[110, 110, 110])
    f.h2("12. Safety annex")
    f.para(
        "Twenty-two fatal accidents with 24 fatalities in 2024 up to November compare with 26 "
        "and 29 in 2023. The fatality rate per million tonnes held at 0.04 with the National "
        "Coal Mines Safety Report Portal tracking all 400 mines live.")
    f.table(["Year", "Fatal accidents", "Fatalities", "Rate / MT"],
            [["2021", "27", "29", "0.05"],
             ["2022", "18", "20", "0.03"],
             ["2023", "26", "29", "0.04"],
             ["2024", "22", "24", "0.04"]],
            col_w=[100, 110, 90, 90])
    f.h2("13. Grade realisation annex")
    f.para(
        "Linkage realisation averaged Rs 1,560 per tonne while e-auction spot touched Rs 3,420 "
        "and coking linkage Rs 6,120. Grade conformity penalties fell to Rs 480 crore company-wide "
        "on 100 percent third-party sampling of rail loading points.")
    f.table(["Channel", "Qty (MT)", "Realisation (Rs/t)"],
            [["Power linkage", "618.40", "1560"],
             ["NRS auction", "68.40", "2980"],
             ["Spot e-auction", "68.40", "3420"],
             ["Coking linkage", "18.40", "6120"]],
            col_w=[140, 100, 130])
    return f


def make_ecl_annual():
    f = FlowDoc()
    f.h1("ECL Annual Report FY2023-24")
    f.h2("1. Overview")
    f.para(
        "Eastern Coalfields Limited produced 47.56 MT during FY2023-24 against 35.02 MT in "
        "the previous year, a recovery of 35.8 percent after the Rajmahal expansion "
        "stabilized and Sonepur Bazari crossed 10 MT. ECL operates in the Raniganj and "
        "Rajmahal coalfields across West Bengal and Jharkhand with 78 operating mines, "
        "of which 60 are underground.")
    f.para(
        "Offtake of 43.75 MT moved largely to West Bengal and Bihar power stations under "
        "SHAKTI linkage. E-auction of 4.20 MT fetched premiums averaging 131 percent as "
        "imported coal prices stayed elevated through the first half.")
    f.h2("2. Area-wise production")
    f.para(
        "Rajmahal Area leads with the 17 MTPA Rajmahal expansion, while Sonepur Bazari "
        "benefits from the new 8 MTPA CHP. Kunustoria remains the underground flagship "
        "with continuous miners in three panels.")
    f.table(["Area", "2021-22", "2022-23", "2023-24"],
            [["Rajmahal Area", "10.20", "11.30", "15.40"],
             ["Sonepur Bazari Area", "7.30", "8.00", "10.20"],
             ["Kunustoria Area", "3.90", "4.20", "5.30"]],
            col_w=[150, 90, 90, 90])
    f.h2("3. Underground mining")
    f.para(
        "ECL runs the largest underground fleet in CIL with 60 UG mines producing 10.10 MT. "
        "Continuous miner panels at Jhanjra and Sarpi delivered 3.40 MT combined. Longwall "
        "powered supports at Jhanjra face II achieved 4,200 tonnes per day in March, a company "
        "record for mass-production technology.")
    f.table(["Technology", "Panels", "Output (MT)", "OMS"],
            [["Continuous miner", "14", "5.60", "2.40"],
             ["Longwall", "2", "1.20", "4.10"],
             ["Manual/SDL", "44", "3.30", "0.90"]],
            col_w=[130, 80, 100, 80])
    f.h2("4. Quality")
    f.para(
        "ECL coal averages GCV 5,200 kcal/kg across grades G11 to G14. Third-party sampling "
        "at 24 sidings upheld declared grades in 94 of 100 referee cases. Beneficiation at the "
        "Dahibari washery treated 1.40 MT at 32 percent ash rejection.")
    f.h2("5. Safety")
    f.para(
        "Four fatal accidents with five fatalities were recorded in 2024 up to November, "
        "against four and four in 2023. Strata control cells instrument 112 depillaring panels "
        "with tell-tales and load cells, and the Sitarampur rescue station ran 96 mock drills.")
    f.table(["Year", "Fatal accidents", "Fatalities"],
            [["2021", "7", "8"], ["2022", "2", "2"],
             ["2023", "4", "4"], ["2024", "4", "5"]],
            col_w=[100, 130, 110])
    f.h2("6. Outlook")
    f.para(
        "FY2024-25 targets 49 MT with Rajmahal at 16.5 MTPA run-rate. The Hura-C captive block "
        "allotted to West Bengal Power adds regional supply, while ECL's two FMC silos of 8 MTPA "
        "cut road movement around Rajmahal by 70 percent.")
    f.bullets([
        "Target FY2024-25: 49 MT production, 46 MT offtake.",
        "Jhanjra longwall III approval for 2.0 MTPA in Q2.",
        "Underground output share targeted at 24 percent by FY2027-28.",
    ])
    f.h2("7. Rajmahal expansion detail")
    f.para(
        "The 17 MTPA Rajmahal expansion adds two 20 cu.m shovels, a 4 km conveyor to the "
        "Lalmatia siding and a 5 MTPA CHP. Land awards over 890 hectares closed in January, and "
        "the first additional shovel logged 1,840 hours in Q4 at 88 percent availability.")
    f.table(["Rajmahal block", "2021-22", "2022-23", "2023-24"],
            [["Rajmahal OCP", "8.20", "9.10", "12.60"],
             ["Urimari OCP", "2.00", "2.20", "2.80"]],
            col_w=[150, 100, 100, 100])
    f.h2("8. Manpower")
    f.para(
        "ECL employed 52,080 persons with OMS at 4.10 tonnes, dragged by the UG share. Retirements "
        "of 4,280 in the year were offset by 1,140 management trainees and 2,860 outsourced "
        "HEMM crew. Underground allowance revisions cut absenteeism to 11.2 percent.")
    f.h2("9. Environment")
    f.para(
        "Backfilling covered 214 hectares with 3.10 lakh saplings at 79 percent survival. Mine "
        "water supplies 28 villages around Sonepur Bazari, and the Raniganj coalfield rejuvenation "
        "plan treats 14 fire-affected hectares with blanketing and trenching.")
    f.h2("10. Financials")
    f.para(
        "Revenue grew 13.2 percent to Rs 22,480 crore with PAT of Rs 3,120 crore. E-auction "
        "premiums contributed Rs 2,840 crore of the Rs 4,260 crore profit growth, and receivables "
        "fell Rs 920 crore on West Bengal genco settlements.")
    f.h2("11. OBR annex")
    f.para(
        "Overburden of 142.60 million cu.m held stripping at 3.00 cu.m per tonne across Rajmahal "
        "and Sonepur Bazari. Shovel availability of 82.4 percent trails the CIL average, and two "
        "replacement rope shovels arrive in Q1.")
    f.table(["Area", "OBR (Mcum)", "Stripping ratio"],
            [["Rajmahal", "68.40", "3.10"],
             ["Sonepur Bazari", "42.20", "2.86"],
             ["Kunustoria", "18.60", "2.42"],
             ["Others", "13.40", "2.10"]],
            col_w=[140, 110, 110])
    f.table(["Year", "OBR (Mcum)", "Availability (%)"],
            [["2021-22", "112.40", "80.20"],
             ["2022-23", "124.80", "81.40"],
             ["2023-24", "142.60", "82.40"]],
            col_w=[140, 110, 110])
    f.h2("12. Linkage annex")
    f.para(
        "West Bengal gencos lift 24.60 MTPA at 93.9 percent materialisation while Bihar takes "
        "8.40 MTPA. E-auction of 4.20 MT at 131 percent premium serves the eastern NRS cluster.")
    f.table(["Consumer", "Linkage (MTPA)", "Lifting (MT)"],
            [["WBPDCL", "24.60", "23.10"],
             ["Bihar gencos", "8.40", "8.10"],
             ["NTPC", "6.20", "6.00"],
             ["NRS/e-auction", "4.20", "3.90"]],
            col_w=[140, 110, 100])
    f.h2("13. Safety annex")
    f.para(
        "Seven strata-control cells instrument 112 depillaring panels, and proximity detection "
        "covers 84 percent of the UG HEMM fleet. Monsoon flooding drills in July rehearsed "
        "evacuation of the three below-drainage galleries at Kunustoria.")
    f.table(["Indicator", "2022", "2023", "2024"],
            [["Fatal accidents", "2", "4", "4"],
             ["Serious accidents", "9", "3", "3"],
             ["Mock drills", "72", "84", "96"]],
            col_w=[140, 90, 90, 90])
    f.h2("14. R&R annex")
    f.para(
        "Rajmahal expansion resettles 1,140 families with Rs 28.40 lakh per acre compensation "
        "and 640 employments offered. The Lalmatia township school enrols 820 children and the "
        "dispensary logs 90 outpatients daily.")
    f.table(["Village", "Families", "Employment offered"],
            [["Lalmatia", "420", "288"],
             ["Rajmahal", "380", "214"],
             ["Urimari", "340", "138"]],
            col_w=[150, 100, 130])
    f.table(["Year", "Compensation (Rs cr)", "Disbursed (%)"],
            [["2021-22", "280", "72"],
             ["2022-23", "420", "80"],
             ["2023-24", "560", "86"]],
            col_w=[150, 130, 110])
    f.bullets([
        "Full Lalmatia township handover by December.",
        "ITI seats reserved for 240 oustee youth yearly.",
        "Grievance cell resolves 94 percent in 30 days.",
    ])
    return f


def make_wcl_annual():
    f = FlowDoc()
    f.h1("WCL Annual Report FY2023-24")
    f.h2("1. Overview")
    f.para(
        "Western Coalfields Limited produced 69.11 MT during FY2023-24 against 64.28 MT in "
        "FY2022-23, serving Maharashtra and Madhya Pradesh power stations. WCL operates 57 "
        "mines across the Chandrapur, Umrer, Kamptee and Wardha areas with a balanced mix of "
        "opencast and underground output.")
    f.para(
        "Offtake of 68.50 MT included 12.40 MT through e-auction to the non-regulated sector. "
        "The Umrer 4 MTPA silo commissioned in March evacuated 1.85 lakh tonnes of G12 coal "
        "in its first month to Korba and Sipat thermal plants.")
    f.h2("2. Area-wise production")
    f.table(["Area", "2021-22", "2022-23", "2023-24"],
            [["Umrer Area", "12.80", "14.10", "15.20"],
             ["Kamptee Area", "8.20", "9.00", "9.60"],
             ["Chandrapur Area", "10.40", "11.30", "12.10"],
             ["Wardha Area", "7.60", "8.20", "8.70"]],
            col_w=[150, 90, 90, 90])
    f.para(
        "Umrer leads on the back of the Dinesh expansion, while Chandrapur benefits from the "
        "Padmapur deepening. Wardha's underground mines held output flat despite a three-month "
        "dewatering shutdown at Ballarpur in Q2.")
    f.h2("3. Power linkage")
    f.para(
        "SHAKTI linkage of 52.40 MTPA covers Mahagenco, MPPGCL and NTPC stations. Letter-of-assurance "
        "coal of 6.80 MT moved to the non-regulated sector through single-window agnostic auctions "
        "at an average premium of 108 percent.")
    f.table(["Consumer", "Linkage (MTPA)", "Lifting (MT)", "Materialisation (%)"],
            [["Mahagenco", "24.60", "23.10", "93.9"],
             ["MPPGCL", "14.20", "13.80", "97.2"],
             ["NTPC", "8.40", "8.10", "96.4"],
             ["NRS auction", "6.80", "6.20", "91.2"]],
            col_w=[120, 110, 100, 120])
    f.h2("4. Quality and beneficiation")
    f.para(
        "WCL despatched grades G10 to G13 with average GCV 4,850 kcal/kg. The Ghugus washery "
        "treated 2.10 MT of Power-grade coal, cutting ash from 38.2 to 33.9 percent for the "
        "Chandrapur super thermal station.")
    f.h2("5. Safety")
    f.para(
        "One fatal accident with one fatality was recorded in 2024 up to November, matching "
        "2023. Slope radar at the Umrer highwall gives 40-minute failure warnings, and drone "
        "surveys map all 12 active dumps fortnightly for stability certification.")
    f.h2("6. Outlook")
    f.para(
        "FY2024-25 targets 68.50 MT with the Kamptee 6 MTPA expansion breaking ground in Q1. "
        "Two more FMC projects of 11 MTPA take mechanised evacuation to 78 percent of despatch, "
        "eliminating 1,900 truck trips daily around Chandrapur.")
    f.bullets([
        "Target FY2024-25: 68.50 MT production.",
        "Kamptee expansion EC secured for 6 MTPA.",
        "Mine-water supply to 28 villages covering 36,000 people.",
    ])
    f.h2("7. Umrer complex detail")
    f.para(
        "Umrer's Dinesh expansion to 8 MTPA adds a surface miner and 240 TPH feeder breaker. "
        "The 4 MTPA silo loads Maharashtra genco rakes in 3.0 hours, and the complex overburden "
        "of 38.40 million cu.m held stripping at 2.52 cu.m per tonne.")
    f.table(["Umrer unit", "2021-22", "2022-23", "2023-24"],
            [["Dinesh OCP", "7.40", "8.10", "8.90"],
             ["Umrer OCP", "5.40", "6.00", "6.30"]],
            col_w=[150, 100, 100, 100])
    f.h2("8. Manpower")
    f.para(
        "WCL employed 38,420 persons with OMS at 7.30 tonnes. The Nagpur training institute "
        "certified 4,280 HEMM operators including 640 women dumper drivers now posted across "
        "Umrer and Chandrapur.")
    f.h2("9. Environment")
    f.para(
        "Concurrent backfilling reclaimed 186 hectares with 2.80 lakh saplings. Zero discharge "
        "holds at all washeries, and the Tadoba buffer-zone mines run wildlife-compliant "
        "blasting windows with forest department observers.")
    f.h2("10. Financials")
    f.para(
        "Revenue of Rs 17,260 crore and PAT of Rs 2,460 crore reflect steady linkage "
        "realisation and 108 percent NRS premiums. Capex of Rs 1,240 crore went largely to the "
        "Umrer silo and Kamptee CHP.")
    f.h2("11. OBR annex")
    f.para(
        "Overburden of 198.40 million cu.m held stripping at 2.87 cu.m per tonne. Surface miners "
        "at Umrer and Kamptee handle 34 percent of coal without blasting, and shovel "
        "availability averaged 84.8 percent.")
    f.table(["Area", "OBR (Mcum)", "Stripping ratio"],
            [["Umrer", "52.40", "2.52"],
             ["Kamptee", "48.60", "2.94"],
             ["Chandrapur", "56.20", "2.98"],
             ["Wardha", "41.20", "2.86"]],
            col_w=[140, 110, 110])
    f.table(["Year", "OBR (Mcum)", "Availability (%)"],
            [["2021-22", "168.40", "83.20"],
             ["2022-23", "182.60", "84.10"],
             ["2023-24", "198.40", "84.80"]],
            col_w=[140, 110, 110])
    f.h2("12. Rake annex")
    f.para(
        "Rake loading averaged 18.2 per day with March at 21 rakes after the Umrer silo "
        "stabilised. Demurrage of Rs 4.10 crore was the lowest in the company's history as "
        "siding detention fell to 4.4 hours.")
    f.table(["Siding", "Rakes/day", "Qty (MT)"],
            [["Umrer silo", "8.00", "6.20"],
             ["Kamptee CHP", "6.00", "4.40"],
             ["Chandrapur", "2.40", "1.80"],
             ["Wardha", "1.80", "1.20"]],
            col_w=[140, 100, 100])
    f.h2("13. Safety annex")
    f.para(
        "One fatal accident with one fatality in 2024 up to November matches 2023. Slope radar "
        "at Umrer gives 40-minute warnings, fortnightly drone dump surveys certify stability, "
        "and 96 mock drills rehearsed monsoon evacuation at Ballarpur.")
    f.table(["Indicator", "2022", "2023", "2024"],
            [["Fatal accidents", "1", "2", "1"],
             ["Serious accidents", "10", "3", "5"],
             ["Mock drills", "72", "84", "96"]],
            col_w=[140, 90, 90, 90])
    f.h2("14. Township annex")
    f.para(
        "WCL townships house 42,000 families with piped water, two referral hospitals and nine "
        "schools enrolling 12,400 children. The Chandrapur sports complex trains 640 athletes "
        "including 28 national-level coal India sports quota holders.")
    f.table(["Township", "Families", "Schools"],
            [["Chandrapur", "12400", "3"],
             ["Umrer", "8600", "2"],
             ["Kamptee", "7200", "2"],
             ["Wardha", "6400", "2"]],
            col_w=[150, 110, 100])
    f.table(["Facility", "Capacity", "Users"],
            [["Referral hospitals", "2", "18400"],
             ["Dispensaries", "24", "86000"],
             ["Training seats", "4280", "4280"]],
            col_w=[150, 110, 100])
    f.bullets([
        "Night-shift creches cover all nursing mothers.",
        "Sports quota recruited 28 athletes in 2024.",
        "Telemedicine links all dispensaries to Nagpur.",
    ])
    f.h2("15. Power-house annex")
    f.para(
        "WCL's own 2x10 MW captive plant at Chandrapur runs on washery rejects with 68 percent "
        "PLF, feeding mine load and the township grid. Solar plants of 6.4 MW across Umrer and "
        "Kamptee cut daytime drawal by 41 percent.")
    f.table(["Plant", "Capacity (MW)", "PLF (%)"],
            [["Captive thermal", "20", "68"],
             ["Umrer solar", "3.40", "19"],
             ["Kamptee solar", "3.00", "18"]],
            col_w=[150, 110, 100])
    f.table(["Year", "Power cost (Rs cr)", "Solar share (%)"],
            [["2021-22", "184", "6"],
             ["2022-23", "196", "9"],
             ["2023-24", "208", "12"]],
            col_w=[150, 120, 110])
    return f


def make_ccl_annual():
    f = FlowDoc()
    f.h1("CCL Annual Report FY2023-24")
    f.h2("1. Overview")
    f.para(
        "Central Coalfields Limited produced 86.05 MT during FY2023-24 against 76.09 MT in "
        "FY2022-23, a growth of 13.1 percent led by the Magadh-Amrapali complex. CCL operates "
        "in the North Karanpura, South Karanpura and Jharia fringes across 38 mines in "
        "Jharkhand.")
    f.h2("2. Flagship projects")
    f.table(["Mine", "2021-22", "2022-23", "2023-24"],
            [["Ashoka OCP", "11.40", "12.60", "13.90"],
             ["Piparwar OCP", "7.90", "8.60", "9.30"],
             ["Magadh OCP", "8.10", "9.40", "10.80"],
             ["Amrapali OCP", "7.20", "8.90", "10.20"]],
            col_w=[150, 90, 90, 90])
    f.para(
        "Magadh crossed 10 MT for the first time after the second 20 cu.m shovel arrived in "
        "October. Amrapali doubled in two years on the new 12 km CHP-conveyor to the Shivpur "
        "siding, which loads 8 rakes daily without a single truck on public roads.")
    f.h2("3. First mile connectivity")
    f.para(
        "The Tori-Shivpur rail line now evacuates 24 MTPA from the North Karanpura fields. "
        "Piparwar's 10 MTPA CHP-silo complex cut loading time to 3.1 hours per rake, and the "
        "Ashoka 5 MTPA wharf-wall siding handles the monsoon surge that road could never clear.")
    f.table(["FMC asset", "Capacity (MTPA)", "Evacuated (MT)", "Status"],
            [["Tori-Shivpur rail", "24.0", "21.60", "Operational"],
             ["Piparwar CHP-silo", "10.0", "8.90", "Operational"],
             ["Ashoka wharf-wall", "5.0", "4.40", "Operational"],
             ["Khadia-style Konar silo", "8.0", "0.00", "Construction"]],
            col_w=[160, 100, 100, 100])
    f.h2("4. Washeries")
    f.para(
        "Kathara washery treated 1.90 MT at 34 percent yield for the steel sector, while the "
        "new Kathara 3.0 MTPA coking washery signed its construction contract during the year. "
        "Rajrappa treated 1.60 MT of medium-coking feed for SAIL linkages.")
    f.h2("5. Manpower and OMS")
    f.para(
        "CCL employed 38,214 persons with OMS at 3.42 tonnes for FY2023-24, rising from 3.18 "
        "in FY2021-22. Contractor workers of 14,200 supplement departmental strength in "
        "overburden removal, where HEMM availability averaged 84.6 percent.")
    f.table(["Year", "Manpower", "OMS (tonnes)"],
            [["2021-22", "40210", "3.18"],
             ["2022-23", "39180", "3.31"],
             ["2023-24", "38214", "3.42"]],
            col_w=[110, 110, 110])
    f.h2("6. Outlook")
    f.para(
        "FY2024-25 targets 87.50 MT with Magadh at 12 MTPA run-rate. The Konar 8 MTPA silo "
        "commissioning in Q3 takes FMC coverage to 68 percent of despatch, and the new Kathara "
        "washery breaks ground in Q4.")
    f.bullets([
        "Target FY2024-25: 87.50 MT production.",
        "Konar silo commissioning in Q3 FY2024-25.",
        "Jharia fire-area rehabilitation covers 12 sites with CCL support.",
    ])
    f.h2("7. Magadh-Amrapali complex")
    f.para(
        "The twin complex produced 21.00 MT combined, nearly a quarter of CCL. A shared 12 km "
        "conveyor to Shivpur eliminates 1,100 truck trips daily, and the second 20 cu.m shovel "
        "at Magadh cut bench cycle time to 42 seconds.")
    f.table(["Complex unit", "2021-22", "2022-23", "2023-24"],
            [["Magadh OCP", "8.10", "9.40", "10.80"],
             ["Amrapali OCP", "7.20", "8.90", "10.20"]],
            col_w=[150, 100, 100, 100])
    f.h2("8. Safety record")
    f.para(
        "One fatal accident with one fatality in 2024 up to November compares with four and "
        "four in 2023. Slope radar on Ashoka and Piparwar highwalls gives 40-minute warnings, "
        "and the Bhurkunda rescue station ran 214 mock drills.")
    f.h2("9. Environment")
    f.para(
        "Piparwar's closed-loop wash water recycles 92 percent of process water. Afforestation "
        "covered 96 hectares with 1.40 lakh saplings, and the Bokaro river monitoring shows no "
        "effluent breach across 48 sampling rounds.")
    f.h2("10. Financials")
    f.para(
        "Revenue of Rs 25,840 crore and PAT of Rs 4,280 crore rode the Magadh volume surge and "
        "Kathara washery margins. Capex of Rs 2,120 crore centred on the Konar silo and Tori-"
        "Shivpur doubling.")
    f.h2("11. OBR annex")
    f.para(
        "Overburden of 176.40 million cu.m held stripping at 2.05 cu.m per tonne across North "
        "Karanpura. The Magadh 20 cu.m shovel logged 7,680 hours at 89 percent availability, "
        "cutting prime cost by Rs 38 per cu.m.")
    f.table(["Mine", "OBR (Mcum)", "Stripping ratio"],
            [["Magadh OCP", "48.20", "2.12"],
             ["Amrapali OCP", "44.60", "2.08"],
             ["Ashoka OCP", "38.40", "1.98"],
             ["Piparwar OCP", "24.20", "1.86"],
             ["Others", "21.00", "1.72"]],
            col_w=[140, 110, 110])
    f.table(["Year", "OBR (Mcum)", "Availability (%)"],
            [["2021-22", "142.60", "83.40"],
             ["2022-23", "158.20", "84.10"],
             ["2023-24", "176.40", "84.60"]],
            col_w=[140, 110, 110])
    f.h2("12. Rake annex")
    f.para(
        "Rake loading averaged 16.4 per day with the Tori-Shivpur line absorbing the Magadh "
        "surge. Demurrage of Rs 5.80 crore halved as detention fell to 3.8 hours at Piparwar.")
    f.table(["Siding", "Rakes/day", "Qty (MT)"],
            [["Shivpur", "8.00", "12.40"],
             ["Piparwar silo", "5.20", "8.90"],
             ["Ashoka", "2.10", "4.40"],
             ["Others", "1.10", "2.10"]],
            col_w=[140, 100, 100])
    f.h2("13. Grade annex")
    f.para(
        "Despatch grades G12 to G14 serve power linkage while washed Steel grades go to SAIL. "
        "Kathara washery yield of 34 percent on medium-coking feed underpins the steel linkage "
        "of 1.60 MT to Bokaro.")
    f.table(["Grade", "Despatch (MT)", "Realisation (Rs/t)"],
            [["G12", "32.40", "1980"], ["G13", "28.60", "1820"],
             ["G14", "18.20", "1640"], ["Steel grades", "3.20", "6120"]],
            col_w=[140, 110, 120])
    f.h2("14. Township annex")
    f.para(
        "CCL townships at Ranchi, Bhurkunda and Piparwar house 38,000 families with two "
        "hospitals and eleven schools. The Ranchi sports academy produced 14 national campers "
        "in athletics and archery this year.")
    f.table(["Township", "Families", "Hospital beds"],
            [["Ranchi", "14200", "320"],
             ["Bhurkunda", "9800", "180"],
             ["Piparwar", "7200", "120"],
             ["Others", "6800", "140"]],
            col_w=[150, 110, 110])
    f.table(["School", "Students", "Board pass (%)"],
            [["DAV Ranchi", "4200", "98.20"],
             ["DAV Piparwar", "2400", "97.40"],
             ["DAV Bhurkunda", "2100", "96.80"]],
            col_w=[150, 110, 110])
    f.bullets([
        "Central hospital adds 120 beds by March.",
        "Creche coverage in all night-shift townships.",
        "Scholarships for 1,240 oustee children.",
    ])
    return f


def make_cmpdi_exploration():
    f = FlowDoc()
    f.h1("CMPDI Exploration Review FY2023-24")
    f.h2("1. Drilling scorecard")
    f.para(
        "CMPDI drilled 4.317 lakh metres departmentally and 4.308 lakh metres through "
        "outsourcing during FY2023-24, deploying 100 to 120 drills of which 67 were "
        "departmental. Promotional drilling of 1.743 lakh metres grew 127 percent over the "
        "previous year across 29 coal and lignite blocks.")
    f.table(["Block class", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24"],
            [["Non-CIL blocks", "7.88", "7.70", "4.28", "2.58", "4.29"],
             ["CIL blocks", "5.80", "5.45", "3.98", "3.58", "3.80"]],
            col_w=[130, 70, 70, 70, 70, 70])
    f.h2("2. Promotional exploration")
    f.para(
        "Regional exploration by CMPDI, MECL and state governments covered 261 sq km and is "
        "expected to add about 11 billion tonnes of indicated and inferred resources. Two "
        "bauxite regional reports added 16.093 MT of aluminium laterite and 9.285 MT of bauxite "
        "to the national inventory.")
    f.h2("3. Geological reports")
    f.para(
        "Thirty-one geological reports were prepared during FY2023-24. Nineteen detailed reports "
        "over 340 sq km are expected to add about 12 billion tonnes to the measured category, "
        "while twelve regional reports cover the 11 billion tonne accretion. From January 2023 "
        "to March 2024, CMPDI submitted 33 detailed reports over 510 sq km proving 18.5 BT.")
    f.table(["Report class", "Reports", "Area (sq km)", "Resource (BT)"],
            [["Detailed", "19", "340", "12.0"],
             ["Regional", "12", "261", "11.0"],
             ["Bauxite regional", "2", "38", "0.025"]],
            col_w=[130, 80, 100, 100])
    f.h2("4. National inventory")
    f.para(
        "Geological resources of coal stand at 378.21 billion tonnes as on 1 April 2023 up to "
        "1,200 m depth: 199.90 BT measured, 151.68 BT indicated and 26.63 BT inferred. Coking "
        "resources total 35.64 BT. Lignite reserves are estimated at 47.37 BT, concentrated in "
        "Tamil Nadu, Gujarat and Rajasthan.")
    f.table(["Category", "Resources (BT)"],
            [["Measured", "199.90"], ["Indicated", "151.68"], ["Inferred", "26.63"]],
            col_w=[150, 130])
    f.table(["State", "Resources (BT)"],
            [[s, v] for s, v in RESOURCES_STATES],
            col_w=[150, 130])
    f.h2("5. Constraints and outlook")
    f.para(
        "Drilling lost six weeks to a camp stoppage in Odisha till November 2023 and adverse "
        "law-and-order conditions in Jharkhand and Chhattisgarh. NMET-funded drilling added "
        "0.34 lakh metres. For FY2024-25 CMPDI targets 4.60 lakh metres departmentally with 74 "
        "drills and 36 geological reports.")
    f.bullets([
        "Target FY2024-25: 4.60 lakh metres departmental drilling.",
        "36 geological reports with 13 BT measured accretion targeted.",
        "Hydrogeology modelling MoUs with two CGWA-accredited consultants.",
    ])
    f.h2("6. State-wise drilling deployment")
    f.para(
        "Odisha hosted 28 drills across the Talcher and Ib valley blocks, Chhattisgarh 22 in "
        "Hasdeo-Arand and Korba, and Jharkhand 19 in North Karanpura and Rajmahal. Madhya "
        "Pradesh and Maharashtra shared 17 rigs on Singrauli and Wardha blocks.")
    f.table(["State", "Rigs", "Metres (lakh)"],
            [["Odisha", "28", "1.42"], ["Chhattisgarh", "22", "1.18"],
             ["Jharkhand", "19", "0.96"], ["Madhya Pradesh", "11", "0.48"],
             ["Maharashtra", "6", "0.28"]],
            col_w=[140, 90, 110])
    f.h2("7. Laboratory throughput")
    f.para(
        "Central laboratory at Ranchi analysed 18,240 coal samples for proximate, ultimate and "
        "washability parameters with a 21-day turnaround. Four regional labs cleared their "
        "NABL surveillance audits, and the new XRF line doubled trace-element capacity.")
    f.h2("8. Consultancy assignments")
    f.para(
        "Outside consultancy included three UCIL uranium reports, SCCL block modelling for two "
        "Godavari blocks, and captive-block geological reports for eight auction allottees. "
        "Fee income of Rs 214 crore covered 68 percent of establishment costs.")
    f.h2("9. Manpower and rigs")
    f.para(
        "Exploration division fields 1,240 geologists and 2,860 drill crew across 74 departmental "
        "rigs with average rig age of 14 years. Six new CBM-capable rigs arrive in Q3, and "
        "wireline logging units grew to 22 with the MECL MoU fleet.")
    f.h2("10. Block-wise drilling annex")
    f.para(
        "Siarmal block led with 0.42 lakh metres proving 1.20 BT, followed by Hasdeo-Arand at "
        "0.38 lakh metres. Korba West infill added 0.86 BT to measured resources, and Rajmahal "
        "deep drilling intersected 4.2 m of coking blend coal.")
    f.table(["Block", "Metres (lakh)", "Resource added (BT)"],
            [["Siarmal", "0.42", "1.20"],
             ["Hasdeo-Arand", "0.38", "0.94"],
             ["Korba West", "0.34", "0.86"],
             ["Rajmahal deep", "0.28", "0.62"],
             ["North Karanpura", "0.26", "0.54"]],
            col_w=[150, 100, 120])
    f.table(["Year", "GRs submitted", "Measured added (BT)"],
            [["2021-22", "24", "6.20"],
             ["2022-23", "27", "8.40"],
             ["2023-24", "31", "12.00"]],
            col_w=[150, 110, 120])
    f.h2("11. Cost annex")
    f.para(
        "Departmental drilling costs Rs 4,820 per metre against Rs 3,940 outsourced, with the "
        "gap funding difficult-terrain and CBM-capable capacity. Total exploration spend of Rs "
        "1,240 crore includes Rs 480 crore of NMET pass-through works.")
    f.table(["Mode", "Cost (Rs/m)", "Share (%)"],
            [["Departmental", "4820", "52"],
             ["Outsourced tender", "3940", "28"],
             ["MECL MoU", "4120", "20"]],
            col_w=[150, 100, 100])
    f.h2("12. Bauxite and NMET annex")
    f.para(
        "Bauxite regional reports added 16.093 MT of aluminium laterite and 9.285 MT of bauxite "
        "in Odisha. NMET drilling of 0.34 lakh metres covered coal, lignite and critical mineral "
        "blocks across five states with 0.45 lakh metres from January 2023 to March 2024.")
    f.table(["Mineral", "Reports", "Resource (MT)"],
            [["Aluminium laterite", "1", "16.093"],
             ["Bauxite", "1", "9.285"]],
            col_w=[150, 100, 110])
    f.h2("13. Geophysical annex")
    f.para(
        "Seismic surveys covered 42 line-km in Hasdeo-Arand resolving seam splits below 60 m "
        "cover. Magnetic surveys over 120 sq km in the Auranga block traced dolerite dykes, and "
        "downhole geophysics logged 240 boreholes for density-calibrated reserve modelling.")
    f.table(["Survey", "Coverage", "Outcome"],
            [["Seismic", "42 line-km", "Split seams mapped"],
             ["Magnetic", "120 sq km", "Dykes traced"],
             ["Downhole logging", "240 holes", "Density calibrated"]],
            col_w=[150, 110, 150])
    f.table(["Year", "Seismic (line-km)", "Logged holes"],
            [["2021-22", "28", "180"],
             ["2022-23", "36", "210"],
             ["2023-24", "42", "240"]],
            col_w=[150, 120, 110])
    f.bullets([
        "3D seismic pilot over 8 sq km at Siarmal approved.",
        "Drone magnetics trial cuts survey cost 30 percent.",
        "Core library digitises 42,000 m of historic core.",
    ])
    return f


def make_fmc_status():
    f = FlowDoc()
    f.h1("First Mile Connectivity Status Note")
    f.h2("1. Programme scale")
    f.para(
        "The Ministry plans 102 first-mile connectivity projects of 1,092 MT capacity by "
        "FY2029-30. Presently 44 projects of 429.5 MTPA are operational. CIL moved 102.5 MT "
        "through FMC in FY2024-25 and targets 125 MT in FY2025-26, with 19 projects of nearly "
        "150 MTPA commissioning during the year.")
    f.table(["Window", "Projects", "Capacity (MTY)"],
            [["Operational", "44", "429.5"]] +
            [[w, p, c] for w, p, c in FMC_ROLLOUT],
            col_w=[130, 100, 120])
    f.h2("2. Mechanised evacuation")
    f.para(
        "FMC replaces truck movement with piped conveyors, crushers, silos and rapid loading "
        "systems. Enclosed handling cuts particulate emissions, ends grade mixing on the road, "
        "and loads precise wagon quantities that avoid overloading penalties. Wagon turnaround "
        "at FMC sidings averages 4.2 hours against 9.6 hours at manual sidings.")
    f.table(["Project", "Capacity (MTPA)", "Mode", "Status"],
            [["Gevra silo complex", "10.0", "Rail", "Operational"],
             ["Dipka rapid loading", "8.0", "Rail", "Operational"],
             ["Lakhanpur silo", "10.0", "Rail", "Commissioning"],
             ["Tori-Shivpur line", "24.0", "Rail", "Operational"]],
            col_w=[160, 100, 80, 110])
    f.h2("3. FY2030 destination")
    f.para(
        "By FY2029-30 about 90 percent of output from CIL, NLCIL and SCCL should move by FMC: "
        "994 MTPA of 1,042.8 MTPA for CIL (95.3 percent), 63.5 of 75.5 for NLCIL and 34.5 of "
        "90 for SCCL. Total capex envisaged is Rs 31,367.66 crore across handling plants, "
        "conveyors, silos, sidings and rail links.")
    f.table(["Company", "FMC dispatch (MTPA)", "Production (MTPA)", "Share (%)"],
            [["CIL", "994", "1042.8", "95.3"],
             ["NLCIL", "63.5", "75.5", "84.1"],
             ["SCCL", "34.5", "90.0", "38.3"]],
            col_w=[100, 130, 120, 90])
    f.h2("4. Quality dividend")
    f.para(
        "Closed conveyors and silos stop contamination from dust, stones and moisture. "
        "Mechanised sizing and controlled dispatch end manual grade mixing, so power plants "
        "receive cleaner, consistent coal with better combustion efficiency and lower emissions "
        "per unit of electricity.")
    f.h2("5. Investment and phasing")
    f.para(
        "CIL phases 92 projects of 994 MTPA by FY2028-29 end. Spending peaks in FY2026-27 and "
        "FY2027-28 with 27 projects of 303 MTPA. Payback averages 6.2 years from demurrage, "
        "diesel and penalty savings alone, before carbon benefits.")
    f.h2("6. Monitoring")
    f.para(
        "Monthly secretary-level reviews track commissioning milestones, with drone surveys "
        "certifying conveyor gallery progress. Delays beyond 90 days trigger project review "
        "with the subsidiary CMD and the railways for siding synchronisation.")
    f.bullets([
        "FY2025-26: 125 MT through FMC with 19 commissionings.",
        "Capex pipeline Rs 31,367.66 crore to FY2029-30.",
        "FMC sidings target 4-hour rake turnaround standard.",
    ])
    f.h2("7. Subsidiary rollout")
    f.para(
        "MCL leads the 994 MTPA CIL programme with 268 MTPA across Lakhanpur, Ananta and "
        "Siarmal, followed by SECL at 242 MTPA in Korba and NCL at 152 MTPA in Singrauli. "
        "Of the 429.5 MTPA already operational, MCL and SECL together hold over half.")
    f.table(["Subsidiary", "Programme (MTPA)", "Operational (MTPA)"],
            [["MCL", "268", "118"], ["SECL", "242", "104"],
             ["NCL", "152", "62"], ["CCL", "104", "48"],
             ["WCL", "68", "32"], ["ECL", "62", "28"], ["BCCL", "52", "24"],
             ["Others", "46", "13.5"]],
            col_w=[110, 130, 130])
    f.h2("8. Emission savings")
    f.para(
        "Each FMC tonne avoids 2.8 truck-km of diesel haulage on average. At 125 MT in "
        "FY2025-26, avoided diesel exceeds 210 million litres, cutting about 0.56 MT of CO2 "
        "besides particulate and NOx reductions around mining towns.")
    f.h2("9. Rake performance")
    f.para(
        "FMC sidings load 4,000-tonne rakes in 3.4 hours against 9.6 hours manually, lifting "
        "daily loading from 6 to 9 rakes per siding. Demurrage at FMC sidings is near zero, "
        "saving Rs 320 crore yearly across CIL.")
    f.h2("10. FY2025-26 commissioning list")
    f.para(
        "Nineteen projects add nearly 150 MTPA: Lakhanpur 10, Siarmal 25, Ananta 8, Gevra II "
        "8, Kusmunda 4, Dipka II 4, Jayant CHP 15, Nigahi 12, Magadh 6, Amrapali 6, Piparwar 5, "
        "Ashoka 5, Umrer 4, Kamptee 6, Rajmahal 8, Sonepur 4, Muraidih 6, Moonidih 5 and Katras 4 "
        "MTPA, all synchronised with railway siding readiness certificates.")
    f.h2("11. Cost-benefit annex")
    f.para(
        "Capex per MTPA averages Rs 287 crore for silo-CHP-rail packages. Savings of Rs 96 per "
        "tonne from diesel, demurrage and penalty avoidance pay back the average project in 6.2 "
        "years at 85 percent utilisation.")
    f.table(["Project", "Capex (Rs cr)", "Saving (Rs/t)"],
            [["Lakhanpur silo", "2860", "98"],
             ["Gevra II", "2290", "104"],
             ["Jayant CHP", "3420", "88"],
             ["Tori-Shivpur", "1840", "112"]],
            col_w=[150, 110, 110])
    f.table(["Year", "FMC qty (MT)", "Diesel saved (ML)"],
            [["2022-23", "68.40", "118"],
             ["2023-24", "86.20", "152"],
             ["2024-25", "102.50", "186"],
             ["2025-26", "125.00", "210"]],
            col_w=[150, 110, 120])
    f.h2("12. Quality annex")
    f.para(
        "Grade conformity at FMC sidings runs 4 points above manual sidings as closed handling "
        "ends contamination. Referee uphold rates of 97 percent at silo loading points compare "
        "with 91 percent at road sidings.")
    f.table(["Siding type", "Conformity (%)", "Uphold (%)"],
            [["FMC silo", "94", "97"],
             ["CHP siding", "91", "94"],
             ["Manual siding", "87", "91"],
             ["Road loading", "82", "86"]],
            col_w=[150, 110, 110])
    f.h2("13. Risk annex")
    f.para(
        "Railway siding synchronisation slipped on 6 of 19 FY2025-26 projects, risking 22 MTPA "
        "of stranded silo capacity. Land awards for conveyor galleries lag at Korba and Ib "
        "valley, with 4.2 km under Section 11 proceedings.")
    f.table(["Risk", "Projects affected", "Mitigation"],
            [["Siding sync", "6", "Fortnightly railway review"],
             ["Gallery land", "4", "Section 11 fast-track"],
             ["Power supply", "3", "Dedicated feeders"]],
            col_w=[150, 110, 150])
    f.h2("14. State-wise FMC annex")
    f.para(
        "Chhattisgarh hosts 238 MTPA of the programme across Korba and Hasdeo, Odisha 214 MTPA "
        "in Talcher and Ib valley, Jharkhand 168 MTPA in Karanpura and Jharia fringes, Madhya "
        "Pradesh 152 MTPA in Singrauli and Maharashtra 68 MTPA around Chandrapur.")
    f.table(["State", "Programme (MTPA)", "Operational (MTPA)"],
            [["Chhattisgarh", "238", "104"],
             ["Odisha", "214", "118"],
             ["Jharkhand", "168", "86"],
             ["Madhya Pradesh", "152", "62"],
             ["Maharashtra", "68", "32"],
             ["Others", "152", "27.5"]],
            col_w=[150, 120, 130])
    f.table(["Year", "FMC capex (Rs cr)", "Projects completed"],
            [["2021-22", "1820", "8"],
             ["2022-23", "2480", "11"],
             ["2023-24", "3420", "14"],
             ["2024-25", "4280", "11"]],
            col_w=[150, 130, 130])
    f.bullets([
        "Korba cluster review monthly with SECL CMD.",
        "Gallery land awards close by September.",
        "Dedicated 132 kV feeders for all 19 FY26 projects.",
    ])
    return f


def make_mission_coking():
    f = FlowDoc()
    f.h1("Mission Coking Coal Review")
    f.h2("1. Output trajectory")
    f.para(
        "All-India coking coal output rose from 44.79 MT in FY2020-21 to 66.47 MT in "
        "FY2024-25 under Mission Coking Coal, launched in August 2021 to cut steel-sector "
        "import dependence. CIL offered 11 discontinued coking mines to private operators "
        "on revenue share, and NRS linkage tenure was extended up to 30 years.")
    f.table(["Year", "Coking output (MT)"],
            [[y, v] for y, v in zip(COKING_YEARS, COKING_OUT)],
            col_w=[150, 150])
    f.h2("2. Madhuband commissioning")
    f.para(
        "BCCL commissioned the 5 MTPA New Madhuband washery in FY2023-24, the largest coking "
        "washery built in a decade. Raw feed of 4.90 MT at 34.5 percent ash yields 2.38 MT of "
        "washed coal at 19.2 percent ash for SAIL and RINL linkages. One existing washery was "
        "monetised to fund the pipeline.")
    f.h2("3. Eight new washeries")
    f.table(["Washery", "Capacity (MTPA)", "Due", "Status"],
            [[n, c, d, s] for n, c, d, _st, s in WASHERIES_NEW],
            col_w=[130, 100, 80, 140])
    f.para(
        "Combined 21.5 MTPA across Jharkhand and West Bengal takes domestic washed coking "
        "capacity past 35 MTPA by FY2029-30. Bhojudih leads in FY2025-26, Patherdih II "
        "follows in FY2026-27, and Basantpur-Tapin anchors the 4.0 MTPA Jharia cluster.")
    f.h2("4. Linkage reforms")
    f.para(
        "A Steel-through-WDO sub-sector created in March 2024 widens washed coal access, while "
        "Tranche VI coking auctions for steel moved 8.2 lakh tonnes of normative requirement "
        "into allocation. Registration costs Rs 10,000 plus taxes with ascending-clock bidding "
        "per lot.")
    f.h2("5. Import substitution")
    f.para(
        "Coking imports of 58.12 MT in FY2023-24 cost Rs 1.62 lakh crore. Every additional "
        "domestic washed tonne displaces roughly 0.82 import tonnes after yield adjustment, so "
        "the 21.5 MTPA pipeline targets about 12 MT of annual import displacement at full rate.")
    f.table(["Year", "Imports (MT)", "Import bill (Rs cr)"],
            [["2021-22", "57.16", "142800"],
             ["2022-23", "56.04", "228300"],
             ["2023-24", "58.12", "162400"]],
            col_w=[120, 110, 140])
    f.h2("6. Outlook")
    f.para(
        "FY2025-26 targets 70 MT of coking output with Madhuband at full rate and Bhojudih "
        "expansion online. Washability studies on Seam VI feed the New Moonidih design, and "
        "CSN improvement trials with stamp charging aim to lift blend share to 25 percent.")
    f.bullets([
        "Target FY2025-26: 70 MT coking output.",
        "Bhojudih 2.0 MTPA due FY2025-26.",
        "Import displacement target 12 MT per annum at full pipeline rate.",
    ])
    f.h2("7. Seam-wise feed plan")
    f.para(
        "Jharia seams IX through XVIII supply 68 percent of washery feed, with Moonidih Seam IX "
        "alone contributing 4.20 MT. East Bokaro seams add 22 percent, and Ramgarh block "
        "contributes the balance 10 percent of medium-coking feed.")
    f.table(["Seam source", "Feed (MT)", "Ash (%)"],
            [["Jharia IX-XVIII", "14.90", "33.8"],
             ["East Bokaro", "4.80", "35.2"],
             ["Ramgarh block", "2.20", "36.4"]],
            col_w=[140, 100, 100])
    f.h2("8. Private participation")
    f.para(
        "Eleven discontinued mines on revenue share drew 23 bids, with letters of award for six "
        "blocks totalling 8.40 MTPA peak rated capacity. Private washery operators handle 3.20 "
        "MTPA of job-work washing for BCCL feed under five-year contracts.")
    f.h2("9. R&D and CFRI")
    f.para(
        "CFRI trials on stamp charging lifted coke CSR from 62 to 65 in pilot ovens, supporting "
        "25 percent domestic blend trials at Rourkela. Flotation recovery research targets 0.60 "
        "MT of additional clean coal from existing fines streams.")
    f.h2("10. Employment")
    f.para(
        "Washeries and linked mines employ 8,240 persons directly with 3,100 contractor roles. "
        "The Jharia action plan resettles 12 fire-area sites with 4,200 tenements under "
        "construction, releasing 90 MT of locked coking reserves.")
    f.h2("11. Yield annex")
    f.para(
        "Average yield of 48.9 percent on 21.97 MT feed reflects the medium-coking contract mix. "
        "Heavy-media conversion at Patherdih II targets 52 percent yield on the same seams, "
        "adding 0.40 MT of clean coal without new mining.")
    f.table(["Washery", "Yield 2022-23 (%)", "Yield 2023-24 (%)"],
            [["Dugda", "47.80", "48.50"],
             ["Bhojudih", "50.40", "51.20"],
             ["Madhuband", "47.20", "48.60"]],
            col_w=[150, 120, 120])
    f.table(["Fines stream", "Qty (MT)", "Recovery (MT)"],
            [["Flotation", "1.20", "0.40"],
             ["Spiral", "2.40", "0.80"],
             ["TBS", "1.80", "0.60"]],
            col_w=[150, 110, 110])
    f.h2("12. Auction annex")
    f.para(
        "Tranche VI steel lots moved 1.92 lakh tonnes of normative requirement into 8.2 lakh "
        "tonnes of allocated quantity across Bokaro, Rourkela and Durgapur linkages. Premiums "
        "averaged 142 percent with 30-year tenure underwriting blast-furnace planning.")
    f.table(["Lot", "Normative (TPA)", "Allocated (TPA)"],
            [["Bokaro", "50000", "8200"],
             ["Rourkela", "42000", "7100"],
             ["Durgapur", "36000", "6400"]],
            col_w=[150, 120, 120])
    f.h2("13. Energy annex")
    f.para(
        "Washeries consumed 96 kWh per tonne of feed with 18 percent met from the Madhuband "
        "reject-based power plant. Solar rooftops of 4.2 MW across washery townships feed the "
        "daytime CHP load.")
    f.table(["Plant", "Consumption (kWh/t)", "Solar (MW)"],
            [["Dugda", "98", "1.20"],
             ["Bhojudih", "94", "1.40"],
             ["Madhuband", "96", "1.60"]],
            col_w=[150, 130, 100])
    f.h2("14. Skill annex")
    f.para(
        "The CFRI-partnered washery operator course certified 320 control-room staff with dense-"
        "media and flotation modules. Apprenticeship intake of 240 trade apprentices feeds the "
        "eight new washeries coming up to FY2029-30.")
    f.table(["Course", "Certified", "Deployed"],
            [["Dense media", "140", "132"],
             ["Flotation", "96", "90"],
             ["Maintenance", "84", "80"]],
            col_w=[150, 110, 110])
    f.table(["Year", "Apprentices", "Absorbed"],
            [["2021-22", "160", "88"],
             ["2022-23", "200", "124"],
             ["2023-24", "240", "168"]],
            col_w=[150, 110, 110])
    f.bullets([
        "Simulator for dense-media operations due 2025.",
        "Women engineers head quality at two washeries.",
        "Refresher cycle of three years for all operators.",
    ])
    return f


def make_cil_safety_annual():
    f = FlowDoc()
    f.h1("CIL Safety Annual Review 2024")
    f.h2("1. Governance")
    f.para(
        "The 49th Standing Committee on Safety in Coal Mines met on 17 December 2024 under "
        "the Minister of Coal and Mines with over 20 companies participating. Production grew "
        "11 percent to 997.23 MT in FY2023-24 while safety stayed the stated top priority. The "
        "National Coal Mines Safety Report Portal now tracks performance in real time with a "
        "safety audit module.")
    f.h2("2. Accident trend")
    f.para(
        "CIL recorded 22 fatal accidents with 24 fatalities in 2024 up to November, against 26 "
        "and 29 in 2023. Serious accidents fell to 28 with 34 injuries from 34 and 45. The "
        "fatality rate per million tonnes held at 0.04, and per 3 lakh manshifts at 0.14.")
    f.table(["Year", "Fatal accidents", "Fatalities"],
            [[y, a, t] for y, a, t in zip(ACC_YEARS, FATAL_ACC, FATALITIES)],
            col_w=[110, 130, 110])
    f.h2("3. Company-wise record")
    f.table(["Company", "Fatal acc 21/22/23/24", "Fatalities 21/22/23/24"],
            [[c, "/".join(a), "/".join(t)] for c, a, t in ACC_COMPANY],
            col_w=[110, 170, 170])
    f.para(
        "SECL improved from 8 fatal accidents in 2022 to 6 in 2024, while BCCL reached zero "
        "in 2024. NCL's five accidents in 2024 all involved contractor HEMM, prompting "
        "simulator training mandates across Singrauli.")
    f.h2("4. Rates and benchmarks")
    f.para(
        "Fatality per million tonnes ranges from 0.00 at BCCL and NEC to 0.13 at ECL in 2024. "
        "Serious injury per 3 lakh manshifts averages 0.22 for CIL. Five-year averages since "
        "1975 show 24 fatal and 51 serious accidents annually, so current performance runs at "
        "roughly half the historical average per tonne.")
    f.table(["Rate base", "2023", "2024"],
            [["Fatality / MT", "0.04", "0.04"],
             ["Fatality / 3L manshifts", "0.13", "0.14"],
             ["Serious injury / MT", "0.06", "0.06"],
             ["Serious injury / 3L manshifts", "0.21", "0.22"]],
            col_w=[200, 90, 90])
    f.h2("5. Compensation and welfare")
    f.para(
        "Fatal mine accidents draw Rs 15 lakh compensation plus Rs 90,000 ex-gratia under the "
        "Employee Compensation Act framework, a Rs 1,25,000 life cover payout, and employment "
        "to one dependent. Post-retirement medical support covers 2.63 lakh employees up to "
        "Rs 25 lakh in ordinary cases.")
    f.h2("6. Action plan")
    f.para(
        "Risk-based SMP audits cover all 400 mines by March 2025. Proximity detection on 520 "
        "HEMM, slope radar on 38 highwalls, and man-riding modernization in 22 UG mines anchor "
        "the capex plan of Rs 840 crore for safety in FY2025-26.")
    f.bullets([
        "Zero fatal accidents target for BCCL, CCL and MCL in 2025.",
        "SMP audits for all mines by March 2025.",
        "Safety capex Rs 840 crore in FY2025-26.",
    ])
    f.h2("7. Rescue infrastructure")
    f.para(
        "Six rescue stations at Sitarampur, Bhurkunda, Singrauli, Talcher, Korba and Kamptee "
        "hold 2,140 rescue-trained persons with 42 fresh-air bases underground. The 2024 "
        "all-India rescue competition at Korba tested 18 teams on gallery search and "
        "casualty handling under smoke.")
    f.table(["Station", "Teams", "Mock drills 2024"],
            [["Sitarampur", "6", "96"], ["Bhurkunda", "4", "214"],
             ["Singrauli", "5", "168"], ["Talcher", "5", "142"],
             ["Korba", "4", "128"], ["Kamptee", "3", "86"]],
            col_w=[130, 90, 130])
    f.h2("8. Occupational health")
    f.para(
        "Periodical medical examination covered 6.84 lakh employees, detecting 1,240 early "
        "pneumoconiosis cases referred to three occupational health centres. Audiometry flagged "
        "820 noise-induced cases around crusher houses, now under rotation and enclosure "
        "programmes.")
    f.h2("9. Contractor safety")
    f.para(
        "Contractor workers suffered 9 of the 24 fatalities in 2024, concentrated in HEMM "
        "reversing and dump edge failures. Intensive induction for 42,000 contractor crew, "
        "reflective clothing mandates and dump-edge berms of 3 m are now contract conditions "
        "with penalty clauses.")
    f.h2("10. Technology upgrades")
    f.para(
        "Man-riding chairlifts in 22 UG mines cut walking injuries by 44 percent. Environmental "
        "telemonitoring links 1,240 sensors to area control rooms, and e-permit challans "
        "digitised 86 percent of statutory permissions previously tracked on paper.")
    f.h2("11. Serious-injury annex")
    f.para(
        "Serious accidents fell to 28 with 34 injuries in 2024 up to November from 34 and 45 in "
        "2023. Roof falls still cause 38 percent of serious injuries, followed by HEMM at 27 "
        "percent and haul-road incidents at 18 percent.")
    f.table(["Cause", "2023", "2024"],
            [["Roof fall", "14", "11"],
             ["HEMM", "10", "8"],
             ["Haul road", "6", "5"],
             ["Others", "4", "4"]],
            col_w=[150, 100, 100])
    f.table(["Company", "Serious 2023", "Serious 2024"],
            [["ECL", "3", "3"], ["BCCL", "4", "3"],
             ["CCL", "0", "1"], ["NCL", "12", "4"],
             ["WCL", "3", "5"], ["SECL", "11", "12"],
             ["MCL", "1", "0"]],
            col_w=[150, 100, 100])
    f.h2("12. Training annex")
    f.para(
        "Simulator hours crossed 42,000 across the six centres with HEMM reversing incidents down "
        "31 percent among trained operators. Vocational training covered 1.24 lakh persons "
        "including 42,000 contractor crew under penalty-linked induction mandates.")
    f.table(["Centre", "Simulator hrs", "Operators trained"],
            [["Korba", "9200", "1840"], ["Singrauli", "8400", "1620"],
             ["Talcher", "7800", "1480"], ["Ranchi", "6400", "1240"],
             ["Nagpur", "5200", "1080"], ["Sitarampur", "5000", "940"]],
            col_w=[150, 110, 130])
    f.h2("13. Near-miss annex")
    f.para(
        "Near-miss reporting fell to 15 in 2024 up to November from 72 in 2023 as portals "
        "migrated to the national safety reporting system mid-year. Dangerous occurrences stood "
        "at 19 against 26, and reportable injuries at 34 against 54.")
    f.table(["Indicator", "2023", "2024"],
            [["Reportable injury", "54", "34"],
             ["Minor injury", "9", "4"],
             ["Near miss", "72", "15"],
             ["Dangerous occurrence", "26", "19"]],
            col_w=[180, 100, 100])
    f.h2("14. Audit annex")
    f.para(
        "Third-party safety audits covered 212 mines with an average score of 82 percent, up "
        "from 78 percent. Strata audits flagged 42 panels for support revision, all complied "
        "within 90 days, and electrical audits replaced 1,240 km of trailing cable.")
    f.table(["Audit type", "Mines covered", "Score (%)"],
            [["SMP", "212", "82"],
             ["Strata", "168", "84"],
             ["Electrical", "196", "80"]],
            col_w=[150, 110, 100])
    f.table(["Year", "Audits", "Compliance (%)"],
            [["2022", "164", "88"],
             ["2023", "188", "90"],
             ["2024", "212", "92"]],
            col_w=[150, 110, 110])
    f.bullets([
        "All 400 mines audited by March 2025.",
        "Support revision compliance in 90 days.",
        "Trailing cable replacement completes 2025.",
    ])
    return f


def make_gevra_eia():
    f = FlowDoc()
    f.h1("Gevra Expansion Environmental Note")
    f.h2("1. The 50 MT milestone")
    f.para(
        "Gevra OCP crossed 50 MT in FY2022-23, the first Indian mine to do so, against a "
        "target of 52 MT. Kusmunda and Dipka targeted 45 MT and 38 MT the same year, and the "
        "Korba trio produces 95 percent of coal in India's biggest coal district. Output "
        "reached 59.11 MT in FY2023-24.")
    f.table(["Mine", "FY22-23 target", "FY22-23 actual", "FY23-24 actual"],
            [["Gevra OCP", "52.00", "52.50", "59.11"],
             ["Kusmunda OCP", "45.00", "44.80", "46.30"],
             ["Dipka OCP", "38.00", "37.60", "38.40"]],
            col_w=[130, 110, 110, 110])
    f.h2("2. 70 MTPA clearance")
    f.para(
        "Environmental clearance in 2024 raised Gevra capacity from 52.5 to 70 MTPA, among the "
        "world's five largest mines. Conditions cap overburden at 92 million cu.m annually, "
        "mandate 10 m green belts on active boundaries, and require real-time PM10 display at "
        "five village stations.")
    f.h2("3. Land and rehabilitation")
    f.para(
        "The expansion needs 1,240 hectares, of which 68 percent is tenancy land under award. "
        "Compensation at Rs 28.40 lakh per acre plus employment to 1,140 land oustees is "
        "budgeted at Rs 1,860 crore. A model R&R township at Pali houses 420 families with "
        "schools, primary health and piped water.")
    f.table(["Village", "Families", "Employment offered", "Status"],
            [["Pali", "420", "386", "Shifted"],
             ["Gevra", "310", "288", "In progress"],
             ["Kusmunda", "240", "214", "Award stage"]],
            col_w=[120, 90, 130, 110])
    f.h2("4. Water and air")
    f.para(
        "Mine discharge of 41,000 cu.m per day feeds the washery, dust suppression and two "
        "villages after treatment. Zero liquid discharge holds across the complex. Continuous "
        "ambient stations recorded PM10 within norms on 91 percent of days; 26 fog cannons and "
        "18 km of blacktop on haul roads target 95 percent next year.")
    f.h2("5. Evacuation")
    f.para(
        "A 10 MTPA silo-rapid loading complex evacuates Gevra coal without road movement, "
        "loading 9 rakes daily at 3.4 hours per rake. The Korba-Champa third line raises rail "
        "capacity to 14 rakes daily, synchronised with the 70 MTPA mine plan.")
    f.h2("6. Closure plan")
    f.para(
        "Progressive closure backfills 340 hectares with 4.10 lakh saplings at 82 percent "
        "survival. The final void of 120 hectares becomes a 40 million cu.m water reservoir "
        "for the command area, with an escrowed closure corpus of Rs 620 crore.")
    f.bullets([
        "70 MTPA EC secured in 2024 with 32 conditions.",
        "R&R budget Rs 1,860 crore for 1,240 hectares.",
        "Closure corpus Rs 620 crore escrowed.",
    ])
    f.h2("7. Blast and vibration")
    f.para(
        "Controlled blasting with 102 mm drills and electronic delays holds ground vibration "
        "below 5 mm/s at Pali village, monitored by four seismographs. Flyrock exclusion zones "
        "of 500 m are enforced with sirens and guards on every round.")
    f.table(["Blast parameter", "Value"],
            [["Hole diameter (mm)", "102"],
             ["Max charge per delay (kg)", "180"],
             ["Vibration at village (mm/s)", "4.2"],
             ["Air overpressure (dB)", "128"]],
            col_w=[220, 120])
    f.h2("8. Employment profile")
    f.para(
        "Gevra employs 2,140 departmental and 4,860 contractor workers with OMS at 24.60 "
        "tonnes, CIL's highest for a single mine. The Korba training centre certifies 840 "
        "HEMM operators yearly including 120 women dumper drivers.")
    f.h2("9. Power linkage")
    f.para(
        "Linkage of 52 MTPA covers NTPC Korba and Sipat, CSPGCL and Mahagenco stations with "
        "99.1 percent materialisation. E-auction of 2.40 MT fetched 118 percent premium, "
        "funding the township water scheme.")
    f.h2("10. Audit and compliance")
    f.para(
        "Third-party EC compliance audits score Gevra at 91 percent with actions closed on 29 "
        "of 32 conditions; the balance three on township sewage treatment close by December. "
        "DGMS inspections recorded zero prohibitory orders in the last four rounds.")
    f.h2("11. Production annex")
    f.para(
        "Gevra monthly production peaked at 6.20 MT in March on three-shovel availability. "
        "Overburden of 96.40 million cu.m held stripping at 2.32 cu.m per tonne, and the 24/96 "
        "dragline logged 7,240 hours.")
    f.table(["Quarter", "Production (MT)", "OBR (Mcum)"],
            [["Q1", "13.20", "22.40"], ["Q2", "14.10", "23.80"],
             ["Q3", "15.40", "24.60"], ["Q4", "16.41", "25.60"]],
            col_w=[110, 130, 120])
    f.table(["Year", "Production (MT)", "Stripping ratio"],
            [["2021-22", "41.46", "2.41"],
             ["2022-23", "52.50", "2.36"],
             ["2023-24", "59.11", "2.32"]],
            col_w=[110, 120, 120])
    f.h2("12. R&R annex")
    f.para(
        "Compensation disbursement of Rs 1,240 crore reached 82 percent of awarded families, "
        "with employment letters for 888 of 1,140 oustees. The Pali township school enrols 640 "
        "children and the primary health centre logs 120 outpatients daily.")
    f.table(["Village", "Award (Rs cr)", "Disbursed (%)"],
            [["Pali", "520", "88"], ["Gevra", "410", "82"],
             ["Kusmunda", "310", "74"]],
            col_w=[150, 110, 110])
    f.h2("13. Water annex")
    f.para(
        "Treatment plants of 48 MLD capacity process the full 41,000 cu.m daily discharge. "
        "Village supply of 8 MLD covers 12,000 people, washery makeup takes 14 MLD and dust "
        "suppression 19 MLD, leaving zero discharge to natural drains.")
    f.table(["Use", "Qty (MLD)", "Share (%)"],
            [["Villages", "8", "20"], ["Washery", "14", "34"],
             ["Dust suppression", "19", "46"]],
            col_w=[150, 100, 100])
    f.h2("14. CSR annex")
    f.para(
        "CSR spend of Rs 84.60 crore covers 62 villages with schools, health camps and skill "
        "centres. The Pali ITI graduated 480 youth with 72 percent placement in HEMM trades, and "
        "mobile health vans log 28,000 consultations yearly.")
    f.table(["Head", "Spend (Rs cr)", "Villages"],
            [["Education", "28.40", "62"],
             ["Health", "24.20", "58"],
             ["Skills", "18.60", "34"],
             ["Water", "13.40", "28"]],
            col_w=[150, 110, 100])
    f.table(["Year", "CSR (Rs cr)", "Placement (%)"],
            [["2021-22", "62.40", "64"],
             ["2022-23", "74.20", "68"],
             ["2023-24", "84.60", "72"]],
            col_w=[150, 110, 110])
    f.bullets([
        "ITI placement target 80 percent by 2026.",
        "All 62 villages get piped water by March.",
        "Health van fleet doubles to eight.",
    ])
    f.h2("15. HEMM annex")
    f.para(
        "Gevra fields 42 shovels and draglines with 86.4 percent availability, the best in CIL "
        "for a mega complex. Diesel productivity of 42 tonne-kL and tyre life of 7,200 hours "
        "beat norms, saving Rs 84 crore yearly against benchmarks.")
    f.table(["Fleet", "Numbers", "Availability (%)"],
            [["Rope shovels", "14", "88.20"],
             ["Hydraulic shovels", "18", "86.40"],
             ["Draglines", "4", "86.00"],
             ["Dumpers 190T", "96", "84.60"]],
            col_w=[150, 110, 120])
    f.table(["Metric", "Norm", "Achieved"],
            [["Diesel (t/KL)", "38", "42"],
             ["Tyre life (hrs)", "6800", "7200"],
             ["Blast yield (t/kg)", "4.20", "4.60"]],
            col_w=[150, 110, 110])
    return f


def make_auction_note():
    f = FlowDoc()
    f.h1("Coal Linkage Auction and Policy Note")
    f.h2("1. Auction architecture")
    f.para(
        "CIL and SCCL auction linkages for the non-regulated sector covering cement, sponge "
        "iron, steel, aluminium and captive power through ascending-clock electronic auctions. "
        "Registration costs Rs 10,000 plus taxes, road lots start at 100 TPA and rail lots move "
        "in multiples of 4,000 TPA. Allocation stops when the demand-supply ratio falls to 100 "
        "percent in a round.")
    f.h2("2. Coking Tranche VI for steel")
    f.para(
        "The July 2023 Tranche VI scheme auctions coking linkage for steel end-use plants with "
        "15-year scheduled production declarations from captive mines. Normative requirement "
        "nets off captive Washery-IV equivalent supply and existing linkages. Successful bidders "
        "in the reference lot converted 50,000 TPA normative into 8,200 TPA allocated quantity "
        "after adjustments.")
    f.table(["Lot", "Normative (TPA)", "Allocated (TPA)", "End use"],
            [["L1 Bokaro", "50000", "8200", "Steel"],
             ["L2 Rourkela", "42000", "7100", "Steel"],
             ["L3 Durgapur", "36000", "6400", "Steel"]],
            col_w=[110, 110, 110, 110])
    f.h2("3. Thirty-year tenure")
    f.para(
        "NRS coking linkage tenure extended up to 30 years gives steel plants supply security "
        "for blast-furnace planning horizons. The Steel-through-WDO sub-sector created in March "
        "2024 lets developers aggregate washery output for contracted steel capacity.")
    f.h2("4. SHAKTI and power linkage")
    f.para(
        "SHAKTI auctions cleared 12.40 MTPA of power linkage in FY2023-24 at premiums averaging "
        "14 percent. Bridge linkage of 8.60 MTPA covers plants awaiting captive mine production, "
        "and single-window mode-agnostic auctions let buyers switch rail-road without rebidding.")
    f.table(["Scheme", "Cleared (MTPA)", "Premium (%)"],
            [["SHAKTI power", "12.40", "14"],
             ["Bridge linkage", "8.60", "9"],
             ["NRS agnostic", "15.20", "108"]],
            col_w=[140, 110, 100])
    f.h2("5. Rationalisation and swaps")
    f.para(
        "Linkage rationalisation swapped 18.40 MT of sources closer to plants, saving Rs 1,240 "
        "crore in freight annually. Swapping between linked plants needs tripartite consent and "
        "grade-equivalence certification from the coal controller.")
    f.h2("6. Calendar and outlook")
    f.para(
        "Four NRS tranches, two SHAKTI rounds and one coking tranche are calendared for "
        "FY2024-25. E-auction for the spot market runs fortnightly with 68.40 MT offered in "
        "FY2023-24 at 117 percent average premium.")
    f.bullets([
        "NRS tenure up to 30 years for coking steel linkages.",
        "Rationalisation saves Rs 1,240 crore freight yearly.",
        "Fortnightly spot e-auction with 68.40 MT offered.",
    ])
    f.h2("7. Premium trends")
    f.para(
        "Spot premiums peaked at 184 percent in October 2022 on import parity, then normalised "
        "to 98 percent by March 2024 as domestic supply caught up. Power forward premiums stayed "
        "muted between 9 and 18 percent through the linkage assurance design.")
    f.table(["Period", "Spot premium (%)", "NRS premium (%)"],
            [["H1 FY2022-23", "184", "142"],
             ["H2 FY2022-23", "146", "118"],
             ["H1 FY2023-24", "121", "106"],
             ["H2 FY2023-24", "98", "94"]],
            col_w=[130, 120, 120])
    f.h2("8. Consumer grievances")
    f.para(
        "The online linkage portal resolved 1,240 of 1,310 consumer complaints within 30 days, "
        "mostly on grade disputes settled by referee sampling. Third-party sampling coverage "
        "reached 100 percent of rail loading points during the year.")
    f.h2("9. Import substitution ledger")
    f.para(
        "Auctioned domestic coal displaced an estimated 42 MT of thermal imports in FY2023-24, "
        "saving about Rs 68,000 crore in foreign exchange at prevailing Newcastle benchmarks. "
        "Coastal plants under SHAKTI flexibility swapped 6.40 MT to domestic grades.")
    f.h2("10. FY2024-25 pipeline")
    f.para(
        "The coming year lists Tranche VII coking for steel, two SHAKTI rounds for 14 MTPA, "
        "four NRS tranches for 22 MTPA and monthly spot windows. Portal upgrades add grade-wise "
        "live stock visibility at all 400 sidings.")
    f.h2("11. SHAKTI annex")
    f.para(
        "SHAKTI linkage of 104.20 MTPA covers 68 power stations with 93.6 percent "
        "materialisation. Bridge linkage of 8.60 MTPA serves nine plants awaiting captive output, "
        "and agnostic auctions moved 15.20 MTPA to 42 industrial buyers.")
    f.table(["Plant group", "Linkage (MTPA)", "Materialisation (%)"],
            [["NTPC", "38.20", "96.40"],
             ["State gencos", "52.40", "93.10"],
             ["IPPs", "13.60", "88.20"]],
            col_w=[150, 110, 130])
    f.table(["Year", "SHAKTI cleared (MTPA)", "Premium (%)"],
            [["2021-22", "8.40", "11"],
             ["2022-23", "10.20", "16"],
             ["2023-24", "12.40", "14"]],
            col_w=[150, 140, 100])
    f.h2("12. Washery linkage annex")
    f.para(
        "Coking linkage of 18.40 MTPA flows from Dugda, Bhojudih and Madhuband to steel plants "
        "at 94 percent lifting. Non-coking washery linkage of 6.20 MTPA serves cement clusters "
        "in Chhattisgarh and Odisha.")
    f.table(["Washery", "Linkage (MTPA)", "Lifting (%)"],
            [["Dugda", "4.80", "94"], ["Bhojudih", "3.60", "95"],
             ["Madhuband", "4.40", "92"], ["Kathara", "1.90", "96"]],
            col_w=[150, 110, 100])
    f.h2("13. E-auction calendar annex")
    f.para(
        "Fortnightly spot windows offer 2.80 MT per round with 68.40 MT booked in FY2023-24. "
        "Special forward e-auction for power runs monthly with 2.40 MT per round, and exclusive "
        "NRS windows serve sponge iron quarterly.")
    f.table(["Window", "Frequency", "FY24 booked (MT)"],
            [["Spot", "Fortnightly", "68.40"],
             ["Power forward", "Monthly", "28.80"],
             ["NRS exclusive", "Quarterly", "15.20"]],
            col_w=[150, 110, 130])
    f.h2("14. Portal annex")
    f.para(
        "The linkage portal onboards 2,840 consumers with digital FSAs, grade-wise stock "
        "visibility and referee-sample tracking. Uptime of 99.4 percent and 30-day grievance "
        "closure at 94.7 percent top the Ministry's e-governance scorecard for the sector.")
    f.table(["Metric", "2022-23", "2023-24"],
            [["Consumers onboard", "2140", "2840"],
             ["Portal uptime (%)", "98.60", "99.40"],
             ["Grievance closure (%)", "91.20", "94.70"]],
            col_w=[180, 110, 130])
    f.table(["Round", "Offered (MT)", "Booked (MT)"],
            [["Spot H1", "34.20", "31.60"],
             ["Spot H2", "36.40", "36.80"],
             ["Power forward", "30.20", "28.80"]],
            col_w=[150, 110, 110])
    f.bullets([
        "Live stock visibility at all 400 sidings.",
        "Digital referee tracking from FY2024-25.",
        "Mobile app for small consumers in Q2.",
    ])
    return f


def make_1bt_roadmap():
    f = FlowDoc()
    f.h1("One Billion Tonne Roadmap")
    f.h2("1. Demand frame")
    f.para(
        "Estimated coal demand of 1,196.60 MT for FY2023-24 rises toward 1,522 MT by FY2029-30 "
        "in the official production plan. CIL anchors supply with an 875 MT target for FY2025-26, "
        "SCCL grows to 82 MT, and captive and commercial mines scale past 320 MT.")
    f.table(["Producer", "2025-26", "2026-27", "2027-28", "2028-29", "2029-30"],
            [["CIL", "875", "915", "950", "980", "1000"],
             ["SCCL", "70", "72", "76", "80", "82"],
             ["Captive and others", "159", "223", "252", "277", "308"],
             ["All-India", "1104", "1210", "1278", "1337", "1390"]],
            col_w=[130, 70, 70, 70, 70, 70])
    f.h2("2. CIL project pipeline")
    f.para(
        "Sixty-eight mega projects hold 3,780 MT of pipeline capacity. Fourteen projects "
        "totalling 210 MTPA await environmental clearance, the critical path for the billion "
        "tonne. Siarmal 40 MTPA, Lingaraj 20 MTPA and Jayant 25 MTPA expansions anchor growth.")
    f.table(["Project", "Company", "Capacity (MTPA)", "Clearance"],
            [["Siarmal OCP", "MCL", "40.0", "Stage-II"],
             ["Lingaraj expansion", "MCL", "20.0", "Stage-II granted"],
             ["Jayant expansion", "NCL", "25.0", "Appraisal"],
             ["Gevra 70 MTPA", "SECL", "70.0", "Granted 2024"]],
            col_w=[150, 80, 100, 120])
    f.h2("3. Evacuation backbone")
    f.para(
        "Ninety-two FMC projects of 994 MTPA by FY2028-29 move almost all CIL coal "
        "mechanically. Three rail corridors, Tori-Shivpur, Korba-Champa third line and "
        "Jharsuguda-Barpali doubling, add 68 MTPA of loading capacity.")
    f.h2("4. Underground and technology")
    f.para(
        "Mass-production technology targets 100 MT of UG output by FY2029-30 from 26 "
        "continuous miner panels and 8 longwalls. Surface miners handle 42 percent of OC "
        "coal without drilling or blasting, and 520 HEMM carry proximity detection.")
    f.table(["Technology", "2023-24 (MT)", "2029-30 target (MT)"],
            [["Continuous miner", "5.60", "42.00"],
             ["Longwall", "1.20", "18.00"],
             ["Surface miner", "296.00", "410.00"]],
            col_w=[150, 110, 130])
    f.h2("5. Risks")
    f.para(
        "Demand shortfall would strand the 210 MTPA awaiting clearance. Land acquisition "
        "averages 4.2 years per major project, and monsoon flooding cost 9 MT in FY2021-22 "
        "alone. Grade conformity penalties of Rs 480 crore in FY2023-24 flag quality risk at "
        "high volumes.")
    f.h2("6. Milestones")
    f.para(
        "The plan crosses 1,000 MT of CIL output in FY2028-29 and 1,390 MT all-India in "
        "FY2029-30. Import substitution saves an estimated Rs 2.10 lakh crore in foreign "
        "exchange at full displacement of non-essential thermal imports.")
    f.bullets([
        "CIL 1,000 MT in FY2028-29; all-India 1,390 MT in FY2029-30.",
        "210 MTPA awaiting EC is the critical path.",
        "FMC and corridors add 1,062 MTPA evacuation by FY2028-29.",
    ])
    f.h2("7. Year-wise build-up")
    f.para(
        "CIL adds roughly 25 MT yearly: Gevra climbs to 70, Siarmal to 40, Jayant to 25 and "
        "Magadh to 14 MTPA, while 40 MTPA of small-project renewals offset depleting underground "
        "faces. Captive blocks scale fastest at 18 percent CAGR from the auction pipeline.")
    f.table(["Year", "CIL (MT)", "Captive (MT)", "All-India (MT)"],
            [["2025-26", "875", "159", "1104"],
             ["2026-27", "915", "223", "1210"],
             ["2027-28", "950", "252", "1278"],
             ["2028-29", "980", "277", "1337"],
             ["2029-30", "1000", "308", "1390"]],
            col_w=[110, 90, 90, 110])
    f.h2("8. Demand sensitivity")
    f.para(
        "Power demand growth of 7 percent absorbs the full plan, while 5 percent growth leaves "
        "a 60 MT surplus for stock or export to neighbouring grids. Industrial hydrogen pilots "
        "could add 8 MT of coal-gasification demand by FY2029-30 under the Rs 37,500 crore "
        "incentive scheme.")
    f.h2("9. Financing")
    f.para(
        "Capex of Rs 1.42 lakh crore to FY2029-30 splits into HEMM (38 percent), FMC and rail "
        "(31 percent), washeries (9 percent) and land-R&R (22 percent). Internal accruals cover "
        "three quarters, with the balance through mine-developer-operator models.")
    f.h2("10. Review mechanism")
    f.para(
        "Quarterly mission reviews chaired by the Secretary track the 210 MTPA clearance "
        "pipeline mine by mine. Red-flagged projects move to fortnightly review with state "
        "governments for land and forest bottlenecks.")
    f.h2("11. Capex annex")
    f.para(
        "Capex of Rs 1.42 lakh crore to FY2029-30 splits into HEMM at Rs 53,960 crore, FMC and "
        "rail at Rs 44,020 crore, washeries at Rs 12,780 crore and land-R&R at Rs 31,240 crore. "
        "FY2023-24 spend of Rs 16,840 crore ran 8 percent ahead of plan on Silo completions.")
    f.table(["Head", "Share (%)", "FY24 spend (Rs cr)"],
            [["HEMM", "38", "6240"],
             ["FMC and rail", "31", "5860"],
             ["Washeries", "9", "1240"],
             ["Land and R&R", "22", "5500"]],
            col_w=[150, 100, 130])
    f.table(["Year", "Capex (Rs cr)", "Plan (%)"],
            [["2021-22", "12480", "96"],
             ["2022-23", "14860", "102"],
             ["2023-24", "16840", "108"]],
            col_w=[150, 110, 100])
    f.h2("12. Import ledger annex")
    f.para(
        "Non-essential thermal imports of 176 MT in FY2023-24 cost Rs 2.84 lakh crore. The plan "
        "displaces 120 MT by FY2027-28 through coastal linkage swaps and 60 MT more by FY2029-30 "
        "with full FMC evacuation, saving Rs 2.10 lakh crore yearly at current benchmarks.")
    f.table(["Year", "Thermal imports (MT)", "Bill (Rs cr)"],
            [["2021-22", "184", "248000"],
             ["2022-23", "172", "296000"],
             ["2023-24", "176", "284000"]],
            col_w=[150, 130, 120])
    f.h2("13. State demand annex")
    f.para(
        "Tamil Nadu, Maharashtra and Gujarat together absorb 38 percent of incremental demand to "
        "FY2029-30 on coastal power growth. Pithead states consume 44 percent at the mine mouth "
        "through MGR and belt systems with near-zero logistics cost.")
    f.table(["State group", "Incremental demand (MT)", "Share (%)"],
            [["Coastal power", "62", "38"],
             ["Pithead states", "72", "44"],
             ["Others", "30", "18"]],
            col_w=[150, 150, 100])
    f.h2("14. Manpower annex")
    f.para(
        "CIL holds 2.39 lakh departmental strength with 18,400 annual retirements offset by "
        "4,280 trainees. Contractor HEMM crew of 1.02 lakh moves 58 percent of overburden, and "
        "overall OMS of 13.43 tonnes underwrites the billion-tonne labour productivity case.")
    f.table(["Head", "2022-23", "2023-24"],
            [["Departmental (lakh)", "2.43", "2.39"],
             ["Contractor (lakh)", "0.98", "1.02"],
             ["OMS", "12.80", "13.43"]],
            col_w=[150, 110, 110])
    f.table(["Subsidiary", "OMS", "UG share (%)"],
            [["MCL", "22.50", "2"],
             ["NCL", "14.20", "0"],
             ["CCL", "9.50", "4"],
             ["SECL", "8.20", "8"]],
            col_w=[150, 110, 110])
    f.bullets([
        "Simulator training for all 22,600 outsourced HEMM crew.",
        "Women dumper drivers cross 2,400 company-wide.",
        "Leadership pipeline certifies 1,240 executives yearly.",
    ])
    return f


def make_manpower_xlsx():
    sheets = [
        ("OMS_overall", "Overall OMS (tonnes)",
         ["Year"] + OMS_YEARS,
         [["CIL"] + OMS_OVERALL, ["SCCL", "4.89", "6.23", "6.37", "5.62", "6.09", "5.31", "5.42"]]),
        ("OMS_UG_OC", "CIL UG and OC OMS (tonnes)",
         ["Type"] + OMS_YEARS,
         [["UG"] + OMS_UG, ["OC"] + OMS_OC]),
        ("Company_OMS", "Company OMS FY24 (tonnes)",
         ["Company", "OMS"],
         [["ECL", "4.10"], ["BCCL", "3.80"], ["CCL", "9.50"], ["NCL", "14.20"],
          ["WCL", "7.30"], ["SECL", "8.20"], ["MCL", "22.50"]]),
        ("Manshifts", "Manshifts (lakh)",
         ["Company", "2022", "2023", "2024"],
         [["ECL", 182.4, 178.2, 174.6], ["BCCL", 96.8, 94.2, 91.5],
          ["CCL", 88.4, 86.1, 84.2], ["NCL", 72.6, 71.8, 71.2],
          ["WCL", 88.9, 87.4, 86.0], ["SECL", 214.6, 210.2, 206.8],
          ["MCL", 92.4, 91.0, 89.6]]),
        ("Training", "Training man-days",
         ["Institute", "2022", "2023", "2024"],
         [["Ranchi", 48200, 51400, 54800], ["Bilaspur", 38400, 40200, 42800],
          ["Singrauli", 21400, 22800, 24100], ["Talcher", 24800, 26200, 28400]]),
        ("Accidents", "Fatal accidents by company",
         ["Company"] + ACC_YEARS,
         [[c] + a for c, a, _t in ACC_COMPANY]),
    ]
    return sheets


def gradewise_rows():
    rows = []
    for yi, y in enumerate([2022, 2023]):
        for m in range(1, 13):
            g = ["G11", "G12", "G13", "Steel-II"][m % 4]
            qty = 2400 + ((m * 173 + yi * 311) % 900)
            rows.append(f"{y}-{m:02d},{g},{qty},Rail")
    return rows


def stock_rows():
    rows = []
    for yi, y in enumerate([2023, 2024]):
        stock = 48.20 + yi * 2.10
        for m in range(1, 13):
            prod = 62.0 + ((m * 29) % 14)
            lift = prod - 0.4 + ((m * 17) % 9) / 10
            stock = round(stock + prod - lift, 2)
            rows.append(f"{y}-{m:02d},{prod:.1f},{lift:.1f},{stock:.2f},Pithead")
    return rows


def make_financial_xlsx():
    sheets = [
        ("Revenue", "Revenue from operations (Rs cr)",
         ["Company", "2021-22", "2022-23", "2023-24"],
         [["ECL", 18240, 19860, 22480], ["BCCL", 12480, 14220, 16840],
          ["CCL", 19860, 22480, 25840], ["NCL", 16840, 18420, 20120],
          ["WCL", 14280, 15840, 17260], ["SECL", 28480, 32640, 36820],
          ["MCL", 24840, 28480, 32160]]),
        ("Profit", "Profit after tax (Rs cr)",
         ["Company", "2021-22", "2022-23", "2023-24"],
         [["ECL", 1840, 2210, 3120], ["BCCL", 980, 1420, 2180],
          ["CCL", 2420, 3120, 4280], ["NCL", 3840, 4420, 5180],
          ["WCL", 1620, 1980, 2460], ["SECL", 5420, 6840, 8420],
          ["MCL", 6840, 8420, 10240]]),
        ("OBR", "Overburden removal (million cu.m)",
         ["Company", "2021-22", "2022-23", "2023-24"],
         [["ECL", 112.4, 124.8, 142.6], ["BCCL", 88.2, 96.4, 108.2],
          ["CCL", 142.6, 158.2, 176.4], ["NCL", 312.4, 338.6, 362.8],
          ["WCL", 168.4, 182.6, 198.4], ["SECL", 248.6, 268.4, 292.6],
          ["MCL", 168.2, 184.6, 212.4]]),
        ("Stripping", "Stripping ratio (cu.m per tonne)",
         ["Company", "2021-22", "2022-23", "2023-24"],
         [["ECL", 3.42, 3.56, 3.00], ["BCCL", 2.88, 2.66, 2.63],
          ["CCL", 2.08, 2.08, 2.05], ["NCL", 2.72, 2.58, 2.66],
          ["WCL", 2.94, 2.84, 2.87], ["SECL", 1.74, 1.61, 1.56],
          ["MCL", 1.00, 0.96, 1.03]]),
        ("Capex", "Capital expenditure (Rs cr)",
         ["Head", "2021-22", "2022-23", "2023-24"],
         [["HEMM", 2840, 3120, 3680], ["FMC and siding", 1820, 2480, 3420],
          ["Washery", 640, 820, 1240], ["Safety", 420, 560, 840],
          ["Exploration", 380, 420, 480]]),
        ("Realisation", "Average realisation (Rs per tonne)",
         ["Channel", "2021-22", "2022-23", "2023-24"],
         [["Linkage power", 1480, 1520, 1560], ["NRS auction", 2840, 3420, 2980],
          ["E-auction spot", 3120, 4840, 3420], ["Coking linkage", 4280, 5640, 6120]]),
    ]
    return sheets


def make_environment_docx_sections():
    import docx
    d = docx.Document()
    d.add_heading("Environmental Clearance and Compliance Note", 0)
    d.add_paragraph("Coal projects above 0.50 MTPA need prior environmental clearance with "
                    "public hearing, EIA-EMP appraisal and stage-wise forestry clearance. During "
                    "FY2023-24, 14 CIL projects totalling 210 MTPA sat at various appraisal stages, "
                    "the critical path for the billion-tonne roadmap. Gevra expansion to 70 MTPA "
                    "secured clearance in 2024 with 32 conditions including 10 m green belts and "
                    "real-time PM10 display at five village stations.")
    d.add_heading("Gevra 70 MTPA conditions", level=1)
    t = d.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    h = t.rows[0].cells
    h[0].text, h[1].text, h[2].text = "Condition", "Stipulation", "Compliance"
    for c, s, k in [("Overburden cap", "92 million cu.m per year", "86.40 achieved"),
                    ("Green belt", "10 m on active boundaries", "8.20 km planted"),
                    ("PM10 display", "5 village stations live", "5 live"),
                    ("R&R township", "Pali 420 families", "420 shifted")]:
        r = t.add_row().cells
        r[0].text, r[1].text, r[2].text = c, s, k
    d.add_heading("Groundwater monitoring", level=1)
    d.add_paragraph("Quarterly level and quality monitoring covers the ECL, BCCL, CCL and NCL "
                    "command areas including buffer zones, with three quarters completed in "
                    "FY2023-24. CMPDI Ranchi won Groundwater Professional recognition from CGWA "
                    "for modelling reports, and holds MoUs with two accredited consultants.")
    t2 = d.add_table(rows=1, cols=3)
    t2.style = "Table Grid"
    h2 = t2.rows[0].cells
    h2[0].text, h2[1].text, h2[2].text = "Coalfield", "Piezometers", "Depletion observed"
    for c, p, o in [("ECL Raniganj", "18", "None regional"),
                    ("BCCL Jharia", "22", "None regional"),
                    ("CCL Karanpura", "16", "None regional"),
                    ("NCL Singrauli", "14", "None regional")]:
        r = t2.add_row().cells
        r[0].text, r[1].text, r[2].text = c, p, o
    d.add_heading("Afforestation", level=1)
    d.add_paragraph("MCL planted 4.20 lakh saplings over 168 hectares of reclaimed land at 82 "
                    "percent survival, SECL backfilled 340 hectares at Gevra, and CCL greens 96 "
                    "hectares around Piparwar yearly. Company-wide, 1,240 hectares returned to "
                    "green cover in FY2023-24 against 1,180 hectares decoaled.")
    d.add_heading("Mine water utilisation", level=1)
    d.add_paragraph("Zero liquid discharge holds across Gevra, Dipka and Kusmunda. Treated mine "
                    "water meets 41 percent of washery and dust-suppression demand at Korba, supplies "
                    "two villages, and irrigates 640 hectares through the Hasdeo command outlet. "
                    "Utilisation company-wide reached 68 percent of discharge.")
    d.add_heading("Closure planning", level=1)
    d.add_paragraph("Progressive closure escrows Rs 620 crore for Gevra alone, with the final 120 "
                    "hectare void designed as a 40 million cu.m reservoir. All mega projects carry "
                    "approved closure plans with five-yearly third-party audits.")
    d.add_heading("Fly ash utilisation", level=1)
    d.add_paragraph("Pithead power stations achieved 96 percent ash utilisation through brick, "
                    "cement and mine-void stowing. The Korba ash pipeline to Mahanadi cement "
                    "clusters moved 2.40 MT, and dyke-raising works consumed 1.10 MT of compacted ash.")
    t3 = d.add_table(rows=1, cols=3)
    t3.style = "Table Grid"
    h3 = t3.rows[0].cells
    h3[0].text, h3[1].text, h3[2].text = "Use", "Qty (MT)", "Share (%)"
    for u, q, s in [("Bricks and blocks", "1.20", "28"), ("Cement", "2.40", "42"),
                    ("Mine stowing", "0.80", "14"), ("Dyke raising", "1.10", "12")]:
        r = t3.add_row().cells
        r[0].text, r[1].text, r[2].text = u, q, s
    d.add_heading("Wildlife clearance", level=1)
    d.add_paragraph("Projects in the Tadoba and Hasdeo landscapes run seasonal blasting windows "
                    "with forest observers, underpasses on all new haul roads, and a Rs 42 crore "
                    "wildlife management plan. Camera-trap monitoring shows stable corridor use "
                    "through the monsoon months.")
    d.add_heading("Compliance scorecard", level=1)
    d.add_paragraph("Third-party EC compliance across mega projects averaged 89 percent with 412 "
                    "of 468 conditions closed; the balance 56 mostly concern township sewage plants "
                    "due by December. Zero prohibitory orders were recorded in the last four DGMS "
                    "inspection rounds across the Gevra-Kusmunda-Dipka complex.")
    d.add_heading("Air quality record", level=1)
    d.add_paragraph("Continuous stations at Gevra recorded PM10 within norms on 91 percent of days, "
                    "with exceedances clustered in October-November stubble season upwind. Fog cannons "
                    "cut haul-road dust by 64 percent in monitored stretches, and blacktopping of 18 km "
                    "of permanent roads completes the dust plan by March.")
    t4 = d.add_table(rows=1, cols=3)
    t4.style = "Table Grid"
    h4 = t4.rows[0].cells
    h4[0].text, h4[1].text, h4[2].text = "Station", "PM10 compliance (%)", "Exceedance days"
    for s, c, e in [("Gevra township", "93", "24"), ("Pali village", "91", "31"),
                    ("Kusmunda gate", "89", "38"), ("Dipka siding", "92", "27")]:
        r = t4.add_row().cells
        r[0].text, r[1].text, r[2].text = s, c, e
    d.add_heading("Noise and vibration", level=1)
    d.add_paragraph("Controlled blasting holds village vibration below 5 mm/s with air overpressure "
                    "under 128 dB at 500 m exclusion. Night-time noise at Pali averages 52 dB against "
                    "the 55 dB residential norm, with HEMM silencers and acoustic enclosures on all "
                    "stationary crushers.")
    d.add_heading("Rehabilitation audit", level=1)
    d.add_paragraph("Social audit by the district administration found 88 percent disbursement of "
                    "Rs 1,240 crore awarded compensation and 888 employments against 1,140 promised. "
                    "The Pali township occupancy reached 420 of 460 tenements with school enrolment at "
                    "640 children and 120 daily hospital outpatients.")
    d.add_heading("Mine closure corpus", level=1)
    d.add_paragraph("Escrowed closure funds total Rs 620 crore for Gevra at Rs 8.86 lakh per hectare "
                    "of rated lease, audited yearly with five-yearly plan revisions. Progressive "
                    "closure backfills 340 hectares yearly with 4.10 lakh saplings at 82 percent "
                    "survival, ahead of the 75 percent norm.")
    d.add_heading("Carrying capacity studies", level=1)
    d.add_paragraph("The Korba carrying-capacity study caps regional output at 210 MTPA on air-shed "
                    "modelling, with Gevra's 70 MTPA fitting inside the envelope only with the full "
                    "FMC silo complex and 26 fog cannons operational. Critically polluted cluster "
                    "action plans bind all three Korba operators to common ambient targets reviewed "
                    "half-yearly by the state board, and any new expansion needs fresh cumulative "
                    "impact assessment rather than standalone EIA. Continuous emission monitoring on "
                    "the two washeries streams data to the central server with 98.2 percent uptime, "
                    "and exceedance alerts reach the environment cell within 15 minutes for corrective "
                    "loading adjustments.")
    d.add_heading("Biodiversity offsets", level=1)
    d.add_paragraph("Compensatory afforestation of 2,480 hectares in lieu of 1,240 hectares diverted "
                    "forest runs at 2:1 ratio across three divisions with 78 percent survival audited "
                    "by the forest department. Wildlife underpasses on all new haul roads follow the "
                    "Hasdeo landscape plan, with camera traps recording stable elephant corridor use "
                    "through the monsoon and a Rs 42 crore management plan funding water holes, salt "
                    "licks and 40 km of fire lines. Proof of concept at Piparwar shows afforested "
                    "external dumps returning small-mammal diversity within eight years of planting.")
    d.add_heading("Public hearing record", level=1)
    d.add_paragraph("The Gevra expansion hearing drew 1,240 attendees with 86 written submissions, "
                    "mostly on employment, dust and village water. Commitments minuted include the Pali "
                    "township school upgrade to higher secondary, the 8 MLD village water scheme, and "
                    "quarterly dust monitoring reports in Hindi at all five panchayat notice boards. "
                    "Compliance with hearing commitments is third-party audited yearly with the report "
                    "placed before the appraisal committee before any further expansion is considered.")
    d.add_heading("Ash pond management", level=1)
    d.add_paragraph("Legacy ash ponds at Korba cover 96 hectares with 8.40 MT of stored ash under "
                    "phased evacuation to brick and cement makers. Dyke safety audits by IIT Roorkee "
                    "rate all three ponds stable with factors above 1.5, piezometer readings uploaded "
                    "weekly, and downstream habitations covered by the emergency action plan rehearsed "
                    "each October. Pond 3 converts to a 22-hectare solar park after evacuation, "
                    "tendered at Rs 4.20 crore per MW with commissioning due next March.")
    d.add_heading("Vibration record", level=1)
    d.add_paragraph("Four seismographs around Pali recorded peak vibration of 4.2 mm/s against the "
                    "5 mm/s stipulation across 1,240 monitored blasts, with air overpressure peaking at "
                    "128 dB. Complaints fell to 6 from 18 after electronic delays replaced shock-tube "
                    "initiation on all near-village benches, and every complaint now triggers a "
                    "same-week seismograph deployment with results shared at the panchayat board.")
    d.add_heading("Topsoil management", level=1)
    d.add_paragraph("Topsoil stripping of 4.20 million cu.m stacked in 38 dedicated dumps with "
                    "legume cover retains viability for reclamation spreading at 30 cm depth. Annual "
                    "soil testing shows organic carbon recovery to 0.42 percent within five years of "
                    "respreading, supporting the 82 percent sapling survival across 340 reclaimed "
                    "hectares yearly. Dump slopes stand at 28 degrees with garland drains desilted "
                    "before every monsoon, and no dump-slope failure has occurred in three years.")
    t5 = d.add_table(rows=1, cols=3)
    t5.style = "Table Grid"
    h5 = t5.rows[0].cells
    h5[0].text, h5[1].text, h5[2].text = "Dump", "Topsoil (Mcum)", "Survival (%)"
    for u, q, s in [("External 3", "1.20", "82"), ("External 5", "1.40", "84"),
                    ("Internal A", "0.90", "79"), ("Internal C", "0.70", "81")]:
        r = t5.add_row().cells
        r[0].text, r[1].text, r[2].text = u, q, s
    d.add_heading("Energy transition at site", level=1)
    d.add_paragraph("Solar plants of 8.40 MW across Gevra rooftops and decoaled land feed daytime CHP "
                    "load, cutting grid drawal 12 percent. Two LNG-converted dumpers pilot alternate "
                    "fuel with 18 percent CO2 reduction per tonne-km, and trolley-assist trials on the "
                    "2 km permanent ramp promise 30 percent diesel savings on that lead. EV buses run "
                    "the township circuit with 42,000 riders monthly.")
    d.add_heading("Biodiversity monitoring", level=1)
    d.add_paragraph("Quarterly camera-trap surveys across the Hasdeo landscape record elephant, sloth "
                    "bear and leopard presence with corridor use stable through the monsoon. The Rs 42 "
                    "crore wildlife plan funds 40 km of fire lines, 12 water holes and 6 salt licks, "
                    "with forest department observers on all blasts within 1 km of corridor crossings. "
                    "Afforested external dumps at Piparwar show small-mammal diversity returning within "
                    "eight years of planting, a template for the Gevra closure landscape.")
    t6 = d.add_table(rows=1, cols=3)
    t6.style = "Table Grid"
    h6 = t6.rows[0].cells
    h6[0].text, h6[1].text, h6[2].text = "Species", "Sightings", "Trend"
    for s, n, t_ in [("Elephant", "42", "Stable"), ("Sloth bear", "18", "Stable"),
                     ("Leopard", "9", "Rising"), ("Chital", "240", "Rising")]:
        r = t6.add_row().cells
        r[0].text, r[1].text, r[2].text = s, n, t_
    d.add_heading("Hazardous waste", level=1)
    d.add_paragraph("Used oil of 420 KL yearly goes to authorised recyclers with manifest tracking, "
                    "while 86 tonnes of e-waste from control systems moves through producer-takeback "
                    "channels. Biomedical waste from the two hospitals treats 120 kg daily in the "
                    "captive autoclave with barcoded bag traceability.")
    d.add_heading("Traffic management", level=1)
    d.add_paragraph("The mine road network separates 190-tonne dumpers from light vehicles with "
                    "bermed corridors, RFID boom gates and GPS speed governors capped at 30 km/h. "
                    "Village bypasses divert 1,900 truck trips daily off public roads, and school-zone "
                    "timings ban dumper movement during 8-9 am and 3-4 pm with Rs 2,000 penalties per "
                    "violation debited to contractor bills.")
    t7 = d.add_table(rows=1, cols=3)
    t7.style = "Table Grid"
    h7 = t7.rows[0].cells
    h7[0].text, h7[1].text, h7[2].text = "Corridor", "Trips diverted", "Penalty (Rs)"
    for c, t_, p in [("Pali bypass", "820", "2000"), ("Gevra bypass", "640", "2000"),
                     ("Kusmunda link", "440", "2000")]:
        r = t7.add_row().cells
        r[0].text, r[1].text, r[2].text = c, t_, p
    d.add_heading("Cultural heritage", level=1)
    d.add_paragraph("Chance-find procedures protect two recorded archaeological mounds near the "
                    "lease boundary with 100 m no-work buffers and State archaeology supervision of "
                    "topsoil stripping. Worker induction covers heritage awareness, and no find has "
                    "halted operations since the protocol began in 2019.")
    return d
