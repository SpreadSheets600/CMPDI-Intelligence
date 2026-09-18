"""SQLAlchemy ORM models. Nullability and defaults mirror schema.sql exactly,
so every raw-SQL INSERT that was valid against schema.sql stays valid.
Python-side ``default=`` is only used where no raw insert omits the column;
DB-level ``server_default`` covers the rest (raw SQL bypasses ORM defaults).
"""

from __future__ import annotations

import math

from sqlalchemy import (REAL, ForeignKey, Index, LargeBinary, Text, text as sql_text)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _clean(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


class Base(DeclarativeBase):
    def to_dict(self) -> dict:
        return {c.key: _clean(getattr(self, c.key)) for c in self.__table__.columns}


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    sha256: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    content_norm: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    subsidiary: Mapped[str | None] = mapped_column(Text)
    doc_date_raw: Mapped[str | None] = mapped_column(Text)
    doc_date_norm: Mapped[str | None] = mapped_column(Text)
    is_current_version: Mapped[int] = mapped_column(nullable=False,
                                                    server_default=sql_text("1"))
    version_group_id: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(server_default=sql_text("0"))
    ocr_pages: Mapped[int | None] = mapped_column(server_default=sql_text("0"))
    upload_ts: Mapped[str] = mapped_column(Text, nullable=False,
                                           server_default=sql_text("datetime('now')"))
    status: Mapped[str] = mapped_column(Text, nullable=False,
                                        server_default=sql_text("'uploaded'"))
    structure_json: Mapped[str | None] = mapped_column(Text)

    pages: Mapped[list["Page"]] = relationship(back_populates="document",
                                               cascade="all, delete-orphan")
    elements: Mapped[list["Element"]] = relationship(back_populates="document",
                                                     cascade="all, delete-orphan")
    tables: Mapped[list["DocTable"]] = relationship(back_populates="document",
                                                    cascade="all, delete-orphan")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document",
                                                 cascade="all, delete-orphan")
    jobs: Mapped[list["Job"]] = relationship(back_populates="document",
                                             cascade="all, delete-orphan")
    keywords: Mapped[list["DocKeyword"]] = relationship(back_populates="document",
                                                        cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(Text, ForeignKey("documents.id", ondelete="CASCADE"),
                                        nullable=False)
    page_no: Mapped[int | None] = mapped_column()
    text: Mapped[str | None] = mapped_column(Text, server_default=sql_text("''"))
    summary: Mapped[str | None] = mapped_column(Text)
    ocr_used: Mapped[int] = mapped_column(nullable=False, server_default=sql_text("0"))
    avg_confidence: Mapped[float | None] = mapped_column(REAL)
    image_path: Mapped[str | None] = mapped_column(Text)
    page_class: Mapped[str | None] = mapped_column(Text)

    document: Mapped[Document] = relationship(back_populates="pages")


class Element(Base):
    __tablename__ = "elements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(Text, ForeignKey("documents.id", ondelete="CASCADE"),
                                        nullable=False)
    page_no: Mapped[int | None] = mapped_column()
    sheet_no: Mapped[int | None] = mapped_column()
    element_type: Mapped[str] = mapped_column(Text, nullable=False)
    order_idx: Mapped[int] = mapped_column(nullable=False)
    bbox: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str | None] = mapped_column(Text, server_default=sql_text("''"))
    conf: Mapped[float | None] = mapped_column(REAL)
    section_path: Mapped[str | None] = mapped_column(Text, server_default=sql_text("''"))
    method: Mapped[str | None] = mapped_column(Text)

    document: Mapped[Document] = relationship(back_populates="elements")


class DocTable(Base):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(Text, ForeignKey("documents.id", ondelete="CASCADE"),
                                        nullable=False)
    page_no: Mapped[int | None] = mapped_column()
    sheet_no: Mapped[int | None] = mapped_column()
    table_idx: Mapped[int] = mapped_column(nullable=False)
    n_rows: Mapped[int] = mapped_column(nullable=False)
    n_cols: Mapped[int] = mapped_column(nullable=False)
    headers_json: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped[Document] = relationship(back_populates="tables")
    cells: Mapped[list["TableCell"]] = relationship(back_populates="table",
                                                    cascade="all, delete-orphan")


