"""Tests for inkscape fleet handoff and pipeline."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from inkscape_mcp.tools.fleet_tools import inkscape_fleet
from inkscape_mcp.utils.fleet_handoff import push_raster_to_gimp, stage_svg_for_blender
from inkscape_mcp.utils.fleet_staging import stage_file


class TestFleetStaging:
    @pytest.mark.asyncio
    async def test_stage_file(self, tmp_path, temp_file):
        temp_file.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
        result = await stage_file(
            source_path=str(temp_file),
            staging_dir=tmp_path,
            subdir="incoming",
        )
        assert result["success"] is True
        assert Path(result["staged_path"]).is_file()


class TestFleetHandoff:
    @pytest.mark.asyncio
    async def test_push_raster_to_gimp(self):
        with patch(
            "inkscape_mcp.utils.fleet_handoff.check_http_health",
            new=AsyncMock(return_value=True),
        ), patch(
            "inkscape_mcp.utils.fleet_handoff.call_http_tool",
            new=AsyncMock(return_value={"success": True, "data": {"passed": True}}),
        ), patch("inkscape_mcp.utils.fleet_handoff.Path") as mock_path:
            mock_path.return_value.is_file.return_value = True
            result = await push_raster_to_gimp(png_path="D:/Temp/test.png")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_stage_blender_svg_copy_only(self, tmp_path, temp_file):
        temp_file.write_text(
            """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>"""
        )
        with patch(
            "inkscape_mcp.utils.fleet_handoff.DEFAULT_BLENDER_DROP_DIR",
            tmp_path / "blender_drop",
        ):
            result = await stage_svg_for_blender(
                svg_path=str(temp_file),
                import_to_blender=False,
            )
        assert result["success"] is True
        assert Path(result["staged_path"]).is_file()


class TestInkscapeFleetTool:
    @pytest.mark.asyncio
    async def test_list_staging(self, tmp_path):
        incoming = tmp_path / "incoming"
        incoming.mkdir(parents=True)
        (incoming / "a.svg").write_text("<svg/>")

        result = await inkscape_fleet(
            operation="list_staging",
            staging_dir=str(tmp_path),
        )
        assert result["success"] is True
        assert len(result["data"]["files"]) >= 1

    @pytest.mark.asyncio
    async def test_run_pipeline_missing_svg(self):
        result = await inkscape_fleet(
            operation="run_pipeline",
            svg_path="/missing/file.svg",
            project_path="D:/Unity/MyProject",
            skip_unity=True,
        )
        assert result["success"] is False
