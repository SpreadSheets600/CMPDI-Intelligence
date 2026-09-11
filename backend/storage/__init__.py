"""Filesystem object store. Original files are the source of truth and are
never modified or deleted by the pipeline."""

import hashlib
import shutil
from pathlib import Path

from backend.core import config


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def doc_dir(sha: str) -> Path:
    d = config.FILES_DIR / sha
    d.mkdir(parents=True, exist_ok=True)
    return d


def store_original(path: Path, sha: str) -> Path:
    dest = doc_dir(sha) / f"original{path.suffix.lower()}"
    if not dest.exists():
        shutil.copy2(path, dest)
    return dest


def original_path(sha: str) -> Path | None:
    d = config.FILES_DIR / sha
    if not d.exists():
        return None
    for f in sorted(d.glob("original.*")):
        return f
    return None
