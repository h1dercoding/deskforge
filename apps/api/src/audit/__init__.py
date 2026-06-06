import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from src.dependencies import get_db, get_team_membership, require_role
from src.models.audit_log import AuditLog
import sqlalchemy as sa

logger = logging.getLogger("deskforge.audit")

router = APIRouter(prefix="/audit-log", tags=["Audit Log"])


@router.get("", response_model=dict)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (tool, team, datasource, etc.)"),
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("viewer")),
):
    """List audit logs for the team with pagination and filtering."""
    current_user, membership = auth_data

    query = sa.select(AuditLog).where(AuditLog.team_id == membership.team_id)

    if action:
        query = query.where(AuditLog.action == action)

    if user_id:
        from uuid import UUID
        try:
            query = query.where(AuditLog.user_id == UUID(user_id))
        except ValueError:
            pass

    if resource_type:
        # Filter by action prefix pattern (e.g., "tool." matches "tool.create", "tool.update")
        query = query.where(AuditLog.action.ilike(f"{resource_type}.%"))

    # Get total count
    count_query = sa.select(sa.func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Get paginated results
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    logs = result.scalars().all()

    # Enrich with user info
    from src.models.user import User
    user_ids = list(set(log.user_id for log in logs))
    users_map = {}
    if user_ids:
        users_result = await db.execute(sa.select(User).where(User.id.in_(user_ids)))
        for user in users_result.scalars().all():
            users_map[user.id] = user

    return {
        "data": {
            "logs": [
                {
                    "id": str(log.id),
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "user_id": str(log.user_id),
                    "user_name": users_map[log.user_id].name if log.user_id in users_map else None,
                    "user_email": users_map[log.user_id].email if log.user_id in users_map else None,
                    "action": log.action,
                    "resource_type": log.action.split(".")[0] if "." in log.action else None,
                    "resource_id": str(log.tool_id) if log.tool_id else None,
                    "details": log.details,
                    "ip_address": log.ip_address,
                }
                for log in logs
            ],
        },
        "meta": {"page": page, "per_page": per_page, "total": total},
    }


@router.get("/actions", response_model=dict)
async def list_audit_actions(
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("viewer")),
):
    """Get all unique audit log actions for the team."""
    current_user, membership = auth_data
    result = await db.execute(
        sa.select(AuditLog.action)
        .where(AuditLog.team_id == membership.team_id)
        .distinct()
    )
    actions = [row[0] for row in result.all()]
    return {"data": {"actions": sorted(actions)}}
