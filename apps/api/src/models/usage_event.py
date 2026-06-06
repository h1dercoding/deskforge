from sqlalchemy import func,  String, ForeignKey
from sqlalchemy import func,  JSON
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import func,  DateTime

from src.database import Base
from src.models.base import UUIDMixin


class UsageEvent(Base, UUIDMixin):
    __tablename__ = "usage_events"

    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Renamed from 'metadata' to avoid conflict with SQLAlchemy's reserved attribute
    event_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
