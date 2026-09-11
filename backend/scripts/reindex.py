"""Rebuild derived indexes for an existing library: keywords/tags,
metadata-enriched chunk embeddings, and the FAISS index. Run after upgrading
the embedding model or enabling keyword enrichment on an old database.

Usage: python -m backend.scripts.reindex"""

import sys

import numpy as np

from backend.core import config, db
from backend.core.keywords import extract_keywords
from backend.core.pipeline import vector_store
from backend.core.pipeline.embedder import embed_texts, model_info


def main():
    config.ensure_dirs()
    db.init_db()
    docs = db.q("SELECT id, doc_type, subsidiary FROM documents WHERE status='completed'")
    print(f"Reindexing {len(docs)} documents")

    # keywords first so embeddings can use them
    for d in docs:
        parts = [r["text"] for r in db.q("SELECT text FROM pages WHERE doc_id=?", (d["id"],))]
        parts += [r["text"] for r in db.q("SELECT text FROM elements WHERE doc_id=?", (d["id"],))]
        keywords, source = extract_keywords("\n".join(parts))
        conn = db.connect()
        conn.execute("DELETE FROM doc_keywords WHERE doc_id=?", (d["id"],))
        for kw in keywords:
            conn.execute("INSERT OR IGNORE INTO doc_keywords (doc_id, keyword, source) VALUES (?,?,?)",
                         (d["id"], kw, source))
        conn.commit()
        print(f"  keywords [{source}]: {d['id'][:10]} {', '.join(keywords[:4])}…")

    # enriched embeddings for every chunk
    model_name, dim = model_info()
    kw_map = {}
    for r in db.q("SELECT doc_id, keyword FROM doc_keywords"):
        kw_map.setdefault(r["doc_id"], []).append(r["keyword"])
    meta = {r["id"]: r for r in db.q("SELECT id, doc_type, subsidiary, filename FROM documents")}

    db.execute("DELETE FROM chunk_embeddings")
    db.execute("DELETE FROM chunks_fts")
    vector_store.invalidate()
    count = 0
    for d in docs:
        chunks = db.q("SELECT id, text FROM chunks WHERE doc_id=?", (d["id"],))
        if not chunks:
            continue
        m = meta[d["id"]]
        prefix = (f"Title: {d['id'][:0]}{m['filename']}\n"
                  f"Subsidiary: {m['subsidiary'] or ''}\n"
                  f"Doc Type: {d['doc_type']}\n"
                  f"Keywords: {', '.join(kw_map.get(d['id'], []))}\n\n")
        texts = [prefix + c["text"] for c in chunks]
        vectors = embed_texts(texts)
        conn = db.connect()
        for chunk, vec in zip(chunks, vectors):
            conn.execute("INSERT INTO chunk_embeddings (chunk_id, dim, model, blob) VALUES (?,?,?,?)",
                         (chunk["id"], int(vec.shape[0]), model_name, vec.astype(np.float32).tobytes()))
            conn.execute("INSERT INTO chunks_fts (rowid, text) VALUES (?,?)",
                         (chunk["id"], chunk["text"]))
        conn.commit()
        vector_store.add([c["id"] for c in chunks], vectors)
        count += len(chunks)
        print(f"  embedded {len(chunks):3d} chunks: {m['filename']}")
    print(f"Done. {count} chunks re-embedded with {model_name}; FAISS index at {config.DATA_DIR / 'faiss_index.bin'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
