import json
import logging
import time
import uuid
from typing import AsyncGenerator, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.generate.classifier import classify_intent, generate_clarifying_questions
from src.generate.builder import build_generation_prompt, build_iteration_prompt
from src.generate.generator import generate_stream, generate_complete
from src.generate.validator import validate_tool_spec, parse_spec_from_llm
from src.generate.sanitizer import sanitize_spec, validate_data_bindings
from src.tools.service import create_tool, update_tool_spec
from src.models.data_source import DataSource
from src.exceptions import GenerationError, LLMTimeoutError, SpecValidationError
import sqlalchemy as sa

logger = logging.getLogger("deskforge.generate.pipeline")


async def load_system_prompt() -> str:
    with open("src/generate/prompts/system.txt", "r") as f:
        return f.read()


async def get_data_source_schema(db: AsyncSession, data_source_id: Optional[UUID]) -> Optional[dict]:
    """Load data source schema for prompt context."""
    if not data_source_id:
        return None
    result = await db.execute(sa.select(DataSource).where(DataSource.id == data_source_id))
    ds = result.scalar_one_or_none()
    if ds and ds.schema_:
        return ds.schema_
    return None


async def run_generation_pipeline(
    db: AsyncSession,
    prompt: str,
    user_id: UUID,
    team_id: UUID,
    data_source_id: Optional[UUID] = None,
    template_context: Optional[dict] = None,
) -> AsyncGenerator[str, None]:
    """Run the full tool generation pipeline with SSE streaming."""
    start_time = time.monotonic()

    # Step 1: Validate prompt
    if len(prompt) < 10:
        yield _sse_event("error", {"message": "Prompt must be at least 10 characters."})
        return
    if len(prompt) > 2000:
        yield _sse_event("error", {"message": "Prompt must be at most 2000 characters."})
        return

    yield _sse_event("progress", {"step": "analyzing", "message": "Understanding your requirements..."})

    # Step 2: Classify intent
    try:
        classification = await classify_intent(prompt)
    except Exception as e:
        logger.warning(f"Classification failed: {e}")
        classification = None

    # Step 3: Check if clarification needed
    if classification and classification.get("clarity") == "AMBIGUOUS":
        try:
            questions = await generate_clarifying_questions(prompt, classification)
            session_id = str(uuid.uuid4())
            yield _sse_event("clarify", {
                "session_id": session_id,
                "questions": questions.get("questions", []),
            })
            return
        except Exception:
            pass  # Fall through to generation

    yield _sse_event("progress", {"step": "generating", "message": "Building your tool..."})

    # Step 4: Build prompt
    system_prompt = await load_system_prompt()
    data_source_schema = await get_data_source_schema(db, data_source_id)

    messages = build_generation_prompt(
        user_prompt=prompt,
        system_prompt=system_prompt,
        classification=classification,
        data_source_schema=data_source_schema,
        template_context=template_context,
    )

    # Step 5: Generate with streaming
    raw_output = ""
    async for chunk in generate_stream(messages):
        raw_output += chunk

    # Step 6: Parse and validate
    yield _sse_event("progress", {"step": "validating", "message": "Validating your tool..."})

    spec = parse_spec_from_llm(raw_output)
    if spec is None:
        yield _sse_event("error", {"message": "Failed to generate a valid tool specification. Please try again."})
        return

    # Retry once if validation fails
    is_valid, issues = validate_tool_spec(spec)
    if not is_valid:
        logger.info(f"First validation failed: {issues}. Retrying with error context.")
        messages.append({"role": "assistant", "content": json.dumps(spec)})
        messages.append({"role": "user", "content": f"The spec has these issues: {', '.join(issues)}. Fix them."})

        raw_output = ""
        async for chunk in generate_stream(messages):
            raw_output += chunk

        spec = parse_spec_from_llm(raw_output)
        if spec is None:
            yield _sse_event("error", {"message": "Failed to generate a valid tool. Please try again."})
            return

        is_valid, issues = validate_tool_spec(spec)
        if not is_valid:
            yield _sse_event("error", {"message": f"Tool specification validation failed: {', '.join(issues)}"})
            return

    # Step 7: Sanitize
    spec = sanitize_spec(spec)
    if not validate_data_bindings(spec):
        yield _sse_event("error", {"message": "Invalid data source references in generated tool."})
        return

    # Step 8: Save tool
    tool_name = spec.get("name", "Generated Tool")
    try:
        tool = await create_tool(
            db=db,
            team_id=team_id,
            user_id=user_id,
            name=tool_name,
            prompt=prompt,
            spec=spec,
            data_source_id=data_source_id,
            description=spec.get("description", ""),
        )
    except Exception as e:
        logger.error(f"Failed to save tool: {e}")
        yield _sse_event("error", {"message": "Failed to save the generated tool."})
        return

    duration_ms = round((time.monotonic() - start_time) * 1000)
    logger.info(f"Tool generated in {duration_ms}ms: {tool.id}")

    yield _sse_event("spec", {
        "spec": spec,
        "tool_id": str(tool.id),
    })
    yield _sse_event("done", {"success": True, "tool_id": str(tool.id)})


async def run_iteration_pipeline(
    db: AsyncSession,
    tool_id: UUID,
    message: str,
    user_id: UUID,
    team_id: UUID,
) -> AsyncGenerator[str, None]:
    """Iterate on an existing tool."""
    from src.tools.service import get_tool

    tool = await get_tool(db, tool_id, team_id)
    system_prompt = await load_system_prompt()

    yield _sse_event("progress", {"step": "generating", "message": "Updating your tool..."})

    messages = build_iteration_prompt(
        current_spec=tool.spec,
        message=message,
        system_prompt=system_prompt,
    )

    raw_output = ""
    async for chunk in generate_stream(messages):
        raw_output += chunk

    spec = parse_spec_from_llm(raw_output)
    if spec is None:
        yield _sse_event("error", {"message": "Failed to generate valid update. Please try again."})
        return

    is_valid, issues = validate_tool_spec(spec)
    if not is_valid:
        yield _sse_event("error", {"message": f"Validation failed: {', '.join(issues)}"})
        return

    spec = sanitize_spec(spec)

    updated_tool = await update_tool_spec(db, tool, spec, message, user_id)

    yield _sse_event("spec", {
        "spec": spec,
        "tool_id": str(updated_tool.id),
    })
    yield _sse_event("done", {"success": True, "tool_id": str(updated_tool.id)})


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
