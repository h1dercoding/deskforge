"""Structured JSON logging setup for DeskForge."""
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any

from src.config import settings


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields from record
        for key in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client",
            "user_id",
            "team_id",
        ):
            value = getattr(record, key, None)
            if value is not None:
                log_data[key] = value

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", None)
        prefix = f"[{request_id[:8]}] " if request_id else ""

        # Use the standard formatter for the base message
        self._style._fmt = f"%(asctime)s %(levelname)-8s {prefix}%(name)s: %(message)s"
        result = super().format(record)

        # Append request context if available
        extras = []
        for key in ("method", "path", "duration_ms", "status_code"):
            value = getattr(record, key, None)
            if value is not None:
                extras.append(f"{key}={value}")

        if extras:
            result += f" | {' '.join(extras)}"

        return result


def setup_logging(level: str = "INFO", format: str = "json") -> None:
    """Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Output format ('json' or 'text')
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    if format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))

    root_logger.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )

    logger = logging.getLogger("deskforge")
    logger.info(f"Logging configured: level={level}, format={format}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the deskforge namespace.

    Args:
        name: Logger name (will be prefixed with 'deskforge.')
    """
    if name.startswith("deskforge."):
        return logging.getLogger(name)
    return logging.getLogger(f"deskforge.{name}")
