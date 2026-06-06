from sqlalchemy import String, ForeignKey, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from uuid import UUID

from src.database import Base
from src.models.base import UUIDMixin, TimestampMixin


class Tool(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tools"

    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    data_source_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    spec: Mapped[dict] = mapped_column(JSON, nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="private", server_default="private")
    theme: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list, server_default="[]")

    data_source = relationship("DataSource", lazy="selectin")
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")
