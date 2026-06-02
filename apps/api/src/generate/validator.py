import json
import logging
from typing import Optional

from src.exceptions import SpecValidationError

logger = logging.getLogger("deskforge.generate.validator")

ALLOWED_COMPONENT_TYPES = {
    "DataTable", "Form", "KpiCard", "BarChart", "LineChart",
    "PieChart", "Heading", "Text", "Container", "Grid",
}


def validate_tool_spec(spec: dict) -> tuple[bool, list[str]]:
    """Validate a tool specification against the schema."""
    issues = []

    # Required top-level fields
    required_fields = ["version", "name", "layout", "components", "dataSources"]
    for field in required_fields:
        if field not in spec:
            issues.append(f"Missing required field: {field}")

    if issues:
        return False, issues

    # Version check
    if spec.get("version") != 1:
        issues.append(f"Invalid version: {spec.get('version')}. Must be 1.")

    # Name validation
    name = spec.get("name", "")
    if not isinstance(name, str) or len(name) < 1 or len(name) > 200:
        issues.append("Name must be a string between 1 and 200 characters.")

    # Layout validation
    layout = spec.get("layout", {})
    if not isinstance(layout, dict):
        issues.append("Layout must be an object.")
    elif layout.get("type") not in ("grid", "flex", "stack"):
        issues.append(f"Invalid layout type: {layout.get('type')}")

    # Components validation
    components = spec.get("components", [])
    if not isinstance(components, list):
        issues.append("Components must be an array.")
    else:
        component_ids = set()
        for i, comp in enumerate(components):
            if not isinstance(comp, dict):
                issues.append(f"Component {i} must be an object.")
                continue

            comp_type = comp.get("type")
            if comp_type not in ALLOWED_COMPONENT_TYPES:
                issues.append(f"Component {i}: invalid type '{comp_type}'")

            comp_id = comp.get("id")
            if not comp_id:
                issues.append(f"Component {i}: missing id")
            elif comp_id in component_ids:
                issues.append(f"Component {i}: duplicate id '{comp_id}'")
            else:
                component_ids.add(comp_id)

            # Validate layout positioning
            comp_layout = comp.get("layout", {})
            if not isinstance(comp_layout, dict):
                issues.append(f"Component {i}: layout must be an object")

    # DataSources validation
    data_sources = spec.get("dataSources", [])
    if not isinstance(data_sources, list):
        issues.append("dataSources must be an array.")
    else:
        source_names = set()
        for i, ds in enumerate(data_sources):
            if not isinstance(ds, dict):
                issues.append(f"DataSource {i} must be an object.")
                continue
            ds_name = ds.get("name")
            if not ds_name:
                issues.append(f"DataSource {i}: missing name")
            elif ds_name in source_names:
                issues.append(f"DataSource {i}: duplicate name '{ds_name}'")
            else:
                source_names.add(ds_name)

            ds_type = ds.get("type")
            if ds_type not in ("static", "api", "csv", "database"):
                issues.append(f"DataSource {i}: invalid type '{ds_type}'")

    # Cross-reference: components' data sources must exist
    for comp in components:
        if isinstance(comp, dict) and "dataSource" in comp:
            ds_ref = comp["dataSource"]
            if isinstance(ds_ref, dict) and ds_ref.get("name"):
                if ds_ref["name"] not in source_names:
                    issues.append(f"Component references non-existent data source: {ds_ref['name']}")

    return len(issues) == 0, issues


def parse_spec_from_llm(raw_output: str) -> Optional[dict]:
    """Parse and extract tool spec from LLM output."""
    # Try direct JSON parse
    try:
        spec = json.loads(raw_output)
        if isinstance(spec, dict):
            return spec
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    import re
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw_output, re.DOTALL)
    if json_match:
        try:
            spec = json.loads(json_match.group(1))
            if isinstance(spec, dict):
                return spec
        except json.JSONDecodeError:
            pass

    # Try finding JSON object in text
    brace_start = raw_output.find("{")
    brace_end = raw_output.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            spec = json.loads(raw_output[brace_start:brace_end + 1])
            if isinstance(spec, dict):
                return spec
        except json.JSONDecodeError:
            pass

    return None
