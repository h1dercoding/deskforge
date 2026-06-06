import csv
import io
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
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
    clone_tool,
)
from src.tools.versioning import get_versions, restore_version, get_version
from src.tools.schemas import (
    CreateToolRequest,
    UpdateToolRequest,
    UpdateSpecRequest,
    ToolResponse,
    ToolVersionResponse,
)
from src.models.tool import Tool
import sqlalchemy as sa

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=dict)
async def list_tools_endpoint(
    status: str = Query("active", pattern="^(active|draft|archived|all)$"),
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated tag list"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    current_user, membership = auth_data

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    tools, total = await list_tools(
        db, membership.team_id, status, page, per_page,
        category=category, tags=tag_list,
    )
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


@router.get("/categories", response_model=dict)
async def list_categories_endpoint(
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    """Get all unique categories for the team's tools."""
    current_user, membership = auth_data
    result = await db.execute(
        sa.select(Tool.category)
        .where(Tool.team_id == membership.team_id, Tool.category.isnot(None))
        .distinct()
    )
    categories = [row[0] for row in result.all() if row[0]]
    return {"data": {"categories": sorted(categories)}}


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


@router.put("/{tool_id}/spec", response_model=dict)
async def update_spec_endpoint(
    tool_id: UUID,
    body: UpdateSpecRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
    _verified: User = Depends(require_verified_email),
):
    """Directly update a tool's spec JSON (bypasses LLM).

    This allows developers to programmatically modify tool specs
    without going through the generation pipeline.
    """
    current_user, membership = auth_data
    tool = await get_tool(db, tool_id, membership.team_id)
    from src.generate.validator import validate_tool_spec
    from src.generate.sanitizer import sanitize_spec

    is_valid, issues = validate_tool_spec(body.spec)
    if not is_valid:
        from src.exceptions import SpecValidationError
        raise SpecValidationError(f"Invalid spec: {', '.join(issues)}")

    spec = sanitize_spec(body.spec)
    updated = await update_tool_spec(db, tool, spec, "Direct spec update", current_user.id)
    return {"data": {"tool": ToolResponse.model_validate(updated)}}


@router.post("/{tool_id}/clone", response_model=dict, status_code=201)
async def clone_tool_endpoint(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
    _verified: User = Depends(require_verified_email),
):
    """Clone/duplicate a tool.

    Creates a copy of the tool with "(Copy)" appended to the name.
    Useful for agencies creating similar tools across clients.
    """
    current_user, membership = auth_data
    original = await get_tool(db, tool_id, membership.team_id)
    cloned = await clone_tool(db, original, current_user.id, membership.team_id)
    return {"data": {"tool": ToolResponse.model_validate(cloned)}}


@router.get("/{tool_id}/data/export")
async def export_tool_data(
    tool_id: UUID,
    format: str = Query("csv", pattern="^(csv)$"),
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(get_team_membership),
):
    """Export tool data as CSV."""
    current_user, membership = auth_data
    tool = await get_tool(db, tool_id, membership.team_id)

    # Get submissions for this tool
    from src.models.form_submission import FormSubmission
    result = await db.execute(
        sa.select(FormSubmission)
        .where(FormSubmission.tool_id == tool_id)
        .order_by(FormSubmission.created_at.desc())
    )
    submissions = result.scalars().all()

    if not submissions:
        # Return empty CSV with headers
        output = io.StringIO()
        output.write("submitted_at,submitted_by,data\n")
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={tool.slug}-export.csv"},
        )

    # Build CSV from submissions
    output = io.StringIO()
    writer = csv.writer(output)

    # Collect all unique keys from submission data
    all_keys = set()
    for sub in submissions:
        if sub.data and isinstance(sub.data, dict):
            all_keys.update(sub.data.keys())

    headers = ["submitted_at", "submitted_by"] + sorted(all_keys)
    writer.writerow(headers)

    for sub in submissions:
        row = [sub.created_at.isoformat() if sub.created_at else "", sub.submitted_by or ""]
        data = sub.data if sub.data and isinstance(sub.data, dict) else {}
        for key in sorted(all_keys):
            row.append(str(data.get(key, "")))
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={tool.slug}-export.csv"},
    )


@router.post("/{tool_id}/submissions", response_model=dict, status_code=201)
async def create_submission(
    tool_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Submit form data for a tool (used by shared/public tools)."""
    body = await request.json()
    from src.models.form_submission import FormSubmission
    from uuid import uuid4

    # Verify tool exists
    result = await db.execute(sa.select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()
    if tool is None:
        from src.exceptions import ToolNotFoundError
        raise ToolNotFoundError()

    submission = FormSubmission(
        id=uuid4(),
        tool_id=tool_id,
        data=body.get("data", {}),
        submitted_by=body.get("submitted_by"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return {
        "data": {
            "id": str(submission.id),
            "tool_id": str(submission.tool_id),
            "created_at": submission.created_at.isoformat() if submission.created_at else None,
        }
    }


@router.get("/{tool_id}/submissions", response_model=dict)
async def list_submissions(
    tool_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("viewer")),
):
    """List form submissions for a tool."""
    current_user, membership = auth_data
    tool = await get_tool(db, tool_id, membership.team_id)

    from src.models.form_submission import FormSubmission
    count_result = await db.execute(
        sa.select(sa.func.count()).select_from(FormSubmission).where(FormSubmission.tool_id == tool_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        sa.select(FormSubmission)
        .where(FormSubmission.tool_id == tool_id)
        .order_by(FormSubmission.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    submissions = result.scalars().all()

    return {
        "data": {
            "submissions": [
                {
                    "id": str(s.id),
                    "data": s.data,
                    "submitted_by": s.submitted_by,
                    "ip_address": s.ip_address,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in submissions
            ],
        },
        "meta": {"page": page, "per_page": per_page, "total": total},
    }
