import json
import logging
from typing import Optional

import httpx
from src.config import settings

logger = logging.getLogger("deskforge.generate.classifier")

CLASSIFY_PROMPT_PATH = "src/generate/prompts/classify.txt"


def _load_prompt() -> str:
    with open(CLASSIFY_PROMPT_PATH, "r") as f:
        return f.read()


async def classify_intent(prompt: str) -> dict:
    """Classify user intent using GPT-4o-mini."""
    system_prompt = _load_prompt()

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MINI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
            )
            if response.status_code != 200:
                logger.error(f"OpenAI classify error: {response.status_code} {response.text}")
                return _default_classification()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return _default_classification()


async def generate_clarifying_questions(prompt: str, classification: dict) -> dict:
    """Generate clarifying questions for ambiguous prompts."""
    with open("src/generate/prompts/clarify.txt", "r") as f:
        clarify_prompt = f.read()

    clarify_prompt = clarify_prompt.replace("{classification}", json.dumps(classification))
    clarify_prompt = clarify_prompt.replace("{prompt}", prompt)

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MINI_MODEL,
                    "messages": [
                        {"role": "system", "content": "Respond with valid JSON only."},
                        {"role": "user", "content": clarify_prompt},
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                },
            )
            if response.status_code != 200:
                return {"questions": []}

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception:
            return {"questions": []}


def _default_classification() -> dict:
    return {
        "clarity": "CLEAR",
        "widgets": ["DataTable"],
        "data_source_type": "csv",
        "category": "operations",
        "confidence": 0.5,
        "clarifying_questions": [],
    }
