"""Filesystem backup: SQLite snapshot plus the content-addressed file store.
Usage: python -m backend.scripts.backup [--out DIR]

Writes backup_<stamp>/ with cmpdi.db (online snapshot via the sqlite3
backup API, safe while the app runs) and files.tar.gz (originals, page
images, OCR artifacts). The FAISS index and word clouds are derived and
rebuild on demand, so they are excluded. Restore: stop the app, put the
snapshot back at CMPDI_DB_PATH, extract the tarball over CMPDI_DATA_DIR,
restart (reindex if versions complain)."""

import sqlite3
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

from backend.core import config


def main(argv):
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else Path.cwd()
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    dest = out / f"backup_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)

    config.ensure_dirs()
    db_snapshot = dest / "cmpdi.db"
    with (
        sqlite3.connect(f"file:{config.DB_PATH}?mode=ro", uri=True) as src,
        sqlite3.connect(db_snapshot) as dst,
    ):
        src.backup(dst)
    print(f"Database Snapshot: {db_snapshot}")

    tar_path = dest / "files.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for sub in ("files", "reports"):
            p = config.DATA_DIR / sub
            if p.is_dir():
                tar.add(p, arcname=sub)
    print(f"File Store Archive: {tar_path}")
    print("Restore: stop app, copy cmpdi.db to CMPDI_DB_PATH,")
    print("extract files.tar.gz over CMPDI_DATA_DIR, restart.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
