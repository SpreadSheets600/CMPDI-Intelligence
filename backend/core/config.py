"""Central configuration. Everything is controlled by environment variables
with working defaults, so the system runs with zero setup."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("CMPDI_DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("CMPDI_DB_PATH", DATA_DIR / "cmpdi.db"))

# Filesystem object store layout
FILES_DIR = DATA_DIR / "files"  # <sha256>/original.<ext>, page images, ocr artifacts
REPORTS_DIR = DATA_DIR / "reports"  # generated DOCX reports
CLOUDS_DIR = DATA_DIR / "clouds"  # rendered word-cloud PNGs

# Embeddings: primary is Gemma-3-family; fallbacks load automatically if the
# primary is unavailable (embeddinggemma is HF-gated and needs license acceptance).
EMBEDDING_MODEL = os.environ.get("CMPDI_EMBEDDING_MODEL", "google/embeddinggemma-300m")
EMBEDDING_FALLBACKS = [
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
]

# LLM backend: "auto" probes ollama, then transformers, then falls back to
# extractive mode (no generation, evidence snippets only).
LLM_BACKEND = os.environ.get("CMPDI_LLM_BACKEND", "auto")
OLLAMA_URL = os.environ.get("CMPDI_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("CMPDI_OLLAMA_MODEL", "gemma4:31b-cloud")
LLM_MODEL = os.environ.get("CMPDI_LLM_MODEL", "gemma4:31b-cloud")

# OCR
OCR_MIN_CONF = float(os.environ.get("CMPDI_OCR_MIN_CONF", "85"))
OCR_DPI = int(os.environ.get("CMPDI_OCR_DPI", "300"))
PAGE_TEXT_FLOOR = int(
    os.environ.get("CMPDI_PAGE_TEXT_FLOOR", "50")
)  # chars below this -> OCR the page

# Chunking
CHUNK_TOKENS = int(os.environ.get("CMPDI_CHUNK_TOKENS", "400"))
CHUNK_OVERLAP = int(os.environ.get("CMPDI_CHUNK_OVERLAP", "60"))

# Retrieval
RETRIEVAL_K = int(os.environ.get("CMPDI_RETRIEVAL_K", "8"))
RRF_K = int(os.environ.get("CMPDI_RRF_K", "60"))
VECTOR_DIM = int(os.environ.get("CMPDI_VECTOR_DIM", "0"))  # 0 = detect from model

# Conflict detection: relative difference above this (per unit) is a conflict
CONFLICT_TOLERANCE = float(os.environ.get("CMPDI_CONFLICT_TOLERANCE", "0.01"))

# Subsidiary gazetteer (CIL ecosystem)
SUBSIDIARIES = {
    "ECL": "Eastern Coalfields Limited",
    "BCCL": "Bharat Coking Coal Limited",
    "CCL": "Central Coalfields Limited",
    "NCL": "Northern Coalfields Limited",
    "WCL": "Western Coalfields Limited",
    "SECL": "South Eastern Coalfields Limited",
    "MCL": "Mahanadi Coalfields Limited",
    "NEC": "North Eastern Coalfields",
    "CMPDI": "Central Mine Planning & Design Institute",
    "CIL": "Coal India Limited",
}


def ensure_dirs():
    for d in (DATA_DIR, FILES_DIR, REPORTS_DIR, CLOUDS_DIR):
        d.mkdir(parents=True, exist_ok=True)
