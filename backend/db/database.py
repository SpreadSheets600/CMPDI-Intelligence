import math
import pathlib
import sqlite3

from backend.core import config

_conn: sqlite3.Connection | None = None


class CleanRow(sqlite3.Row):
    def __getitem__(self, key):
        v = super().__getitem__(key)
        if isinstance(v, float) and math.isnan(v):
            return None
        return v


def connect() -> sqlite3.Connection:
    """Single shared connection. WAL mode lets UI reads run while the
    ingestion worker writes. check_same_thread=False because Flask serves
    requests from worker threads; all writes are short transactions."""
    global _conn
    if _conn is None:
        config.ensure_dirs()
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.row_factory = CleanRow
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
    rcols = {r["name"] for r in conn.execute("PRAGMA table_info(reports)")}
    for col, ddl in [("review_status", "TEXT NOT NULL DEFAULT 'pending'"),
                     ("review_note", "TEXT")]:
        if col not in rcols:
            conn.execute(f"ALTER TABLE reports ADD COLUMN {col} {ddl}")


def _no_nan(value):
    """NaN can enter numeric columns from parsed spreadsheets; JSON forbids
    it (the browser's response.json() throws on the literal), so every float
    leaving this module is null instead of NaN."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


class CleanRow(dict):
    """A plain dict that (a) sanitizes NaN to null on every access and
    (b) still supports the integer indexing sqlite3.Row offered. Doubles as
    the sqlite3 row factory (called as CleanRow(cursor, row_tuple))."""

    _order: tuple = ()

    def __init__(self, cursor_or_row, row=None):
        if row is not None:  # row-factory invocation: (cursor, value_tuple)
            keys = [d[0] for d in cursor_or_row.description]
            super().__init__(zip(keys, row))
            self._order = tuple(keys)
        else:                # direct construction from a Row
            super().__init__(cursor_or_row)
            self._order = tuple(cursor_or_row.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            key = self._order[key]
        return _no_nan(super().__getitem__(key))


def q(sql: str, params=()) -> list[sqlite3.Row]:
    return [CleanRow(r) for r in connect().execute(sql, params).fetchall()]


def q1(sql: str, params=()) -> sqlite3.Row | None:
    row = connect().execute(sql, params).fetchone()
    return CleanRow(row) if row is not None else None


def execute(sql: str, params=()) -> int:
    cur = connect().execute(sql, params)
    connect().commit()
    return cur.lastrowid
