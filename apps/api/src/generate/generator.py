import json
import logging
import asyncio
from typing import AsyncGenerator, Optional

import httpx
from src.config import settings

logger = logging.getLogger("deskforge.generate.generator")


async def generate_stream(
    messages: list[dict],
    timeout: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """Stream LLM response via SSE."""
    timeout = timeout or settings.OPENAI_TIMEOUT_SECONDS

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5.0)) as client:
        try:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "stream": True,
                    "response_format": {"type": "json_object"},
                },
            ) as response:
                if response.status_code != 200:
                    error_body = ""
                    async for chunk in response.aiter_text():
                        error_body += chunk
                    logger.error(f"OpenAI stream error: {response.status_code} {error_body}")
                    yield f"data: {json.dumps({'error': 'LLM service error'})}\n\n"
                    return

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line or line == "data: [DONE]":
                            continue
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue

        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            yield f"data: {json.dumps({'error': 'LLM request timed out'})}\n\n"
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            yield f"data: {json.dumps({'error': 'Generation failed'})}\n\n"


async def generate_complete(
    messages: list[dict],
    timeout: Optional[int] = None,
) -> str:
    """Get complete LLM response (non-streaming)."""
    timeout = timeout or settings.OPENAI_TIMEOUT_SECONDS

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5.0)) as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                },
            )
            if response.status_code != 200:
                logger.error(f"OpenAI error: {response.status_code} {response.text}")
                raise Exception(f"LLM error: {response.status_code}")

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            raise Exception("LLM request timed out")
