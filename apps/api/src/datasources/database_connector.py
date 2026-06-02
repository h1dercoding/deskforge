"""PostgreSQL/MySQL async database connector."""
import asyncio
import logging
import time
from typing import Optional
from uuid import UUID

from src.datasources.encryption import decrypt_dict
from src.exceptions import DatabaseConnectionError, DatabaseQueryError

logger = logging.getLogger("deskforge.datasources.database")


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
    try:
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
    finally:
        await conn.close()


async def _get_mysql_schema(config: dict) -> dict:
    """Get MySQL schema."""
    import aiomysql
    conn = await aiomysql.connect(
        host=config["host"],
        port=config["port"],
        db=config["database"],
        user=config["username"],
        password=config["password"],
        connect_timeout=10,
    )
    try:
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
    finally:
        conn.close()


async def execute_query(
    config: dict,
    table: str,
    columns: Optional[list[str]] = None,
    where: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Execute a read query against a database."""
    db_type = config.get("type")
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
            return await _pg_query(config, query, count_query)
        elif db_type == "mysql":
            return await _mysql_query(config, query, count_query)
        else:
            raise DatabaseQueryError(f"Unsupported type: {db_type}")
    except DatabaseQueryError:
        raise
    except Exception as e:
        raise DatabaseQueryError(str(e))


async def _pg_query(config: dict, query: str, count_query: str) -> tuple[list[dict], int]:
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
    try:
        rows = await conn.fetch(query)
        count = await conn.fetchval(count_query)
        results = [dict(row) for row in rows]
        return results, count
    finally:
        await conn.close()


async def _mysql_query(config: dict, query: str, count_query: str) -> tuple[list[dict], int]:
    import aiomysql
    conn = await aiomysql.connect(
        host=config["host"],
        port=config["port"],
        db=config["database"],
        user=config["username"],
        password=config["password"],
        connect_timeout=10,
    )
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            await cur.execute(count_query)
            count = (await cur.fetchone())[count_value_key(count_query)]
        return rows, count
    finally:
        conn.close()


def count_value_key(q: str) -> str:
    return "COUNT(*)"
