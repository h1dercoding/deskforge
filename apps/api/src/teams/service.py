from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import sqlalchemy as sa

from src.models.team import Team
from src.models.team_member import TeamMember
from src.models.user import User
from src.exceptions import (
    TeamNotFoundError,
    InsufficientRoleError,
    NotTeamMemberError,
)


async def get_team_for_user(db: AsyncSession, user_id: UUID) -> tuple[Team, TeamMember]:
    """Get the team and membership for a user."""
    result = await db.execute(
        sa.select(TeamMember, Team)
        .join(Team, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id, TeamMember.accepted_at.isnot(None))
    )
    row = result.one_or_none()
    if row is None:
        raise TeamNotFoundError()
    return row[1], row[0]


async def create_team_for_user(db: AsyncSession, user: User) -> Team:
    """Auto-create a team when a user signs up."""
    team = Team(
        name=f"{user.name}'s Team",
        owner_id=user.id,
        plan="free",
    )
    db.add(team)
    await db.flush()

    from datetime import datetime, timezone
    member = TeamMember(
        team_id=team.id,
        user_id=user.id,
        role="owner",
        invited_at=datetime.now(timezone.utc),
        accepted_at=datetime.now(timezone.utc),
    )
    db.add(member)
    return team


async def update_team(db: AsyncSession, team: Team, name: str) -> Team:
    """Update team name."""
    team.name = name
    await db.commit()
    await db.refresh(team)
    return team


async def get_team_members(db: AsyncSession, team_id: UUID) -> list[dict]:
    """List all team members with user info."""
    result = await db.execute(
        sa.select(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .where(TeamMember.team_id == team_id)
        .order_by(TeamMember.invited_at)
    )
    members = []
    for membership, user in result.all():
        members.append({
            "id": membership.id,
            "user_id": user.id,
            "role": membership.role,
            "invited_at": membership.invited_at,
            "accepted_at": membership.accepted_at,
            "user_name": user.name,
            "user_email": user.email,
            "user_avatar": user.avatar_url,
        })
    return members


async def remove_team_member(db: AsyncSession, team: Team, user_id: UUID) -> None:
    """Remove a member from the team."""
    result = await db.execute(
        sa.select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise NotTeamMemberError()
    if member.role == "owner":
        raise InsufficientRoleError("Cannot remove the team owner")

    await db.delete(member)
    await db.commit()


async def change_member_role(db: AsyncSession, team: Team, user_id: UUID, new_role: str) -> TeamMember:
    """Change a team member's role."""
    result = await db.execute(
        sa.select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise NotTeamMemberError()
    if member.role == "owner":
        raise InsufficientRoleError("Cannot change the owner's role")

    member.role = new_role
    await db.commit()
    await db.refresh(member)
    return member
