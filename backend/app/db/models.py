from __future__ import annotations

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    source_url: Mapped[str] = mapped_column(Text)
    agency: Mapped[str] = mapped_column(String(100))
    regulation_id: Mapped[str] = mapped_column(String(100))
    jurisdiction: Mapped[str] = mapped_column(String(20))
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    county: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry_sectors: Mapped[list[str]] = mapped_column(ARRAY(Text))
    min_employee_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_employee_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    full_text: Mapped[str] = mapped_column(Text)
    extra_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    required_document_types: Mapped[list[str]] = mapped_column(ARRAY(Text))
    required_workflows: Mapped[list[str]] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    token_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="chunks")
