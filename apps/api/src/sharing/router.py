"""Sharing API endpoints."""
import copy
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.dependencies import get_db, get_current_user, require_role, get_team_membership, get_optional_user
from src.models.user import User
from src.models.team_member import TeamMember
from src.sharing.service import (
    get_shared_tool,
    get_shared_tool_authenticated,
    update_visibility,
    regenerate_link,
)
from src.sharing.schemas import (
    SharedToolResponse,
    UpdateVisibilityRequest,
    UpdateVisibilityResponse,
    RegenerateLinkResponse,
)

logger = logging.getLogger("deskforge.sharing")

router = APIRouter(tags=["Sharing"])


def _sanitize_spec_for_public(spec: dict) -> dict:
    """Strip internal data from tool spec for public access.

    Removes connectionId references from dataSources to prevent leaking
    internal data source identifiers to unauthenticated users.
    """
    sanitized = copy.deepcopy(spec)
    for ds in sanitized.get("dataSources", []):
        ds.pop("connectionId", None)
    return sanitized


@router.get("/sharing/{slug}", response_model=dict)
async def get_shared_tool_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_db),
    optional_user: User | None = Depends(get_optional_user),
):
    """Get a shared tool by slug.

    Public endpoint - no auth required for public tools.
    If authenticated, also allows access to private tools within the user's team.
    For public (unauthenticated) access, internal data like connectionId is stripped.
    """
    user_id = optional_user.id if optional_user else None
    tool = await get_shared_tool_authenticated(db, slug, user_id)

    # Strip internal data for public/unauthenticated access
    spec = tool.spec
    if not user_id and tool.visibility == "public":
        spec = _sanitize_spec_for_public(spec)

    return {
        "data": SharedToolResponse(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            spec=spec,
            theme=tool.theme,
            visibility=tool.visibility,
            slug=tool.slug,
            is_public=tool.visibility == "public",
        )
    }


@router.patch("/tools/{tool_id}/sharing", response_model=dict)
async def update_sharing_endpoint(
    tool_id: UUID,
    body: UpdateVisibilityRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    """Update tool visibility (public/private).

    Editors and owners can change sharing settings. Previously this was
    owner-only which was too restrictive for teams where editors create tools.
    """
    current_user, membership = auth_data

    if body.visibility not in ("public", "private"):
        from src.exceptions import ValidationError
        raise ValidationError("Visibility must be 'public' or 'private'.")

    tool = await update_visibility(db, tool_id, membership.team_id, body.visibility)

    return {
        "data": UpdateVisibilityResponse(
            id=tool.id,
            visibility=tool.visibility,
            slug=tool.slug,
        )
    }


@router.post("/tools/{tool_id}/sharing/regenerate", response_model=dict)
async def regenerate_link_endpoint(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    """Regenerate the share URL for a tool."""
    current_user, membership = auth_data

    new_slug = await regenerate_link(db, tool_id, membership.team_id)

    return {
        "data": RegenerateLinkResponse(slug=new_slug)
    }
