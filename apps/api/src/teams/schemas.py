from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class TeamResponse(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateTeamRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class TeamMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    role: str
    invited_at: datetime
    accepted_at: Optional[datetime] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(editor|viewer)$")


class InvitationResponse(BaseModel):
    id: UUID
    email: str
    role: str
    token: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeRoleRequest(BaseModel):
    role: str = Field(pattern="^(editor|viewer)$")


class AcceptInviteResponse(BaseModel):
    team: TeamResponse
