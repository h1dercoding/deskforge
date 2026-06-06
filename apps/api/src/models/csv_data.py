"""CSV row data stored in a dedicated table instead of JSONB config."""
from sqlalchemy import ForeignKey, Integer, Index
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID

from src.database import Base
from src.models.base import UUIDMixin


class CsvData(Base, UUIDMixin):
    """Stores individual CSV rows in a dedicated relational table.

    This replaces the previous approach of storing all CSV data as JSON
    in the DataSource.config JSONB column, which caused:
    - PostgreSQL bloat and slow queries
    - JSONB size limits for large datasets
    - Inefficient pagination (entire dataset loaded into memory)
    """
    __tablename__ = "csv_data"

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index("ix_csv_data_source_row", "source_id", "row_idx"),
    )
