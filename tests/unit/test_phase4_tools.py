"""Tests for Phase 4 telemetry, logging, and metrics routes."""

from __future__ import annotations

import logging
from unittest.mock import patch

from inkscape_mcp.utils.structured_logging import JsonLogFormatter


class TestTelemetry:
    def test_metrics_disabled_render(self):
        from inkscape_mcp.utils import telemetry

        telemetry._metrics_initialized = False
        with patch.object(telemetry, "metrics_enabled", return_value=False):
            telemetry.init_metrics()
        body = telemetry.render_metrics()
        assert b"disabled" in body

    def test_json_log_formatter(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        line = JsonLogFormatter().format(record)
        assert '"service": "inkscape-mcp"' in line
        assert "hello" in line

    def test_register_metrics_routes(self):
        from fastmcp import FastMCP

        from inkscape_mcp.utils.telemetry import register_metrics_routes

        mcp = FastMCP("test")
        register_metrics_routes(mcp)
        paths = {getattr(r, "path", None) for r in mcp.http_app().routes}
        assert "/api/metrics" in paths
        assert "/metrics" in paths
