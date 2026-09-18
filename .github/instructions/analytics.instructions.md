---
description: 'Deterministic analytics for CMPDI Intelligence: pandas computation, evidence-first signals, sandboxed agent tools'
applyTo: 'backend/core/insights.py,backend/core/knowledge/**/*.py,backend/core/quality/**/*.py,backend/core/reporting/**/*.py,backend/core/retrieval/**/*.py'
---

# Deterministic Analytics Development

All trends, anomalies, comparisons, statistics, and report figures are computed deterministically in Python. The LLM interprets results and writes narrative; it never invents numbers.

## General Instructions

- For every analytical computation, define first: input dataset, grain, metric definition, filters, time range, aggregation, calculation, output interpretation.
- Prefer pandas for tabular work, NumPy for numerics, matplotlib for charts. No new dependencies for trivial helpers.
- Reuse shared conventions: MT scale normalization and the reporting window from `reporting.content`; current versions only for present-tense values; the raw `quantity` per-cell bucket is excluded from named metrics.
- Never silently pick one value when sources disagree: surface every value with its receipt and let the officer decide.

## Best Practices

- Tag every derived payload with its origin: `origin: "reference"` for curated public context, `origin: "evidence"` for library roll-ups. Reference rows must never enter the fact index, conflicts, answers, or reports.
- Bound every scan (`LIMIT`, top-N caps) and carry `doc_id` (plus page/sheet where a single point is shown) so the UI can link back to receipts.
- Thresholds and constants live at module top with a comment stating why; configuration that varies by environment belongs in env vars, not scattered literals.
- Agent sandbox tools (`search_documents`, `get_facts`, `run_python`) run in an isolated process with a time budget, preloaded pandas/numpy/matplotlib, `load_table()`/`load_facts()` readers, restricted builtins, and no filesystem or network access. Keep tool code verifiable by another developer.

## Validation

- Cover normal, empty-library, unknown-entity, and single-source cases with a throwaway script against an isolated `CMPDI_DATA_DIR`; assert payload shapes and provenance fields.
- Confirm empty inputs return empty lists (never crash) and invalid inputs return errors, not guesses.
