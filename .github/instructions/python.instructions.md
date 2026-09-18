---
description: 'Backend Python standards for CMPDI Intelligence: Flask, SQLAlchemy, SQLite, Ruff, offline-first evidence engineering'
applyTo: 'backend/**/*.py'
---

# Backend Python Development

Offline-first document intelligence backend. Python 3.11+, Flask 3, SQLAlchemy 2 over a single SQLite file (WAL mode). No network calls anywhere.

## General Instructions

- Prefer the standard library; check existing modules before adding helpers or dependencies.
- Keep functions small with one responsibility; use domain modules (`pipeline/`, `facts/`, `retrieval/`, `reporting/`), never a generic `utils.py`.
- Reuse before extending before creating: `reuse → extend → refactor → new abstraction`.
- Never silently modify source data: always preserve raw value, normalized value, source, provenance, confidence.

## Best Practices

- Database access goes through `backend.db.database`: `db.q(sql, params)`, `db.q1(sql, params)`, `db.execute(sql, params)` with `?` placeholders. Rows are `CleanRow` dicts (NaN already sanitized to null for JSON).
- Use explicit short transactions, batch bulk ingestion, add indexes for frequently queried fields, avoid N+1 queries.
- New tables need three coordinated changes: ORM model in `backend/db/models.py`, DDL in `backend/db/schema.sql`, and seeding/migration handling (`Base.metadata.create_all` covers new tables on existing DBs).
- Handle expected failures explicitly with context (`logger.exception(..., extra={...})`); reserve broad `except Exception` for genuine system boundaries (worker loops, request handlers), always logging.
- Indian domain formats are load-bearing: lakh/crore, `1,23,456` grouping, fiscal years starting April, unit normalization (MT, lakh tonnes, GCV, %). Never drop the raw string.

## Code Standards

- Format with `ruff format`, lint with `ruff check`; type-annotate public functions, service interfaces, and API boundaries.
- Name things with domain terms (`normalized_value`, `source_document`, `conflict_records`, `evidence_chain`); never `data`, `tmp`, `x`, `info`.
- Comments explain why, never what. Docstrings only for public interfaces and non-obvious domain operations.

## Validation

- Build: `python -m backend.scripts.init_system`
- Format: `ruff format --check .` Lint: `ruff check .`
- Verify normal, empty, invalid, and missing-data inputs; confirm no existing behavior changed via `git diff`.
