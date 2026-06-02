import re
import html
import logging

logger = logging.getLogger("deskforge.generate.sanitizer")

# Patterns that indicate XSS or injection attempts
SCRIPT_PATTERN = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
EVENT_HANDLER_PATTERN = re.compile(r"\bon\w+\s*=", re.IGNORECASE)
JAVASCRIPT_URI_PATTERN = re.compile(r"javascript\s*:", re.IGNORECASE)
DATA_URI_PATTERN = re.compile(r"data\s*:\s*text/html", re.IGNORECASE)
IFRAME_PATTERN = re.compile(r"<\s*iframe[^>]*>", re.IGNORECASE)
OBJECT_EMBED_PATTERN = re.compile(r"<\s*(object|embed|applet)[^>]*>", re.IGNORECASE)
STYLE_EXPRESSION_PATTERN = re.compile(r"expression\s*\(", re.IGNORECASE)
VBS_PATTERN = re.compile(r"vbscript\s*:", re.IGNORECASE)


def sanitize_spec(spec: dict) -> dict:
    """Sanitize a tool spec to prevent XSS and injection attacks."""
    return _sanitize_value(spec)


def _sanitize_value(value):
    """Recursively sanitize all string values in a nested structure."""
    if isinstance(value, str):
        return _sanitize_string(value)
    elif isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


def _sanitize_string(text: str) -> str:
    """Sanitize a single string value."""
    # Remove script tags and their content
    text = SCRIPT_PATTERN.sub("", text)

    # Remove event handlers
    text = EVENT_HANDLER_PATTERN.sub("", text)

    # Remove javascript: URIs
    text = JAVASCRIPT_URI_PATTERN.sub("", text)

    # Remove data:text/html URIs
    text = DATA_URI_PATTERN.sub("", text)

    # Remove iframes
    text = IFRAME_PATTERN.sub("", text)

    # Remove object/embed/applet tags
    text = OBJECT_EMBED_PATTERN.sub("", text)

    # Remove CSS expressions
    text = STYLE_EXPRESSION_PATTERN.sub("", text)

    # Remove vbscript: URIs
    text = VBS_PATTERN.sub("", text)

    return text


def sanitize_html_content(text: str) -> str:
    """More aggressive sanitization for HTML content."""
    # Remove all HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html.unescape(text)
    # Re-encode special characters
    text = html.escape(text)
    return text


def validate_data_bindings(spec: dict) -> bool:
    """Validate that all data bindings reference valid sources."""
    sources = {ds.get("name") for ds in spec.get("dataSources", []) if isinstance(ds, dict)}

    for comp in spec.get("components", []):
        if not isinstance(comp, dict):
            continue
        ds_ref = comp.get("dataSource")
        if isinstance(ds_ref, dict):
            ds_name = ds_ref.get("name")
            if ds_name and ds_name not in sources:
                logger.warning(f"Invalid data binding: {ds_name} not in data sources")
                return False

    return True
