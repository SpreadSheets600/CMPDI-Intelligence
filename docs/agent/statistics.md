# Statistical capabilities guide

Context for the analytical agent: what statistics are available and when to
use each. Everything below runs through the `run_python` tool with preloaded
pandas (`pd`), numpy (`np`), matplotlib (`plt`), `load_table()` and
`load_facts()`. Compute; never estimate in prose.

## Core operations

- **Aggregation**: group by entity, period, unit or document; totals, means,
  medians, min/max, counts.
- **Comparison**: absolute and percentage differences between entities or
  periods; always state the baseline and direction of change.
- **Growth and change**: year-over-year change in absolute and percentage
  terms; compound annual growth rate when three or more periods exist.
- **Shares and composition**: each entity's share of a total (e.g. one
  subsidiary's share of production); report as percentages that sum to 100.
- **Distributions**: spread, quartiles and outliers of a metric across
  entities or documents.
- **Trends**: direction and steepness over available periods; note gaps in
  the series instead of interpolating silently.
- **Correlation**: only with at least 6 aligned pairs; report r and the
  number of pairs; never imply causation.

## Rules

- Prefer the fact index (`load_facts(entity=..., attribute=...)`) for
  reported figures; use `load_table(doc_id, sheet_no)` for whole tables.
- Clean numerics explicitly: strip units, drop `value_norm IS NULL` rows,
  state how many rows were dropped.
- Where the same key has multiple reported values, show the distinct values
  with their sources rather than averaging.
- State the period basis (fiscal years start in April) next to every time
  comparison.
- Present computed results as derived ("computed from reported values") and
  distinguish them from cited document values.

## Presentation

- Lead with the answer (one sentence), then the supporting numbers, then the
  method in one line (e.g. "share = entity / total of latest period").
- Round sensibly (3 significant figures for shares, 1 decimal for MT).
- Every cited document value keeps its [E#] receipt marker.
