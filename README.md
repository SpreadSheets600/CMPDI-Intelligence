# CMPDI Intelligence

**AI-Powered Geological, Mining & Reporting Solution for CMPDI/CIL Subsidiaries (SIH26023)**

An offline, evidence-first document intelligence platform: it turns scattered
geological, mining and production documents into a searchable, cross-validated
knowledge base where **every number, answer and generated report carries a
verifiable receipt back to its exact source** (document → page → table → row →
cell). 100% local — no API calls, no cloud, no data leaves the machine.

## What It Does

| Feature | Where |
|---|---|
| Ingest digital / scanned / mixed PDFs, DOCX, XLSX, CSV, images with live pipeline status | Ingest page |
| SHA-256 dedup + automatic document version chains (superseded revisions struck through) | Documents page |
| Source viewer: page images with element overlays, OCR confidence, spreadsheet grids | click any document |
| Hybrid retrieval: FTS5 BM25 + local embeddings + Reciprocal Rank Fusion | Search page |
| Grounded Q&A with per-claim citations, numeric fact lookup, and honest abstention | Ask page |
| **Conflict Radar**: documents disagreeing about the same fact, side by side, human-resolved | Conflict Radar |
| Word clouds, keyphrases and document clusters | Topics page |
| Template-driven DOCX reports where every figure has a receipt + Sources appendix | Report Studio |
| **Click-to-receipt**: any figure in a report opens the exact source page/sheet | Report Studio → viewer |

## Quickstart

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and either a
Tesseract install **or** nothing (RapidOCR is used automatically — models
download on first run).

```bash
uv venv
uv pip install -e .            # or: uv sync
.venv/bin/python -m cmpdi_intel.scripts.init_system
.venv/bin/python -m cmpdi_intel.scripts.make_demo_corpus    # optional demo data
.venv/bin/python -m cmpdi_intel.scripts.ingest demo_corpus  # process it

.venv/bin/python -m cmpdi_intel.web.app     # open http://127.0.0.1:5000
```

Then: drag files in on the Ingest page, watch the pipeline strip, ask a
question, click a citation, resolve a conflict, download a report.

## Configuration (environment variables, all optional)

| Variable | Default | Meaning |
|---|---|---|
| `CMPDI_LLM_BACKEND` | `auto` | `auto` \| `ollama` \| `transformers` \| `extractive` |
| `CMPDI_OLLAMA_MODEL` | `qwen3:4b` | Model when Ollama is running locally |
| `CMPDI_LLM_MODEL` | `Qwen/Qwen3-1.7B` | HF model for the raw Transformers backend |
| `CMPDI_EMBEDDING_MODEL` | `google/embeddinggemma-300m` | Gemma-3-family embeddings; auto-falls back to bge-small / MiniLM (e.g. when the Gemma model is HF-gated) |
| `CMPDI_OCR_MIN_CONF` | `85` | OCR word confidence below which digits are quarantined from reports |
| `CMPDI_DATA_DIR` | `./data` | SQLite DB + file store location |

**Backend resolution (`auto`)**: Ollama if running → cached HF model →
extractive mode (no generation: verbatim evidence + citations). The platform
never hard-depends on a generative model and never answers without evidence.

## Architecture

```
files → classify → parse (PyMuPDF/OCR/python-docx/openpyxl) → canonical model
      → normalize (Indian numbers, lakh/crore, units, FY Apr–Mar)
      → chunk (structure-aware, tables row-precise) → embed (local)
      → index (SQLite FTS5 BM25 + float32 vectors) → facts → conflicts
                                                                    ↓
        ask / search / reports / conflict radar / topics ← hybrid retrieval
```

Data flow golden rule: `answer/fact → chunk → element → page/sheet →
document → data/files/<sha256>/original.*`. SQLite (WAL) is the only
database; the filesystem is the object store; both are the source of truth —
the vector index is disposable and rebuildable.

## Verified End-to-End (demo corpus)

- 9-file demo corpus: digital PDF, revised PDF (auto version group), scanned
  PDF (OCR), mixed PDF (per-page OCR), multi-sheet XLSX (merged title cells,
  two tables per sheet), CSV, parliamentary DOCX, exact duplicate (rejected),
  corrupt file (clean failure with reason).
- Planted conflict detected and surfaced: Kusunda Mine FY2021-22 production —
  scanned report says 4.35 MT, workbook says 48.5 lakh tonnes (4.85 MT) —
  both linked to their exact sources.
- Numbers normalize correctly: `1,23,456.78`, `12.5 lakh tonnes`, `3.2 MT`,
  `FY22` → absolute values + Indian fiscal-year starts (April).

## Known Limitations (MVP)

- Single-user, no authentication.
- OCR quality on badly degraded scans limits fact extraction (low-confidence
  digits are flagged rather than trusted).
- Table detection targets ruled tables (typical of official reports);
  borderless-table layouts are best-effort.
- Knowledge-graph visualization and chart-image data extraction are deferred.
