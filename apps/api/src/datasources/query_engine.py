"""Unified query interface for all data source types."""
import logging
import re
from typing import Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import sqlalchemy as sa

from src.models.data_source import DataSource
from src.datasources.encryption import decrypt_dict
from src.exceptions import DataSourceNotFoundError, DatabaseQueryError

logger = logging.getLogger("deskforge.datasources.query")


async def execute_query(
    db: AsyncSession,
    data_source_id: UUID,
    team_id: UUID,
    filter_params: Optional[dict] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    page: int = 1,
    per_page: int = 50,
) -> dict:
    """Execute a query against a data source using the unified interface."""
    result = await db.execute(
        sa.select(DataSource).where(
            DataSource.id == data_source_id,
            DataSource.team_id == team_id,
        )
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise DataSourceNotFoundError()

    if source.type == "csv":
        return await _query_csv_source(source, filter_params, sort_by, sort_order, page, per_page)
    elif source.type == "google_sheets":
        return await _query_sheets_source(source, filter_params, sort_by, sort_order, page, per_page)
    elif source.type in ("postgresql", "mysql"):
        return await _query_database_source(source, filter_params, sort_by, sort_order, page, per_page)
    else:
        raise DatabaseQueryError(f"Unsupported source type: {source.type}")


async def _query_csv_source(
    source: DataSource,
    filter_params: Optional[dict],
    sort_by: Optional[str],
    sort_order: str,
    page: int,
    per_page: int,
) -> dict:
    """Query a CSV data source (stored as JSON in config)."""
    config = source.config
    rows = config.get("data", [])

    # Apply filters
    if filter_params:
        rows = _apply_filters(rows, filter_params)

    total = len(rows)

    # Apply sorting
    if sort_by and rows:
        reverse = sort_order == "desc"
        try:
            rows.sort(key=lambda r: r.get(sort_by, ""), reverse=reverse)
        except TypeError:
            pass

    # Apply pagination
    start = (page - 1) * per_page
    rows = rows[start:start + per_page]

    return {"rows": rows, "total": total}


async def _query_sheets_source(
    source: DataSource,
    filter_params: Optional[dict],
    sort_by: Optional[str],
    sort_order: str,
    page: int,
    per_page: int,
) -> dict:
    """Query a Google Sheets data source."""
    from src.datasources.google_sheets import fetch_sheet_data

    config = source.config
    access_token = config.get("access_token")
    spreadsheet_id = config.get("spreadsheet_id")
    tab_name = config.get("tab_name")

    if not access_token:
        raise DatabaseQueryError("Google Sheets access token missing")

    sheet_data = await fetch_sheet_data(access_token, spreadsheet_id, tab_name)
    rows = sheet_data.get("rows", [])

    if filter_params:
        rows = _apply_filters(rows, filter_params)

    total = len(rows)

    if sort_by and rows:
        reverse = sort_order == "desc"
        try:
            rows.sort(key=lambda r: r.get(sort_by, ""), reverse=reverse)
        except TypeError:
            pass

    start = (page - 1) * per_page
    rows = rows[start:start + per_page]

    return {"rows": rows, "total": total}


async def _query_database_source(
    source: DataSource,
    filter_params: Optional[dict],
    sort_by: Optional[str],
    sort_order: str,
    page: int,
    per_page: int,
) -> dict:
    """Query a PostgreSQL/MySQL data source."""
    from src.datasources.database_connector import execute_query as db_execute_query

    config = decrypt_dict(source.config)

    table = config.get("table", config.get("default_table", "public"))

    # Validate table and sort_by identifiers to prevent injection
    _validate_identifier(table)
    if sort_by:
        _validate_identifier(sort_by)

    where_clause = None
    bind_params: dict[str, Any] = {}
    if filter_params:
        where_clause, bind_params = _build_where_clause(filter_params)

    order_by = None
    if sort_by:
        order = "DESC" if sort_order == "desc" else "ASC"
        order_by = f"{sort_by} {order}"

    offset = (page - 1) * per_page
    rows, total = await db_execute_query(
        config=config,
        table=table,
        where=text(where_clause) if where_clause else None,
        where_params=bind_params,
        order_by=order_by,
        limit=per_page,
        offset=offset,
    )

    return {"rows": rows, "total": total}


def _apply_filters(rows: list[dict], filter_params: dict) -> list[dict]:
    """Apply filters to a list of rows."""
    filtered = rows
    for field, value in filter_params.items():
        if isinstance(value, dict):
            op = value.get("op", "eq")
            val = value.get("value")
            if op == "eq":
                filtered = [r for r in filtered if str(r.get(field, "")).lower() == str(val).lower()]
            elif op == "contains":
                filtered = [r for r in filtered if str(val).lower() in str(r.get(field, "")).lower()]
            elif op == "gt":
                filtered = [r for r in filtered if _compare(r.get(field), val, "gt")]
            elif op == "lt":
                filtered = [r for r in filtered if _compare(r.get(field), val, "lt")]
            elif op == "gte":
                filtered = [r for r in filtered if _compare(r.get(field), val, "gte")]
            elif op == "lte":
                filtered = [r for r in filtered if _compare(r.get(field), val, "lte")]
        else:
            filtered = [r for r in filtered if str(r.get(field, "")).lower() == str(value).lower()]
    return filtered


def _compare(a, b, op: str) -> bool:
    try:
        a_num = float(a) if a is not None else 0
        b_num = float(b) if b is not None else 0
        if op == "gt":
            return a_num > b_num
        elif op == "lt":
            return a_num < b_num
        elif op == "gte":
            return a_num >= b_num
        elif op == "lte":
            return a_num <= b_num
    except (ValueError, TypeError):
        return False
    return False


def _validate_identifier(name: str) -> None:
    """Validate that a string is a safe SQL identifier (alphanumeric + underscore only)."""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise DatabaseQueryError(f"Invalid identifier: {name}")


def _build_where_clause(filter_params: dict) -> tuple[Optional[str], dict[str, Any]]:
    """Build a parameterized SQL WHERE clause from filter params.

    Returns (clause_string, bind_params_dict). Uses numbered bind parameters
    to prevent SQL injection.
    """
    clauses: list[str] = []
    bind_params: dict[str, Any] = {}
    param_idx = 0

    for field, value in filter_params.items():
        # Validate field name as a safe identifier
        _validate_identifier(field)

        if isinstance(value, dict):
            op = value.get("op", "eq")
            val = value.get("value", "")

            if op == "eq":
                param_name = f"p{param_idx}"
                clauses.append(f"{field} = :{param_name}")
                bind_params[param_name] = val
                param_idx += 1
            elif op == "contains":
                param_name = f"p{param_idx}"
                clauses.append(f"{field}::text ILIKE :{param_name}")
                bind_params[param_name] = f"%{val}%"
                param_idx += 1
            elif op == "gt":
                param_name = f"p{param_idx}"
                clauses.append(f"{field} > :{param_name}")
                bind_params[param_name] = val
                param_idx += 1
            elif op == "lt":
                param_name = f"p{param_idx}"
                clauses.append(f"{field} < :{param_name}")
                bind_params[param_name] = val
                param_idx += 1
            elif op == "gte":
                param_name = f"p{param_idx}"
                clauses.append(f"{field} >= :{param_name}")
                bind_params[param_name] = val
                param_idx += 1
            elif op == "lte":
                param_name = f"p{param_idx}"
                clauses.append(f"{field} <= :{param_name}")
                bind_params[param_name] = val
                param_idx += 1
        else:
            param_name = f"p{param_idx}"
            clauses.append(f"{field} = :{param_name}")
            bind_params[param_name] = value
            param_idx += 1

    clause_str = " AND ".join(clauses) if clauses else None
    return clause_str, bind_params
