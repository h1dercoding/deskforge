import logging
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.dependencies import get_db, get_current_user, get_team_membership, require_role
from src.models.user import User
from src.models.team_member import TeamMember
from src.teams.service import get_team_for_user
from src.datasources.service import (
    list_sources,
    get_source,
    create_csv_source,
    confirm_csv_source,
    create_database_source,
    delete_source,
    get_source_schema,
)
from src.datasources.database_connector import test_connection, get_schema as get_db_schema
from src.datasources.encryption import encrypt_dict
from src.datasources.query_engine import execute_query
from src.datasources.schemas import (
    DataSourceResponse,
    CSVUploadResponse,
    ConfirmCSVRequest,
    GoogleSheetsRequest,
    DatabaseConnectRequest,
    ConnectionTestResponse,
    QueryRequest,
    QueryResponse,
    ColumnSchema,
)
from src.auth.oauth import get_google_auth_url, exchange_google_code
from src.datasources.google_sheets import extract_spreadsheet_id, fetch_sheet_data, get_spreadsheet_metadata

logger = logging.getLogger("deskforge.datasources")

router = APIRouter(prefix="/datasources", tags=["Data Sources"])


@router.get("", response_model=dict)
async def list_sources_endpoint(
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    current_user, membership = auth_data
    sources = await list_sources(db, membership.team_id)
    return {
        "data": {
            "sources": [
                DataSourceResponse(
                    id=s.id,
                    team_id=s.team_id,
                    name=s.name,
                    type=s.type,
                    status=s.status,
                    row_count=s.row_count,
                    schema=s.schema_,
                    created_at=s.created_at,
                )
                for s in sources
            ]
        }
    }


@router.post("/csv", response_model=dict, status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    current_user, membership = auth_data
    content = await file.read()
    source, preview, schema = await create_csv_source(
        db, membership.team_id, content, file.filename or "upload.csv"
    )
    return {
        "data": {
            "source": DataSourceResponse(
                id=source.id,
                team_id=source.team_id,
                name=source.name,
                type=source.type,
                status=source.status,
                row_count=source.row_count,
                schema=source.schema_,
                created_at=source.created_at,
            ),
            "preview": preview,
        }
    }


@router.post("/csv/{source_id}/confirm", response_model=dict)
async def confirm_csv(
    source_id: UUID,
    body: ConfirmCSVRequest = ConfirmCSVRequest(),
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    current_user, membership = auth_data
    source = await confirm_csv_source(db, source_id, membership.team_id, body.column_types)
    return {
        "data": {
            "source": DataSourceResponse(
                id=source.id,
                team_id=source.team_id,
                name=source.name,
                type=source.type,
                status=source.status,
                row_count=source.row_count,
                schema=source.schema_,
                created_at=source.created_at,
            )
        }
    }


@router.get("/google-sheets/auth-url", response_model=dict)
async def google_sheets_auth_url(current_user: User = Depends(get_current_user)):
    url = await get_google_auth_url()
    return {"data": {"url": url}}


@router.get("/google-sheets/callback", response_model=dict)
async def google_sheets_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    current_user, membership = auth_data
    tokens = await exchange_google_code(code)
    if not tokens:
        from src.exceptions import GoogleSheetsError
        raise GoogleSheetsError("Failed to exchange OAuth code")
    return {"data": {"connected": True, "access_token": tokens.get("access_token")}}


@router.post("/google-sheets", response_model=dict, status_code=201)
async def connect_google_sheets(
    body: GoogleSheetsRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    current_user, membership = auth_data
    spreadsheet_id = extract_spreadsheet_id(body.sheet_url)
    if not spreadsheet_id:
        from src.exceptions import ValidationError
        raise ValidationError("Invalid Google Sheets URL")

    # For now, return placeholder - full integration requires OAuth token storage
    return {
        "data": {
            "source": {
                "id": str(UUID(int=0)),
                "name": f"Google Sheet: {spreadsheet_id}",
                "type": "google_sheets",
                "status": "connected",
            }
        }
    }


@router.post("/database", response_model=dict, status_code=201)
async def connect_database(
    body: DatabaseConnectRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    current_user, membership = auth_data

    config = {
        "type": body.type,
        "host": body.host,
        "port": body.port,
        "database": body.database,
        "username": body.username,
        "password": body.password,
        "ssl": body.ssl,
        "readonly": body.readonly,
    }

    # Test connection first
    await test_connection(config)

    # Get schema
    schema_info = await get_db_schema(config)

    source = await create_database_source(db, membership.team_id, body.type, config, schema_info)

    return {
        "data": {
            "source": DataSourceResponse(
                id=source.id,
                team_id=source.team_id,
                name=source.name,
                type=source.type,
                status=source.status,
                row_count=source.row_count,
                schema=source.schema_,
                created_at=source.created_at,
            )
        }
    }


@router.post("/{source_id}/test", response_model=dict)
async def test_source_connection(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    current_user, membership = auth_data
    source = await get_source(db, source_id, membership.team_id)

    if source.type in ("postgresql", "mysql"):
        from src.datasources.encryption import decrypt_dict
        config = decrypt_dict(source.config)
        result = await test_connection(config)
        return {"data": result}

    return {"data": {"status": "connected"}}


@router.get("/{source_id}/schema", response_model=dict)
async def get_source_schema_endpoint(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    current_user, membership = auth_data
    schema = await get_source_schema(db, source_id, membership.team_id)
    columns = schema.get("columns", [])
    return {
        "data": {
            "columns": [
                ColumnSchema(
                    name=c.get("name", ""),
                    type=c.get("type", "text"),
                    nullable=c.get("nullable", True),
                    sample_values=c.get("sample_values"),
                )
                for c in columns
            ]
        }
    }


@router.delete("/{source_id}", response_model=dict)
async def delete_source_endpoint(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    current_user, membership = auth_data
    await delete_source(db, source_id, membership.team_id)
    return {"data": {"success": True}}


@router.post("/{source_id}/query", response_model=dict)
async def query_source(
    source_id: UUID,
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    current_user, membership = auth_data
    query_params = body.query

    result = await execute_query(
        db=db,
        data_source_id=source_id,
        team_id=membership.team_id,
        filter_params=query_params.get("filter"),
        sort_by=query_params.get("sort"),
        sort_order=query_params.get("sort_order", "asc"),
        page=query_params.get("page", 1),
        per_page=query_params.get("per_page", 50),
    )

    return {
        "data": {
            "rows": result["rows"],
            "total": result["total"],
        }
    }
