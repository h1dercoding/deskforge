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

# Maximum rows that can be requested
MAX_PER_PAGE = 10000


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
    # Enforce max per_page
    per_page = min(per_page, MAX_PER_PAGE)

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
        return await _query_csv_source(db, source, filter_params, sort_by, sort_order, page, per_page)
    elif source.type == "google_sheets":
        return await _query_sheets_source(source, filter_params, sort_by, sort_order, page, per_page)
    elif source.type in ("postgresql", "mysql"):
        return await _query_database_source(source, filter_params, sort_by, sort_order, page, per_page)
    else:
        raise DatabaseQueryError(f"Unsupported source type: {source.type}")


async def _query_csv_source(
    db: AsyncSession,
    source: DataSource,
    filter_params: Optional[dict],
    sort_by: Optional[str],
    sort_order: str,
    page: int,
    per_page: int,
) -> dict:
    """Query a CSV data source stored in the dedicated csv_data table.

    Uses SQL queries with OFFSET/LIMIT for efficient pagination
    instead of loading all rows into memory.
    """
    import sqlalchemy as sa
    from src.models.csv_data import CsvData
    # Build base query
    base_query = sa.select(CsvData.data).where(CsvData.source_id == source.id)
    count_query = sa.select(sa.func.count()).select_from(CsvData).where(CsvData.source_id == source.id)

    # Apply filters (in-memory for JSON data since SQLite/PostgreSQL JSON
    # query syntax differs; for large datasets, consider PostgreSQL JSONB operators)
    if filter_params:
        # Fetch all for filtering (we still paginate after)
        result = await db.execute(base_query.order_by(CsvData.row_idx))
        all_rows = [row[0] for row in result.all()]
        filtered = _apply_filters(all_rows, filter_params)
        total = len(filtered)

        # Apply sorting
        if sort_by and filtered:
            reverse = sort_order == "desc"
            try:
                filtered.sort(key=lambda r: r.get(sort_by, ""), reverse=reverse)
            except TypeError:
                pass

        # Apply pagination
        start = (page - 1) * per_page
        rows = filtered[start:start + per_page]
    else:
        # No filters — use SQL pagination directly
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        offset = (page - 1) * per_page
        query = base_query.order_by(CsvData.row_idx).offset(offset).limit(per_page)
        result = await db.execute(query)
        rows = [row[0] for row in result.all()]

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
    """Query a PostgreSQL/MySQL data source with readonly enforcement."""
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

    # Check readonly flag from config
    readonly = config.get("readonly", False)

    rows, total = await db_execute_query(
        config=config,
        table=table,
        where=text(where_clause) if where_clause else None,
        where_params=bind_params,
        order_by=order_by,
        limit=per_page,
        offset=offset,
        readonly=readonly,
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


async def execute_aggregation(
    db: AsyncSession,
    data_source_id: UUID,
    team_id: UUID,
    aggregations: list[dict],
) -> dict:
    """Execute aggregation queries on a data source.

    Args:
        aggregations: List of aggregation specs, e.g.:
            [{"field": "status", "op": "count", "group_by": "category"}]
    """
    result = await db.execute(
        sa.select(DataSource).where(
            DataSource.id == data_source_id,
            DataSource.team_id == team_id,
        )
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise DataSourceNotFoundError()

    results = []

    for agg in aggregations:
        field = agg.get("field")
        op = agg.get("op", "count").lower()
        group_by = agg.get("group_by")
        alias = agg.get("alias", f"{op}_{field}")

        if source.type == "csv":
            agg_result = await _aggregate_csv_source(db, source, field, op, group_by)
        elif source.type in ("postgresql", "mysql"):
            agg_result = await _aggregate_database_source(source, field, op, group_by)
        elif source.type == "google_sheets":
            agg_result = await _aggregate_sheets_source(source, field, op, group_by)
        else:
            raise DatabaseQueryError(f"Unsupported source type for aggregation: {source.type}")

        results.append({
            "field": field,
            "op": op,
            "group_by": group_by,
            "alias": alias,
            "data": agg_result,
        })

    return {"aggregations": results}


async def _aggregate_csv_source(
    db: AsyncSession,
    source: DataSource,
    field: str,
    op: str,
    group_by: Optional[str],
) -> list[dict]:
    """Aggregate CSV data in-memory."""
    from src.models.csv_data import CsvData
    result = await db.execute(
        sa.select(CsvData.data).where(CsvData.source_id == source.id).order_by(CsvData.row_idx)
    )
    rows = [row[0] for row in result.all()]

    return _compute_aggregation(rows, field, op, group_by)


async def _aggregate_database_source(
    source: DataSource,
    field: str,
    op: str,
    group_by: Optional[str],
) -> list[dict]:
    """Aggregate database source using SQL."""
    from src.datasources.database_connector import execute_query as db_execute_query
    from src.datasources.encryption import decrypt_dict

    config = decrypt_dict(source.config)
    table = config.get("table", config.get("default_table", "public"))
    readonly = config.get("readonly", False)

    _validate_identifier(field)
    if group_by:
        _validate_identifier(group_by)

    # Map operation to SQL function
    sql_ops = {
        "count": "COUNT",
        "sum": "SUM",
        "avg": "AVG",
        "min": "MIN",
        "max": "MAX",
    }
    sql_func = sql_ops.get(op, "COUNT")

    if group_by:
        sql = f"SELECT {group_by}, {sql_func}({field}) as result FROM {table} GROUP BY {group_by} ORDER BY {group_by}"
    else:
        sql = f"SELECT {sql_func}({field}) as result FROM {table}"

    rows, _ = await db_execute_query(
        config=config,
        table=table,
        where=text(sql),
        readonly=readonly,
    )

    return rows


async def _aggregate_sheets_source(
    source: DataSource,
    field: str,
    op: str,
    group_by: Optional[str],
) -> list[dict]:
    """Aggregate Google Sheets data."""
    from src.datasources.google_sheets import fetch_sheet_data

    config = source.config
    access_token = config.get("access_token")
    spreadsheet_id = config.get("spreadsheet_id")
    tab_name = config.get("tab_name")

    sheet_data = await fetch_sheet_data(access_token, spreadsheet_id, tab_name)
    rows = sheet_data.get("rows", [])

    return _compute_aggregation(rows, field, op, group_by)


def _compute_aggregation(rows: list[dict], field: str, op: str, group_by: Optional[str]) -> list[dict]:
    """Compute aggregation on in-memory rows."""
    if group_by:
        groups: dict[str, list] = {}
        for row in rows:
            key = str(row.get(group_by, "unknown"))
            if key not in groups:
                groups[key] = []
            groups[key].append(row)

        results = []
        for key, group_rows in sorted(groups.items()):
            value = _apply_aggregation(group_rows, field, op)
            results.append({group_by: key, "result": value})
        return results
    else:
        value = _apply_aggregation(rows, field, op)
        return [{"result": value}]


def _apply_aggregation(rows: list[dict], field: str, op: str):
    """Apply a single aggregation operation."""
    if op == "count":
        if field == "*":
            return len(rows)
        return sum(1 for r in rows if r.get(field) is not None)

    # For numeric ops, extract numeric values
    values = []
    for r in rows:
        val = r.get(field)
        if val is not None:
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                pass

    if not values:
        return None

    if op == "sum":
        return sum(values)
    elif op == "avg":
        return sum(values) / len(values)
    elif op == "min":
        return min(values)
    elif op == "max":
        return max(values)
    else:
        return len(values)
