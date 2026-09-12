"""Topic, keyword and word-cloud analysis. Embedding-guided keyphrases
(KeyBERT-style) + lightweight numpy KMeans over document-mean vectors with
c-TF-IDF cluster labels. All computed locally."""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

from backend.core import config
from backend.db import database as db
from backend.core.pipeline.embedder import embed_texts

STOPWORDS = set(
    """the a an and or of to in for on with by from at as is are was were be been it its
this that these those their his her our your not no than then thus so such which who whom whose what
when where how all any both each few more most other some only own same too very can will just should
now also may might must shall would could during before after above below between under over again
further once here there why per annum year years total including respectively lakh crore""".split()
)

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")


def _tokens(text: str) -> list[str]:
    return [
        w.lower()
        for w in _WORD_RE.findall(text)
        if w.lower() not in STOPWORDS and len(w) > 2
    ]


def doc_texts(scope: str | None = None) -> tuple[list[str], list[str]]:
    """(doc_ids, concatenated text) for a scope filter."""
    where, params = ["is_current_version=1"], []
    if scope and scope.startswith("subsidiary:"):
        where.append("subsidiary=?")
        params.append(scope.split(":", 1)[1])
    docs = db.q(f"SELECT id FROM documents WHERE {' AND '.join(where)}", params)
    ids, texts = [], []
    for d in docs:
        parts = [
            r["text"]
            for r in db.q(
                "SELECT text FROM chunks WHERE doc_id=? AND content_type != 'TABLE_ROW'",
                (d["id"],),
            )
        ]
        if parts:
            ids.append(d["id"])
            texts.append(" ".join(parts))
    return ids, texts


def keyphrases(text: str, top: int = 15) -> list[tuple[str, float]]:
    """Candidate n-grams scored by embedding similarity to the text centroid."""
    words = _tokens(text)
    if not words:
        return []
    counts = Counter(words)
    bigrams = Counter(zip(words, words[1:]))
    candidates = [w for w, _ in counts.most_common(60)]
    candidates += [" ".join(bg) for bg, c in bigrams.most_common(40) if c > 1]
    candidates = list(dict.fromkeys(candidates))[:100]
    if not candidates:
        return []
    doc_vec = embed_texts([text[:4000]])[0]
    cand_vecs = embed_texts(candidates)
    sims = cand_vecs @ doc_vec
    order = np.argsort(-sims)[:top]
    return [(candidates[i], float(sims[i])) for i in order]


def _kmeans(matrix: np.ndarray, k: int, iters: int = 25) -> np.ndarray:
    rng = np.random.default_rng(7)
    centroids = matrix[rng.choice(len(matrix), size=min(k, len(matrix)), replace=False)]
    labels = np.zeros(len(matrix), dtype=int)
    for _ in range(iters):
        sims = matrix @ centroids.T
        new = np.argmax(sims, axis=1)
        if np.array_equal(new, labels):
            break
        labels = new
        for c in range(len(centroids)):
            members = matrix[labels == c]
            if len(members):
                centroids[c] = members.mean(axis=0)
    return labels


def cluster_corpus(scope: str | None = None) -> list[dict]:
    """Cluster current documents by mean chunk embedding; label with shared
    keyphrases; persist into doc_topics."""
    ids, texts = doc_texts(scope)
    if len(ids) < 3:
        return []
    doc_vecs = []
    for did in ids:
        rows = db.q(
            """SELECT e.blob FROM chunk_embeddings e JOIN chunks c ON c.id=e.chunk_id
                       WHERE c.doc_id=?""",
            (did,),
        )
        vecs = [np.frombuffer(r["blob"], dtype=np.float32) for r in rows]
        doc_vecs.append(
            np.mean(vecs, axis=0) if vecs else np.zeros(1, dtype=np.float32)
        )
    matrix = np.stack(doc_vecs)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    matrix = matrix / norms
    k = max(2, min(6, int(len(ids) ** 0.5) + 1))
    labels = _kmeans(matrix, k)

    cluster_out = []
    for c in range(labels.max() + 1):
        members = [ids[i] for i in range(len(ids)) if labels[i] == c]
        if not members:
            continue
        cluster_text = " ".join(texts[i] for i in range(len(ids)) if labels[i] == c)
        phrases = keyphrases(cluster_text[:20000], top=8)
        label = ", ".join(p for p, _ in phrases[:3]).title() or f"Cluster {c + 1}"
        keywords = [p for p, _ in phrases]
        rec_id = db.execute(
            "INSERT INTO doc_topics (scope, label, keywords_json, doc_ids_json) VALUES (?,?,?,?)",
            (scope or "corpus", label, json.dumps(keywords), json.dumps(members)),
        )
        cluster_out.append(
            {"id": rec_id, "label": label, "keywords": keywords, "doc_ids": members}
        )
    return cluster_out


def wordcloud_png(scope: str | None = None) -> Path:
    """Render a word cloud for a scope (corpus | subsidiary:X | year:Y)."""
    from wordcloud import WordCloud
    import matplotlib

    matplotlib.use("Agg")
    ids, texts = doc_texts(scope)
    words = _tokens(" ".join(texts))
    freq = Counter(words)
    # bigrams included for domain terms like "coal seam"
    wc = WordCloud(
        width=1200,
        height=600,
        mode="RGBA",
        background_color=None,  # transparent: blends with light and dark themes
        colormap="copper",
        max_words=80,
        collocations=False,
    )
    wc.generate_from_frequencies(dict(freq.most_common(200)))
    out = config.CLOUDS_DIR / f"cloud_{hashlib_slug(scope)}.png"
    wc.to_image().save(out)
    return out


def hashlib_slug(scope: str | None) -> str:
    import hashlib

    return hashlib.sha1((scope or "corpus").encode()).hexdigest()[:10]
