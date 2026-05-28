"""Tests for Agent Lab Phase 5 fab art and fleet E2E offline smoke."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def fab_svg(tmp_path: Path) -> Path:
    path = tmp_path / "part.svg"
    path.write_text(
        """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50"><circle cx="25" cy="25" r="20"/></svg>""",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def mock_cli():
    wrapper = AsyncMock()
    wrapper._execute_actions = AsyncMock(return_value=(0, "ok", ""))
    wrapper._execute_command = AsyncMock(return_value="Inkscape 1.3")
    return wrapper


@pytest.fixture
def mock_config(tmp_path):
    class _Cfg:
        process_timeout = 30
        inkscape_executable = "mock_inkscape"
        temp_directory = str(tmp_path)

    return _Cfg()


class TestFabPresets:
    @pytest.mark.asyncio
    async def test_list_presets(self):
        from inkscape_mcp.tools.fab_art_tools import inkscape_fab_art

        result = await inkscape_fab_art("list_presets")
        assert result["success"] is True
        assert result["data"]["laser_dot_presets"]


class TestLaserDots:
    @pytest.mark.asyncio
    async def test_batch_laser_dots(self, tmp_path: Path, mock_cli, mock_config):
        from inkscape_mcp.tools.fab_art_tools import inkscape_fab_art

        out = tmp_path / "laser"
        result = await inkscape_fab_art(
            "batch_laser_dots",
            output_dir=str(out),
            laser_preset_id="fab_calibration_grid",
            cli_wrapper=mock_cli,
            config=mock_config,
        )
        assert result["success"] is True
        assert len(result["files"]) == 4


class TestDxfBatch:
    @pytest.mark.asyncio
    async def test_batch_dxf_export(self, fab_svg: Path, tmp_path: Path, mock_cli, mock_config):
        from inkscape_mcp.tools.fab_art_tools import inkscape_fab_art

        input_dir = fab_svg.parent
        out = tmp_path / "dxf"
        result = await inkscape_fab_art(
            "batch_dxf_export",
            input_dir=str(input_dir),
            output_dir=str(out),
            cli_wrapper=mock_cli,
            config=mock_config,
        )
        assert result["success"] is True
        assert result["data"]["count"] == 1


class TestExportDxf:
    @pytest.mark.asyncio
    async def test_export_dxf_vector_op(self, fab_svg: Path, tmp_path: Path, mock_cli, mock_config):
        from inkscape_mcp.tools.vector_operations import inkscape_vector

        dest = tmp_path / "part.dxf"
        result = await inkscape_vector(
            operation="export_dxf",
            input_path=str(fab_svg),
            output_path=str(dest),
            cli_wrapper=mock_cli,
            config=mock_config,
        )
        assert result["success"] is True
        assert "exported successfully" in result["message"]


class TestGazeboSchematic:
    @pytest.mark.asyncio
    async def test_gazebo_schematic(self, fab_svg: Path, tmp_path: Path, mock_cli, mock_config):
        from inkscape_mcp.tools.fab_art_tools import inkscape_fab_art

        png = tmp_path / "schematic.png"
        with patch(
            "inkscape_mcp.tools.fab_art_tools.inkscape_render",
            new=AsyncMock(return_value={"success": True, "data": {"output_path": str(png)}}),
        ):
            result = await inkscape_fab_art(
                "gazebo_schematic",
                svg_path=str(fab_svg),
                png_path=str(png),
                staging_dir=str(tmp_path / "stage"),
                cli_wrapper=mock_cli,
                config=mock_config,
            )
        assert result["success"] is True
        assert result["files"] == [str(png)]


class TestFleetE2eOffline:
    @pytest.mark.asyncio
    async def test_offline_smoke(self, tmp_path: Path):
        from inkscape_mcp.utils.fleet_e2e_offline import run_offline_smoke

        report = await run_offline_smoke(work_dir=tmp_path / "e2e")
        assert report["success"] is True
        assert report["mode"] == "offline"
        assert len(report["steps"]) >= 5
