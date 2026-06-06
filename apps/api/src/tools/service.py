import logging
from uuid import UUID
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tool import Tool
from src.models.team import Team
from src.tools.slug import generate_unique_slug
from src.tools.versioning import create_version, get_versions, get_version, restore_version
from src.billing.plan_enforcer import check_tool_limit
from src.exceptions import ToolNotFoundError, AuthorizationError

logger = logging.getLogger("deskforge.tools")


async def list_tools(
    db: AsyncSession,
    team_id: UUID,
    status: str = "active",
    page: int = 1,
    per_page: int = 25,
    category: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> tuple[list[Tool], int]:
    """List tools for a team with pagination."""
    query = sa.select(Tool).where(Tool.team_id == team_id)

    if status != "all":
        query = query.where(Tool.status == status)

    if category:
        query = query.where(Tool.category == category)

    if tags:
        # Filter tools that contain ALL specified tags
        for tag in tags:
            query = query.where(sa.cast(Tool.tags, sa.String).contains(tag))

    # Get total count
    count_query = sa.select(sa.func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Get paginated results
    query = query.order_by(Tool.updated_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)

    return list(result.scalars().all()), total


async def get_tool(db: AsyncSession, tool_id: UUID, team_id: UUID) -> Tool:
    """Get a tool by ID."""
    result = await db.execute(
        sa.select(Tool).where(Tool.id == tool_id, Tool.team_id == team_id)
    )
    tool = result.scalar_one_or_none()
    if tool is None:
        raise ToolNotFoundError()
    return tool


async def get_tool_by_slug(db: AsyncSession, slug: str) -> Optional[Tool]:
    """Get a tool by slug."""
    result = await db.execute(sa.select(Tool).where(Tool.slug == slug))
    return result.scalar_one_or_none()


async def create_tool(
    db: AsyncSession,
    team_id: UUID,
    user_id: UUID,
    name: str,
    prompt: str,
    spec: dict,
    data_source_id: Optional[UUID] = None,
    description: Optional[str] = None,
) -> Tool:
    """Create a new tool."""
    # Check plan limits
    team_result = await db.execute(sa.select(Team).where(Team.id == team_id))
    team = team_result.scalar_one_or_none()
    if team:
        await check_tool_limit(db, team)

    slug = await generate_unique_slug(db, name)

    tool = Tool(
        team_id=team_id,
        created_by=user_id,
        data_source_id=data_source_id,
        name=name,
        slug=slug,
        description=description,
        prompt=prompt,
        spec=spec,
        status="active",
    )
    db.add(tool)
    await db.flush()

    # Create initial version
    await create_version(db, tool, user_id)
    await db.commit()
    await db.refresh(tool)

    logger.info(f"Tool created: {tool.id} ({tool.name}) for team {team_id}")
    return tool


async def update_tool(
    db: AsyncSession,
    tool: Tool,
    user_id: UUID,
    **kwargs,
) -> Tool:
    """Update tool metadata."""
    if "name" in kwargs and kwargs["name"]:
        tool.name = kwargs["name"]
    if "description" in kwargs and kwargs["description"] is not None:
        tool.description = kwargs["description"]
    if "theme" in kwargs and kwargs["theme"] is not None:
        tool.theme = kwargs["theme"]
    if "spec" in kwargs and kwargs["spec"] is not None:
        tool.spec = kwargs["spec"]
        await create_version(db, tool, user_id)
    if "prompt" in kwargs and kwargs["prompt"] is not None:
        tool.prompt = kwargs["prompt"]
    if "status" in kwargs:
        tool.status = kwargs["status"]
    if "visibility" in kwargs:
        tool.visibility = kwargs["visibility"]

    await db.commit()
    await db.refresh(tool)
    return tool


async def archive_tool(db: AsyncSession, tool: Tool) -> None:
    """Archive a tool."""
    tool.status = "archived"
    await db.commit()


async def update_tool_spec(db: AsyncSession, tool: Tool, spec: dict, prompt: str, user_id: UUID) -> Tool:
    """Update tool spec (from generation pipeline)."""
    tool.spec = spec
    tool.prompt = prompt
    tool.status = "active"
    await create_version(db, tool, user_id)
    await db.commit()
    await db.refresh(tool)
    return tool


async def clone_tool(db: AsyncSession, original: Tool, user_id: UUID, team_id: UUID) -> Tool:
    """Clone/duplicate a tool.

    Creates a copy with '(Copy)' appended to the name and a new slug.
    """
    import copy

    # Check plan limits for the new tool
    team_result = await db.execute(sa.select(Team).where(Team.id == team_id))
    team = team_result.scalar_one_or_none()
    if team:
        await check_tool_limit(db, team)

    cloned_name = f"{original.name} (Copy)"
    slug = await generate_unique_slug(db, cloned_name)

    tool = Tool(
        team_id=team_id,
        created_by=user_id,
        data_source_id=original.data_source_id,
        name=cloned_name,
        slug=slug,
        description=original.description,
        prompt=original.prompt,
        spec=copy.deepcopy(original.spec),
        theme=copy.deepcopy(original.theme) if original.theme else {},
        status="active",
        visibility="private",
    )
    db.add(tool)
    await db.flush()

    # Create initial version
    await create_version(db, tool, user_id)
    await db.commit()
    await db.refresh(tool)

    logger.info(f"Tool cloned: {original.id} -> {tool.id} ({tool.name})")
    return tool
