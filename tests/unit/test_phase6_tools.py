"""Tests for Agent Lab Phase 6 SVG icon packs, icon sheets, and AI refine loop."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def icon_sources(tmp_path: Path) -> Path:
    folder = tmp_path / "icons_in"
    folder.mkdir()
    for idx, color in enumerate(["#ff0000", "#00ff00", "#0000ff"], start=1):
        (folder / f"icon_{idx}.svg").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="8" y="8" width="48" height="48" fill="{color}" stroke="#000"/>
</svg>""",
            encoding="utf-8",
        )
    return folder


class TestSvgPackPresets:
    def test_detect_svg_icons(self, icon_sources: Path):
        from inkscape_mcp.utils.svg_pack_presets import detect_svg_icons, list_svg_pack_presets

        icons = detect_svg_icons(icon_sources)
        assert len(icons) == 3
        catalog = list_svg_pack_presets()
        assert "ui_icon_128" in {t["id"] for t in catalog["icon_templates"]}


class TestSvgPackBatch:
    @pytest.mark.asyncio
    async def test_svg_pack_batch(self, icon_sources: Path, tmp_path: Path):
        from inkscape_mcp.tools.sim_art_tools import inkscape_sim_art

        out = tmp_path / "pack_out"
        result = await inkscape_sim_art(
            "svg_pack_batch",
            input_dir=str(icon_sources),
            output_dir=str(out),
            template_id="ui_icon_128",
            validate=True,
        )
        assert result["success"] is True
        assert len(result["files"]) == 3
        assert (out / "icon_1_ui_icon_128.svg").is_file()


class TestIconSheet:
    @pytest.mark.asyncio
    async def test_build_icon_sheet_margin_bleed(self, icon_sources: Path, tmp_path: Path):
        from inkscape_mcp.tools.sim_art_tools import inkscape_sim_art

        sheet_path = tmp_path / "icons.svg"
        result = await inkscape_sim_art(
            "build_icon_sheet",
            input_dir=str(icon_sources),
            output_path=str(sheet_path),
            layout="2x2",
            cell_size=64,
            margin_px=4,
            bleed_px=2,
        )
        assert result["success"] is True
        assert result["data"]["margin_px"] == 4
        assert result["data"]["bleed_px"] == 2
        manifest = sheet_path.with_suffix(".manifest.json")
        assert manifest.is_file()
        assert sheet_path.is_file()


class TestSvgPackAudit:
    @pytest.mark.asyncio
    async def test_audit_svg_pack(self, icon_sources: Path):
        from inkscape_mcp.tools.validation_tools import inkscape_validation

        audit = await inkscape_validation("audit_svg_pack", str(icon_sources))
        assert audit["success"] is True
        assert audit["data"]["passed"] is True


class TestAiSvgRefineLoop:
    @pytest.mark.asyncio
    async def test_ai_svg_refine_loop(self, icon_sources: Path):
        from inkscape_mcp.tools.sim_art_tools import inkscape_sim_art

        result = await inkscape_sim_art(
            "ai_svg_refine_loop",
            input_dir=str(icon_sources),
            goal="Fleet UI icon QA",
        )
        assert result["success"] is True
        assert "ai_handoff" in result["data"]
        assert result["data"]["ai_handoff"]["refine_loop"]


class TestFleetE2eOffline:
    @pytest.mark.asyncio
    async def test_offline_smoke(self, tmp_path: Path):
        from inkscape_mcp.utils.fleet_e2e_offline import run_offline_smoke

        report = await run_offline_smoke(work_dir=tmp_path / "e2e")
        assert report["success"] is True
        assert report["mode"] == "offline"
        assert len(report["steps"]) >= 10
