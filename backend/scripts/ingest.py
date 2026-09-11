"""CLI ingestion: enqueue files and process them to completion, then print
a summary. Usage: python -m backend.scripts.ingest <file-or-dir> [...]"""

import sys
from pathlib import Path

from backend.core import config
from backend.db import database as db
from backend.core.pipeline import pipeline


def main(argv):
    if not argv:
        print("Usage: python -m backend.scripts.ingest <file-or-dir> [...]")
        return 2
    paths = []
    for a in argv:
        p = Path(a)
        if p.is_dir():
            paths.extend(sorted(f for f in p.iterdir() if f.is_file()
                                and f.name not in ("README.md",)))
        elif p.is_file():
            paths.append(p)
        else:
            print(f"Skipping Missing Path: {a}")
    if not paths:
        print("No Files To Ingest")
        return 1

    config.ensure_dirs()
    db.init_db()
    queued = []
    for p in paths:
        r = pipeline.ingest_file(p)
        tag = "duplicate" if r["duplicate"] else "queued"
        print(f"{tag}: {p.name} -> {r['doc_id'][:12]}")
        if not r["duplicate"]:
            queued.append(r["doc_id"])

    # process inline (no worker thread) for a predictable CLI run
    for doc_id in queued:
        pipeline.process_document(doc_id)
        doc = db.q1("SELECT filename, status, page_count FROM documents WHERE id=?", (doc_id,))
        job = db.q1("SELECT stats_json, error FROM jobs WHERE doc_id=? ORDER BY id DESC LIMIT 1", (doc_id,))
        import json
        stats = json.loads(job["stats_json"] or "{}")
        if doc["status"] == "failed":
            print(f"FAILED: {doc['filename']}: {job['error'].splitlines()[0] if job['error'] else '?'}")
        else:
            print(f"completed: {doc['filename']} | pages={stats.get('pages')} "
                  f"tables={stats.get('tables')} ocr={stats.get('ocr_pages')} "
                  f"chunks={stats.get('chunks')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
