"""Prometheus metrics helpers for inkscape-mcp."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_metrics_initialized = False
_tool_calls_total = None
_tool_duration_seconds = None
_execution_mode = None
_app_info = None


def metrics_enabled() -> bool:
    value = os.getenv("INKSCAPE_MCP_METRICS_ENABLED", "true").strip().lower()
    return value not in {"0", "false", "no", "off"}


def init_metrics() -> None:
    """Initialize Prometheus metrics (idempotent)."""
    global _metrics_initialized, _tool_calls_total, _tool_duration_seconds
    global _execution_mode, _app_info

    if _metrics_initialized or not metrics_enabled():
        return

    try:
        from prometheus_client import REGISTRY

        if "inkscape_mcp_tool_calls_total" in getattr(REGISTRY, "_names_to_collectors", {}):
            _metrics_initialized = True
            return
    except ImportError:
        pass

    try:
        from prometheus_client import Counter
        from prometheus_client import Gauge
        from prometheus_client import Histogram
        from prometheus_client import Info
    except ImportError:
        logger.warning(
            "prometheus_client not installed; metrics disabled. "
            "Install with: uv sync --extra monitoring"
        )
        return

    try:
        _tool_calls_total = Counter(
            "inkscape_mcp_tool_calls_total",
            "Total MCP tool invocations",
            ["tool", "status"],
        )
        _tool_duration_seconds = Histogram(
            "inkscape_mcp_tool_duration_seconds",
            "MCP tool execution duration",
            ["tool"],
            buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
        )
        _execution_mode = Gauge(
            "inkscape_mcp_execution_mode",
            "Execution mode: 0=hands_off batch CLI, 1=hands_in GUI watch",
        )
        _app_info = Info("inkscape_mcp", "Inkscape MCP application info")

        from inkscape_mcp import __version__

        _app_info.info({"version": __version__, "service": "inkscape-mcp"})
    except ValueError as exc:
        if "Duplicated timeseries" not in str(exc):
            raise
        logger.debug("Prometheus metrics already registered")

    _metrics_initialized = True


def record_tool_call(tool: str, status: str, duration_seconds: float | None = None) -> None:
    if not _metrics_initialized:
        init_metrics()
    if _tool_calls_total is not None:
        _tool_calls_total.labels(tool=tool, status=status).inc()
    if duration_seconds is not None and _tool_duration_seconds is not None:
        _tool_duration_seconds.labels(tool=tool).observe(duration_seconds)


def set_execution_mode(hands_in: bool) -> None:
    if not _metrics_initialized:
        init_metrics()
    if _execution_mode is not None:
        _execution_mode.set(1 if hands_in else 0)


def render_metrics() -> bytes:
    if not _metrics_initialized:
        return b"# metrics disabled\n"
    from prometheus_client import generate_latest

    return generate_latest()


def metrics_content_type() -> str:
    from prometheus_client import CONTENT_TYPE_LATEST

    return CONTENT_TYPE_LATEST


def start_metrics_server(port: int | None = None) -> None:
    if not _metrics_initialized:
        init_metrics()
    if not _metrics_initialized:
        return

    scrape_port = port or int(os.getenv("PROMETHEUS_PORT", "9074"))
    try:
        from prometheus_client import start_http_server

        start_http_server(scrape_port)
        logger.info("Prometheus metrics server listening on port %s", scrape_port)
    except OSError as exc:
        logger.error("Failed to start Prometheus metrics server on %s: %s", scrape_port, exc)


def register_metrics_routes(mcp: Any) -> None:
    """Attach /api/metrics and /metrics to the FastMCP HTTP app."""
    if not hasattr(mcp, "custom_route"):
        logger.warning("FastMCP custom_route unavailable; skipping metrics HTTP routes")
        return

    from starlette.requests import Request
    from starlette.responses import Response

    @mcp.custom_route("/api/metrics", methods=["GET"])
    async def _api_metrics(_request: Request) -> Response:
        return Response(content=render_metrics(), media_type=metrics_content_type())

    @mcp.custom_route("/metrics", methods=["GET"])
    async def _metrics(_request: Request) -> Response:
        return Response(content=render_metrics(), media_type=metrics_content_type())

    logger.info("Registered /api/metrics and /metrics routes")


def install_tool_call_wrapper(app: Any) -> None:
    if not metrics_enabled():
        return
    init_metrics()
    if not _metrics_initialized:
        return
    if getattr(app, "_telemetry_wrapped", False):
        return

    original = app.call_tool

    async def wrapped_call_tool(name: str, arguments: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        with ToolMetricsContext(name) as ctx:
            try:
                return await original(name, arguments or {}, **kwargs)
            except Exception:
                ctx.status = "error"
                raise

    app.call_tool = wrapped_call_tool
    app._telemetry_wrapped = True
    logger.info("Installed MCP tool telemetry wrapper")


class ToolMetricsContext:
    def __init__(self, tool: str) -> None:
        self.tool = tool
        self._start = 0.0
        self.status = "ok"

    def __enter__(self) -> ToolMetricsContext:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is not None:
            self.status = "error"
        duration = time.perf_counter() - self._start
        record_tool_call(self.tool, self.status, duration)
