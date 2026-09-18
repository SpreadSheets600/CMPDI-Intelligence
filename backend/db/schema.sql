PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    sha256 TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    display_name TEXT,                  -- user rename; falls back to filename
    doc_type TEXT NOT NULL,             -- digital_pdf | scanned_pdf | mixed_pdf | docx | xlsx | csv | image
    content_norm TEXT,                  -- normalized representation label, e.g. "Structured Tabular Document"
    summary TEXT,                       -- LLM summary; doubles as a searchable semantic layer
    subsidiary TEXT,
    doc_date_raw TEXT,
    doc_date_norm TEXT,                 -- ISO start date of detected period
    is_current_version INTEGER NOT NULL DEFAULT 1,
    version_group_id TEXT,
    page_count INTEGER DEFAULT 0,
    ocr_pages INTEGER DEFAULT 0,
    upload_ts TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'uploaded',
    structure_json TEXT               -- deterministic structural inspection profile
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_no INTEGER NOT NULL,
    text TEXT DEFAULT '',
    summary TEXT,
    ocr_used INTEGER NOT NULL DEFAULT 0,
    avg_confidence REAL,
    image_path TEXT,
    page_class TEXT                   -- TEXT_ONLY | IMAGE_ONLY | TEXT_IMAGE | TEXT_TABLE | IMAGE_TABLE | COMPLEX_LAYOUT | LOW_CONFIDENCE
);

CREATE TABLE IF NOT EXISTS elements (
    id INTEGER PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_no INTEGER,
    sheet_no INTEGER,
    element_type TEXT NOT NULL,        -- HEADING | PARAGRAPH | TABLE | FIGURE | CAPTION | LIST | CELL
    order_idx INTEGER NOT NULL,
    bbox TEXT,                          -- JSON [x0,y0,x1,y1] in page pixels
    text TEXT DEFAULT '',
    conf REAL,
    section_path TEXT DEFAULT '',
    method TEXT                       -- native | ocr | table | sheet | vision
);
CREATE INDEX IF NOT EXISTS idx_elements_doc ON elements(doc_id);

CREATE TABLE IF NOT EXISTS tables (
    id INTEGER PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_no INTEGER,
    sheet_no INTEGER,
    table_idx INTEGER NOT NULL,
    n_rows INTEGER NOT NULL,
    n_cols INTEGER NOT NULL,
    headers_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS table_cells (
    table_id INTEGER NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
    row_idx INTEGER NOT NULL,
    col_idx INTEGER NOT NULL,
    value_raw TEXT,
    value_norm REAL,
    conf REAL
);
CREATE INDEX IF NOT EXISTS idx_cells_table ON table_cells(table_id);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content_type TEXT NOT NULL,        -- TEXT | HEADING | TABLE | TABLE_ROW | FIGURE_CAPTION | LIST
    section_path TEXT DEFAULT '',
    page_no INTEGER,
    sheet_no INTEGER,
    text TEXT NOT NULL,
    token_count INTEGER,
    element_ids_json TEXT DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text, content='', content_rowid='id', tokenize='porter unicode61'
);

