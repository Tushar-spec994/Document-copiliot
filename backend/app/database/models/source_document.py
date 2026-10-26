import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base

if TYPE_CHECKING:
    from app.database.models.document_chunk import DocumentChunk


class SourceDocument(Base):
    """Source filing document (e.g. 10-K) with normalized Markdown content."""

    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ticker: Mapped[str] = mapped_column(
        String(10),
        index=True,
        nullable=False,
        comment="Ticker symbol, e.g. AAPL, NVDA",
    )
    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    filing_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="10-K",
    )
    fiscal_year: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )
    filing_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    report_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    accession_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
        comment="SEC EDGAR accession number",
    )
    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    content_markdown: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full normalized Markdown extracted from SEC filing",
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )
