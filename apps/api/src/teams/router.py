from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.dependencies import get_db, get_current_user, require_role, get_team_membership
from src.models.user import User
from src.models.team import Team
from src.models.team_member import TeamMember
from src.teams.service import (
    get_team_for_user,
    update_team,
    get_team_members,
    remove_team_member,
    change_member_role,
)
from src.teams.invitations import create_invitation, accept_invitation
from src.teams.schemas import (
    TeamResponse,
    UpdateTeamRequest,
    TeamMemberResponse,
    InviteMemberRequest,
    InvitationResponse,
    ChangeRoleRequest,
    AcceptInviteResponse,
)

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/current", response_model=dict)
async def get_current_team(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team, membership = await get_team_for_user(db, current_user.id)
    return {"data": {"team": TeamResponse.model_validate(team)}}


@router.patch("/current", response_model=dict)
async def update_current_team(
    body: UpdateTeamRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    current_user, membership = auth_data
    team, _ = await get_team_for_user(db, current_user.id)
    updated = await update_team(db, team, body.name)
    return {"data": {"team": TeamResponse.model_validate(updated)}}


@router.get("/current/members", response_model=dict)
async def list_members(
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    current_user, membership = auth_data
    members = await get_team_members(db, membership.team_id)
    return {
        "data": {
            "members": [
                TeamMemberResponse(
                    id=m["id"],
                    user_id=m["user_id"],
                    role=m["role"],
                    invited_at=m["invited_at"],
                    accepted_at=m["accepted_at"],
                    user_name=m["user_name"],
                    user_email=m["user_email"],
                    user_avatar=m["user_avatar"],
                )
                for m in members
            ]
        }
    }


@router.post("/current/invites", response_model=dict)
async def invite_member(
    body: InviteMemberRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    current_user, membership = auth_data
    team, _ = await get_team_for_user(db, current_user.id)
    invitation = await create_invitation(db, team, body.email, body.role)
    return {
        "data": {
            "invite": InvitationResponse.model_validate(invitation)
        }
    }


@router.post("/invites/{token}/accept", response_model=dict)
async def accept_invite(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = await accept_invitation(db, token, current_user)
    return {"data": {"team": TeamResponse.model_validate(team)}}


@router.delete("/current/members/{user_id}", response_model=dict)
async def remove_member(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    current_user, membership = auth_data
    team, _ = await get_team_for_user(db, current_user.id)
    await remove_team_member(db, team, user_id)
    return {"data": {"success": True}}


@router.patch("/current/members/{user_id}", response_model=dict)
async def change_role(
    user_id: UUID,
    body: ChangeRoleRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    current_user, membership = auth_data
    team, _ = await get_team_for_user(db, current_user.id)
    updated_member = await change_member_role(db, team, user_id, body.role)
    user_result = await db.execute(
        __import__("sqlalchemy").select(User).where(User.id == updated_member.user_id)
    )
    user = user_result.scalar_one_or_none()
    return {
        "data": {
            "member": TeamMemberResponse(
                id=updated_member.id,
                user_id=updated_member.user_id,
                role=updated_member.role,
                invited_at=updated_member.invited_at,
                accepted_at=updated_member.accepted_at,
                user_name=user.name if user else None,
                user_email=user.email if user else None,
                user_avatar=user.avatar_url if user else None,
            )
        }
    }
