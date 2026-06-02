from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import DateTime

from src.database import Base
from src.models.base import UUIDMixin


class PasswordReset(Base, UUIDMixin):
    __tablename__ = "password_resets"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")
