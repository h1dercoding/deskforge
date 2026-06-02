from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from src.database import async_session_factory
from src.auth.jwt import decode_access_token
from src.exceptions import AuthenticationError, NotTeamMemberError, InsufficientRoleError, EmailNotVerifiedError
from src.models.user import User
from src.models.team_member import TeamMember
import sqlalchemy as sa


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid authorization header")

    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    if payload is None:
        raise AuthenticationError("Invalid or expired access token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    result = await db.execute(sa.select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationError("User not found")

    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    try:
        return await get_current_user(request, db)
    except AuthenticationError:
        return None


def require_role(minimum_role: str):
    """Dependency factory requiring a minimum team role.

    NOTE: DeskForge uses a single-team-per-user model. Each user belongs to
    exactly one team (created on registration). This dependency finds the
    user's accepted team membership. If a user has multiple memberships
    (e.g., from invitations), it deterministically selects the first one.

    To support multi-team in the future, accept a team_id path/query parameter
    and filter TeamMember by (user_id, team_id).
    """
    role_hierarchy = {"viewer": 0, "editor": 1, "owner": 2}

    async def _require_role(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> tuple[User, TeamMember]:
        result = await db.execute(
            sa.select(TeamMember).where(
                TeamMember.user_id == current_user.id,
                TeamMember.accepted_at.isnot(None),
            ).order_by(TeamMember.accepted_at.asc())
        )
        membership = result.scalars().first()
        if membership is None:
            raise NotTeamMemberError()

        if role_hierarchy.get(membership.role, -1) < role_hierarchy.get(minimum_role, 0):
            raise InsufficientRoleError(minimum_role)

        return current_user, membership

    return _require_role


async def get_team_membership(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, TeamMember]:
    result = await db.execute(
        sa.select(TeamMember).where(
            TeamMember.user_id == current_user.id,
            TeamMember.accepted_at.isnot(None),
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise NotTeamMemberError()
    return current_user, membership


async def require_verified_email(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the user's email is verified (FR-004)."""
    if not current_user.email_verified:
        raise EmailNotVerifiedError()
    return current_user
