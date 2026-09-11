# CMPDI Intelligence — Full Project Plan (MVP)

**Project:** AI-Powered Geological, Mining & Reporting Solution for CMPDI/CIL Subsidiaries (SIH26023)
**Document type:** Master ideation + build checklist. Everything is written as checkable steps.
**Status:** Planning → ready to build.

---

## 0. Problem Understanding (read this first)

### What CMPDI/CIL actually does with these documents
- CMPDI (Central Mine Planning & Design Institute) and CIL (Coal India Limited) subsidiaries answer **geological, mining, and production questions from the Ministry of Coal**, including **Parliamentary questions (Rajya Sabha / Lok Sabha) and high-priority administrative inquiries**.
- To answer even one such question, officers manually dig through: scanned exploration reports, annual reports, production spreadsheets, geological survey documents, historical archives, images/maps, and Word files.
- This is slow, depends on a few domain experts' memory, and is error-prone. A wrong number in a Parliamentary reply is a serious institutional embarrassment.

### What the problem statement demands (verbatim mapping)
| Problem statement requirement | What it means in our product |
|---|---|
| AI-assisted document processing | Ingest PDFs (digital/scanned/mixed), DOCX, XLSX, CSV, images → structured data |
| Data validation & consistency checking | Detect conflicting values across documents; never silently pick one |
| Traceability | Every fact, answer, and report figure links back to source file/page/table/cell |
| Automated report generation | Template-driven DOCX reports with citations, human-approved before official use |
| Word-cloud / topic identification | Per-corpus, per-subsidiary, per-year topic & keyword analysis |
| AI-based query/response | Grounded Q&A with citations and "insufficient evidence" abstention |
| Reduce prep time, improve accuracy/transparency | The measurable MVP outcome: minutes instead of days, with receipts |

### The one-sentence product definition
> **An offline, evidence-first intelligence layer that turns scattered geological/mining/production documents into a searchable, cross-validated knowledge base where every number, answer, and generated report carries a verifiable receipt back to its exact source.**

### The critical reframe (why this wins)
- **It is NOT a chatbot over PDFs.** It is an *information system with an AI on top*. Judges and officers don't trust AI; they trust auditable provenance. The AI earns trust by always showing where facts came from.
- **The system must be able to say "I don't know."** Abstention with a pointer to what was searched is a feature, not a failure.
- **Conflicts are surfaced, not resolved.** If two documents say different production figures for the same mine/year, the system shows both with sources. Humans decide.
- **100% local.** Coal data is sensitive. Zero API calls, zero cloud. This is a headline selling point, not a limitation.

---

## 1. Locked Constraints & Design Principles

