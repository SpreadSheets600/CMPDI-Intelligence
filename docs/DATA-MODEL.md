# Data Model & Provenance

One SQLite database (WAL mode) plus one file directory hold the entire system
state. The database is rebuildable; the file store is the source of truth.

Code: `backend/db/models.py` (ORM, mirrors `schema.sql`),
`backend/db/database.py` (connection, helpers, migrations),
`backend/storage/__init__.py` (file store), `backend/models/documents.py`
(parser contract).

## Storage layout

```mermaid
flowchart TB
    subgraph data["data/ (CMPDI_DATA_DIR)"]
        DB[("cmpdi.db<br/>SQLite WAL + FTS5")]
        FAISS["faiss_index.bin<br/>IndexIDMap2 over IndexFlatIP"]
        FILES["files/<sha256>/<br/>original.* + page images + ocr.json"]
        REPORTS["reports/<br/>generated DOCX files"]
        CLOUDS["clouds/<br/>rendered word-cloud PNGs"]
        AGENT["agent_runs/<run_id>/<br/>charts + trace"]
        SETTINGS["app_settings.json<br/>runtime overrides"]
    end
```

- Document id **is** the file SHA-256. `doc_dir()` resolves
  `data/files/<sha256>/`; `store_original()` writes `original.<ext>` once and
  never mutates it. Page images and OCR artifacts sit beside it.
- The FAISS index persists to `data/faiss_index.bin`; a dimension or count
  drift against the DB triggers an automatic rebuild from stored vectors.
- DB access goes through `q()` / `q1()` / `execute()` with a `?` → `:p#`
  placeholder shim; `CleanRow` maps NaN to NULL on the way out.

## Entity-relationship map

```mermaid
erDiagram
    documents ||--o{ pages : has
    documents ||--o{ elements : has
    documents ||--o{ tables : has
    documents ||--o{ chunks : has
    tables ||--o{ table_cells : has
    chunks ||--o| chunk_embeddings : "1:1 vector"
    chunks ||--o{ facts : "provenance"
    entities ||--o{ facts : resolves

    documents {
        text id "sha256, also the file directory name"
        text doc_type "digital_pdf / scanned_pdf / mixed_pdf / docx / xlsx / csv / image"
        text subsidiary
        int is_current_version "version-chain member flag"
    }
    pages {
        int page_no
        int ocr_used
        real avg_confidence
        text image_path
        text summary "per-page LLM summary"
    }
    elements {
        text element_type "HEADING / PARAGRAPH / TABLE / FIGURE / CAPTION / LIST"
        text bbox "rendered pixel coordinates"
        text section_path
    }
    chunks {
        text content_type "TEXT / TABLE / TABLE_ROW / FIGURE_CAPTION / LIST / SUMMARY / PAGE_SUMMARY"
        text element_ids_json "provenance refs"
    }
    facts {
        text attribute
        text period_norm
        real value_norm
        text unit
        text flags "low_confidence_number"
    }
```

Supporting tables: `entities` (+ `entity_mentions`), `entity_reference`
(context only — never evidence), `doc_keywords`, `doc_topics`, `kg_edges`,
`conflict_status`, `jobs`, `reports`, `agent_runs`, and the FTS5 virtual table
`chunks_fts` backing BM25.

## Provenance chain

Every derived value keeps this chain. Nothing downstream ever touches the raw
file; indexes are rebuildable from the store.

```mermaid
flowchart RL
    ANSWER["answer / report figure"] --> FACT["fact row"]
    FACT --> CHUNK["chunk"]
    CHUNK --> ELEMENT["element or table cell"]
    ELEMENT --> PAGE["page / sheet"]
    PAGE --> DOC["document"]
    DOC --> FILE["data/files/<sha256>/original.*"]
```

Conventions that protect the chain:

- Raw values are never overwritten: `value_raw` + `value_norm`, `unit` +
  conversion provenance, `section_path` + `element_ids_json` on every chunk.
- Low-confidence OCR digits are flagged (`low_confidence_number`), searchable
  but excluded from reports/answers until corroborated or approved.
- Superseded revisions stay in the DB with `is_current_version = 0` — still
  visible, struck through, excluded from default retrieval scope.
- Deletion removes a document everywhere (vectors, chunks, facts, tags, page
  images, stored original) and elects a new current version in its group.

Next: [PIPELINE.md](PIPELINE.md) builds these rows; [RETRIEVAL.md](RETRIEVAL.md)
and [KNOWLEDGE.md](KNOWLEDGE.md) read them.
