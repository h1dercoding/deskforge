from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import DateTime

from src.database import Base
from src.models.base import UUIDMixin


class AuditLog(Base, UUIDMixin):
    __tablename__ = "audit_logs"

    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    tool_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("tools.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")
