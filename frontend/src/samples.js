// Curated demo samples, hand-verified against the generated demo corpus
// (backend/scripts/make_demo_corpus.py regenerates it; run.sh ingests it on
// first launch). Every entry below returns a grounded answer over that
// corpus: exact figures resolve from the fact index, conflicts surface both
// values with receipts, analysis questions route to the computing agent,
// and concepts retrieve cited passages. Clicking a pill runs it.

export const ASK_SAMPLES = [
  { kind: 'Exact figure', q: 'How much coal did Kusunda Mine produce in 2021-22?' },
  { kind: 'Conflict', q: 'Which sources disagree on Jayant OCP offtake for 2022-23?' },
  { kind: 'Analysis', q: 'Chart Lakhanpur OCP production from 2019-20 to 2023-24' },
  { kind: 'Analysis', q: 'Compare MCL and NCL production in 2023-24' },
  { kind: 'Concept', q: 'What does the library say about coking coal washeries?' },
  { kind: 'Concept', q: 'Summarize drilling performance across subsidiaries' },
];

export const SEARCH_SAMPLES = [
  'Kusunda Mine',
  'Lakhanpur OCP production',
  'washery yield',
  'exploratory drilling',
  'rake despatch',
  'manpower safety',
];
