"""Initialize the system: folders, database, entities, report templates."""

import sys

from backend.core import config
from backend.core.knowledge import facts, reference
from backend.db import database as db


def main():
    config.ensure_dirs()
    db.init_db()
    facts.ensure_subsidiary_entities()
    seeded = reference.seed_reference()
    print(f"System Initialized At {config.DATA_DIR}")
    print(f"Database: {config.DB_PATH}")
    print(f"Reference entries: {seeded['entries']} across {seeded['entities']} entities")
    print(f"LLM Backend Mode: {config.LLM_BACKEND} "
          f"(Ollama URL: {config.OLLAMA_URL}, Model: {config.OLLAMA_MODEL})")
    print(f"Embedding Model: {config.EMBEDDING_MODEL} (fallbacks: {', '.join(config.EMBEDDING_FALLBACKS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
