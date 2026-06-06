import json
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db, get_current_user, require_role, require_verified_email
from src.models.user import User
from src.models.team_member import TeamMember
from src.teams.service import get_team_for_user
from src.generate.pipeline import run_generation_pipeline, run_iteration_pipeline
from src.generate.templates import get_all_templates, get_template_by_id
from src.generate.schemas import GenerateRequest, IterateRequest, ClarifyRequest, TemplateResponse
from src.tools.service import get_tool
from src.exceptions import TemplateNotFoundError

logger = logging.getLogger("deskforge.generate")

router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post("")
async def generate_tool(
    body: GenerateRequest,
    x_debug: Optional[str] = Header(None, alias="X-Debug"),
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
    _verified: User = Depends(require_verified_email),
):
    current_user, membership = auth_data

    template_context = None
    if body.template_id:
        template = get_template_by_id(body.template_id)
        if template is None:
            raise TemplateNotFoundError()
        template_context = template

    # Debug mode: return raw output instead of streaming
    if x_debug:
        from src.generate.pipeline import run_generation_debug
        debug_result = await run_generation_debug(
            db=db,
            prompt=body.prompt,
            user_id=current_user.id,
            team_id=membership.team_id,
            data_source_id=body.data_source_id,
            template_context=template_context,
        )
        return JSONResponse(
            content={
                "data": {
                    "debug": True,
                    "raw_llm_output": debug_result.get("raw_output"),
                    "validation_errors": debug_result.get("validation_errors", []),
                    "spec": debug_result.get("spec"),
                    "explanation": debug_result.get("explanation"),
                }
            }
        )

    return StreamingResponse(
        run_generation_pipeline(
            db=db,
            prompt=body.prompt,
            user_id=current_user.id,
            team_id=membership.team_id,
            data_source_id=body.data_source_id,
            template_context=template_context,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{tool_id}/iterate")
async def iterate_tool(
    tool_id: UUID,
    body: IterateRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
    _verified: User = Depends(require_verified_email),
):
    current_user, membership = auth_data

    return StreamingResponse(
        run_iteration_pipeline(
            db=db,
            tool_id=tool_id,
            message=body.message,
            user_id=current_user.id,
            team_id=membership.team_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/clarify")
async def clarify_generation(
    body: ClarifyRequest,
    db: AsyncSession = Depends(get_db),
    auth_data: tuple = Depends(require_role("editor")),
    _verified: User = Depends(require_verified_email),
):
    current_user, membership = auth_data

    # Reconstruct prompt from clarification answers
    combined_prompt = f"Session: {body.session_id}\nAnswers: {json.dumps(body.answers)}"

    return StreamingResponse(
        run_generation_pipeline(
            db=db,
            prompt=combined_prompt,
            user_id=current_user.id,
            team_id=membership.team_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


templates_router = APIRouter(prefix="/templates", tags=["Templates"])


@templates_router.get("", response_model=dict)
async def list_templates(current_user: User = Depends(get_current_user)):
    templates = get_all_templates()
    return {
        "data": {
            "templates": [TemplateResponse(**t) for t in templates],
        }
    }


@templates_router.get("/{template_id}", response_model=dict)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    template = get_template_by_id(template_id)
    if template is None:
        raise TemplateNotFoundError()
    return {"data": {"template": TemplateResponse(**template)}}
