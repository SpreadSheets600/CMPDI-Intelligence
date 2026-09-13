"""Central configuration. Everything is controlled by environment variables
with working defaults, so the system runs with zero setup. A `.env` file in
the project root is loaded first (real environment always wins)."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv():
    """Minimal .env loader (stdlib only): KEY=VALUE lines, # comments and
    quoted values handled, existing environment never overridden."""
    path = ROOT / ".env"
    try:
        text = path.read_text()
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def _abs(p: Path) -> Path:
    """Relative paths (e.g. CMPDI_DATA_DIR=./data from .env) resolve against
    the project root, never the process working directory. Relative paths
    otherwise break send_file (resolved against the app package) and any
    worker started from another directory."""
    return p if p.is_absolute() else ROOT / p


DATA_DIR = _abs(Path(os.environ.get("CMPDI_DATA_DIR", ROOT / "data")))
_db_default = DATA_DIR / "cmpdi.db"
DB_PATH = _abs(Path(os.environ.get("CMPDI_DB_PATH") or _db_default))

# Frontend assets served by the same process
FRONTEND_DIR = ROOT / "frontend"

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
# Canonical selector: ollama | huggingface | openai_compatible | auto | none.
# CMPDI_LLM_PROVIDER wins; CMPDI_LLM_BACKEND is kept for compatibility.
LLM_PROVIDER = os.environ.get("CMPDI_LLM_PROVIDER",
                              os.environ.get("CMPDI_LLM_BACKEND", "auto"))
OLLAMA_URL = os.environ.get("CMPDI_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("CMPDI_OLLAMA_MODEL", "gemma4:31b-cloud")
OLLAMA_TIMEOUT = float(os.environ.get("CMPDI_OLLAMA_TIMEOUT", "180"))
LLM_MODEL = os.environ.get("CMPDI_LLM_MODEL", "gemma4:31b-cloud")
# Hugging Face local generative model: identifier or local directory.
# Never downloaded automatically; must already be present locally.
HF_MODEL = os.environ.get("CMPDI_HF_MODEL", os.environ.get("CMPDI_LLM_MODEL", ""))
# OpenAI-compatible endpoint: any server speaking /chat/completions.
OPENAI_BASE_URL = os.environ.get("CMPDI_OPENAI_BASE_URL", "")
OPENAI_MODEL = os.environ.get("CMPDI_OPENAI_MODEL", "")
# API key comes from the environment only and is never persisted or logged.
OPENAI_API_KEY = os.environ.get("CMPDI_OPENAI_API_KEY", "")
OPENAI_TIMEOUT = float(os.environ.get("CMPDI_OPENAI_TIMEOUT", "60"))

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