class TableCell(Base):
    __tablename__ = "table_cells"

    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"),
                                          primary_key=True)
    row_idx: Mapped[int] = mapped_column(primary_key=True)
    col_idx: Mapped[int] = mapped_column(primary_key=True)
    value_raw: Mapped[str | None] = mapped_column(Text)
    value_norm: Mapped[float | None] = mapped_column(REAL)
    conf: Mapped[float | None] = mapped_column(REAL)

    table: Mapped[DocTable] = relationship(back_populates="cells")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(Text, ForeignKey("documents.id", ondelete="CASCADE"),
                                        nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    section_path: Mapped[str | None] = mapped_column(Text, server_default=sql_text("''"))
    page_no: Mapped[int | None] = mapped_column()
    sheet_no: Mapped[int | None] = mapped_column()
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column()
    element_ids_json: Mapped[str | None] = mapped_column(Text, server_default=sql_text("'[]'"))

    document: Mapped[Document] = relationship(back_populates="chunks")
    facts: Mapped[list["Fact"]] = relationship(back_populates="chunk",
                                               cascade="all, delete-orphan")
    embedding: Mapped["ChunkEmbedding | None"] = relationship(back_populates="chunk",
                                                              cascade="all, delete-orphan",
                                                              single_parent=True)


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"),
                                          primary_key=True)
    dim: Mapped[int] = mapped_column(nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    chunk: Mapped[Chunk] = relationship(back_populates="embedding")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    aliases_json: Mapped[str | None] = mapped_column(Text, server_default=sql_text("'[]'"))

    facts: Mapped[list["Fact"]] = relationship(back_populates="entity")

    reference: Mapped[list["EntityReference"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan")


class EntityReference(Base):
    """Curated public reference context for an organizational entity.

    Reference rows are context, never evidence: they describe the entity
    (headquarters, operating states, coalfields, dated public statistics)
    and must never enter the fact index, conflicts, answers or reports.
    Every row carries its public source and as-of date so staleness is
    visible instead of silent."""

    __tablename__ = "entity_reference"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"),
                                           nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    # profile | geography | production | statistic
    label: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(Text)
    as_of: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, nullable=False)

    entity: Mapped[Entity] = relationship(back_populates="reference")


class Fact(Base):
    __tablename__ = "facts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int | None] = mapped_column(ForeignKey("entities.id"))
    entity_text: Mapped[str | None] = mapped_column(Text)
    attribute: Mapped[str] = mapped_column(Text, nullable=False)
    period_norm: Mapped[str | None] = mapped_column(Text)
    value_raw: Mapped[str] = mapped_column(Text, nullable=False)
    value_norm: Mapped[float | None] = mapped_column(REAL)
    unit: Mapped[str | None] = mapped_column(Text)
    conf: Mapped[float | None] = mapped_column(REAL, server_default=sql_text("1.0"))
    flags: Mapped[str | None] = mapped_column(Text, server_default=sql_text("''"))
    chunk_id: Mapped[int | None] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"))

    entity: Mapped[Entity | None] = relationship(back_populates="facts")
    chunk: Mapped[Chunk | None] = relationship(back_populates="facts")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[str | None] = mapped_column(Text, ForeignKey("documents.id", ondelete="CASCADE"))
    stage: Mapped[str] = mapped_column(Text, nullable=False,
                                       server_default=sql_text("'uploaded'"))
    status: Mapped[str] = mapped_column(Text, nullable=False,
                                        server_default=sql_text("'pending'"))
    error: Mapped[str | None] = mapped_column(Text)
    stats_json: Mapped[str | None] = mapped_column(Text, server_default=sql_text("'{}'"))
    created_ts: Mapped[str] = mapped_column(Text, nullable=False,
                                            server_default=sql_text("datetime('now')"))
    updated_ts: Mapped[str] = mapped_column(Text, nullable=False,
                                            server_default=sql_text("datetime('now')"))

    document: Mapped[Document | None] = relationship(back_populates="jobs")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    params_json: Mapped[str] = mapped_column(Text, nullable=False)
    docx_path: Mapped[str | None] = mapped_column(Text)
    provenance_json: Mapped[str | None] = mapped_column(Text)
    human_approved: Mapped[int] = mapped_column(nullable=False, server_default=sql_text("0"))
    review_status: Mapped[str] = mapped_column(Text, nullable=False,
                                               server_default=sql_text("'pending'"))
    review_note: Mapped[str | None] = mapped_column(Text)
    created_ts: Mapped[str] = mapped_column(Text, nullable=False,
                                            server_default=sql_text("datetime('now')"))


class DocKeyword(Base):
    __tablename__ = "doc_keywords"

    doc_id: Mapped[str] = mapped_column(Text, ForeignKey("documents.id", ondelete="CASCADE"),
                                        primary_key=True)
    keyword: Mapped[str] = mapped_column(Text, primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False,
                                        server_default=sql_text("'tf'"))

    document: Mapped[Document] = relationship(back_populates="keywords")


class DocTopic(Base):
    __tablename__ = "doc_topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    keywords_json: Mapped[str] = mapped_column(Text, nullable=False)
    doc_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_ts: Mapped[str] = mapped_column(Text, nullable=False,
                                            server_default=sql_text("datetime('now')"))


class ConflictStatus(Base):
    __tablename__ = "conflict_status"

    conflict_key: Mapped[str] = mapped_column(Text, primary_key=True)
    status: Mapped[str] = mapped_column(Text, nullable=False,
                                        server_default=sql_text("'open'"))
    note: Mapped[str | None] = mapped_column(Text)
    updated_ts: Mapped[str] = mapped_column(Text, nullable=False,
                                            server_default=sql_text("datetime('now')"))


class KgEdge(Base):
    """P1 knowledge-graph edge: a typed relationship between two nodes.

    Nodes span organizations, mines, locations, geology, documents, metrics
    and events. Every evidence-backed edge carries its chunk -> page ->
    document provenance; derived edges (SUPERSEDES) carry doc ids only."""

    __tablename__ = "kg_edges"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    src_kind: Mapped[str] = mapped_column(Text, nullable=False)
    src_label: Mapped[str] = mapped_column(Text, nullable=False)
    src_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"))
    dst_kind: Mapped[str] = mapped_column(Text, nullable=False)
    dst_label: Mapped[str] = mapped_column(Text, nullable=False)
    dst_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"))
    relation: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("chunks.id", ondelete="CASCADE"))
    doc_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("documents.id", ondelete="CASCADE"))
    page_no: Mapped[int | None] = mapped_column()
    sheet_no: Mapped[int | None] = mapped_column()
    period_norm: Mapped[str | None] = mapped_column(Text)
    conf: Mapped[float | None] = mapped_column(REAL, server_default=sql_text("1.0"))


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    steps_json: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text)
    citations_json: Mapped[str | None] = mapped_column(Text)
    created_ts: Mapped[str] = mapped_column(Text, nullable=False,
                                            server_default=sql_text("datetime('now')"))


Index("idx_elements_doc", Element.doc_id)
Index("idx_cells_table", TableCell.table_id)
Index("idx_chunks_doc", Chunk.doc_id)
Index("idx_facts_key", Fact.entity_id, Fact.attribute, Fact.period_norm)
Index("idx_doc_keywords_kw", DocKeyword.keyword)
Index("idx_kg_edges_src", KgEdge.src_kind, KgEdge.src_label)
Index("idx_kg_edges_dst", KgEdge.dst_kind, KgEdge.dst_label)
Index("idx_kg_edges_doc", KgEdge.doc_id)
Index("idx_kg_edges_relation", KgEdge.relation)

__all__ = [
    "Base", "Document", "Page", "Element", "DocTable", "TableCell",
    "Chunk", "ChunkEmbedding", "Entity", "Fact", "Job", "Report",
    "DocKeyword", "DocTopic", "ConflictStatus", "AgentRun", "KgEdge",
]
