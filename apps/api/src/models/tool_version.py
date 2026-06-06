from sqlalchemy import func,  String, ForeignKey, Text, Integer, UniqueConstraint
from sqlalchemy import func,  JSON
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from sqlalchemy import func,  DateTime

from src.database import Base
from src.models.base import UUIDMixin


class ToolVersion(Base, UUIDMixin):
    __tablename__ = "tool_versions"
    __table_args__ = (UniqueConstraint("tool_id", "version_number", name="uq_tool_versions_tool_version"),)

    tool_id: Mapped[UUID] = mapped_column(ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    spec: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
