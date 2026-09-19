"""Shared researched figures for the demo corpus. Subsidiary totals track the
Ministry of Coal annual-report tables (FY19-20..FY25-26, MT); mine-level detail
is plausible synthetic detail consistent with those totals. Planted conflicts
(used by Conflict Radar demos) are marked CONFLICT and must keep exact values:

1. Kusunda Mine production FY2021-22: 4.85 MT (SECL annual) vs 4.35 MT (scan).
2. Jayant OCP offtake FY2022-23: 195.4 lt (NCL workbook) vs 197.9 lt (ops note).
3. Lingaraj OCP production FY2023-24: 17.85 MT (MCL report) vs 18.30 (revised).
4. SECL extractable reserves: 812.45 MT (annual) vs 818.90 MT (revised).
Corroborated: Nigahi OCP production FY2023-24 208.6 lt (workbook + ops note).
"""

FY = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

# Subsidiary raw-coal production, MT (Ministry tables; FY25-26 CIL dept page).
SUB_PROD = {
    "ECL": ["40.50", "34.00", "32.43", "35.02", "47.56", "49.00"],
    "BCCL": ["27.70", "24.70", "30.50", "36.18", "41.10", "38.50"],
    "CCL": ["66.50", "62.20", "68.85", "76.09", "86.05", "87.50"],
    "NCL": ["115.10", "115.04", "122.43", "131.17", "136.15", "139.00"],
    "WCL": ["57.60", "50.00", "57.70", "64.28", "69.11", "68.50"],
    "SECL": ["150.60", "146.20", "142.51", "167.01", "187.38", "167.50"],
    "MCL": ["148.01", "148.00", "168.17", "193.26", "206.10", "225.17"],
}
CIL_TOTAL = ["622.63", "622.63", "622.63", "703.20", "773.65", "781.06"]
CIL_TOTAL[0] = "602.14"
CIL_TOTAL[1] = "596.22"

# SECL Korba mega trio, MT (Gevra first 50 MT mine, FY22-23).
KORBA_TRIO = {
    "Gevra OCP": ["38.20", "40.10", "41.46", "52.50", "59.11", "55.80"],
    "Kusmunda OCP": ["34.50", "36.20", "38.90", "44.80", "46.30", "45.10"],
    "Dipka OCP": ["30.10", "31.40", "33.80", "37.60", "38.40", "37.90"],
}

# MCL featured OCPs, MT (five-year hand-checkable series).
MCL_PROD = {
    "Lakhanpur OCP": ["18.20", "19.45", "20.10", "21.65", "22.80"],
    "Ananta OCP": ["12.40", "12.85", "13.60", "13.15", "14.20"],
    "Lingaraj OCP": ["15.00", "15.90", "16.40", "17.20", "17.85"],
}
MCL_YEARS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]

# NCL mines, lakh tonnes (six-year series; offtake two-year).
NCL_PROD = {
    "Jayant OCP": [172.5, 178.0, 184.6, 190.2, 196.8, 201.5],
    "Nigahi OCP": [180.4, 186.1, 191.7, 197.3, 203.0, 208.6],
    "Dudhichua OCP": [142.8, 147.5, 152.9, 158.4, 163.1, 168.7],
    "Amlohri OCP": [96.3, 99.8, 103.2, 106.9, 110.4, 114.0],
}
NCL_YEARS = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]
NCL_OFFTAKE = {
    "Jayant OCP": [195.4, 200.1],  # CONFLICT: ops note says 197.9 for 2022-23
    "Nigahi OCP": [201.8, 207.2],
    "Dudhichua OCP": [161.9, 167.5],
    "Amlohri OCP": [109.6, 113.2],
}

# CCL flagship OCPs, MT.
CCL_PROD = {
    "Ashoka OCP": ["9.80", "10.20", "11.40", "12.60", "13.90", "14.20"],
    "Piparwar OCP": ["7.40", "7.10", "7.90", "8.60", "9.30", "9.50"],
    "Magadh OCP": ["6.20", "6.80", "8.10", "9.40", "10.80", "11.20"],
    "Amrapali OCP": ["5.10", "5.60", "7.20", "8.90", "10.20", "10.60"],
}

# WCL areas, MT.
WCL_PROD = {
    "Umrer Area": ["12.40", "11.20", "12.80", "14.10", "15.20", "15.00"],
    "Kamptee Area": ["8.60", "7.40", "8.20", "9.00", "9.60", "9.40"],
    "Chandrapur Area": ["10.20", "9.10", "10.40", "11.30", "12.10", "11.90"],
    "Wardha Area": ["7.80", "6.90", "7.60", "8.20", "8.70", "8.50"],
}

