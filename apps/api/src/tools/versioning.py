import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.models.tool import Tool
from src.models.tool_version import ToolVersion


async def create_version(db: AsyncSession, tool: Tool, user_id: UUID) -> ToolVersion:
    """Create a new version of a tool."""
    # Get the latest version number
    result = await db.execute(
        sa.select(sa.func.max(ToolVersion.version_number))
        .where(ToolVersion.tool_id == tool.id)
    )
    max_version = result.scalar() or 0

    version = ToolVersion(
        tool_id=tool.id,
        version_number=max_version + 1,
        prompt=tool.prompt,
        spec=tool.spec,
        created_by=user_id,
    )
    db.add(version)
    return version


async def get_versions(db: AsyncSession, tool_id: UUID) -> list[ToolVersion]:
    """Get all versions of a tool."""
    result = await db.execute(
        sa.select(ToolVersion)
        .where(ToolVersion.tool_id == tool_id)
        .order_by(ToolVersion.version_number.desc())
    )
    return list(result.scalars().all())


async def restore_version(db: AsyncSession, tool: Tool, version: ToolVersion, user_id: UUID) -> Tool:
    """Restore a tool to a previous version.

    Only saves the current state as a new version if it differs from the
    target version, to avoid creating duplicate version entries.
    """
    # Only save current state if it differs from the version being restored
    if tool.spec != version.spec or tool.prompt != version.prompt:
        await create_version(db, tool, user_id)

    # Restore
    tool.spec = version.spec
    tool.prompt = version.prompt
    await db.commit()
    await db.refresh(tool)
    return tool


async def get_version(db: AsyncSession, tool_id: UUID, version_id: UUID) -> ToolVersion | None:
    """Get a specific version."""
    result = await db.execute(
        sa.select(ToolVersion).where(
            ToolVersion.tool_id == tool_id,
            ToolVersion.id == version_id,
        )
    )
    return result.scalar_one_or_none()
