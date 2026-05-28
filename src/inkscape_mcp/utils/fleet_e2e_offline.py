"""In-process Phase 5 fleet smoke (no live HTTP services required)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch


async def run_offline_smoke(*, work_dir: Path) -> dict[str, object]:
    """Run fab art, fleet staging, and robotics-bridge surface checks locally."""
    from inkscape_mcp.tools.fab_art_tools import inkscape_fab_art

    steps: list[dict[str, object]] = []
    fab_in = work_dir / "fab_in"
    fab_out = work_dir / "fab_out"
    fab_in.mkdir(parents=True, exist_ok=True)
    fab_out.mkdir(parents=True, exist_ok=True)

    sample_svg = fab_in / "bracket_cut.svg"
    sample_svg.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80" fill="none" stroke="#000"/>
</svg>""",
        encoding="utf-8",
    )

    mock_wrapper = AsyncMock()
    mock_wrapper._execute_actions = AsyncMock(return_value=(0, "ok", ""))
    mock_wrapper._execute_command = AsyncMock(return_value="Inkscape 1.3")

    class _Cfg:
        process_timeout = 30
        inkscape_executable = "mock_inkscape"
        temp_directory = str(work_dir)

    presets = await inkscape_fab_art("list_presets")
    steps.append({"name": "offline_list_presets", "success": bool(presets.get("success")), "detail": presets})

    laser = await inkscape_fab_art(
        "batch_laser_dots",
        output_dir=str(fab_out / "laser"),
        laser_preset_id="presentation_single",
        cli_wrapper=mock_wrapper,
        config=_Cfg(),
    )
    steps.append({"name": "offline_batch_laser_dots", "success": bool(laser.get("success")), "detail": laser})

    dxf = await inkscape_fab_art(
        "batch_dxf_export",
        input_dir=str(fab_in),
        output_dir=str(fab_out / "dxf"),
        cli_wrapper=mock_wrapper,
        config=_Cfg(),
    )
    dxf_dir = fab_out / "dxf"
    dxf_dir.mkdir(parents=True, exist_ok=True)
    (dxf_dir / "bracket_cut.dxf").write_text("mock dxf", encoding="utf-8")
    steps.append({"name": "offline_batch_dxf_export", "success": bool(dxf.get("success")), "detail": dxf})

    schematic_png = fab_out / "schematic.png"
    schematic_png.write_bytes(b"\x89PNG\r\n\x1a\n")
    with patch(
        "inkscape_mcp.tools.fab_art_tools.inkscape_render",
        new=AsyncMock(
            return_value={
                "success": True,
                "data": {"output_path": str(schematic_png), "dpi": 192},
            }
        ),
    ), patch(
        "inkscape_mcp.tools.fab_art_tools.check_http_health",
        new=AsyncMock(return_value=False),
    ):
        schematic = await inkscape_fab_art(
            "gazebo_schematic",
            svg_path=str(sample_svg),
            png_path=str(schematic_png),
            staging_dir=str(work_dir / "stage"),
            cli_wrapper=mock_wrapper,
            config=_Cfg(),
        )
    steps.append({"name": "offline_gazebo_schematic", "success": bool(schematic.get("success")), "detail": schematic})

    with patch(
        "inkscape_mcp.tools.fab_art_tools.check_http_health",
        new=AsyncMock(return_value=False),
    ):
        staged = await inkscape_fab_art(
            "stage_for_robotics",
            input_dir=str(fab_out / "dxf"),
            staging_dir=str(work_dir / "stage"),
            cli_wrapper=mock_wrapper,
            config=_Cfg(),
        )
    steps.append({"name": "offline_stage_for_robotics", "success": bool(staged.get("success")), "detail": staged})

    return {
        "success": all(bool(s.get("success")) for s in steps),
        "mode": "offline",
        "steps": steps,
    }
