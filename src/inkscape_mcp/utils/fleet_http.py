"""HTTP helpers for cross-fleet MCP tool calls."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BLENDER_URL = "http://127.0.0.1:10849"
DEFAULT_UNITY_URL = "http://127.0.0.1:10831"
DEFAULT_GIMP_URL = "http://127.0.0.1:10773"
DEFAULT_INKSCAPE_URL = "http://127.0.0.1:10900"


async def check_http_health(base_url: str, *, health_path: str = "/api/health") -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(base_url.rstrip("/") + health_path)
            return response.status_code == 200
    except httpx.HTTPError:
        return False


async def call_http_tool(
    base_url: str,
    tool: str,
    params: dict[str, Any],
    *,
    tool_path: str = "/api/v1/tool",
    timeout: float = 300.0,
) -> dict[str, Any]:
    """Call a fleet MCP POST tool endpoint."""
    url = base_url.rstrip("/") + tool_path
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json={"tool": tool, "params": params})
            response.raise_for_status()
            body = response.json()
    except httpx.HTTPError as exc:
        logger.exception("HTTP tool call failed tool=%s url=%s", tool, url)
        return {"success": False, "error": str(exc), "tool": tool}

    if isinstance(body, dict) and body.get("data") is not None:
        data = body["data"]
        if isinstance(data, dict):
            if body.get("success") is False and "success" not in data:
                data = {**data, "success": False}
            elif "success" not in data:
                data = {**data, "success": bool(body.get("success", True))}
            return data
    return body if isinstance(body, dict) else {"success": False, "error": "Invalid tool response"}


def parse_tool_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        if "data" in result and isinstance(result["data"], dict):
            return result["data"]
        return result
    content = getattr(result, "content", None)
    if content:
        text = getattr(content[0], "text", str(content[0]))
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"output": text}
    return {"raw": str(result)}
