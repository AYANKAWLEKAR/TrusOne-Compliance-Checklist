from __future__ import annotations

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Regulation(Base):
    __tablename__ = "regulations"
    __table_args__ = (
        UniqueConstraint(
            "industry",
            "function",
            "state",
            "county",
            "city_jurisdiction",
            "level",
            "regulation_code_reference",
            name="uq_regulations_canonical_identity",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    industry: Mapped[str] = mapped_column(String(100))
    function: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    county: Mapped[str] = mapped_column(String(150))
    city_jurisdiction: Mapped[str] = mapped_column(String(150))
    level: Mapped[str] = mapped_column(String(50))
    jurisdiction_scope: Mapped[str] = mapped_column(String(50))
    applies_to_all_states: Mapped[bool] = mapped_column(default=False)
    applies_to_all_counties: Mapped[bool] = mapped_column(default=False)
    applies_to_all_cities: Mapped[bool] = mapped_column(default=False)
    regulation_name: Mapped[str] = mapped_column(String(500))
    regulation_code_reference: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    action_required: Mapped[str] = mapped_column(Text)
    external_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    vectors: Mapped[list["RegulationVector"]] = relationship(
        back_populates="regulation",
        cascade="all, delete-orphan",
    )
    document_links: Mapped[list["RegulationDocumentLink"]] = relationship(
        back_populates="regulation",
        cascade="all, delete-orphan",
    )


class RegulationVector(Base):
    __tablename__ = "regulation_vectors"

    id: Mapped[int] = mapped_column(primary_key=True)
    regulation_id: Mapped[int] = mapped_column(
        ForeignKey("regulations.id", ondelete="CASCADE"),
        unique=True,
    )
    search_text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    token_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    regulation: Mapped[Regulation] = relationship(back_populates="vectors")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    source_type: Mapped[str] = mapped_column(String(100))
    publisher_agency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    external_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingestion_status: Mapped[str] = mapped_column(String(50), default="pending")
    external_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    chunks: Mapped[list["SourceDocumentChunk"]] = relationship(
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    regulation_links: Mapped[list["RegulationDocumentLink"]] = relationship(
        back_populates="source_document",
        cascade="all, delete-orphan",
    )


class SourceDocumentChunk(Base):
    __tablename__ = "source_document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "chunk_index",
            name="uq_source_document_chunk_position",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE")
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    token_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_document: Mapped[SourceDocument] = relationship(back_populates="chunks")


class RegulationDocumentLink(Base):
    __tablename__ = "regulation_document_links"
    __table_args__ = (
        UniqueConstraint(
            "regulation_id",
            "source_document_id",
            "relationship_type",
            name="uq_regulation_document_link",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    regulation_id: Mapped[int] = mapped_column(ForeignKey("regulations.id", ondelete="CASCADE"))
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE")
    )
    relationship_type: Mapped[str] = mapped_column(String(100), default="supports")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    citation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    regulation: Mapped[Regulation] = relationship(back_populates="document_links")
    source_document: Mapped[SourceDocument] = relationship(back_populates="regulation_links")
