"""SOTA dialogic tool return patterns."""

import logging
from typing import Any

logger = logging.getLogger("inkscape-mcp.response")


def success_response(
    result: Any,
    operation: str,
    message: str = "",
    recommendations: list[str] | None = None,
    next_steps: list[str] | None = None,
    execution_time_ms: float | None = None,
) -> dict[str, Any]:
    """Enhanced success response for dialogic MCP."""
    if execution_time_ms is None:
        execution_time_ms = 0.0
    out: dict[str, Any] = {
        "success": True,
        "operation": operation,
        "result": result,
        "execution_time_ms": execution_time_ms,
    }
    if message:
        out["message"] = message
    if recommendations:
        out["recommendations"] = recommendations
    if next_steps:
        out["next_steps"] = next_steps
    return out


def error_response(
    operation: str,
    error: str,
    recovery_options: list[str] | None = None,
    suggested_fixes: list[str] | None = None,
) -> dict[str, Any]:
    """Enhanced error response for dialogic MCP — auto-logs on failure."""
    logger.exception("Tool error: %s [%s]", error, operation)
    out: dict[str, Any] = {
        "success": False,
        "operation": operation,
        "error": error,
    }
    if recovery_options:
        out["recovery_options"] = recovery_options
    if suggested_fixes:
        out["suggested_fixes"] = suggested_fixes
    return out
