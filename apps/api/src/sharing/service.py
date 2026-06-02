"""Sharing service - link management and access control."""
import logging
import secrets
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tool import Tool
from src.models.share_link import ShareLink
from src.models.team_member import TeamMember
from src.exceptions import NotFoundError, AuthorizationError

logger = logging.getLogger("deskforge.sharing")


async def get_shared_tool(db: AsyncSession, slug: str) -> Optional[Tool]:
    """Get a shared tool by its slug.

    Returns the tool if it's public, or checks if the viewer has team membership.
    For public access (no auth), only returns tools with 'public' visibility.
    """
    result = await db.execute(
        sa.select(Tool).where(
            Tool.slug == slug,
            Tool.status != "archived",
        )
    )
    tool = result.scalar_one_or_none()

    if tool is None:
        raise NotFoundError("Shared tool not found.")

    if tool.visibility != "public":
        raise NotFoundError("This tool is not publicly shared.")

    return tool


async def get_shared_tool_authenticated(
    db: AsyncSession, slug: str, user_id: Optional[UUID] = None
) -> Tool:
    """Get a shared tool, allowing private access if user is a team member."""
    result = await db.execute(
        sa.select(Tool).where(
            Tool.slug == slug,
            Tool.status != "archived",
        )
    )
    tool = result.scalar_one_or_none()

    if tool is None:
        raise NotFoundError("Shared tool not found.")

    # If public, anyone can access
    if tool.visibility == "public":
        return tool

    # If private, check team membership
    if user_id is None:
        raise NotFoundError("This tool is not publicly shared.")

    member_result = await db.execute(
        sa.select(TeamMember).where(
            TeamMember.team_id == tool.team_id,
            TeamMember.user_id == user_id,
            TeamMember.accepted_at.isnot(None),
        )
    )
    membership = member_result.scalar_one_or_none()

    if membership is None:
        raise NotFoundError("This tool is not publicly shared.")

    return tool


async def update_visibility(
    db: AsyncSession,
    tool_id: UUID,
    team_id: UUID,
    visibility: str,
) -> Tool:
    """Update a tool's visibility (public/private).

    When set to public, generates a share link if one doesn't exist.
    When set to private, deactivates all share links.
    """
    result = await db.execute(
        sa.select(Tool).where(
            Tool.id == tool_id,
            Tool.team_id == team_id,
            Tool.status != "archived",
        )
    )
    tool = result.scalar_one_or_none()

    if tool is None:
        raise NotFoundError("Tool not found.")

    tool.visibility = visibility

    if visibility == "public":
        # Ensure a share link exists
        link_result = await db.execute(
            sa.select(ShareLink).where(
                ShareLink.tool_id == tool_id,
                ShareLink.is_active == True,
            )
        )
        existing_link = link_result.scalar_one_or_none()

        if existing_link is None:
            # Generate a new share link using the tool's slug
            # The tool already has a slug, just ensure a share link record exists
            new_link = ShareLink(
                tool_id=tool_id,
                token=tool.slug,
                is_active=True,
            )
            db.add(new_link)
    elif visibility == "private":
        # Deactivate all share links
        await db.execute(
            sa.update(ShareLink)
            .where(ShareLink.tool_id == tool_id, ShareLink.is_active == True)
            .values(is_active=False)
        )

    await db.commit()
    await db.refresh(tool)

    logger.info(f"Updated tool {tool_id} visibility to {visibility}")
    return tool


async def regenerate_link(db: AsyncSession, tool_id: UUID, team_id: UUID) -> str:
    """Regenerate a share link for a tool.

    Deactivates old links and creates a new one with a fresh slug.
    Returns the new slug.
    """
    result = await db.execute(
        sa.select(Tool).where(
            Tool.id == tool_id,
            Tool.team_id == team_id,
            Tool.status != "archived",
        )
    )
    tool = result.scalar_one_or_none()

    if tool is None:
        raise NotFoundError("Tool not found.")

    # Generate new slug
    from src.tools.slug import generate_unique_slug
    new_slug = await generate_unique_slug(db, tool.name, tool_id)

    # Update tool slug
    tool.slug = new_slug

    # Deactivate old share links
    await db.execute(
        sa.update(ShareLink)
        .where(ShareLink.tool_id == tool_id, ShareLink.is_active == True)
        .values(is_active=False)
    )

    # Create new share link
    new_link = ShareLink(
        tool_id=tool_id,
        token=new_slug,
        is_active=True,
    )
    db.add(new_link)

    # If tool was private, make it public since they're regenerating the link
    if tool.visibility == "private":
        tool.visibility = "public"

    await db.commit()

    logger.info(f"Regenerated share link for tool {tool_id}: {new_slug}")
    return new_slug
