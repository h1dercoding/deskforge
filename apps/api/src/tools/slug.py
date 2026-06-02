import re
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a tool name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        slug = "tool"
    return slug[:100]


async def generate_unique_slug(db: AsyncSession, name: str, exclude_id=None) -> str:
    """Generate a unique slug, handling collisions by appending a number."""
    from src.models.tool import Tool

    base_slug = generate_slug(name)
    slug = base_slug
    counter = 1

    while True:
        query = sa.select(Tool).where(Tool.slug == slug)
        if exclude_id:
            query = query.where(Tool.id != exclude_id)
        result = await db.execute(query)
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1
        if counter > 1000:
            import uuid
            return f"{base_slug}-{uuid.uuid4().hex[:8]}"
