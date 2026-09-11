PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    sha256 TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    doc_type TEXT NOT NULL,             -- digital_pdf | scanned_pdf | mixed_pdf | docx | xlsx | csv | image
    subsidiary TEXT,
    doc_date_raw TEXT,
    doc_date_norm TEXT,                 -- ISO start date of detected period
    is_current_version INTEGER NOT NULL DEFAULT 1,
    version_group_id TEXT,
    page_count INTEGER DEFAULT 0,
    ocr_pages INTEGER DEFAULT 0,
    upload_ts TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'uploaded'
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_no INTEGER NOT NULL,
    text TEXT DEFAULT '',
    ocr_used INTEGER NOT NULL DEFAULT 0,
    avg_confidence REAL,
    image_path TEXT
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
    section_path TEXT DEFAULT ''
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

CREATE TABLE IF NOT EXISTS conflicts (
    id INTEGER PRIMARY KEY,
    fact_key TEXT NOT NULL,            -- entity|attribute|period
    values_json TEXT NOT NULL,         -- [{value_norm, value_raw, unit, doc_id, page_no, sheet_no, cell_ref, flags}]
    status TEXT NOT NULL DEFAULT 'open',   -- open | acknowledged | resolved
    chosen_fact_id INTEGER,
    notes TEXT DEFAULT '',
    created_ts TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_conflicts_key ON conflicts(fact_key, status);

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
