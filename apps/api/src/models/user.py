from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from src.database import Base
from src.models.base import UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False, default="local", server_default="'local'")
    google_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
