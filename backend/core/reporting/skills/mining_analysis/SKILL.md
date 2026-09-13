# Production Analysis Skill

Procedural rules for coal production performance analysis.

## Required inputs

- Production quantity with unit (normalize to MT)
- Fiscal year (April-start FY labels)
- Mine or subsidiary, target where available

## Required calculations

- YoY change: (current - previous) / previous * 100
- Achievement: actual / target * 100
- Share: entity / total * 100

## Interpretation rules

- Never call an increase positive without checking target achievement.
- A latest-year drop against a mid-year cutoff is a partial year, not a collapse.
- Prefer current-version documents; note when values come from superseded revisions.

## Evidence requirements

- Every numeric conclusion cites its source ref.
- Conflicting values are shown side by side, never silently picked.
