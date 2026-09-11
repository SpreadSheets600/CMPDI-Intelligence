"""Initialize the system: folders, database, entities, report templates."""

import sys

from cmpdi_intel import config, db, facts, reports


def main():
    config.ensure_dirs()
    db.init_db()
    facts.ensure_subsidiary_entities()
    reports.ensure_templates()
    print(f"System Initialized At {config.DATA_DIR}")
    print(f"Database: {config.DB_PATH}")
    print(f"LLM Backend Mode: {config.LLM_BACKEND} "
          f"(Ollama URL: {config.OLLAMA_URL}, Model: {config.OLLAMA_MODEL})")
    print(f"Embedding Model: {config.EMBEDDING_MODEL} (fallbacks: {', '.join(config.EMBEDDING_FALLBACKS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
