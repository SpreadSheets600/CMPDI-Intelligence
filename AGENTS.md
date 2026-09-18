# CMPDI Intelligence — Agent Engineering Guide

## 1. Project Identity

CMPDI Intelligence is an offline-first intelligence and reporting platform for geological, mining, production and administrative information used by CMPDI/CIL subsidiaries. It is not a generic PDF chatbot: it transforms heterogeneous documents into a structured, traceable knowledge layer supporting document ingestion and processing, OCR and structured extraction, domain-aware normalization, hybrid retrieval, numeric fact extraction, cross-document validation, conflict detection, grounded Q&A, topic and word-cloud analysis, analytical data processing, automated report generation, and evidence-backed operational intelligence.

The central principle:

> Every important piece of derived information must be traceable back to the original evidence.

Any answer, chart, statistic or report value must trace `answer/report → fact/evidence → chunk → element/table cell → page/sheet → document → original file`. Prefer evidence and deterministic computation over model output. The system runs locally and stays useful with no generative LLM available.

---

## 2. Product Direction

Development is incremental: the developer supplies one feature at a time — implement it completely, integrate it, validate it, stop. Never build the whole roadmap at once, and never implement P1/P2/P3 work for interest while a P0 feature is unfinished.

### P0 — MVP (the working product)

Multi-format ingestion, file classification, canonical document representation, PDF/DOCX/XLSX/CSV/image extraction, OCR, domain normalization, structure-aware chunking, embeddings, hybrid retrieval, numeric fact extraction, provenance, grounded Q&A, Conflict Radar, automated reports, human review, Source Viewer, pipeline dashboard, topics and word clouds, analytical agent, demonstration corpus.

### P1 — Operational Intelligence

Organization/entity context, entity resolution, knowledge graph, asset/mine intelligence, cross-report comparison, version/change detection, temporal intelligence, organizational insight dashboards, investigation workflows, cross-source validation, knowledge-gap detection, AI-assisted investigation.

### P2 — Advanced Intelligence (must not destabilize P0/P1)

Anomaly detection, trend analysis, forecasting, root-cause analysis, multimodal geological analysis, chart-to-data extraction, advanced evidence-quality analysis, advanced natural-language analytics, additional intelligence workflows.

### P3 — Experimental (never dependencies of the core system)

Custom ML/entity-recognition/anomaly/predictive models, autonomous insight generation, experimental knowledge-graph models, other AI research.

---

## 3. Operating Principle

Act as a senior engineer inside an existing production-oriented codebase, not a code generator. Before writing code: understand the feature, read the relevant docs, inspect the existing implementation, reuse existing abstractions, place the change in the correct layer, map data flow, enumerate failure modes, plan small, implement only the requested scope, validate, format/lint, review the diff, commit cleanly.

Do not rewrite working systems for elegance, introduce architecture the existing design cannot justify, or duplicate functionality. Do not invent architecture, APIs, database fields, or requirements — inspect the repo first. Be decisive; say so when evidence is insufficient; prefer deterministic solutions.

---

## 4. Repository Investigation

For every feature, inspect before modifying: repository structure, the relevant subsystem's implementation, data models, service layer, API routes, frontend components, utilities, configuration, database schema, existing tests/verification scripts, related documentation. Search for existing functionality first. Prefer `reuse → extend → refactor → create new abstraction`, in that order. Never create an abstraction merely because an existing name is imperfect.

---

## 5. Implementation Method

**Understand.** What problem is solved? Who uses it? What data does it consume/produce? Where does the data come from? Where is the result stored? Which subsystem owns it? What must explicitly NOT change?

**Architect.** Assign backend, frontend, database, API, model/service, retrieval, agent/tool, and UI-state responsibilities. No business logic in UI components, no presentation logic in data modules, no heavy domain computation in route handlers.

**Implement.** The smallest complete version. No speculative features, no abstractions for hypothetical futures.

**Validate.** Normal, empty, invalid, and missing inputs; unexpected types; duplicates; failure behavior; performance-sensitive paths; provenance preservation; API response shape; UI loading/error states. A feature is complete only when backend and frontend behavior work, data flow is correct, errors are handled, provenance is preserved, performance is reasonable, conventions are followed, code is formatted/linted, validation passes, the diff is clean, and the feature is demonstrable end-to-end. If it cannot be demonstrated, it is not complete.

