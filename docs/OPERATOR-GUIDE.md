# Operator Guide

Running CMPDI Intelligence as a pilot in a subsidiary: who does what,
how review works, and how the numbers on the dashboard become trustworthy.

## Roles

The box is single-user by design (no logins). Accountability comes from
**attribution**, not authentication:

- Set `CMPDI_OPERATOR` (or type the officer name on the Review / Conflict
  screens — it persists per machine) to stamp every approval and conflict
  decision with `reviewed_by` / `decided_by`.
- For a shared pilot machine, set `CMPDI_API_TOKEN`: all mutating `/api`
  calls then need header `X-API-Token`. Reads stay open. This is a
  deterrent, not access control — full auth is still out of scope.

## Review workflow

1. Generate from Report Studio (`/reports`) or the parliamentary endpoint.
2. Open the review screen (`/reports/:rid`): check sources, OCR flags,
   retrieval stats, verification notes.
3. **Approve** (first-pass approvals feed the automation metric) or
   **Return for Revision** with a note (bumps `review_rounds`).
4. The DOCX downloads anytime; the audit trail downloads from
   `/reports/<id>/audit` — review history plus the full figure-to-source
   map. Attach it wherever the report goes.

## Conflict triage

`/api/conflicts/summary` returns counts, detected-open, and the 10 most
recent decisions — poll it after each ingest batch for the "what changed"
digest. Acknowledge with a note when a difference is understood (partial
period, revised figure); resolve only when the officer picks the standing
value, which is recorded with their name.

## Making the KPIs real

The dashboard starts honest: automation components read `null` until
observed, and the manual baseline is flagged `manual_stated: true`.

- **Manual baseline**: time an officer producing the equivalent summary by
  hand once, then set `manual_baseline_minutes` in Settings (or
  `CMPDI_MANUAL_BASELINE_MINUTES`). The flag flips to measured.
- **Extraction accuracy**: run `python -m backend.scripts.eval_extraction`
  after adding corpus ground truths; the panel reads `eval_metrics.json`.
- **Automation %**: emerges from use — first-pass approvals, conflict
  resolutions, grounded-vs-abstained answers. No events, no percentage.

## Backup & restore

```bash
python -m backend.scripts.backup --out /mnt/backups   # DB snapshot + files.tar.gz
```

The FAISS index and word clouds are derived and rebuild automatically.
Restore: stop the app, copy `cmpdi.db` to `CMPDI_DB_PATH`, extract
`files.tar.gz` over `CMPDI_DATA_DIR`, restart, run `reindex` if the
embedder version moved on.

## Demo runbook (5 minutes)

1. `./run.sh --fresh` → Pipeline shows live per-page OCR + summaries.
2. Conflicts screen: open the planted FY disagreement, click both receipts.
3. Ask a numeric question (exact value + citation), a semantic one, and an
   unknowable one (clean abstention).
4. Generate a production summary → review → approve → download DOCX + audit JSON.
5. Topics (`/topics`): word cloud + clusters. Close on the offline pledge:
   everything ran on this machine.
