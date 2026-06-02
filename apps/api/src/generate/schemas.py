from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=10, max_length=2000)
    data_source_id: Optional[UUID] = None
    template_id: Optional[str] = None


class IterateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ClarifyRequest(BaseModel):
    session_id: str
    answers: list[str]


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    prompt: str
    icon: Optional[str] = None
    preview_image: Optional[str] = None


class ToolSpecSchema:
    """JSON Schema for DeskForge tool specifications."""
    pass
