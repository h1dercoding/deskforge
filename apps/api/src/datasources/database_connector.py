"""PostgreSQL/MySQL async database connector with connection pooling."""
import asyncio
import logging
import time
import re
from typing import Optional
from uuid import UUID

from src.datasources.encryption import decrypt_dict
from src.exceptions import DatabaseConnectionError, DatabaseQueryError

logger = logging.getLogger("deskforge.datasources.database")

# ── Connection Pool Manager ──
# Pools are keyed by (host, port, database, username) to reuse connections
# to the same database across multiple queries.
_pools: dict[str, object] = {}

# Maximum rows returned per query
MAX_ROWS = 10000

# Query execution timeout in seconds
QUERY_TIMEOUT = 30

# Connection pool limits
POOL_MIN_SIZE = 1
POOL_MAX_SIZE = 10
POOL_MAX_IDLE = 300  # 5 minutes idle before closing


def _pool_key(config: dict) -> str:
    """Generate a unique key for the connection pool."""
    return f"{config.get('host')}:{config.get('port')}:{config.get('database')}:{config.get('username')}"


def _validate_identifier(name: str) -> None:
    """Validate that a string is a safe SQL identifier."""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise DatabaseQueryError(f"Invalid identifier: {name}")


async def _get_pg_pool(config: dict):
    """Get or create an asyncpg connection pool."""
    import asyncpg

    key = _pool_key(config)
    pool = _pools.get(key)

    if pool is None or pool._closed:
        pool = await asyncpg.create_pool(
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["username"],
            password=config["password"],
            ssl="require" if config.get("ssl") else None,
            min_size=POOL_MIN_SIZE,
            max_size=POOL_MAX_SIZE,
            max_inactive_connection_lifetime=POOL_MAX_IDLE,
            command_timeout=QUERY_TIMEOUT,
            timeout=10,
        )
        _pools[key] = pool
        logger.info(f"Created connection pool for {config['host']}/{config['database']}")

    return pool


async def _get_mysql_pool(config: dict):
    """Get or create an aiomysql connection pool."""
    import aiomysql

    key = _pool_key(config)
    pool = _pools.get(key)

    if pool is None or pool._closed:
        pool = await aiomysql.create_pool(
            host=config["host"],
            port=config["port"],
            db=config["database"],
            user=config["username"],
            password=config["password"],
            minsize=POOL_MIN_SIZE,
            maxsize=POOL_MAX_SIZE,
            connect_timeout=10,
        )
        _pools[key] = pool
        logger.info(f"Created MySQL connection pool for {config['host']}/{config['database']}")

    return pool


async def close_all_pools() -> None:
    """Close all connection pools (call on shutdown)."""
    for key, pool in list(_pools.items()):
        try:
            pool.close()
            await pool.wait_closed()
        except Exception as e:
            logger.warning(f"Error closing pool {key}: {e}")
    _pools.clear()


async def test_connection(config: dict) -> dict:
    """Test a database connection and return latency."""
    start = time.monotonic()
    db_type = config.get("type")

    try:
        if db_type == "postgresql":
            await _test_postgresql(config)
        elif db_type == "mysql":
            await _test_mysql(config)
        else:
            raise DatabaseConnectionError(f"Unsupported database type: {db_type}")

        latency_ms = round((time.monotonic() - start) * 1000, 2)
        return {"status": "connected", "latency_ms": latency_ms}
    except DatabaseConnectionError:
        raise
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise DatabaseConnectionError(str(e))


async def _test_postgresql(config: dict) -> None:
    """Test PostgreSQL connection."""
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["username"],
            password=config["password"],
            ssl="require" if config.get("ssl") else None,
            timeout=10,
        )
        await conn.execute("SELECT 1")
        await conn.close()
    except ImportError:
        raise DatabaseConnectionError("asyncpg not installed")
    except Exception as e:
        raise DatabaseConnectionError(f"PostgreSQL connection failed: {e}")


async def _test_mysql(config: dict) -> None:
    """Test MySQL connection."""
    try:
        import aiomysql
        conn = await aiomysql.connect(
            host=config["host"],
            port=config["port"],
            db=config["database"],
            user=config["username"],
            password=config["password"],
            connect_timeout=10,
        )
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
        conn.close()
    except ImportError:
        raise DatabaseConnectionError("aiomysql not installed")
    except Exception as e:
        raise DatabaseConnectionError(f"MySQL connection failed: {e}")


async def get_schema(config: dict) -> dict:
    """Get database schema (table/column information)."""
    db_type = config.get("type")

    try:
        if db_type == "postgresql":
            return await _get_postgresql_schema(config)
        elif db_type == "mysql":
            return await _get_mysql_schema(config)
        else:
            raise DatabaseConnectionError(f"Unsupported type: {db_type}")
    except DatabaseConnectionError:
        raise
    except Exception as e:
        raise DatabaseConnectionError(f"Schema fetch failed: {e}")


async def _get_postgresql_schema(config: dict) -> dict:
    """Get PostgreSQL schema."""
    pool = await _get_pg_pool(config)
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)
        tables = {}
        for row in rows:
            table = row["table_name"]
            if table not in tables:
                tables[table] = []
            tables[table].append({
                "name": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
            })
        return {"tables": tables, "columns": tables}


