import secrets
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.team import Team
from src.models.team_member import TeamMember
from src.models.team_invitation import TeamInvitation
from src.models.user import User
from src.utils.email import send_team_invite_email
from src.exceptions import (
    AlreadyTeamMemberError,
    InvitationNotFoundError,
    InvitationAlreadyAcceptedError,
    PlanLimitError,
    TeamNotFoundError,
)

logger = logging.getLogger("deskforge.teams.invitations")

INVITATION_EXPIRY_HOURS = 72


async def create_invitation(
    db: AsyncSession,
    team: Team,
    email: str,
    role: str,
) -> TeamInvitation:
    """Create a team invitation."""
    email = email.lower().strip()

    # Check if already a member
    existing_user = await db.execute(sa.select(User).where(User.email == email))
    user = existing_user.scalar_one_or_none()
    if user:
        existing_member = await db.execute(
            sa.select(TeamMember).where(
                TeamMember.team_id == team.id,
                TeamMember.user_id == user.id,
            )
        )
        if existing_member.scalar_one_or_none():
            raise AlreadyTeamMemberError()

    # Check plan limits for free plan
    if team.plan == "free":
        member_count = await db.execute(
            sa.select(sa.func.count()).select_from(TeamMember).where(TeamMember.team_id == team.id)
        )
        count = member_count.scalar()
        if count >= 10:
            raise PlanLimitError("team members", 10, "free")

    token = secrets.token_urlsafe(32)
    invitation = TeamInvitation(
        team_id=team.id,
        email=email,
        role=role,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=INVITATION_EXPIRY_HOURS),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    try:
        await send_team_invite_email(
            email=email,
            team_name=team.name,
            token=token,
            role=role,
        )
    except Exception as e:
        logger.warning(f"Failed to send invite email: {e}")

    return invitation


async def accept_invitation(db: AsyncSession, token: str, user: User) -> Team:
    """Accept a team invitation."""
    result = await db.execute(
        sa.select(TeamInvitation).where(
            TeamInvitation.token == token,
            TeamInvitation.expires_at > datetime.now(timezone.utc),
        )
    )
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise InvitationNotFoundError()

    if invitation.accepted_at is not None:
        raise InvitationAlreadyAcceptedError()

    # Check if already a member
    existing = await db.execute(
        sa.select(TeamMember).where(
            TeamMember.team_id == invitation.team_id,
            TeamMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise AlreadyTeamMemberError()

    invitation.accepted_at = datetime.now(timezone.utc)

    member = TeamMember(
        team_id=invitation.team_id,
        user_id=user.id,
        role=invitation.role,
        invited_at=invitation.created_at,
        accepted_at=datetime.now(timezone.utc),
    )
    db.add(member)
    await db.commit()

    team_result = await db.execute(sa.select(Team).where(Team.id == invitation.team_id))
    team = team_result.scalar_one_or_none()
    if team is None:
        raise TeamNotFoundError()

    return team
