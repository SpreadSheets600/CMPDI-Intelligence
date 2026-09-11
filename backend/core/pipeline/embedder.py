"""Local embedding service. Tries the configured Gemma-family model first
and falls back down EMBEDDING_FALLBACKS automatically (e.g. when the primary
is HF-gated or the download fails). Vectors are normalized so FAISS inner
product equals cosine similarity."""

import numpy as np

from backend.core import config

_model = None
_model_name = None


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
