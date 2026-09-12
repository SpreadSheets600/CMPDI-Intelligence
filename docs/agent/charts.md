# Chart capabilities guide

Context for the analytical agent: when to draw a chart, which type fits the
question, and how charts are produced. Charts come from the `run_python`
tool; every `plt` figure is captured automatically, so never save files.

## Choosing the chart

| Question shape | Chart |
|---|---|
| One metric across categories (entities, mines, states) | Bar chart, sorted descending |
| One metric over periods | Line chart (markers on); bar if 3 periods or fewer |
| Parts of a whole | Horizontal stacked bar or sorted bar with share labels; avoid pie for more than 4 parts |
| Two metrics side by side | Grouped bar with a legend |
| Relationship between two metrics | Scatter with axis labels and units |
| Distribution of one metric | Histogram with sensible bins |

## Style rules (matplotlib defaults are already set)

- Title states the finding, not the topic ("BCCL leads coking coal output"
  not "Coking coal output by subsidiary").
- Label axes with units (MT, %, kcal/kg).
- Annotate the key bar or point (the maximum, the latest year) when it
  carries the answer.
- Never overlay more than 4 series; never use dual axes.
- If the data is too sparse to chart (fewer than 2 groups or periods), say so
  in prose instead of forcing a chart.

## Data hygiene before plotting

- Filter to the latest consistent period basis; fiscal years start in April.
- Drop null `value_norm` rows and report how many were dropped.
- Where the same key has conflicting reported values, chart the value from
  the current-version document and note the alternative in the caption.
