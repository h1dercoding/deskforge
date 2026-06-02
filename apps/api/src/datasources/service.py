"""Data source CRUD and schema detection."""
import logging
from uuid import UUID
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.data_source import DataSource
from src.datasources.encryption import encrypt_dict, decrypt_dict
from src.datasources.csv_handler import parse_csv, get_preview, df_to_records
from src.exceptions import DataSourceNotFoundError, AuthorizationError
import pandas as pd

logger = logging.getLogger("deskforge.datasources.service")


async def list_sources(db: AsyncSession, team_id: UUID) -> list[DataSource]:
    """List all data sources for a team."""
    result = await db.execute(
        sa.select(DataSource).where(DataSource.team_id == team_id).order_by(DataSource.created_at.desc())
    )
    return list(result.scalars().all())


async def get_source(db: AsyncSession, source_id: UUID, team_id: UUID) -> DataSource:
    """Get a data source by ID."""
    result = await db.execute(
        sa.select(DataSource).where(DataSource.id == source_id, DataSource.team_id == team_id)
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise DataSourceNotFoundError()
    return source


async def create_csv_source(
    db: AsyncSession,
    team_id: UUID,
    file_content: bytes,
    filename: str,
) -> tuple[DataSource, list[dict], dict]:
    """Create a data source from CSV/Excel upload.

    TODO: For production, CSV data should be stored in a dedicated table or file storage
    (e.g., S3/local file) rather than in the JSONB config column. Storing large datasets
    (potentially 100K+ rows per FR-030) as JSON in a single row causes:
    - PostgreSQL bloat and slow queries
    - JSONB size limits for very large datasets
    - Inefficient pagination (entire dataset loaded into memory)
    Consider migrating to a `csv_data` table with (source_id, row_idx, data) schema.
    """
    df, schema = parse_csv(file_content, filename)
    preview = get_preview(df, 20)
    records = df_to_records(df)

    name = filename.rsplit(".", 1)[0]
    config = {"data": records, "filename": filename}

    source = DataSource(
        team_id=team_id,
        name=name,
        type="csv",
        config=config,
        schema_=schema,
        row_count=len(records),
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    return source, preview, schema


async def confirm_csv_source(
    db: AsyncSession,
    source_id: UUID,
    team_id: UUID,
    column_types: Optional[dict[str, str]] = None,
) -> DataSource:
    """Confirm CSV import with optional column type overrides."""
    source = await get_source(db, source_id, team_id)

    if column_types and source.schema_:
        columns = source.schema_.get("columns", [])
        for col in columns:
            if col["name"] in column_types:
                col["type"] = column_types[col["name"]]
        source.schema_["columns"] = columns
        await db.commit()
        await db.refresh(source)

    return source


async def create_sheets_source(
    db: AsyncSession,
    team_id: UUID,
    access_token: str,
    spreadsheet_id: str,
    tab_name: str,
    sheet_data: dict,
) -> DataSource:
    """Create a data source from Google Sheets."""
    from src.datasources.encryption import encrypt

    config = {
        "access_token": access_token,
        "spreadsheet_id": spreadsheet_id,
        "tab_name": tab_name,
    }
    encrypted_config = encrypt_dict(config)

    columns = []
    for col_name in sheet_data.get("columns", []):
        columns.append({"name": col_name, "type": "text", "nullable": True})

    schema = {"columns": columns, "row_count": sheet_data.get("row_count", 0)}

    source = DataSource(
        team_id=team_id,
        name=f"Google Sheet: {spreadsheet_id}",
        type="google_sheets",
        config=encrypted_config if isinstance(encrypted_config, dict) else config,
        schema_=schema,
        row_count=sheet_data.get("row_count", 0),
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def create_database_source(
    db: AsyncSession,
    team_id: UUID,
    db_type: str,
    config: dict,
    schema_info: dict,
) -> DataSource:
    """Create a data source from database connection."""
    encrypted_config = encrypt_dict(config)

    source = DataSource(
        team_id=team_id,
        name=f"{db_type}: {config.get('host')}/{config.get('database')}",
        type=db_type,
        config={"encrypted": encrypted_config},
        schema_=schema_info,
        row_count=0,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def delete_source(db: AsyncSession, source_id: UUID, team_id: UUID) -> None:
    """Delete a data source."""
    source = await get_source(db, source_id, team_id)
    await db.delete(source)
    await db.commit()


async def get_source_schema(db: AsyncSession, source_id: UUID, team_id: UUID) -> dict:
    """Get the schema for a data source."""
    source = await get_source(db, source_id, team_id)
    if source.schema_:
        return source.schema_
    return {"columns": []}