CREATE TABLE IF NOT EXISTS chunk_embeddings (
    chunk_id INTEGER PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    dim INTEGER NOT NULL,
    model TEXT NOT NULL,
    blob BLOB NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY,
    canonical_name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,                -- subsidiary | mine | coalfield | seam | block | organization
    aliases_json TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS entity_reference (
    id INTEGER PRIMARY KEY,
    entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    category TEXT NOT NULL,            -- profile | geography | production | statistic
    label TEXT NOT NULL,
    value TEXT NOT NULL,
    unit TEXT,                         -- e.g. MT, MTPA, % (NULL for prose values)
    as_of TEXT,                        -- when the public source reported it (NULL for stable facts)
    source TEXT NOT NULL,              -- public source; reference context, never evidence
    UNIQUE (entity_id, category, label)
);
CREATE INDEX IF NOT EXISTS idx_entity_reference_entity ON entity_reference(entity_id);

CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY,
    entity_id INTEGER REFERENCES entities(id),
    entity_text TEXT,                   -- raw mention when entity unresolved
    attribute TEXT NOT NULL,            -- production | offtake | reserves | gcv | ash_pct | ...
    period_norm TEXT,                   -- canonical fiscal year start, e.g. 2021-04-01
    value_raw TEXT NOT NULL,
    value_norm REAL,
    unit TEXT,
    conf REAL DEFAULT 1.0,
    flags TEXT DEFAULT '',              -- low_confidence_number | ...
    chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_facts_key ON facts(entity_id, attribute, period_norm);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    doc_id TEXT REFERENCES documents(id) ON DELETE CASCADE,
    stage TEXT NOT NULL DEFAULT 'uploaded',
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | running | completed | failed
    error TEXT,
    stats_json TEXT DEFAULT '{}',
    created_ts TEXT NOT NULL DEFAULT (datetime('now')),
    updated_ts TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    template TEXT NOT NULL,
    params_json TEXT NOT NULL,
    docx_path TEXT,
    provenance_json TEXT,               -- slot -> fact -> chunk -> page -> file chain
    human_approved INTEGER NOT NULL DEFAULT 0,
    review_status TEXT NOT NULL DEFAULT 'pending',   -- pending | approved | returned
    review_note TEXT,
    created_ts TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS doc_keywords (
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'tf',   -- llm | tf
    PRIMARY KEY (doc_id, keyword)
);
CREATE INDEX IF NOT EXISTS idx_doc_keywords_kw ON doc_keywords(keyword);

CREATE TABLE IF NOT EXISTS doc_topics (
    id INTEGER PRIMARY KEY,
    scope TEXT NOT NULL,               -- corpus | subsidiary:<X> | year:<Y>
    label TEXT NOT NULL,
    keywords_json TEXT NOT NULL,
    doc_ids_json TEXT NOT NULL,
    created_ts TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS conflict_status (
    conflict_key TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'open',   -- open | acknowledged | resolved
    note TEXT,
    updated_ts TEXT NOT NULL DEFAULT (datetime('now'))
);

-- P1 knowledge graph: typed relationships with evidence provenance.
-- Nodes are organizations, mines, locations, geology, documents, metrics
-- and events; every edge keeps its chunk -> page -> document chain so any
-- relationship opens its source receipt. Reference context never lands here.
CREATE TABLE IF NOT EXISTS kg_edges (
    id INTEGER PRIMARY KEY,
    src_kind TEXT NOT NULL,               -- organization | mine | location | geology | document | metric | event
    src_label TEXT NOT NULL,
    src_entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    dst_kind TEXT NOT NULL,
    dst_label TEXT NOT NULL,
    dst_entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    relation TEXT NOT NULL,               -- OPERATES | LOCATED_IN | BASED_IN | HAS_GEOLOGY | MENTIONS | HAS_METRIC | REPORTS_METRIC | OCCURRED_AT | INVOLVES | REPORTED_IN | SUPERSEDES
    chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
    doc_id TEXT REFERENCES documents(id) ON DELETE CASCADE,
    page_no INTEGER,
    sheet_no INTEGER,
    period_norm TEXT,
    conf REAL DEFAULT 1.0,
    UNIQUE (src_kind, src_label, dst_kind, dst_label, relation, chunk_id)
);
CREATE INDEX IF NOT EXISTS idx_kg_edges_src ON kg_edges(src_kind, src_label);
CREATE INDEX IF NOT EXISTS idx_kg_edges_dst ON kg_edges(dst_kind, dst_label);
CREATE INDEX IF NOT EXISTS idx_kg_edges_doc ON kg_edges(doc_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_relation ON kg_edges(relation);

CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY,
    task TEXT NOT NULL,
    steps_json TEXT NOT NULL,           -- full thought/tool/observation trace
    answer TEXT,
    citations_json TEXT,
    created_ts TEXT NOT NULL DEFAULT (datetime('now'))
);
