import pathlib
import sqlite3

from backend.core import config

_conn: sqlite3.Connection | None = None


def connect() -> sqlite3.Connection:
    """Single shared connection. WAL mode lets UI reads run while the
    ingestion worker writes. check_same_thread=False because Flask serves
    requests from worker threads; all writes are short transactions."""
    global _conn
    if _conn is None:
        config.ensure_dirs()
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _conn.execute("PRAGMA busy_timeout=10000")
    return _conn


def init_db():
    conn = connect()
    schema = (pathlib.Path(__file__).parent / "schema.sql").read_text()
    conn.executescript(schema)
    _migrate(conn)
    conn.commit()


def _migrate(conn):
    """Idempotent column additions for databases created before these fields
    existed; CREATE TABLE IF NOT EXISTS alone never amends an existing table."""
    existing = {r["name"] for r in conn.execute("PRAGMA table_info(documents)")}
    for col, ddl in [
        ("display_name", "TEXT"),
        ("summary", "TEXT"),
        ("content_norm", "TEXT"),
    ]:
        if col not in existing:
            conn.execute(f"ALTER TABLE documents ADD COLUMN {col} {ddl}")


def q(sql: str, params=()) -> list[sqlite3.Row]:
    return connect().execute(sql, params).fetchall()


def q1(sql: str, params=()) -> sqlite3.Row | None:
    return connect().execute(sql, params).fetchone()


def execute(sql: str, params=()) -> int:
    cur = connect().execute(sql, params)
    connect().commit()
    return cur.lastrowid
