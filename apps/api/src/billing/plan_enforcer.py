"""Plan limit enforcement for DeskForge billing."""
import logging
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory
from src.models.team import Team
from src.models.tool import Tool
from src.models.team_member import TeamMember
from src.models.data_source import DataSource
from src.exceptions import PlanLimitError

logger = logging.getLogger("deskforge.billing")

# ── Plan Definitions ──

PLAN_LIMITS: dict[str, dict] = {
    "free": {
        "tools": 3,
        "members": 3,
        "datasources": 2,
        "db_connections": False,
    },
    "starter": {
        "tools": None,  # unlimited
        "members": None,
        "datasources": 5,
        "db_connections": True,
    },
    "pro": {
        "tools": None,
        "members": None,
        "datasources": None,
        "db_connections": True,
    },
    "enterprise": {
        "tools": None,
        "members": None,
        "datasources": None,
        "db_connections": True,
    },
}


def get_plan_limits(plan: str) -> dict:
    """Get limits for a given plan. Falls back to 'free' if unknown."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


async def get_team_plan(db: AsyncSession, team_id: UUID) -> str:
    """Get the current plan for a team."""
    result = await db.execute(sa.select(Team.plan).where(Team.id == team_id))
    plan = result.scalar_one_or_none()
    return plan or "free"


async def get_usage(team_id: UUID) -> dict:
    """Get current usage counts for a team."""
    async with async_session_factory() as db:
        # Count tools (non-archived)
        tools_result = await db.execute(
            sa.select(sa.func.count(Tool.id)).where(
                Tool.team_id == team_id,
                Tool.status != "archived",
            )
        )
        tools_count = tools_result.scalar() or 0

        # Count members (accepted)
        members_result = await db.execute(
            sa.select(sa.func.count(TeamMember.id)).where(
                TeamMember.team_id == team_id,
                TeamMember.accepted_at.isnot(None),
            )
        )
        members_count = members_result.scalar() or 0

        # Count data sources
        ds_result = await db.execute(
            sa.select(sa.func.count(DataSource.id)).where(
                DataSource.team_id == team_id,
            )
        )
        ds_count = ds_result.scalar() or 0

    return {
        "tools": tools_count,
        "members": members_count,
        "datasources": ds_count,
    }


async def check_tool_limit(db: AsyncSession, team_or_id) -> None:
    """Check if the team can create another tool. Raises PlanLimitError if exceeded.

    Accepts either a Team object or a UUID team_id.
    """
    # Handle both Team object and UUID
    if hasattr(team_or_id, "id"):
        team_id = team_or_id.id
        plan = team_or_id.plan or "free"
    else:
        team_id = team_or_id
        plan = await get_team_plan(db, team_id)

    limits = get_plan_limits(plan)
    tool_limit = limits["tools"]

    if tool_limit is None:
        return  # unlimited

    result = await db.execute(
        sa.select(sa.func.count(Tool.id)).where(
            Tool.team_id == team_id,
            Tool.status != "archived",
        )
    )
    count = result.scalar() or 0

    if count >= tool_limit:
        raise PlanLimitError("tools", tool_limit, plan)


async def check_member_limit(db: AsyncSession, team_id: UUID) -> None:
    """Check if the team can add another member. Raises PlanLimitError if exceeded."""
    plan = await get_team_plan(db, team_id)
    limits = get_plan_limits(plan)
    member_limit = limits["members"]

    if member_limit is None:
        return  # unlimited

    result = await db.execute(
        sa.select(sa.func.count(TeamMember.id)).where(
            TeamMember.team_id == team_id,
            TeamMember.accepted_at.isnot(None),
        )
    )
    count = result.scalar() or 0

    if count >= member_limit:
        raise PlanLimitError("members", member_limit, plan)


async def check_datasource_limit(db: AsyncSession, team_id: UUID) -> None:
    """Check if the team can add another data source. Raises PlanLimitError if exceeded."""
    plan = await get_team_plan(db, team_id)
    limits = get_plan_limits(plan)
    ds_limit = limits["datasources"]

    if ds_limit is None:
        return  # unlimited

    result = await db.execute(
        sa.select(sa.func.count(DataSource.id)).where(
            DataSource.team_id == team_id,
        )
    )
    count = result.scalar() or 0

    if count >= ds_limit:
        raise PlanLimitError("datasources", ds_limit, plan)


async def check_db_connection_available(db: AsyncSession, team_id: UUID) -> None:
    """Check if the plan allows database connections."""
    plan = await get_team_plan(db, team_id)
    limits = get_plan_limits(plan)

    if not limits["db_connections"]:
        from src.exceptions import FeatureNotAvailableError
        raise FeatureNotAvailableError("Database connections")
