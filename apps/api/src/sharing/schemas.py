"""Pydantic models for sharing endpoints."""
from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID
from datetime import datetime


class SharedToolResponse(BaseModel):
    """Response for a publicly shared tool."""
    id: UUID
    name: str
    description: Optional[str] = None
    spec: dict[str, Any]
    theme: dict[str, Any]
    visibility: str
    slug: str
    is_public: bool


class UpdateVisibilityRequest(BaseModel):
    """Request to update tool visibility."""
    visibility: str  # "public" or "private"


class UpdateVisibilityResponse(BaseModel):
    """Response after updating visibility."""
    id: UUID
    visibility: str
    slug: str


class RegenerateLinkResponse(BaseModel):
    """Response after regenerating share link."""
    slug: str
