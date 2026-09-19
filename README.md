# CMPDI Intelligence

Offline document intelligence for geological, mining, and production reporting
(SIH26023). Upload PDFs, spreadsheets, Word files, and scans — ask questions,
compare sources, and generate reports where **every number carries a receipt**
back to its document, page, table row, or spreadsheet cell.

Runs on one machine. No cloud, no external API calls, no data leaving the
premises. Works with no generative LLM installed (extractive mode).

## Capabilities

| Area | What it does |
|---|---|
| Ingest | Multi-format pipeline (digital / scanned / mixed PDFs, DOCX, XLSX, CSV, images) with per-page OCR decisions and live job status |
| Search | Hybrid lexical + semantic retrieval with filters (type, subsidiary, tag, reporting period) |
| Ask | Grounded Q&A with per-claim citations, conflict notes, and honest abstention; analytical questions run sandboxed Python (pandas, charts) |
| Verify | Conflict Radar for disagreeing values, two-document compare, evidence-quality grades, human report review |
| Report | DOCX generation (production summary, comparative analysis, parliamentary reply) with sources appendix |
| Explore | Knowledge graph, asset/mine profiles, fact explorer, timelines + forecasts, topics and word clouds |

Full tour: [`docs/`](docs/README.md) · Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Quickstart

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and Node.js.

```bash
./run.sh            # setup + demo corpus + app on http://127.0.0.1:5000
./run.sh --fresh    # wipe data/ and start over
./run.sh --no-llm   # skip Ollama; run in extractive mode
```

Manual setup and configuration: [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

> First run downloads the embedding and OCR models. After that, everything
> works offline.

## Provenance guarantee

```text
answer / report → fact → chunk → element / cell → page / sheet → document → original file
```

Conflicting sources are shown side by side, never silently merged.
Low-confidence OCR digits are quarantined, not trusted. Superseded revisions
stay visible but are excluded from answers.

## Limitations

- Single-user; no logins (decisions are attributed via operator name, and
  mutating API calls can be gated with `CMPDI_API_TOKEN`).
- Heavily degraded scans reduce fact extraction quality; low-confidence
  digits are flagged rather than trusted.
- Table detection targets ruled tables, which official reports use;
  borderless layouts are best effort.
- Documents ingested before the tag/enrichment upgrade need
  `python -m backend.scripts.reindex` to gain tags and enriched embeddings.
