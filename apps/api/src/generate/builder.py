import json
from typing import Optional


def build_generation_prompt(
    user_prompt: str,
    system_prompt: str,
    classification: Optional[dict] = None,
    data_source_schema: Optional[dict] = None,
    existing_spec: Optional[dict] = None,
    template_context: Optional[dict] = None,
    clarification_answers: Optional[dict] = None,
) -> list[dict]:
    """Build the full prompt for LLM tool generation."""
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    user_content = f"Generate an internal tool based on this description:\n\n{user_prompt}"

    if classification:
        user_content += f"\n\nDetected category: {classification.get('category', 'general')}"
        user_content += f"\nSuggested widgets: {', '.join(classification.get('widgets', []))}"

    if data_source_schema:
        user_content += f"\n\nConnected data source schema:\n```json\n{json.dumps(data_source_schema, indent=2)}\n```"

    if existing_spec:
        with open("src/generate/prompts/iterate.txt", "r") as f:
            iterate_template = f.read()
        iterate_content = iterate_template.replace("{current_spec}", json.dumps(existing_spec, indent=2))
        iterate_content = iterate_content.replace("{message}", user_prompt)
        messages.append({"role": "user", "content": iterate_content})
        return messages

    if template_context:
        user_content += f"\n\nTemplate context:\n```json\n{json.dumps(template_context, indent=2)}\n```"

    if clarification_answers:
        user_content += f"\n\nUser's answers to clarification:\n```json\n{json.dumps(clarification_answers, indent=2)}\n```"

    messages.append({"role": "user", "content": user_content})
    return messages


def build_iteration_prompt(
    current_spec: dict,
    message: str,
    system_prompt: str,
) -> list[dict]:
    """Build prompt for tool iteration."""
    with open("src/generate/prompts/iterate.txt", "r") as f:
        iterate_template = f.read()

    iterate_content = iterate_template.replace("{current_spec}", json.dumps(current_spec, indent=2))
    iterate_content = iterate_content.replace("{message}", message)

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": iterate_content},
    ]
