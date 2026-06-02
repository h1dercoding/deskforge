from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from uuid import UUID

from src.database import Base
from src.models.base import UUIDMixin, TimestampMixin


class DataSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "data_sources"

    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    schema_: Mapped[Optional[dict]] = mapped_column("schema", JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="connected", server_default="'connected'")
    row_count: Mapped[int] = mapped_column(Integer, server_default="0", default=0)