**Quality pass.** Run Ruff, relevant checks, the subsystem where practical. Inspect the diff; remove unrelated or unnecessary changes; check naming, imports, formatting, error handling, and that existing behavior is untouched.

---

## 6. Python Standards

Write readable, typed-where-useful, modular, explicit code. Optimize only on evidence (complexity, I/O, repeated queries, serialization, inference, memory, network, filesystem); prefer simple over clever. Small single-responsibility functions; domain-specific modules (`pipeline/classify.py`, `facts/extract.py`, `retrieval/fusion.py`); no giant functions, deep nesting, hidden globals, metaprogramming, or `utils.py` dumping grounds. Extract a helper at the third duplication, not the first.

Annotate public functions, service interfaces, API boundaries, classes, and non-obvious returns — API endpoints and Pydantic models especially. Skip noise annotations on obvious internals.

Ruff is the only formatter/linter: `ruff format .`, `ruff check .`, `ruff format --check .`. Never fight it, never add a second formatter, never reformat unrelated files, never scatter `# noqa` — keep exceptions local and explained.

Readable spacing: readability beats line count — separate conceptual stages with blank lines; no random whitespace, no dense unrelated blocks. Comments explain intent, constraints, and decisions, never the obvious; docstrings for public classes/interfaces, complex domain operations, and external APIs — not one-liners on private helpers. Name descriptively with domain terms (`normalized_value`, `source_document`, `conflict_records`, `evidence_chain` — never `data`, `tmp`, `x`, `info`); one concept keeps one name (`Fact` stays `Fact`).

---

## 7. Errors, Integrity, Provenance

Errors must carry context: catch specific exceptions, log with identifiers, re-raise. Broad handling only at genuine boundaries (worker loops, request handlers, job execution). A failed document must never crash the pipeline; record enough to diagnose.

The system is evidence-first. Never silently modify source information — preserve raw value, normalized value, source, provenance, confidence, and transformations. Never silently pick one conflicting value; represent conflicts explicitly:

```text
"Source A reports 12.4 MT. Source B reports 13.1 MT. These values conflict."
```

Every derived value keeps its chain: `answer/report → fact/evidence → chunk → element/table cell → page/sheet → document → original file`. Never break it without recording why elsewhere — this defines the product.

---

## 8. Database

SQLite (WAL) is primary. Prefer parameterized queries, explicit short write transactions, indexes on hot fields, batch bulk operations, deterministic migrations. Avoid N+1 queries; filter in SQL rather than loading corpora into Python; fetch only needed columns/rows for analytics.

---

## 9. API Rules

Routes stay thin: validate input → call the service → return the result (`Route → Service → Repository/Domain → Database/Storage`). Use Pydantic models for request/response contracts — they provide validation, serialization, and docs. Keep response structures stable; changing a contract means updating frontend and backend together.

---

## 10. React Rules

React owns presentation, interaction, and client-side state: `Page ├── Header, FilterBar, Content (Chart, Table, InsightCard), DetailPanel` — never one enormous component. No API clients, business rules, or large transforms in components; shared logic goes in hooks/services. Store minimum state (derive the rest); keep server state separate from UI state; no Redux without demonstrated need.

For data-heavy screens: paginate/virtualize, memoize only when justified, aggregate on the backend, skip unused fields — but measure before optimizing. UI communicates: hierarchy first, important changes obvious, no excessive cards or animations, units labeled, actual vs derived values distinguished, evidence shown, loading/empty/error states everywhere. Every visualization answers a question — never decorate empty space.

---

## 11. Analytics and Agents

Correctness beats visual complexity. For trends, anomalies, comparisons, distributions, statistics, forecasts, correlations, define input dataset, grain, metric, filters, time range, aggregation, calculation, and interpretation — computed with Python/Pandas/NumPy, never invented by the LLM. The LLM interprets results and writes narrative. Exact lookup → fact index; aggregation → Python; filtering → query layer; charts → matplotlib; semantics → retrieval; comparison → structured diff. If evidence is insufficient, say so.

