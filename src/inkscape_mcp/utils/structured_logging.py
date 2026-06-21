"""Structured JSON logging for Loki ingestion."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC
from datetime import datetime
from typing import Any


class JsonLogFormatter(logging.Formatter):
    """Emit one JSON object per log line for Promtail/Loki."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "inkscape-mcp",
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("operation", "tool", "duration_ms", "status", "mode"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=True)


def configure_json_logging(root: logging.Logger | None = None) -> None:
    target = root or logging.getLogger()
    formatter = JsonLogFormatter()
    for handler in target.handlers:
        handler.setFormatter(formatter)


def configure_json_logging_if_enabled() -> None:
    if os.getenv("INKSCAPE_MCP_LOG_FORMAT", "").strip().lower() != "json":
        return
    try:
        configure_json_logging()
    except Exception as exc:
        logging.getLogger(__name__).warning("JSON logging setup failed: %s", exc)