async def _get_mysql_schema(config: dict) -> dict:
    """Get MySQL schema."""
    pool = await _get_mysql_pool(config)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION
            """, (config["database"],))
            rows = await cur.fetchall()

        tables = {}
        for row in rows:
            table = row[0]
            if table not in tables:
                tables[table] = []
            tables[table].append({
                "name": row[1],
                "type": row[2],
                "nullable": row[3] == "YES",
            })
        return {"tables": tables, "columns": tables}


async def execute_query(
    config: dict,
    table: str,
    columns: Optional[list[str]] = None,
    where=None,
    where_params: Optional[dict] = None,
    order_by: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    readonly: bool = False,
) -> tuple[list[dict], int]:
    """Execute a read query against a database with connection pooling.

    Enforces:
    - Input validation on identifiers
    - Query timeout (QUERY_TIMEOUT seconds)
    - Maximum row limit (MAX_ROWS)
    - Read-only transaction mode when readonly=True
    """
    db_type = config.get("type")

    # Validate identifiers
    _validate_identifier(table)
    if columns:
        for col in columns:
            _validate_identifier(col)

    # Enforce max row limit
    limit = min(limit, MAX_ROWS)

    # Build column list
    cols = ", ".join(columns) if columns else "*"
    query = f"SELECT {cols} FROM {table}"
    count_query = f"SELECT COUNT(*) FROM {table}"

    if where:
        query += f" WHERE {where}"
        count_query += f" WHERE {where}"
    if order_by:
        query += f" ORDER BY {order_by}"
    query += f" LIMIT {limit} OFFSET {offset}"

    try:
        if db_type == "postgresql":
            return await _pg_query(config, query, count_query, where_params, readonly)
        elif db_type == "mysql":
            return await _mysql_query(config, query, count_query, where_params, readonly)
        else:
            raise DatabaseQueryError(f"Unsupported type: {db_type}")
    except DatabaseQueryError:
        raise
    except Exception as e:
        raise DatabaseQueryError(str(e))


async def _pg_query(
    config: dict,
    query: str,
    count_query: str,
    where_params: Optional[dict] = None,
    readonly: bool = False,
) -> tuple[list[dict], int]:
    """Execute PostgreSQL query using connection pool."""
    import asyncpg

    pool = await _get_pg_pool(config)
    async with pool.acquire() as conn:
        # Enforce read-only transaction if requested
        if readonly:
            await conn.execute("SET TRANSACTION READ ONLY")

        # Set statement timeout
        await conn.execute(f"SET statement_timeout = '{QUERY_TIMEOUT}s'")

        # Execute with timeout
        try:
            if where_params:
                # Convert named params to positional for asyncpg
                # asyncpg uses $1, $2, etc. but we use :p0, :p1 from SQLAlchemy text()
                # We need to pass params separately
                rows = await asyncio.wait_for(
                    conn.fetch(query, *where_params.values()),
                    timeout=QUERY_TIMEOUT,
                )
                count = await asyncio.wait_for(
                    conn.fetchval(count_query, *where_params.values()),
                    timeout=QUERY_TIMEOUT,
                )
            else:
                rows = await asyncio.wait_for(
                    conn.fetch(query),
                    timeout=QUERY_TIMEOUT,
                )
                count = await asyncio.wait_for(
                    conn.fetchval(count_query),
                    timeout=QUERY_TIMEOUT,
                )
        except asyncio.TimeoutError:
            raise DatabaseQueryError(f"Query timed out after {QUERY_TIMEOUT}s")

        results = [dict(row) for row in rows]
        return results, count


async def _mysql_query(
    config: dict,
    query: str,
    count_query: str,
    where_params: Optional[dict] = None,
    readonly: bool = False,
) -> tuple[list[dict], int]:
    """Execute MySQL query using connection pool."""
    import aiomysql

    pool = await _get_mysql_pool(config)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Enforce read-only if requested
            if readonly:
                await cur.execute("SET SESSION TRANSACTION READ ONLY")

            # Set query timeout
            await cur.execute(f"SET SESSION MAX_EXECUTION_TIME = {QUERY_TIMEOUT * 1000}")

            try:
                if where_params:
                    await asyncio.wait_for(
                        cur.execute(query, list(where_params.values())),
                        timeout=QUERY_TIMEOUT,
                    )
                else:
                    await asyncio.wait_for(
                        cur.execute(query),
                        timeout=QUERY_TIMEOUT,
                    )
                rows = await cur.fetchall()

                if where_params:
                    await asyncio.wait_for(
                        cur.execute(count_query, list(where_params.values())),
                        timeout=QUERY_TIMEOUT,
                    )
                else:
                    await asyncio.wait_for(
                        cur.execute(count_query),
                        timeout=QUERY_TIMEOUT,
                    )
                count_result = await cur.fetchone()
                count = count_result.get("COUNT(*)", 0) if count_result else 0
            except asyncio.TimeoutError:
                raise DatabaseQueryError(f"Query timed out after {QUERY_TIMEOUT}s")

        return rows, count
