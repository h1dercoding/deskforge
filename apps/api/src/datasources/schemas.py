from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID


class CSVUploadResponse(BaseModel):
    source_id: UUID
    name: str
    row_count: int
    columns: list[dict]
    preview: list[dict]


class ConfirmCSVRequest(BaseModel):
    column_types: Optional[dict[str, str]] = None


class GoogleSheetsRequest(BaseModel):
    sheet_url: str
    tab_name: Optional[str] = None


class DatabaseConnectRequest(BaseModel):
    type: str = Field(pattern="^(postgresql|mysql)$")
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl: bool = True
    readonly: bool = True


class DataSourceResponse(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    type: str
    status: str
    row_count: int
    schema: Optional[dict] = None
    created_at: Any

    model_config = {"from_attributes": True}


class ConnectionTestResponse(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class ColumnSchema(BaseModel):
    name: str
    type: str
    nullable: bool = True
    sample_values: Optional[list] = None


class QueryRequest(BaseModel):
    query: dict = Field(default_factory=dict)


class QueryResponse(BaseModel):
    rows: list[dict]
    total: int
