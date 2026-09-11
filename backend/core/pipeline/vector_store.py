"""FAISS vector index: IndexFlatIP on L2-normalized vectors, wrapped in an
IDMap keyed by chunk id. With unit-length vectors, inner product equals
cosine similarity. The index persists to data/faiss_index.bin; a dimension
mismatch (embedding model changed) triggers a rebuild from the database.
A numpy brute-force fallback is used when faiss is not installed."""

import numpy as np

from backend.core import config
from backend.db import database as db

INDEX_PATH = config.DATA_DIR / "faiss_index.bin"

_index = None
_dim = None
_use_faiss = True

try:
    import faiss
except ImportError:
    _use_faiss = False


def _load_from_db() -> tuple[np.ndarray, np.ndarray]:
    rows = db.q("SELECT chunk_id, blob FROM chunk_embeddings")
    if not rows:
        return np.zeros((0,), dtype=np.int64), np.zeros((0, 1), dtype=np.float32)
    ids = np.array([r["chunk_id"] for r in rows], dtype=np.int64)
    matrix = np.stack([np.frombuffer(r["blob"], dtype=np.float32) for r in rows])
    return ids, matrix


def _rebuild():
    global _index, _dim
    ids, matrix = _load_from_db()
    _dim = matrix.shape[1] if matrix.size else None
    if not matrix.size:
        _index = None
        return
    if _use_faiss:
        base = faiss.IndexFlatIP(matrix.shape[1])
        _index = faiss.IndexIDMap2(base)
        _index.add_with_ids(matrix, ids)
        faiss.write_index(_index, str(INDEX_PATH))
    else:
        _index = (ids, matrix)


def get_index():
    """Lazy-loaded index. The database is the source of truth: rebuild when
    the file is missing, empty, dimension-changed, or its vector count has
    drifted from the stored embeddings (self-heals stale or doubled files)."""
    global _index, _dim
    if _index is not None:
        return _index, _dim
    stored = db.q1("SELECT dim, COUNT(*) n FROM chunk_embeddings")
    db_dim, db_count = (stored["dim"], stored["n"]) if stored else (None, 0)
    if _use_faiss and INDEX_PATH.exists() and db_count:
        index = faiss.read_index(str(INDEX_PATH))
        if index.d == db_dim and index.ntotal == db_count:
            _index, _dim = index, index.d
            return _index, _dim
    _rebuild()
    return _index, _dim


def add(chunk_ids: list[int], vectors: np.ndarray):
    """Add freshly embedded chunks and persist the index."""
    global _index, _dim
    if not chunk_ids:
        return
    vectors = vectors.astype(np.float32)
    if _use_faiss:
        if _index is None:
            _index = faiss.IndexIDMap2(faiss.IndexFlatIP(vectors.shape[1]))
            _dim = vectors.shape[1]
        _index.add_with_ids(vectors, np.array(chunk_ids, dtype=np.int64))
        faiss.write_index(_index, str(INDEX_PATH))
    else:
        _rebuild()


def sync():
    """Rebuild the index from stored embeddings. Call after deletions so the
    file never keeps vectors whose rows are gone."""
    global _index, _dim
    _index, _dim = None, None
    if INDEX_PATH.exists():
        INDEX_PATH.unlink()
    _rebuild()


def invalidate():
    global _index, _dim
    _index, _dim = None, None


def search(query_vec: np.ndarray, k: int = 30,
           allowed_ids: set[int] | None = None) -> list[tuple[int, float]]:
    """Top-k cosine similarities as [(chunk_id, score), ...]."""
    index, dim = get_index()
    if index is None:
        return []
    q = query_vec.astype(np.float32).reshape(1, -1)
    if _use_faiss:
        fetch = max(k * 3, 50) if allowed_ids else k
        scores, ids = index.search(q, min(fetch, index.ntotal))
        out = [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i != -1]
        if allowed_ids is not None:
            out = [(i, s) for i, s in out if i in allowed_ids]
        return out[:k]
    # numpy fallback
    ids, matrix = index
    mask = np.isin(ids, list(allowed_ids)) if allowed_ids else np.ones(len(ids), bool)
    if not mask.any():
        return []
    sims = matrix[mask] @ q[0]
    sub_ids = ids[mask]
    order = np.argsort(-sims)[:k]
    return [(int(sub_ids[i]), float(sims[i])) for i in order]
