"""Curated public reference data for organizational entities.

Offline-first by design: this is a versioned, locally bundled snapshot of
trustworthy public information (subsidiary profiles, operating geography,
dated production and sector statistics), not a live web connector. The
project must stay useful with no network, so "external knowledge" ships
with the app and is refreshed by editing this file.

Every row carries its public source and, for dated figures, an as-of
marker. Rows are reference context only: ``reference.py`` stores them in
``entity_reference`` and they must never enter the fact index, conflicts,
answers or reports.

Production figures are rounded to one decimal from Ministry of Coal annual
report tables so minor inter-report revisions do not read as disagreements.
"""

# category -> entity abbreviation -> rows
ENTRIES: dict[str, list[dict]] = {
    "CIL": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "Coal India Limited (Maharatna)",
            "source": "coalindia.in — CIL official site",
        },
        {
            "category": "profile",
            "label": "Headquarters",
            "value": "Kolkata, West Bengal",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
        {
            "category": "profile",
            "label": "Formation",
            "value": "Formed November 1975 as a holding company; 79 MT production at inception",
            "source": "coalindia.in — CIL official site",
        },
        {
            "category": "geography",
            "label": "Operating states",
            "value": "Eight Indian states, 84 mining areas",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
        {
            "category": "production",
            "label": "Coal production FY 2023-24",
            "value": "773.7",
            "unit": "MT",
            "as_of": "FY 2023-24",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
        {
            "category": "production",
            "label": "Coal production FY 2024-25",
            "value": "781.1",
            "unit": "MT",
            "as_of": "FY 2024-25",
            "source": "Ministry of Coal, Annual Report 2025-26",
        },
        {
            "category": "statistic",
            "label": "Share of domestic coal production",
            "value": "~75% of domestic coal production; ~40% of primary commercial energy",
            "source": "coalindia.in — CIL official site",
        },
        {
            "category": "statistic",
            "label": "Working mines",
            "value": "313 (131 underground, 168 opencast, 14 mixed)",
            "as_of": "1 April 2024",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
        {
            "category": "statistic",
            "label": "Manpower",
            "value": "228861",
            "as_of": "1 April 2024",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
    ],
    "ECL": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "Eastern Coalfields Limited (CIL producing subsidiary)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "profile",
            "label": "Headquarters",
            "value": "Sanctoria, Asansol, West Bengal",
            "source": "easterncoal.nic.in — ECL official site",
        },
        {
            "category": "geography",
            "label": "Operating states",
            "value": "West Bengal, Jharkhand",
            "source": "ECL public tender record (ICCC bid)",
        },
        {
            "category": "geography",
            "label": "Major coalfields",
            "value": "Raniganj, Mugma, Rajmahal, Saharjuri",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "production",
            "label": "Coal production FY 2023-24",
            "value": "47.6",
            "unit": "MT",
            "as_of": "FY 2023-24",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
    ],
    "BCCL": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "Bharat Coking Coal Limited (CIL producing subsidiary)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "profile",
            "label": "Headquarters",
            "value": "Dhanbad, Jharkhand",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "geography",
            "label": "Operating states",
            "value": "Jharkhand (primarily), West Bengal (part)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "geography",
            "label": "Major coalfields",
            "value": "Jharia (coking coal), Raniganj (part)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "production",
            "label": "Coal production FY 2023-24",
            "value": "41.1",
            "unit": "MT",
            "as_of": "FY 2023-24",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
    ],
    "CCL": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "Central Coalfields Limited (CIL producing subsidiary)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "profile",
            "label": "Headquarters",
            "value": "Ranchi, Jharkhand",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "geography",
            "label": "Operating states",
            "value": "Jharkhand",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "geography",
            "label": "Major coalfields",
            "value": "East Bokaro, West Bokaro, Ramgarh, North Karanpura, South Karanpura, Giridih",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "production",
            "label": "Coal production FY 2023-24",
            "value": "86.1",
            "unit": "MT",
            "as_of": "FY 2023-24",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
    ],
    "NCL": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "Northern Coalfields Limited (CIL producing subsidiary)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "profile",
            "label": "Headquarters",
            "value": "Singrauli, Madhya Pradesh",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "profile",
            "label": "Formation",
            "value": "Formed 28 November 1985",
            "source": "coal.nic.in — Ministry of Coal, Agencies under Ministry",
        },
        {
            "category": "geography",
            "label": "Operating states",
            "value": "Madhya Pradesh, Uttar Pradesh",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "geography",
            "label": "Major coalfields",
            "value": "Singrauli",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "production",
            "label": "Coal production FY 2023-24",
            "value": "136.1",
            "unit": "MT",
            "as_of": "FY 2023-24",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
    ],
    "WCL": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "Western Coalfields Limited (CIL producing subsidiary)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "profile",
            "label": "Headquarters",
            "value": "Nagpur, Maharashtra",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "geography",
            "label": "Operating states",
            "value": "Maharashtra, Madhya Pradesh",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "geography",
            "label": "Major coalfields",
            "value": "Nagpur (Kamptee), Umrer, Wardha Valley, Pench-Kanhan, Pathakhera",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "production",
            "label": "Coal production FY 2023-24",
            "value": "69.1",
            "unit": "MT",
            "as_of": "FY 2023-24",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
    ],
    "SECL": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "South Eastern Coalfields Limited (CIL producing subsidiary)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "profile",
            "label": "Headquarters",
            "value": "Bilaspur, Chhattisgarh",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "profile",
            "label": "Formation",
            "value": "Formed 28 November 1985",
            "source": "coal.nic.in — Ministry of Coal, Agencies under Ministry",
        },
        {
            "category": "geography",
            "label": "Operating states",
            "value": "Chhattisgarh, Madhya Pradesh",
            "source": "CIL company profile filing (85 mines: 52 CG, 33 MP)",
        },
        {
            "category": "geography",
            "label": "Major coalfields",
            "value": "Korba, Raigarh, Sohagpur, Hasdeo-Arand, Chirimiri",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "production",
            "label": "Coal production FY 2023-24",
            "value": "187.4",
            "unit": "MT",
            "as_of": "FY 2023-24",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
        {
            "category": "statistic",
            "label": "Gevra opencast mine FY 2023-24",
            "value": "59 MT produced (70 MTPA capacity), Korba district — among the world's largest coal mines",
            "as_of": "FY 2023-24",
            "source": "PIB release, Ministry of Coal, 18 Jul 2024",
        },
        {
            "category": "statistic",
            "label": "Kusmunda opencast mine FY 2023-24",
            "value": "50+ MT produced, Korba district — second Indian mine past 50 MT",
            "as_of": "FY 2023-24",
            "source": "PIB release, Ministry of Coal, 18 Jul 2024",
        },
    ],
    "MCL": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "Mahanadi Coalfields Limited (CIL producing subsidiary)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "profile",
            "label": "Headquarters",
            "value": "Sambalpur, Odisha",
            "source": "coal.nic.in — Ministry of Coal, Agencies under Ministry",
        },
        {
            "category": "profile",
            "label": "Formation",
            "value": "Incorporated 3 April 1992 to manage Talcher and IB Valley coalfields",
            "source": "coal.nic.in — Ministry of Coal, Agencies under Ministry",
        },
        {
            "category": "geography",
            "label": "Operating states",
            "value": "Odisha",
            "source": "coal.nic.in — Ministry of Coal, Agencies under Ministry",
        },
        {
            "category": "geography",
            "label": "Major coalfields",
            "value": "Talcher, Ib Valley",
            "source": "coal.nic.in — Ministry of Coal, Agencies under Ministry",
        },
        {
            "category": "production",
            "label": "Coal production FY 2023-24",
            "value": "206.1",
            "unit": "MT",
            "as_of": "FY 2023-24",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
    ],
    "NEC": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "North Eastern Coalfields (CIL-managed unit, Assam)",
            "source": "coal.nic.in — Ministry of Coal, Agencies under Ministry",
        },
        {
            "category": "geography",
            "label": "Operating states",
            "value": "Assam (mines managed directly by CIL)",
            "source": "coal.nic.in — Ministry of Coal, Agencies under Ministry",
        },
        {
            "category": "geography",
            "label": "Major coalfields",
            "value": "Makum (Margherita)",
            "source": "CIL subsidiary public directory records",
        },
        {
            "category": "production",
            "label": "Coal production FY 2023-24",
            "value": "0.2",
            "unit": "MT",
            "as_of": "FY 2023-24",
            "source": "Ministry of Coal, Annual Report 2024-25",
        },
    ],
    "CMPDI": [
        {
            "category": "profile",
            "label": "Full name",
            "value": "Central Mine Planning & Design Institute Limited (CIL consultancy subsidiary, Mini Ratna)",
            "source": "cmpdi.co.in — CMPDI official site",
        },
        {
            "category": "profile",
            "label": "Headquarters",
            "value": "Ranchi, Jharkhand",
            "source": "cmpdi.co.in — CMPDI official site",
        },
        {
            "category": "profile",
            "label": "Role",
            "value": "Mine planning, design and consultancy for the coal sector (not a coal producer)",
            "source": "cmpdi.co.in — CMPDI official site",
        },
    ],
}

CATEGORIES = ("profile", "geography", "production", "statistic")
