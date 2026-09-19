# Operations

Run, configure, and troubleshoot the system. Everything runs on one machine;
after the first run (model downloads), the network cable can be pulled.

## Quickstart

Requires Python 3.11+ with [uv](https://docs.astral.sh/uv/) and Node.js.
OCR works out of the box via RapidOCR; a Tesseract install is used instead
when present.

```bash
./run.sh            # setup + demo corpus + app on http://127.0.0.1:5000
./run.sh --fresh    # wipe data/, re-ingest the demo corpus, start over
./run.sh --no-llm   # skip Ollama; answers use extractive mode
```

Manual equivalent:

```bash
uv venv && uv pip install -e .
cd frontend && npm install && npm run build && cd ..
python -m backend.scripts.init_system
python -m backend.scripts.make_demo_corpus
python -m backend.scripts.ingest data/demo_corpus
python -m backend.app
```

First ingestion downloads the embedding model. On machines without access to
the gated Gemma model it falls back to bge-small automatically.

## Configuration

All configuration is environment-driven (`.env` file, real env wins) with
working defaults; a subset is overridable at runtime via Settings
(`data/app_settings.json`). See `.env.example` and
`backend/core/config.py`.

| Variable | Default | Purpose |
|---|---|---|
| `CMPDI_LLM_PROVIDER` | `auto` | `auto`, `ollama`, `huggingface`, `openai_compatible`, `none` (Settings-overridable; legacy `CMPDI_LLM_BACKEND` honored) |
| `CMPDI_OLLAMA_MODEL` | `gemma4:31b-cloud` | Model when Ollama runs locally |
| `CMPDI_OLLAMA_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint |
| `CMPDI_HF_MODEL` | _(empty)_ | Local HF model id/directory (never auto-downloaded) |
| `CMPDI_OPENAI_BASE_URL` / `_MODEL` / `_API_KEY` | _(empty)_ | OpenAI-compatible endpoint; key is env-only, never persisted/logged |
| `CMPDI_EMBEDDING_MODEL` | `google/embeddinggemma-300m` | Embedding model, with automatic fallbacks |
| `CMPDI_RETRIEVAL_K` | `8` | Top-K results (Settings-overridable, 1–50) |
| `CMPDI_OCR_MIN_CONF` | `85` | OCR confidence below which digits are quarantined |
| `CMPDI_DATA_DIR` | `./data` | SQLite DB + file store location |

Provider resolution: Ollama (when the server answers) → OpenAI-compatible →
local HF → extractive. `HF_TOKEN` unlocks gated HF downloads.

## Scripts

| Command | Purpose |
|---|---|
| `python -m backend.scripts.init_system` | Create DB + folders, seed entities/reference, health summary |
| `python -m backend.scripts.make_demo_corpus` | Generate the curated demo corpus (digital + scanned + mixed PDFs, workbook, DOCX) |
| `python -m backend.scripts.ingest <dir>` | CLI ingest (warns if `:5000` is live — prefer the running app's worker) |
| `python -m backend.scripts.reindex` | Rebuild FAISS/tags/embeddings (needed for docs ingested before upgrades) |
| `python -m backend.scripts.eval_extraction` | Gold-set extraction-accuracy harness |
| `python -m backend.scripts.llm_check` | Probe the configured LLM backend |

Real documents (e.g. annual-report chapters, statistics workbooks) can be
dropped into `samples/` and ingested with the same `ingest` command.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Empty answers on a fresh machine | Embedding model still downloading; wait for first ingestion to finish |
| `ollama → transformers → extractive` fallback badge | No generative backend reachable; run `./run.sh` (starts Ollama) or accept extractive mode |
| Stale tags / missing embeddings on old docs | `python -m backend.scripts.reindex` |
| Port 5000 busy | `run.sh` kills the stale listener automatically; check `lsof -iTCP:5000` otherwise |
| Frontend shows old UI after changes | Rebuild: `cd frontend && npm run build`, restart Flask |
| Heavily degraded scans, few facts | Expected: low-confidence digits are quarantined, not trusted — see [PIPELINE.md](PIPELINE.md) |

Known limitations: single-user with no auth; ruled-table detection (official
reports) with borderless layouts best-effort; `PORT` / `OLLAMA_MODEL` are
`run.sh`-only overrides.