- [x] **Language:** Python 3.10+ only.
- [x] **Database:** SQLite (WAL mode) — no Postgres, no server. One `.db` file + a files directory = the whole system state. Trivially backuppable and demoable.
- [x] **Everything runs locally.** No external API calls at any stage. Must be demonstrable on a laptop with no internet.
- [x] **Embeddings are local:** primary = **embeddinggemma** (Google's 300M embedding model built on Gemma 3, 768-dim, runs via `sentence-transformers`, supports Matryoshka truncation to 512/256/128 dims for speed); fallback = `bge-small-en-v1.5` or `all-MiniLM-L6-v2` (weaker machines).
- [x] **LLM backend abstraction:** `LLM_BACKEND=transformers` (default, raw model loaded from disk) **or** `LLM_BACKEND=ollama` (`OLLAMA_MODEL=qwen3:4b` etc.). If no LLM is available at all, the system still works in **extractive mode** (answers = retrieved evidence snippets + citations, no generation). The platform never hard-depends on a generative model.
- [x] **BM25 comes free:** SQLite **FTS5** has `bm25()` built in — zero extra dependency, exactly matches the problem statement's lexical search requirement.
- [x] **UI:** Flask (server-rendered Jinja2 HTML + a light sprinkle of vanilla JS / Alpine.js). **No Streamlit, no React build toolchain** — the whole frontend stays plain HTML/CSS/JS that Flask serves, keeping the project pure-Python and build-free. Light theme, minimal aesthetic (spec in Step 12).
- [x] **No shipped test suite.** Verification happens via throwaway dev scripts and manual checklists during the build; they are working tools, not deliverables. The shipped repo ships features, not tests.
- [x] **Vector search:** embeddings stored as BLOBs in SQLite; search via in-memory **numpy** cosine (brute force — instant up to ~100k chunks). Optional upgrade path: `sqlite-vec` extension. FAISS is unnecessary at MVP scale.
- [x] **"Object store" = filesystem:** `data/files/<sha256>/original.<ext>` etc., behind a tiny `Storage` interface so MinIO/S3 can be swapped in later.
- [x] **Modular interfaces everywhere:** `DocumentParser`, `EmbeddingBackend`, `LLMBackend`, `VectorStore` — every component replaceable without redesign.
- [x] **MVP quality bar:** not production-hardened, but every advertised feature must *work end-to-end* in a live demo. Some bugs acceptable; broken core flow not.

---

## 2. Architecture (target shape)

```
                         ┌─────────────────────────────────────────────┐
                         │        Flask App (UI + API in one)          │
                         │  server-rendered Jinja2 · light/minimal     │
                         │  Upload · Pipeline Status · Viewer · Search │
                         │  Ask (citations) · Conflict Radar · Topics  │
                         │  Word Cloud · Report Studio                 │
                         │  + JSON endpoints for interactive bits      │
                         └───────────────────┬─────────────────────────┘
                                             │
                         ┌───────────────────▼─────────────────────────┐
                         │      Service layer (pure Python modules)    │
                         └──────┬─────────────┬──────────────┬─────────┘
                                │             │              │
              ┌─────────────────▼──┐  ┌───────▼───────┐  ┌───▼──────────────┐
   files ───▶ │ INGESTION PIPELINE │  │ QUERY ENGINE  │  │ REPORT GENERATOR │
   (any type) │ classify→parse→OCR │  │ route→hybrid  │  │ templates+facts  │
              │ normalize→chunk→   │  │ retrieve→LLM/ │  │ + provenance map │
              │ embed→index        │  │ extractive    │  │ → DOCX/PDF       │
              └───────┬────────────┘  └───────┬───────┘  └───┬──────────────┘
                      │                       │              │
   ┌──────────────────▼───────────────────────▼──────────────▼───────────────┐
   │                            SQLite (WAL)                                 │
   │  documents · pages · elements · tables/cells · chunks · embeddings      │
   │  facts (numeric index) · conflicts · entities · topics · jobs · reports │
   │  + FTS5 (BM25) virtual tables                                           │
   └──────────────────┬──────────────────────────────────────────────────────┘
                      │
   ┌──────────────────▼───────────────────────────────────────────────────────┐
   │  data/files/ (filesystem "object store", source of truth, never deleted) │
   │  <sha256>/original.pdf · page_0003.png · ocr.json · extracted_images/    │
   └──────────────────────────────────────────────────────────────────────────┘

   Models (local only):  embeddinggemma (embeddings)  ·  Tesseract (OCR)
                         LLM via Ollama OR Transformers  ·  optional cross-encoder
```

**Golden rule of data flow:** `vector/fact/answer → chunk_id → element → page → document → original file`. Every row in SQLite can trace its ancestry to a byte range of an original file.

---

## 3. Tech Stack (decided, with reasons)

| Concern | Choice | Why |
|---|---|---|
| PDF (digital) | **PyMuPDF** | Fast, gives text + bounding boxes + layout in one pass |
| PDF (scanned/mixed) | **OCRmyPDF / Tesseract** (`pytesseract`) | Page-level OCR with word confidences (critical for digit-flagging) |
| DOCX | **python-docx** | Preserves heading hierarchy, tables, paragraphs |
| XLSX / CSV | **openpyxl + pandas** | Workbook/sheet/row/cell fidelity, merged-cell handling |
| DB | **SQLite + WAL + FTS5** | Zero-ops, built-in BM25, single-file portability |
| Vectors | **numpy** (+ optional `sqlite-vec`) | Brute-force cosine is instant at MVP scale |
| Embeddings | **embeddinggemma** via `sentence-transformers` | Gemma-3-family as requested, 300M params, laptop-friendly |
| OCR | **Tesseract** (+ `RapidOCR` as optional better-CJK/skew alternative) | Word-level confidence scores |
| LLM serving | **Ollama** (optional) / **Transformers** (default) | Config-driven backend switch, as specified |
| Reranking (optional) | `bge-reranker-base` cross-encoder | Noticeable quality jump; toggleable, off by default on weak machines |
| Entity/fact extraction | Gazetteer + regex first; optional **GLiNER** (local); optional LLM extraction | Deterministic > probabilistic for numbers |
| Topics/keywords | c-TF-IDF + KeyBERT-style embedding keywording + KMeans/HDBSCAN-lite + `wordcloud` | Lightweight BERTopic-equivalent |
| Report generation | **docxtpl** (Jinja in DOCX) + python-docx | Officer-editable output, template-controlled |
| UI | **Flask + Jinja2** (server-rendered HTML) + **Alpine.js/vanilla JS** for interactivity + minimal hand-written CSS | Pure-Python stack, zero build toolchain, no node_modules; interactive features (chat, viewer overlays, live status) work with fetch/polling; FastAPI/React upgrade paths noted below |
| Charts in reports | matplotlib | Production trend charts etc., embedded into DOCX |

---

## 4. Feature Taxonomy

### 4.1 Core features (the spine — must all work in MVP)
1. **Ingestion & auto-classification** — drop in any file; system identifies type (digital PDF / scanned PDF / mixed PDF / DOCX / XLSX / CSV / image), routes to the right parser.
2. **Canonical Document Model** — everything becomes `Document → Page/Sheet → Element (heading/paragraph/table/figure/list/cell)` with layout boxes, confidence, and section hierarchy.
3. **Provenance engine** — SHA-256 dedup, version tracking, every element/chunk/fact carries source coordinates.
4. **Structure-aware chunking** — chunks respect headings, tables, and sections; content-type tagged (TEXT / HEADING / TABLE / TABLE_ROW / FIGURE_CAPTION / LIST).
5. **Hybrid retrieval** — FTS5 BM25 + vector search + Reciprocal Rank Fusion, with metadata filters (subsidiary, year, doc type).
6. **Grounded Q&A with citations** — query router (numeric-fact vs semantic vs table vs listing), RAG with per-claim citations, abstention when evidence is weak, Ollama/Transformers/extractive backends.
7. **Numeric fact index + validation (Conflict Radar)** — facts `(entity, attribute, period, normalized value, unit)` extracted and cross-checked across documents; conflicts surfaced side-by-side.
8. **Automated report generation** — template-driven DOCX (production summary, geological overview, comparative analysis, parliamentary reply format), every figure injected with provenance, auto-generated Sources appendix.
9. **Topic & word-cloud explorer** — corpus-wide and filtered keyword clouds, topic clusters, recurring themes, similar-document finder.
10. **Pipeline dashboard & source viewer** — live job status (`Uploaded → Classifying → Extracting → OCR → Normalizing → Chunking → Embedding → Indexing → Completed/Failed`), and a viewer that shows page images with element overlays and table cells clickable.

### 4.2 Differentiating features (above-average implementations)
- Word-level OCR confidence gating — **low-confidence digits are quarantined**, never silently used in reports or answers.
- Indian-format normalization — lakh/crore → absolute values, `1,23,456` parsing, FY (Apr–Mar) ↔ calendar mapping, dual storage of raw + normalized values.
- Unit normalization dictionary (tonnes / lakh tonnes / MT / cu.m / GCV kcal/kg / % ash / grades) with provenance-preserving conversions.
- Near-duplicate & version-chain detection (exact SHA-256 + text-similarity fingerprinting) — marks superseded documents, so "latest value" queries don't hit stale reports.
- Extractive fallback mode — the full demo works even on a machine with no LLM at all.
- Evidence-coverage reporting in answers: "Answer built from 3 sources; 1 conflict detected; OCR confidence high."

### 4.3 Unique / mic-drop features (the things nobody else will show)
1. **"Every number has a receipt."** Click any figure in a generated report or an AI answer → system opens the source: the exact PDF page rendered as an image with the value's bounding box highlighted, or the exact spreadsheet cell selected. This single feature *is* the demo.
2. **Conflict Radar.** A dedicated screen: "These 4 documents disagree about SECL's FY2021-22 offtake" with normalized values, units as reported, and side-by-side source snippets. Turns the *validation requirement* of the problem statement into a visible product.
3. **Parliamentary Reply Mode.** Paste a parliamentary question (or pick a template) → system retrieves evidence, drafts a formal reply in government answer format, every line numbered with citations, plus a flagged-uncertainties section for the reviewing officer.
4. **Numeric Question Router.** "How much coal did MCL produce in 2021-22?" doesn't go to semantic search at all — it hits the fact index, returns the exact number with its receipt, and *also* warns if a conflicting value exists elsewhere. Semantic search is for concepts; exact match is for numbers. This split is rare in student/demo RAG systems.
5. **Document version DNA.** Upload a revised annual report → system detects it's a new version of an existing document, shows a *diff of changed numbers* between versions ("Reserves figure changed from 1,240 MT to 1,318 MT on page 47"). Officeworthy and unforgettable.
6. **Offline pledge panel.** A UI badge: "0 network calls made. Verified: no sockets opened beyond localhost." For sensitive coal data, this is a persuasive flex in any pitch.

### 4.4 Nice-to-have features (build only if time remains)
- Cross-encoder reranking toggle; chart-to-data (extract values from bar charts in scanned reports); multi-language (Hindi) OCR; report trend charts auto-generated from the fact index; "ask across only these 5 documents" scoped sessions; export of a full audit trail for one answer as a PDF; email-like digest of new conflicts after each upload batch.

---

## 5. Edge-Case Catalogue (and how each is handled)

### 5.1 File-level edge cases
- [ ] **Corrupt / password-protected / zero-byte files** → pre-flight validation at intake; move to `failed/` with explicit reason in job record; never crash the pipeline.
- [ ] **Huge files (500+ page PDFs)** → page-batched processing with progress checkpoints; a crash resumes from last completed page (job state in SQLite).
- [ ] **Mixed PDFs (some pages digital, some scanned)** → **per-page decision**: if PyMuPDF gets < N chars on a page, route that page to OCR. Never a whole-file decision.
- [ ] **Wrong extension / disguised files** → classify by magic bytes (libmagic), not extension.
- [ ] **Exact duplicates** → SHA-256 match → reject as duplicate, link to original.
- [ ] **Near-duplicates (same report, slightly different revision)** → text fingerprint (MinHash or embedding cosine of doc-level summary vector) → mark as **version chain**, newest by embedded date wins as "current"; old ones flagged `superseded` (not deleted).
- [ ] **Files with no extractable date** → version ordering falls back to upload time; UI shows "date unknown."

### 5.2 PDF/OCR edge cases
- [ ] **Skewed / rotated / low-DPI scans** → deskew + rotate via OSD (Tesseract `--psm` tuning, orientation detection); minimum-DPI check, re-render pages at 300 DPI from PDF before OCR.
- [ ] **Stamps, signatures, handwriting over text** → treated as noise; confidence scores drop; zones marked low-confidence rather than dropped (dropping would hide evidence).
- [ ] **Two-column layouts read out of order** → PyMuPDF block coordinates sort reading order (top-to-bottom, column-aware); verify against sample docs.
- [ ] **Running headers/footers/page numbers polluting text** → detect repeated lines across pages (top/bottom 5% bands appearing on >60% of pages) → strip from body, store separately as page furniture.
- [ ] **OCR digit corruption (6↔8, 1↔7, 0↔O, 5↔S)** → the dangerous one. Word-level confidences from Tesseract; **any number extracted from OCR with confidence < threshold (e.g., 85) is flagged `low_confidence_number`** — it is searchable but excluded from auto-generated reports and answers unless a human approves it or it's corroborated by another source. Cross-check: the same fact found in a digital document outranks an OCR'd one.
- [ ] **Devanagari / bilingual text** → Tesseract `hin+eng` if Hindi pack installed; feature-flagged, not MVP-blocking.
- [ ] **Tables without ruling lines / tables spanning pages** → PyMuPDF `find_tables()` where possible; for page-spanning tables, continuation detection (repeated header row or no-header numeric rows) → merge into one logical table with per-row source page provenance.
- [ ] **Multi-row / merged header cells** → header-tree flattening (`"GCV (kcal/kg)"` × `"(ARB)"` → `GCV kcal/kg (ARB)`), stored as column path, not just column name.

### 5.3 Spreadsheet edge cases
- [ ] **Merged cells** → value propagated to all covered cells with a `merged_source` flag (no empty-cell confusion).
- [ ] **Formulas vs values** → read cached values (`data_only=True`), record formula string as metadata when present.
- [ ] **Header not in row 1, multiple tables per sheet, title rows** → table-region detection: find header row = first row with ≥2 non-empty string cells followed by data; blank-row/column bands split regions. Each region becomes its own logical table.
- [ ] **Units inside headers vs inside cells** ("Production (Mt)" vs "12.4 Mt") → unit parser reads both positions; normalized value stores both raw and normalized.
- [ ] **Indian number formats** (`1,23,456.78`, "12.5 lakh tonnes", "3.2 MT") → dedicated Indian-format number parser + unit dictionary → normalized absolute values; raw string always preserved.
- [ ] **Years as "2021-22" / "FY22" / "2021–2022"** → fiscal-year normalizer (India: Apr–Mar). "2021-22" = 2021-04-01→2022-03-31. All period comparisons happen in normalized space.
- [ ] **CSV encoding chaos** (UTF-8 / UTF-16 / latin-1, comma vs semicolon) → `charset-normalizer` sniffing + delimiter sniffing.

### 5.4 Data & semantics edge cases
- [ ] **Same mine, different spellings** ("Kusunda", "Kusunda Colliery", "KUSDUNG") → gazetteer of subsidiaries/mine names built from corpus itself (frequent capitalized n-grams near entity keywords) + fuzzy matching (rapidfuzz); alias table editable in UI.
- [ ] **Same seam/formation names across different mines** → entities are namespaced `(mine, feature)`, never bare strings.
- [ ] **Conflicting values across documents** → the core feature, not a bug: fact key = `(entity, attribute, normalized_period, unit)`. Multiple distinct normalized values → **conflict record**. System never picks a winner; UI and reports show both with sources. If one source is `superseded`, it may be *marked* as likely-outdated — still shown.
- [ ] **Same value, different units** (12.4 Mt vs 12,400 thousand tonnes) → unit normalization resolves these *out* of the conflict list (this is why normalization must precede conflict detection).
- [ ] **Percentages vs absolute values confusion** → attribute namespacing (`production_tonnes` ≠ `production_growth_pct`); a fact never merges across attributes.
- [ ] **Ambiguous entity in query** ("production of the mine" — which mine?) → answer engine asks a clarifying inline question listing candidates with counts ("Did you mean: Kusunda (14 docs), Dipka (9 docs)?").

### 5.5 Retrieval & generation edge cases
- [ ] **No relevant evidence** → retrieval score floor; below it → explicit "No supporting evidence found in the 37 indexed documents. Closest matches: …" Never hallucinate to fill silence.
- [ ] **Query needs a table, retrieval returns prose** → table chunks and row chunks are first-class indexed content types; numeric queries prefer TABLE_ROW chunks.
- [ ] **Long tables exceeding chunk/embedding budget** → chunk per logical row-group with header context repeated in each chunk (so every row chunk is self-describing).
- [ ] **LLM cites something not in context** → constrained generation: citations must reference evidence IDs present in the prompt; post-generation citation validator strips/denies unsupported citations and logs them.
- [ ] **Ollama not running when configured** → health check at startup; automatic fallback chain `ollama → transformers → extractive`, with visible mode indicator in UI ("Answer generated by: qwen3:4b via Ollama").
- [ ] **Embedding model context overflow** → chunk max token length enforced below model limit; embeddinggemma 2048-token window is plenty for row-groups and paragraphs.
- [ ] **SQLite write contention (UI + worker + query)** → WAL mode + single writer thread (job queue) + short transactions; readers never blocked.

### 5.6 MVP-scope honesty list (known simplifications, documented, not hidden)
- [ ] Single-user, no auth (fine for demo; note in README).
- [ ] Knowledge-graph UI is deferred (entity/relation tables exist, graph viz is stretch).
- [ ] Chart-image data extraction is stretch, not core.
- [ ] Some bugs acceptable; silent wrong answers are not.

---

## 6. Build Steps (the checklist)

> Sequential. Each step ends with a **Done when** gate. Tick boxes as you go.

### Step 0 — Skeleton, config, storage, schema
**Goal:** an empty-but-running system: config loads, DB initializes, files store works, logging works.

- [ ] Create repo layout:
  ```
  cmpdi_intel/
    config.py            # pydantic-settings: paths, model names, LLM_BACKEND, OLLAMA_MODEL, thresholds
    db.py                # connection, WAL, schema init, migrations folder
    storage.py           # Storage interface: put/get/open/delete by sha256 (filesystem impl now, S3 later)
    pipeline/            # ingestion, parsers, normalizer, chunker, embedder, indexer
    retrieval/           # bm25, vector, hybrid, router
    facts/               # extraction, units, conflicts
    llm/                 # backends: transformers, ollama, extractive
    reports/             # templates, generator
    ui/                  # flask app: templates/, static/, blueprints
    data/  scripts/  _dev/   # _dev/ = throwaway verification scripts & checklists (never shipped)
  ```
- [ ] SQLite schema v1 (all tables below; write `schema.sql`, init script, and a `scripts/reset_db.py`):
  - `documents(id, sha256 UNIQUE, filename, doc_type, subsidiary, doc_date_raw, doc_date_norm, is_current_version, version_group_id, page_count, upload_ts, status)`
  - `pages(id, doc_id, page_no, text, ocr_used, avg_confidence)` ; `sheets(id, doc_id, sheet_no, name)`
  - `elements(id, doc_id, page_no/sheet_no, element_type, order_idx, bbox_json, text, conf, section_path)`
  - `tables(id, doc_id, loc_ref, n_rows, n_cols, header_json)` ; `table_cells(table_id, row, col, value_raw, value_norm, conf, source_ref)`
  - `chunks(id, doc_id, content_type, section_path, page_no/sheet_no, text, token_count, element_ids_json)`
  - `chunk_embeddings(chunk_id, dim, blob)` ; FTS5 virtual table over chunks (`chunks_fts`) for BM25
  - `facts(id, entity_id, attribute, period_norm, value_raw, value_norm, unit, conf, flags, chunk_id)` — the numeric index
  - `entities(id, canonical_name, type, aliases_json)` ; `entity_mentions(fact_id/entity_id, mention_text, chunk_id)`
  - `conflicts(id, fact_key, values_json, status(open/resolved/acknowledged), notes)`
  - `jobs(id, doc_id, stage, status, error, stats_json, timestamps)`
  - `reports(id, template, params_json, docx_path, provenance_json, created_ts, human_approved)`
- [ ] Config system with `.env` + defaults; `LLM_BACKEND`, `OLLAMA_MODEL`, `EMBEDDING_MODEL`, `OCR_MIN_CONFIDENCE=85`, `RETRIEVAL_SCORE_FLOOR`.
- [ ] Structured logging (per-stage, per-document) — you will need it to debug OCR/parsing pain.
- [ ] **Done when:** `python -m cmpdi_intel.scripts.init_system` creates DB + folders and prints a health summary.

### Step 1 — Intake: classification, hashing, dedup, job queue
**Goal:** drop any file; it's identified, hashed, deduplicated, version-grouped, and a job row appears.

- [ ] Intake service: reads file → magic-byte type detection → SHA-256 → insert/merge document record.
- [ ] Exact-dupe rejection with pointer to original; near-dupe check via text fingerprint (after Step 2 parsing, second pass).
- [ ] Simple in-process job queue (worker thread consuming `jobs` table) with the visible stage machine: `Uploaded → Classifying → Extracting → OCR → Normalizing → Chunking → Embedding → Indexing → Completed/Failed`.
- [ ] Each stage writes stats (pages processed, tables found, OCR pages, chunks, errors) into `jobs.stats_json` — the dashboard reads this.
- [ ] Failure isolation: one bad file never stops the queue; job → `Failed` with full traceback captured.
- [ ] **Done when:** dropping 5 files (including 1 corrupt) yields 4 `Completed-to-Classified` jobs + 1 clean failure with reason.

### Step 2 — Parsers → Canonical Document Model
**Goal:** every supported type becomes elements with provenance. This is the hardest, most valuable step.

- [ ] `DocumentParser` interface: `parse(file) -> CanonicalDoc(pages/sheets, elements, tables, metadata)`.
- [ ] **Digital PDF (PyMuPDF):** text blocks with bbox + font size → heading detection (font-size clustering relative to body) → paragraph merging across line breaks → `find_tables()` with header/cell extraction → image/figure regions + captions (nearest text below/above) → reading-order sort (column-aware).
- [ ] **Mixed PDF:** per-page text-yield test (< ~50 chars → OCR that page); store per-page `ocr_used` flag and confidence.
- [ ] **Scanned PDF:** render pages at 300 DPI → OCRmyPDF/Tesseract → text with word-level bboxes and confidences → same elementization as digital path. Store page images for the viewer.
- [ ] **DOCX (python-docx):** style-based heading hierarchy (Heading 1–4), paragraphs, tables (rows/cols incl. merged cells), inline images noted.
- [ ] **XLSX (openpyxl `data_only=True`):** sheets → per-sheet table-region detection (blank-band splitting) → header-row inference → cells with raw + parsed values → merged-cell propagation → formula strings as metadata.
- [ ] **CSV:** sniff encoding/delimiter → treat as single-sheet workbook.
- [ ] **Images:** OCR → single-page canonical doc; store original + OCR overlay.
- [ ] Every element carries: `element_type, bbox or sheet coordinates, text, confidence, section_path` (e.g., `Chapter 3 > 3.2 Reserves > Table 3.1`).
- [ ] **Done when:** for each of the 6 sample doc types, the viewer can render the page/sheet and highlight any element chosen at random from the DB.

### Step 3 — Normalization engine (the accuracy-critical step)
**Goal:** raw text becomes comparable, normalized, trustworthy values.

- [ ] Header/footer/page-number stripper (repeated-line detection across pages).
- [ ] Indian number parser: `1,23,456.78`, `12.5 lakh`, `3.2 crore`, `MT/Mt/million tonnes/thousand tonnes/tonnes`, `cu.m`, `ha`, `kcal/kg`, `%`.
- [ ] Unit dictionary + normalization: `unit_raw`, `value_raw`, `value_norm` (SI), conversion provenance kept (never overwrite raw).
- [ ] Fiscal-year normalizer: `2021-22`, `FY22`, `FY 2021-22`, `2021–2022`, date strings → canonical `period_start/period_end`.
- [ ] Whitespace/ligature/hyphenation cleanup; Unicode NFC.
- [ ] Number-hygiene gate: numbers from OCR below confidence threshold get `flags=low_confidence_number` (searchable, not reportable without approval).
- [ ] **Done when:** a dev-only scratch script (`_dev/check_normalization.py`) with 40+ nasty real-style strings ("₹ 1,23,456.78", "12.5 lakh tonnes", "FY22", "GCV (ARB) kcal/kg") all normalize correctly — kept in `_dev/`, not part of the deliverable.

### Step 4 — Structure-aware chunking
**Goal:** retrieval-ready chunks that never orphan context.

- [ ] Chunk types: TEXT, HEADING (context only), TABLE (serialized AI-readable form: header + all rows), TABLE_ROW (header context + single row — the workhorse for numeric queries), FIGURE_CAPTION, LIST.
- [ ] Paragraph grouping under section path; split at token budget (~400 tokens, 15% overlap) respecting sentence/section boundaries; never split a table row; never mix sections in one chunk.
- [ ] Table serialization format for chunks (also used in LLM prompts):
  `TABLE [Doc: Annual Report 2022, p.47] | Mine | FY | Production (Mt) | ... | Kusunda | 2021-22 | 4.85 |`
- [ ] Every chunk stores `element_ids_json` + `section_path` + `page_no/sheet_no` — full ancestry.
- [ ] **Done when:** `scripts/inspect_chunks.py <doc_id>` prints chunks that a human agrees are self-contained and traceable.

### Step 5 — Embedding service (local, backend-switchable)
**Goal:** every chunk embedded by a local Gemma-family model, cheaply and cacheably.

- [ ] `EmbeddingBackend` interface; primary: `embeddinggemma` via sentence-transformers (768-dim; use Matryoshka truncation to 512-dim for speed if needed); fallbacks: `bge-small-en-v1.5` / `all-MiniLM-L6-v2`.
- [ ] Store `dim` per chunk so a model swap triggers a documented re-embed script (dimension mismatch detection at startup).
- [ ] Batch embedding with progress; embeddings cached in SQLite as BLOBs; numpy matrix cache in memory (lazy load, invalidated on insert).
- [ ] Prompt/instruction prefix per model family if the model card requires one (embeddinggemma does for task types — follow its task prompts: query vs document).
- [ ] **Done when:** embedding 500 chunks takes minutes not hours on a laptop; a `_dev/similarity_smoke.py` run shows related geological paragraphs scoring > unrelated ones.

### Step 6 — Hybrid retrieval (FTS5 BM25 + vectors + fusion + filters)
**Goal:** the retrieval substrate the whole AI layer stands on.

- [ ] FTS5 table populated on chunk insert; BM25 ranking with `bm25()`; prefix/phrase support for identifiers (mine codes, doc names).
- [ ] Vector search: numpy cosine over in-memory matrix; top-k with score floor.
- [ ] Reciprocal Rank Fusion (k=60) merging both lists; optional cross-encoder rerank toggle.
- [ ] Metadata filters: subsidiary, doc_type, date/period range, version (`current only` default ON — this is how superseded docs stop polluting answers), content_type.
- [ ] Result object: chunk + document + page/sheet + element refs + scores + provenance bundle (ready for UI deep-links).
- [ ] **Done when:** a dev-only checklist of 15 questions — half semantic ("what are the geological characteristics of the Korba coalfield"), half exact ("offtake of SECL in 2021-22") — returns the right doc+page in top-3 for ≥80% when tried by hand.

### Step 7 — Fact extraction & numeric index
**Goal:** the structured spine: entities, quantities, periods — queryable exactly, checkable for conflicts.

- [ ] Entity gazetteer bootstrapped from config (CIL subsidiaries: ECL, BCCL, CCL, NCL, WCL, SECL, MCL, NEC, CMPDI) + auto-mined corpus candidates (frequent proper n-grams near keywords like "mine", "colliery", "coalfield", "seam", "block") → alias table with UI editing.
- [ ] Quantity extraction: regex + unit dictionary over TABLE_ROW/TEXT chunks → `(entity, attribute, period, value_raw, value_norm, unit, conf, chunk_id)`. Attribute vocabulary: production, offtake, dispatch, reserves, extractable reserves, GCV, ash %, grade, depth, stripping ratio, manpower, OBF… (extensible YAML).
- [ ] Attribute classifier: context windows around numbers determine the attribute (the number after "production of" vs "reserves" vs "ash content"); LLM-assisted classification only when regex confidence is low (works in extractive mode too — falls back to nearest-heading heuristic).
- [ ] Period binding: nearest fiscal-year mention in row/section/table header wins; ambiguity → flag.
- [ ] **Done when:** loading the demo corpus yields ≥50 facts each with a working chunk→page→file provenance chain, spot-checked by hand.

### Step 8 — Conflict Radar (validation layer)
**Goal:** cross-document consistency checking that surfaces rather than resolves.

- [ ] Group facts by `(entity_id, attribute, period_norm)` after unit normalization; distinct `value_norm` beyond tolerance (e.g., >1% relative) → `conflicts` row with all values + sources.
- [ ] Superseded-version awareness: conflict notes which value comes from a `superseded` document.
- [ ] OCR-confidence awareness: conflict notes which value is `low_confidence_number`.
- [ ] Resolution workflow: `open → acknowledged (human picks/explains) → resolved`; chosen value recorded with the human's note for the audit trail — the system remembers, it doesn't decide silently.
- [ ] Conflict summary generated after every ingestion batch (UI banner: "3 new conflicts detected").
- [ ] **Done when:** a deliberately planted conflict in the demo corpus (two docs, different FY2021-22 production for one mine) appears in the Radar with both receipts.

### Step 9 — Query engine & grounded Q&A (RAG)
**Goal:** natural-language questions → routed retrieval → cited answers → honest abstention.

- [ ] Query router (rules first, tiny-LLM optional): NUMERIC_FACT (hit fact index first, fallback hybrid) / SEMANTIC (hybrid) / TABLE_LIST ("list all mines in WCL with >2 Mt production" → table scan + filters) / DOCUMENT scoped.
- [ ] Context assembly: top-k chunks with content-type diversity (always include the TABLE_ROW if a numeric fact was matched); token-budgeted; each evidence item gets an evidence ID.
- [ ] `LLMBackend` interface with three implementations:
  - `OllamaBackend` (if `LLM_BACKEND=ollama`): chat with the configured `OLLAMA_MODEL`, JSON-ish structured prompts.
  - `TransformersBackend` (default): local HF model (e.g., Qwen3-1.7B/4B or Gemma-3-1B class) loaded once, 4-bit/quant optional.
  - `ExtractiveBackend` (always available): no generation — returns top evidence snippets verbatim with citations. Startup auto-falls back `ollama → transformers → extractive`.
- [ ] System prompt contract: answer ONLY from evidence; cite evidence IDs per claim; say "insufficient evidence" when grounded answer isn't possible; never merge conflicting numbers — report the conflict.
- [ ] Post-generation citation validator: every citation must map to a provided evidence ID; violations stripped + logged.
- [ ] Answer payload: answer text + inline citation markers + evidence list (each deep-linkable) + meta (backend used, retrieval scores, conflicts touched, OCR-confidence warnings) + "closest matches" on abstention.
- [ ] **Done when:** the demo Q&A set runs end-to-end in all three backend modes; ≥2 questions deliberately outside corpus knowledge produce clean abstentions.

### Step 10 — Topics, keywords & word clouds
**Goal:** the problem statement's word-cloud requirement, done properly.

- [ ] Keyword extraction per doc & corpus: embedding-based keyphrase candidate extraction (KeyBERT-style with the local embedding model) + c-TF-IDF across clusters.
- [ ] Topic clustering: embeddings → KMeans (k auto by silhouette) or HDBSCAN-lite; c-TF-IDF labels per cluster ("Coal seam correlation", "Offtake dispatch", "Environmental clearance").
- [ ] Word clouds: corpus-wide, per subsidiary, per year, per doc-type; rendered via `wordcloud` lib in UI.
- [ ] Similar-document finder: doc-level mean embedding cosine → "reports similar to this one."
- [ ] Topic-over-time view: cluster prevalence by fiscal year (stretch but cheap once facts exist).
- [ ] **Done when:** demo corpus produces 4+ coherent named clusters and a word cloud that a domain person would nod at.

### Step 11 — Automated report generation
**Goal:** DOCX reports where every number has provenance and a Sources appendix is automatic.

- [ ] Template store (docxtpl): `production_summary.docx`, `geological_overview.docx`, `comparative_analysis.docx`, `parliamentary_reply.docx` — each with Jinja slots and instructions where facts go.
- [ ] Report planner: template params (entity, period, doc scope) → fact queries (fact index) + semantic retrieval (narrative sections) → fact bundle with conflicts resolved-or-flagged.
- [ ] Injection rules: only facts with `conf` above threshold and not `low_confidence_number` (unless human-approved in conflict workflow) may be injected; conflicting facts inserted as "Value A (Source, p.X) vs Value B (Source, p.Y) — pending verification."
- [ ] Provenance map: report builder emits `provenance_json` — for every generated figure: template slot → fact id → chunk → page/sheet → file. Powers click-to-receipt.
- [ ] Sources appendix auto-generated (document, page, table/row/cell, OCR confidence note).
- [ ] Export: DOCX primary; PDF via LibreOffice headless if present (optional).
- [ ] Human-in-loop state: `draft → human_approved` flag; UI shows a review checklist (conflicts pending, low-confidence numbers used).
- [ ] **Done when:** one-click "Production Summary for [Mine], FY2021-22" produces a clean DOCX where clicking the tonnage figure in the app opens the source page highlight; a planted conflict appears as a flagged note, not a silent pick.

### Step 12 — UI (Flask) — the demo surface
**Goal:** one Flask app that shows everything; judges' first 3 minutes land here. Plain HTML served by Jinja2, made interactive with Alpine.js/vanilla JS + `fetch` — no React, no bundler, no node_modules.

- [ ] **Design direction (locked):** light theme, minimal, aesthetic, modern, functional.
  - Near-white background (`#FAFAF8`), white cards with hairline borders and soft shadows; one accent color (e.g., deep amber/coal-orange) used sparingly for actions and highlights.
  - Clean typography: Inter or system font stack, clear type scale, generous whitespace, content max-width ~1200px centered.
  - Status communicated via subtle chips/badges (pipeline stages, OCR confidence, backend used) — information density without clutter.
  - No gradients, no dark mode, no dashboard-kit look; restraint *is* the design. Every screen answers "what do I do here?" in one glance.
- [ ] Pages (Flask blueprints, one per surface):
  - **Ingest** — drag-drop upload, live pipeline stage strip per file (poll a JSON status endpoint every ~2s).
  - **Documents** — list with filters (type, subsidiary, year, status), version chains marked, superseded docs struck through.
  - **Source Viewer** — the crown jewel: rendered page image with SVG/canvas bbox overlays for elements, tables, and highlighted search hits; spreadsheet pages render as HTML grids with clickable cells; every highlight deep-linkable (`/doc/<id>/page/47?hl=<element_id>`).
  - **Search** — hybrid search box + filter sidebar, result cards with content-type icons, evidence snippets with inline citation chips that deep-link into the viewer.
  - **Ask** — chat interface: question box, streaming-friendly answer rendering, citation chips per claim, "show receipts" toggle revealing all evidence cards, backend badge ("qwen3:4b via Ollama" / "extractive mode"), abstention UX with "closest matches".
  - **Conflict Radar** — side-by-side value comparison cards (each value links to its source location), status workflow buttons (acknowledge/resolve with note).
  - **Topics & Clouds** — rendered word-cloud PNGs (matplotlib/wordcloud), cluster cards with representative snippets, similar-document finder.
  - **Report Studio** — template picker → parameter form (entity, period, scope) → generate → report preview with click-to-receipt on every figure → approve/download DOCX.
- [ ] Global: subsidiary/period filter sidebar shared across Search/Ask/Reports, pipeline health strip in the header, **"0 network calls" local-mode badge**.
- [ ] JSON endpoints alongside page routes (`/api/status`, `/api/ask`, `/api/search`, `/api/conflicts`, …) so the same Flask app is both UI and API — proves the modular-backend story without a second server.
- [ ] Interactivity budget: Alpine.js (one small file, no build step) for dropdowns/toggles/modals; vanilla `fetch` + polling for live status and chat; SVG overlay math in plain JS. Anything needing more than that is backend work, not frontend cleverness.
- [ ] **Done when:** a stranger can run `flask run`, drag in 3 files, ask a question, click a citation, see a conflict, and download a report — without help — and the first reaction to the UI is "this looks clean," not "this looks like a student project."

### Step 13 — Demo corpus, verification pass, hardening
**Goal:** repeatable proof that everything works — via a demo corpus and manual verification, not a shipped test suite. (Dev-only scripts in `_dev/` may be written along the way to understand behavior; they are working tools and explicitly **not part of the deliverable**.)

- [ ] Build a **synthetic demo corpus** (no confidential real data needed):
  - 1 digital "Annual Report of [fictional subsidiary]" PDF (10–15 pp, headings, tables, figures)
  - 1 scanned geological report (print → scan → or render pages as images with noise/rotation to force OCR path)
  - 1 mixed PDF (half digital pages, half image pages)
  - 1 production workbook XLSX (multi-sheet: production, offtake, dispatch; merged cells; lakh/MT units)
  - 1 CSV (dispatch records)
  - 1 parliamentary Q&A DOCX
  - 1 near-duplicate revised annual report (changed numbers → version chain + conflict)
  - 1 corrupt file + 1 duplicate file (for failure/dedup demo)
- [ ] Manual verification checklist (kept in `_dev/`): normalization spot-checks, a 15-question retrieval sanity pass, fact-extraction spot checks, and one end-to-end run of ingest → ask → report. Checked off by hand; results noted in the README, no test code shipped.
- [ ] Seed/entity tuning pass on the demo corpus; README quickstart (`install → pull models → init → ingest demo → flask run`).
- [ ] **Done when:** fresh-machine setup to full demo in ≤ 30 minutes following only the README.

### Step 14 — Pitch & write-up assets
- [ ] Architecture diagram + data-flow diagram (final versions).
- [ ] One-page "why this is different" (provenance-first, offline, conflict-honest).
- [ ] Measured demo metrics: ingestion time per doc type, retrieval latency, time-to-answered-question vs the manual baseline (even a rough comparison sells hard).

---

## 7. MVP Demo Script (the 5-minute run-through)

1. **Drag in** the demo corpus → dashboard shows the stage strip live; corrupt file fails cleanly with reason; duplicate is rejected with pointer.
2. **Conflict Radar** already shows the planted FY2021-22 conflict — click through both receipts.
3. **Ask:** "How much coal did Kusunda produce in 2021-22?" → exact number, citation chip → click → PDF page with the value highlighted. Ask a semantic one → grounded answer with 3 sources. Ask an unknowable one → honest abstention.
4. **Report Studio:** generate Production Summary → open DOCX → Sources appendix → in-app click-to-receipt on any figure.
5. **Topics:** word cloud + clusters for the corpus.
6. Point at the badge: **"Everything you just saw ran offline on this laptop."**

---

## 8. Risks & Mitigations (kept visible)

| Risk | Mitigation |
|---|---|
| OCR quality on real scans is worse than demo | Confidence gating means bad OCR degrades gracefully (flagged), never silently wrong; RapidOCR swap-in ready |
| Heading/table detection fails on exotic layouts | Per-page manual review affordance in viewer; extraction rules tuned on the sample pack; MVP scope = "common layouts work" |
| embeddinggemma unfamiliar quirks | Follow model-card task prompts; bge/MiniLM fallback one config line away |
| Local LLM too slow/weak on demo laptop | Extractive mode is the guaranteed floor; Ollama quantized 1.7–4B class models are the demo target |
| Scope explosion | Section 4.4 is explicitly "don't build until 4.1 + 4.3 receipts work" |
| SQLite concurrency during ingestion + querying | WAL + single writer; queries are read-only; proven pattern at this scale |

---

## 9. Deliberately Deferred (say no now, revisit post-MVP)

Knowledge-graph visualization · chart-image data extraction · Hindi OCR · multi-user auth · Postgres/MinIO/S3 backends (interfaces exist) · cross-encoder reranking on by default · incremental re-processing of edited documents · web-scale crawling of archives.
