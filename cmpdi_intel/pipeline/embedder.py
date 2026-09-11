"""Local embedding service. Tries the configured Gemma-family model first,
falls back down EMBEDDING_FALLBACKS automatically (e.g. when the primary is
HF-gated or download fails). Embeddings are cached in SQLite as float32 BLOBs."""

import numpy as np

from .. import config, db

_model = None
_model_name = None
_matrix = None  # np.ndarray (n, dim), rows aligned with chunk ids list
_ids = None


class EmbeddingUnavailable(RuntimeError):
    pass


def _prompt_wrap(text: str, is_query: bool) -> str:
    if "embeddinggemma" in _model_name.lower():
        if is_query:
            return f"task: search result | query: {text}"
        return f"title: none | text: {text}"
    return text


def load_model():
    global _model, _model_name
    if _model is not None:
        return
    from sentence_transformers import SentenceTransformer
    errors = []
    for name in [config.EMBEDDING_MODEL] + config.EMBEDDING_FALLBACKS:
        try:
            _model = SentenceTransformer(name, device="cpu")
            _model_name = name
            return
        except Exception as e:
            errors.append(f"{name}: {e}")
    raise EmbeddingUnavailable("No Embedding Model Could Be Loaded:\n" + "\n".join(errors))


def model_info() -> tuple[str, int]:
    load_model()
    return _model_name, _model.get_sentence_embedding_dimension()


def embed_texts(texts: list[str], is_query: bool = False) -> np.ndarray:
    load_model()
    wrapped = [_prompt_wrap(t, is_query) for t in texts]
    vecs = _model.encode(wrapped, batch_size=32, show_progress_bar=False,
                         normalize_embeddings=True)
    return np.asarray(vecs, dtype=np.float32)


def to_blob(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()


def from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def invalidate_cache():
    global _matrix, _ids
    _matrix, _ids = None, None


def vector_matrix():
    """Lazily loaded (ids, matrix) of all stored chunk embeddings."""
    global _matrix, _ids
    if _matrix is None:
        rows = db.q("SELECT chunk_id, blob FROM chunk_embeddings")
        _ids = np.array([r["chunk_id"] for r in rows], dtype=np.int64)
        if len(rows):
            _matrix = np.stack([from_blob(r["blob"]) for r in rows])
        else:
            _matrix = np.zeros((0, 1), dtype=np.float32)
    return _ids, _matrix