# ECL areas, MT.
ECL_PROD = {
    "Rajmahal Area": ["12.10", "10.40", "10.20", "11.30", "15.40", "16.10"],
    "Sonepur Bazari Area": ["8.20", "7.10", "7.30", "8.00", "10.20", "10.50"],
    "Kunustoria Area": ["4.60", "4.10", "3.90", "4.20", "5.30", "5.40"],
}

# CMPDI drilling, lakh metres (Ministry exploration chapter).
DRILL_NONCIL = ["7.88", "7.70", "4.28", "2.58", "4.29"]
DRILL_CILBLOCKS = ["5.80", "5.45", "3.98", "3.58", "3.80"]
DRILL_YEARS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]

# Geological resources of coal, billion tonnes (GSI inventory 01.04.2023).
RESOURCES_TOTAL = "378.21"
RESOURCES_SPLIT = [("Measured", "199.90"), ("Indicated", "151.68"), ("Inferred", "26.63")]
RESOURCES_STATES = [
    ("Odisha", "94.52"), ("Jharkhand", "87.84"), ("Chhattisgarh", "80.77"),
    ("West Bengal", "33.93"), ("Madhya Pradesh", "32.22"), ("Telangana", "23.19"),
    ("Maharashtra", "13.34"),
]

# CIL overall OMS, tonnes (Ministry productivity tables).
OMS_YEARS = ["2017-18", "2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]
OMS_OVERALL = ["7.44", "8.51", "8.53", "9.02", "9.56", "12.80", "13.43"]
OMS_UG = ["0.86", "0.95", "0.99", "0.93", "0.97", "1.05", "1.18"]
OMS_OC = ["13.15", "14.68", "14.25", "15.09", "15.46", "22.04", "25.43"]

# CIL fatal accidents / fatalities, calendar year (DGMS-conformant reporting).
FATAL_ACC = ["27", "18", "26", "22"]
FATALITIES = ["29", "20", "29", "24"]
ACC_YEARS = ["2021", "2022", "2023", "2024"]
ACC_COMPANY = [  # company, fatal accidents 21-24, fatalities 21-24
    ("ECL", ["7", "2", "4", "4"], ["8", "2", "4", "5"]),
    ("BCCL", ["2", "4", "5", "0"], ["3", "5", "6", "0"]),
    ("CCL", ["1", "2", "4", "3"], ["1", "2", "4", "3"]),
    ("NCL", ["3", "1", "2", "5"], ["3", "1", "2", "6"]),
    ("WCL", ["6", "1", "2", "1"], ["6", "2", "2", "1"]),
    ("SECL", ["7", "8", "3", "6"], ["7", "8", "3", "6"]),
    ("MCL", ["1", "0", "6", "3"], ["1", "0", "8", "3"]),
]

# First Mile Connectivity (PIB, Ministry).
FMC_ROLLOUT = [  # FY, projects, capacity MTY
    ("2025-26", "11", "88"), ("2026-27", "12", "102"), ("2027-28", "15", "201"),
    ("2028-29", "18", "229"), ("2029-30", "2", "42"),
]

# Mission Coking Coal: all-India coking output MT + 8 new washeries (MTPA, FY, state).
COKING_YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
COKING_OUT = ["44.79", "46.60", "54.63", "60.43", "66.47"]
WASHERIES_NEW = [
    ("Bhojudih", "2.0", "2025-26", "West Bengal", "Under construction"),
    ("Patherdih II", "2.5", "2026-27", "Jharkhand", "Under construction"),
    ("New Moonidih", "2.5", "2028-29", "Jharkhand", "Tendering"),
    ("New Kathara", "3.0", "2028-29", "Jharkhand", "Contract signed"),
    ("New Rajrappa", "3.0", "2029-30", "Jharkhand", "Intent issued"),
    ("Dhori", "3.0", "2029-30", "Jharkhand", "Tendering"),
    ("Basantpur-Tapin", "4.0", "2028-29", "Jharkhand", "Award issued"),
    ("New Sawang", "1.5", "2028-29", "Jharkhand", "Intent issued"),
]

# 1-billion-tonne roadmap: all-India plan totals + CIL share, MT.
ROADMAP_YEARS = ["2025-26", "2026-27", "2027-28", "2028-29", "2029-30"]
ROADMAP_TOTAL = ["1104", "1210", "1278", "1337", "1390"]
ROADMAP_CIL = ["875", "915", "950", "980", "1000"]
