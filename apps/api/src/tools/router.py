from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.dependencies import get_db, get_current_user, get_team_membership, require_role, require_verified_email
from src.models.user import User
from src.models.team_member import TeamMember
from src.teams.service import get_team_for_user
from src.tools.service import (
    list_tools,
    get_tool,
    create_tool,
    update_tool,
    archive_tool,
)
from src.tools.versioning import get_versions, restore_version, get_version
from src.tools.schemas import (
    CreateToolRequest,
    UpdateToolRequest,
    ToolResponse,
    ToolVersionResponse,
)
from src.models.tool import Tool
import sqlalchemy as sa

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=dict)
async def list_tools_endpoint(
    status: str = Query("active", regex="^(active|draft|archived|all)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    current_user, membership = auth_data
    tools, total = await list_tools(db, membership.team_id, status, page, per_page)
    return {
        "data": {
            "tools": [ToolResponse.model_validate(t) for t in tools],
        },
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
        },
    }


@router.get("/{tool_id}", response_model=dict)
async def get_tool_endpoint(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    current_user, membership = auth_data
    tool = await get_tool(db, tool_id, membership.team_id)
    versions = await get_versions(db, tool.id)
    return {
        "data": {
            "tool": ToolResponse.model_validate(tool),
            "versions": [ToolVersionResponse.model_validate(v) for v in versions],
        }
    }


@router.post("", response_model=dict, status_code=201)
async def create_tool_endpoint(
    body: CreateToolRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
    _verified: User = Depends(require_verified_email),
):
    current_user, membership = auth_data
    tool = await create_tool(
        db,
        team_id=membership.team_id,
        user_id=current_user.id,
        name=body.name,
        prompt=body.prompt,
        spec=body.spec,
        data_source_id=body.data_source_id,
        description=body.description,
    )
    return {"data": {"tool": ToolResponse.model_validate(tool)}}


@router.patch("/{tool_id}", response_model=dict)
async def update_tool_endpoint(
    tool_id: UUID,
    body: UpdateToolRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    current_user, membership = auth_data
    tool = await get_tool(db, tool_id, membership.team_id)
    updated = await update_tool(
        db, tool, current_user.id,
        name=body.name,
        description=body.description,
        theme=body.theme,
    )
    return {"data": {"tool": ToolResponse.model_validate(updated)}}


@router.delete("/{tool_id}", response_model=dict)
async def archive_tool_endpoint(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("owner")),
):
    current_user, membership = auth_data
    tool = await get_tool(db, tool_id, membership.team_id)
    await archive_tool(db, tool)
    return {"data": {"success": True}}


@router.get("/{tool_id}/versions", response_model=dict)
async def list_versions_endpoint(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    current_user, membership = auth_data
    tool = await get_tool(db, tool_id, membership.team_id)
    versions = await get_versions(db, tool.id)
    return {
        "data": {
            "versions": [ToolVersionResponse.model_validate(v) for v in versions],
        }
    }


@router.post("/{tool_id}/versions/{version_id}/restore", response_model=dict)
async def restore_version_endpoint(
    tool_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
):
    current_user, membership = auth_data
    tool = await get_tool(db, tool_id, membership.team_id)
    version = await get_version(db, tool_id, version_id)
    if version is None:
        from src.exceptions import NotFoundError
        raise NotFoundError("Version not found.")
    restored = await restore_version(db, tool, version, current_user.id)
    return {"data": {"tool": ToolResponse.model_validate(restored)}}
