from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID
from datetime import datetime


class CreateToolRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=10, max_length=2000)
    spec: dict[str, Any]
    data_source_id: Optional[UUID] = None
    description: Optional[str] = None


class UpdateToolRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    theme: Optional[dict[str, Any]] = None


class ToolResponse(BaseModel):
    id: UUID
    team_id: UUID
    created_by: UUID
    data_source_id: Optional[UUID] = None
    name: str
    slug: str
    description: Optional[str] = None
    prompt: str
    spec: dict[str, Any]
    visibility: str
    theme: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ToolVersionResponse(BaseModel):
    id: UUID
    tool_id: UUID
    version_number: int
    prompt: str
    spec: dict[str, Any]
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ToolListResponse(BaseModel):
    tools: list[ToolResponse]