Agent tools (`search_documents`, `get_facts`, `run_python`) are purposeful: know the missing info, the right tool, its arguments, and expected output. Never repeat fruitless calls or redo cached deterministic results. Sandbox code: Pandas/NumPy/matplotlib, no filesystem or network access unless the tool provides it, reproducible, structured results plus charts, verifiable by another developer.

Reports are evidence-backed artifacts assembled as Question → Fact Retrieval → Semantic Retrieval → Validation → Conflict Detection → Assembly → Provenance → Human Review → Final. Never pure LLM text when facts exist; every important number has a source.

---

## 12. Performance, Dependencies, Configuration

Prefer batching, caching, vectorization, indexed queries, lazy loading, streaming, bounded concurrency, and avoiding duplicate model calls/parsing/serialization. No premature multiprocessing, async, microservices, or cleverness without evidence. Keep the project understandable.

Before adding a dependency: check stdlib, then existing deps; weigh size, offline operation, maintenance, deployment. Never add one for trivial functionality or duplicate responsibilities.

Configuration lives in env/config files, not scattered constants (model names, paths, thresholds, URLs, flags, limits) — unless genuinely fixed architectural constants.

---

## 13. Git Workflow

One focused branch per feature, never work on `main`:

```bash
git status
git checkout main
git pull
git checkout -b feature/<short-name>   # e.g. feature/conflict-radar, fix/ocr-confidence
```

Small logical commits in Conventional Commit style (`feat:`, `fix:`, `refactor:`, `perf:`, `docs:`, `chore:`, `test:`); separate DB/API/UI/test commits when clearer, never microscopic or bundled-unrelated ones. Subjects describe intent (`feat: add conflict radar`), never `update`, `changes`, `stuff`, `final`, `fixes`, `done`, `work`, or `implemented feature`.

Every change must reach the website as a pull request so it is visible and reviewable — local-only merges are not done:

```bash
git push -u origin feature/<short-name>
gh pr create --base main --head feature/<short-name> \
  --title "<type>: <concise description>" \
  --body "What changed, how it was validated, and what to check in review."
```

Before opening the PR: feature works, formatting/linting/tests pass, diff inspected, no unrelated files, docs updated if needed, branch synced with `main`. Use meaningful merge messages (`Merge feature/insight-dashboard: add operational intelligence dashboard`) or a clean squash commit. After merging on the website: `git checkout main && git pull && git branch -d feature/<name>`. No abandoned branches.

Definition of done:

```text
UNDERSTAND → INSPECT → PLAN → BRANCH → IMPLEMENT → VALIDATE
  → RUFF FORMAT → RUFF CHECK → REVIEW DIFF → COMMIT
  → PUSH → PR (website) → MERGE → PULL → CLEAN BRANCH
```

---

## 14. Scope Control

When asked to build something (e.g. "Build the Insight Dashboard"), do not redesign the application: understand the requirement, identify needed APIs/data, implement only what it requires on existing infrastructure, build the UI, validate, stop. Park side ideas as future work.

This is a hackathon/MVP product: no auth/RBAC, Kubernetes, microservices, queues, distributed databases, or cloud orchestration unless explicitly requested. Infrastructure complexity is not a feature.

The product is an evidence-first intelligence platform turning scattered mining information into searchable, validated organizational knowledge. Never morph it into a generic chatbot, document manager, BI dashboard, RAG demo, or writing assistant — the intelligence layer is the product.

---

## 15. Path-Scoped Copilot Instructions

`.github/instructions/` holds per-stack guidance consumed by GitHub Copilot (frontmatter `description` + `applyTo` glob per file):

* `python.instructions.md` — backend Python (Flask, SQLAlchemy, SQLite, Ruff, offline-first)
* `react.instructions.md` — React frontend (Vite, Tailwind, Motion, Lucide, receipt-linked UI)
* `api.instructions.md` — Flask JSON API conventions (thin Blueprints, stable shapes)
* `analytics.instructions.md` — deterministic analytics (pandas computation, evidence-first signals)

Keep them concise, imperative, and repo-specific; they restate this guide's rules per stack, never contradict it. This guide remains authoritative — update both together when conventions change.
