"""Pagination utilities for DeskForge API."""
from typing import Any, Optional, Sequence, TypeVar
from fastapi import Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")


class PaginationParams:
    """FastAPI dependency for pagination parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page


async def paginate(
    db: AsyncSession,
    query: Select,
    count_query: Optional[Select] = None,
    page: int = 1,
    per_page: int = 25,
) -> dict[str, Any]:
    """Execute a paginated query and return results with metadata.

    Args:
        db: Database session
        query: SQLAlchemy select query
        count_query: Optional separate count query (auto-generated if not provided)
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Dict with 'items', 'total', 'page', 'per_page', 'total_pages'
    """
    offset = (page - 1) * per_page

    # Get total count
    if count_query is not None:
        total_result = await db.execute(count_query)
    else:
        # Auto-generate count query from the main query
        count_q = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_q)

    total = total_result.scalar() or 0

    # Get paginated results
    paginated_query = query.offset(offset).limit(per_page)
    result = await db.execute(paginated_query)
    items = list(result.scalars().all())

    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def build_pagination_meta(total: int, page: int, per_page: int) -> dict:
    """Build standard pagination metadata for API responses."""
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }
