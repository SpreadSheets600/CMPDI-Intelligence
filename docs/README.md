# Documentation Map

Start here. Each guide is scoped to one subsystem and links to the code that
owns it. Read top-down for a full tour, or jump to the layer you need.

## Study path

| Order | Guide | What you will learn | Key code |
|---|---|---|---|
| 1 | [ARCHITECTURE.md](ARCHITECTURE.md) | System overview, request path, storage layout | `backend/app/__init__.py`, `backend/api/__init__.py` |
| 2 | [DATA_MODEL.md](DATA_MODEL.md) | SQLite schema, provenance chain, file store | `backend/db/models.py`, `backend/storage/__init__.py` |
| 3 | [PIPELINE.md](PIPELINE.md) | Ingestion: classify → parse → OCR → chunk → embed → index → summarize | `backend/core/pipeline/` |
| 4 | [RETRIEVAL.md](RETRIEVAL.md) | Hybrid search, grounded Q&A, abstention, org search | `backend/core/retrieval/` |
| 5 | [KNOWLEDGE.md](KNOWLEDGE.md) | Facts, Conflict Radar, compare, graph, assets, topics, temporal | `backend/core/knowledge/`, `backend/core/conflicts.py` |
| 6 | [AGENT_AND_REPORTS.md](AGENTS-REPORTS.md) | Analytical agent, sandbox, report engines, review gate | `backend/core/llm/`, `backend/core/reporting/` |
| 7 | [FRONTEND.md](FRONTEND.md) | SPA routes, data hooks, layout, theme, dev/prod serving | `frontend/src/` |
| 8 | [OPERATIONS.md](OPERATIONS.md) | Setup, configuration, scripts, demo corpus, troubleshooting | `run.sh`, `backend/scripts/`, `.env.example` |

## Reference (not tutorials)

- [agent/](agent/) — editable capability guides (`statistics.md`, `charts.md`)
  loaded into the agent's system prompt. Change these to change agent behavior
  without touching code.
- [PLAN.md](PLAN.md) — the original MVP build plan. Historical record; it no
  longer tracks the implementation (e.g. it specifies server-rendered Flask
  templates, while the product is now a React SPA).
- [AGENTS.md](AGENTS.md) — generic engineering workflow for AI contributors.
  The product-specific contributor rules live in the repo-root `AGENTS.md`.
- Repo root [README.md](../README.md) — concise product overview + quickstart.
- Per-stack Copilot guidance: `.github/instructions/` (repo root).

## The one principle behind everything

```text
answer / report → fact → chunk → element / table cell → page / sheet
  → document → data/files/<sha256>/original.*
```

Every guide below traces its layer back to this chain. If a feature cannot
show its receipt, it is unfinished — see [DATA_MODEL.md](DATA_MODEL.md).
