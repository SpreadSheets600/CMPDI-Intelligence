"""SQLAlchemy-backed database layer. Single SQLite file, WAL mode.

Public API:
  init_db()        create tables (incl. FTS5) + idempotent migrations
  session_scope()  transactional scope: ``with session_scope() as s: ...``
  get_session()    raw scoped session (caller manages commit/close)
  q(sql, params)   SELECT-many -> list[CleanRow]  (compat, via SQLAlchemy text())
  q1(sql, params)  SELECT-one  -> CleanRow | None (compat)
  execute(sql, params)  INSERT/UPDATE/DELETE + commit -> lastrowid (compat)
  connect()        legacy shim returning a SQLAlchemy-backed connection so
                   existing ``conn.execute(...); conn.commit()`` blocks keep
                   working while modules migrate to ORM sessions.

Complex lexical queries (FTS5 MATCH / bm25) stay as text() — virtual tables
have no PK and cannot be mapped. Everything else should prefer the ORM
models in backend.db.models.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

from backend.core import config
from backend.db.models import Base

_engine: Engine | None = None
_Session: scoped_session | None = None


def _apply_pragmas(dbapi_conn, _rec):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA busy_timeout=10000")
    cur.close()


def _get_engine() -> Engine:
    global _engine, _Session
    if _engine is None:
        config.ensure_dirs()
        _engine = create_engine(
            f"sqlite:///{config.DB_PATH}",
            connect_args={"check_same_thread": False, "timeout": 10},
            future=True,
        )
        event.listen(_engine, "connect", _apply_pragmas)
        _Session = scoped_session(
            sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
        )
    return _engine


def get_session():
    """Return the thread-local scoped session (SQLAlchemy ORM)."""
    _get_engine()
    assert _Session is not None
    return _Session()


@contextmanager
def session_scope() -> Iterator:
    """Transactional ORM scope with automatic commit/rollback.

    Usage:
        with session_scope() as s:
            s.add(Document(id=..., ...))
    """
    s = get_session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise


# ---------------------------------------------------------------- clean rows


def _no_nan(value):
    """NaN can enter numeric columns from parsed spreadsheets; JSON forbids
    it (the browser's response.json() throws on the literal), so every float
    leaving this module is null instead of NaN."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


class CleanRow(dict):
    """A plain dict that sanitizes NaN to null on every access and still
    supports the integer indexing the old sqlite3.Row offered."""

    _order: tuple = ()

    def __init__(self, keys, values=None):
        if values is not None:
            super().__init__(zip(keys, values))
            self._order = tuple(keys)
        else:
            super().__init__(keys)
            try:
                self._order = tuple(keys.keys())
            except Exception:
                self._order = tuple(super().keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            key = self._order[key]
        return _no_nan(super().__getitem__(key))


def _named(sql: str, params) -> tuple[str, dict]:
    """Convert ``?`` placeholders to ``:p0, :p1, ...`` for text()."""
    if not params:
        return sql, {}
    seq = list(params.values()) if isinstance(params, dict) else list(params)
    if isinstance(params, dict):
        return sql, dict(params)
    out, idx = [], 0
    for ch in sql:
        if ch == "?":
            out.append(f":p{idx}")
            idx += 1
        else:
            out.append(ch)
    return "".join(out), {f"p{i}": v for i, v in enumerate(seq)}


def q(sql: str, params=()) -> list[CleanRow]:
    stmt, bind = _named(sql, params or ())
    with _get_engine().connect() as conn:
        res = conn.execute(text(stmt), bind)
        keys = list(res.keys())
        return [CleanRow(keys, row) for row in res.fetchall()]


def q1(sql: str, params=()):
    stmt, bind = _named(sql, params or ())
    with _get_engine().connect() as conn:
        res = conn.execute(text(stmt), bind)
        keys = list(res.keys())
        row = res.fetchone()
        return CleanRow(keys, row) if row is not None else None


def execute(sql: str, params=()) -> int:
    stmt, bind = _named(sql, params or ())
    with _get_engine().begin() as conn:
        res = conn.execute(text(stmt), bind)
        try:
            return res.lastrowid or 0
        except Exception:
            return 0


# ------------------------------------------------------- legacy connect shim


class _CompatCursor:
    def __init__(self, result):
        self._r = result
        try:
            self.lastrowid = result.lastrowid or 0
        except Exception:
            self.lastrowid = 0

    def fetchall(self):
        return self._r.fetchall()

    def fetchone(self):
        return self._r.fetchone()


class _CompatConnection:
    """Mimics the subset of sqlite3.Connection used across the codebase:
    execute(sql, params?) -> cursor with .lastrowid/.fetch*, commit()."""

    def __init__(self, sa_conn):
        self._c = sa_conn  # SQLAlchemy autobegins on execute; commit() below ends it

    def execute(self, sql: str, params=()):
        # PRAGMA / DDL pass through untouched
        if sql.strip().upper().startswith("PRAGMA"):
            self._c.exec_driver_sql(sql)
            return _CompatCursor(_EmptyResult())
        stmt, bind = _named(sql, params or ())
        try:
            res = self._c.execute(text(stmt), bind)
        except Exception:
            # DDL with ? never happens; fall back to driver SQL
            res = self._c.exec_driver_sql(sql)
        keys = []
        try:
            keys = list(res.keys())
        except Exception:
            pass
        cur = _CompatCursor(res)
        cur.keys = keys
        return cur

    def executescript(self, script: str):
        for stmt in script.split(";"):
            if stmt.strip():
                self._c.exec_driver_sql(stmt)
        return self

    def cursor(self):
        """DBAPI cursor for drivers that need it (e.g. pandas read_sql)."""
        return self._c.connection.cursor()

    def rollback(self):
        try:
            if self._c.in_transaction():
                self._c.rollback()
        except Exception:
            pass
        return self

    def commit(self):
        try:
            if self._c.in_transaction():
                self._c.commit()
        except Exception:
            pass
        return self

    def close(self):
        try:
            self._c.close()
        except Exception:
            pass


class _EmptyResult:
    def fetchall(self):
        return []

    def fetchone(self):
        return None


def connect():
    """Legacy entry point. Returns a SQLAlchemy-backed connection shim.

    New code should use ``session_scope()`` + ORM models instead.
    """
    return _CompatConnection(_get_engine().connect())


# ------------------------------------------------------------------- schema

_FTS_DDL = """CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text, content='', content_rowid='id', tokenize='porter unicode61'
)"""


def init_db():
    eng = _get_engine()
    with eng.begin() as conn:
        Base.metadata.create_all(bind=conn)
        conn.execute(text(_FTS_DDL))
    _migrate()
    # keep FTS rows consistent with chunks on fresh boots (no-op otherwise)
    try:
        with eng.begin() as conn:
            n_chunks = conn.execute(text("SELECT COUNT(*) FROM chunks")).scalar() or 0
            try:
                n_fts = (
                    conn.execute(text("SELECT COUNT(*) FROM chunks_fts")).scalar() or 0
                )
            except Exception:
                n_fts = 0
            if n_chunks and not n_fts:
                for cid, txt in conn.execute(text("SELECT id, text FROM chunks")):
                    conn.execute(
                        text("INSERT INTO chunks_fts (rowid, text) VALUES (:c, :t)"),
                        {"c": cid, "t": txt},
                    )
    except Exception:
        pass


def _migrate():
    """Idempotent column additions for databases created before these fields
    existed; create_all() alone never amends an existing table."""
    eng = _get_engine()
    insp = inspect(eng)
    with eng.begin() as conn:
        if "documents" in insp.get_table_names():
            existing = {c["name"] for c in insp.get_columns("documents")}
            for col, ddl in [
                ("display_name", "TEXT"),
                ("summary", "TEXT"),
                ("content_norm", "TEXT"),
                ("structure_json", "TEXT"),
            ]:
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE documents ADD COLUMN {col} {ddl}"))
        if "reports" in insp.get_table_names():
            rcols = {c["name"] for c in insp.get_columns("reports")}
            for col, ddl in [
                ("review_status", "TEXT NOT NULL DEFAULT 'pending'"),
                ("review_note", "TEXT"),
            ]:
                if col not in rcols:
                    conn.execute(text(f"ALTER TABLE reports ADD COLUMN {col} {ddl}"))
        if "pages" in insp.get_table_names():
            pcols = {c["name"] for c in insp.get_columns("pages")}
            if "page_class" not in pcols:
                conn.execute(text("ALTER TABLE pages ADD COLUMN page_class TEXT"))
            if "summary" not in pcols:
                conn.execute(text("ALTER TABLE pages ADD COLUMN summary TEXT"))
        if "elements" in insp.get_table_names():
            ecols = {c["name"] for c in insp.get_columns("elements")}
            if "method" not in ecols:
                conn.execute(text("ALTER TABLE elements ADD COLUMN method TEXT"))
        if "kg_edges" not in insp.get_table_names():
            conn.execute(text(
                """CREATE TABLE kg_edges (
                    id INTEGER PRIMARY KEY,
                    src_kind TEXT NOT NULL,
                    src_label TEXT NOT NULL,
                    src_entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                    dst_kind TEXT NOT NULL,
                    dst_label TEXT NOT NULL,
                    dst_entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                    relation TEXT NOT NULL,
                    chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
                    doc_id TEXT REFERENCES documents(id) ON DELETE CASCADE,
                    page_no INTEGER,
                    sheet_no INTEGER,
                    period_norm TEXT,
                    conf REAL DEFAULT 1.0,
                    UNIQUE (src_kind, src_label, dst_kind, dst_label, relation, chunk_id)
                )"""))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_kg_edges_src ON kg_edges(src_kind, src_label)"))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_kg_edges_dst ON kg_edges(dst_kind, dst_label)"))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_kg_edges_doc ON kg_edges(doc_id)"))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_kg_edges_relation ON kg_edges(relation)"))
