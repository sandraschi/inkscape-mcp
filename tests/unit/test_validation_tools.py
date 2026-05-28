"""Tests for inkscape_validation portmanteau (Phase 2)."""

import pytest

from inkscape_mcp.tools.validation_tools import inkscape_validation


class TestInkscapeValidation:
    @pytest.mark.asyncio
    async def test_validate_svg_passes_minimal(self, temp_file):
        temp_file.write_text(
            """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <rect x="10" y="10" width="80" height="80" fill="blue"/>
</svg>"""
        )
        result = await inkscape_validation(
            operation="validate_svg",
            input_path=str(temp_file),
        )
        assert result["success"] is True
        assert result["issues"] == []

    @pytest.mark.asyncio
    async def test_check_viewbox_missing(self, temp_file):
        temp_file.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"></svg>'
        )
        result = await inkscape_validation(
            operation="check_viewbox",
            input_path=str(temp_file),
        )
        assert result["success"] is False
        assert any("viewBox" in issue for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_audit_web_svg_with_viewbox(self, temp_file):
        temp_file.write_text(
            """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <rect x="10" y="10" width="80" height="80" fill="blue"/>
</svg>"""
        )
        result = await inkscape_validation(
            operation="audit_web_svg",
            input_path=str(temp_file),
        )
        assert result["success"] is True
        assert result["data"]["painted_shape_count"] >= 1

    @pytest.mark.asyncio
    async def test_missing_file(self):
        result = await inkscape_validation(
            operation="validate_svg",
            input_path="/nonexistent/file.svg",
        )
        assert result["success"] is False
        assert result["error"] == "FileNotFoundError"
