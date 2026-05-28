"""Fleet E2E pipeline: inkscape SVG -> PNG -> gimp QA -> unity sprite."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from .fleet_handoff import export_png_preview
from .fleet_handoff import push_raster_to_gimp
from .fleet_handoff import push_sprite_to_unity
from .fleet_handoff import stage_svg_for_blender
from .fleet_handoff import validate_svg_for_handoff
from .fleet_http import DEFAULT_BLENDER_URL
from .fleet_http import DEFAULT_GIMP_URL
from .fleet_http import DEFAULT_UNITY_URL
from .fleet_http import check_http_health
from .fleet_staging import DEFAULT_STAGING_DIR
from .fleet_staging import list_staging_files
from .fleet_staging import stage_file

logger = logging.getLogger(__name__)


@dataclass
class PipelineStep:
    name: str
    success: bool
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineReport:
    success: bool
    steps: list[PipelineStep] = field(default_factory=list)
    svg_path: str | None = None
    png_path: str | None = None
    project_path: str | None = None
    staging_dir: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "svg_path": self.svg_path,
            "png_path": self.png_path,
            "project_path": self.project_path,
            "staging_dir": self.staging_dir,
            "steps": [{"name": s.name, "success": s.success, "detail": s.detail} for s in self.steps],
        }


async def run_fleet_pipeline(
    *,
    svg_path: str,
    project_path: str,
    png_path: str | None = None,
    staging_dir: Path | None = None,
    dpi: int = 192,
    gimp_url: str | None = None,
    blender_url: str | None = None,
    unity_url: str | None = None,
    skip_validate: bool = False,
    skip_gimp: bool = False,
    skip_blender_stage: bool = True,
    import_to_blender: bool = False,
    skip_unity: bool = False,
    target_platform: str = "unity",
    cli_wrapper: Any = None,
    config: Any = None,
) -> PipelineReport:
    """Run inkscape validate/export -> gimp QA -> optional blender stage -> unity sprite."""
    gurl = gimp_url or DEFAULT_GIMP_URL
    burl = blender_url or DEFAULT_BLENDER_URL
    uurl = unity_url or DEFAULT_UNITY_URL
    stage = staging_dir or DEFAULT_STAGING_DIR
    report = PipelineReport(success=False, project_path=project_path, svg_path=svg_path)
    report.staging_dir = str(stage)

    svg = Path(svg_path)
    if not svg.is_file():
        report.steps.append(PipelineStep("precheck", False, {"error": f"SVG not found: {svg_path}"}))
        return report

    project = Path(project_path)
    if not skip_unity and not project.is_dir():
        report.steps.append(
            PipelineStep("precheck", False, {"error": f"Unity project not found: {project_path}"})
        )
        return report

    staged = await stage_file(source_path=svg_path, staging_dir=stage, subdir="incoming")
    report.steps.append(PipelineStep("inkscape_staging", bool(staged.get("success")), staged))
    if not staged.get("success"):
        return report

    if not skip_validate:
        val = await validate_svg_for_handoff(svg_path, cli_wrapper=cli_wrapper, config=config)
        ok = bool(val.get("success"))
        report.steps.append(PipelineStep("inkscape_validate", ok, val))
        if not ok:
            return report

    resolved_png = Path(png_path) if png_path else stage / "processed" / f"{svg.stem}_{dpi}dpi.png"
    if not png_path or not resolved_png.is_file():
        export_result = await export_png_preview(
            svg_path=svg_path,
            output_path=str(resolved_png),
            dpi=dpi,
            cli_wrapper=cli_wrapper,
            config=config,
        )
        report.steps.append(PipelineStep("inkscape_export_png", bool(export_result.get("success")), export_result))
        if not export_result.get("success"):
            return report

    report.png_path = str(resolved_png)

    if not skip_gimp:
        if not await check_http_health(gurl):
            report.steps.append(
                PipelineStep(
                    "gimp_validate",
                    False,
                    {"error": f"gimp-mcp not reachable at {gurl}", "hint": "Use --skip-gimp to bypass"},
                )
            )
            return report
        gimp_result = await push_raster_to_gimp(
            png_path=str(resolved_png),
            gimp_url=gurl,
            target_platform=target_platform,
        )
        report.steps.append(PipelineStep("gimp_validate", bool(gimp_result.get("success")), gimp_result))
        if not gimp_result.get("success"):
            return report

    if not skip_blender_stage:
        blender_result = await stage_svg_for_blender(
            svg_path=svg_path,
            blender_url=burl,
            import_to_blender=import_to_blender,
        )
        report.steps.append(PipelineStep("blender_stage_svg", bool(blender_result.get("success")), blender_result))
        if not blender_result.get("success"):
            return report

    if skip_unity:
        report.success = all(s.success for s in report.steps)
        return report

    if not await check_http_health(uurl, health_path="/api/v1/health"):
        report.steps.append(
            PipelineStep(
                "unity_sprite_push",
                False,
                {"error": f"unity3d-mcp not reachable at {uurl}"},
            )
        )
        return report

    unity_result = await push_sprite_to_unity(
        png_path=str(resolved_png),
        project_path=project_path,
        unity_url=uurl,
    )
    report.steps.append(PipelineStep("unity_sprite_push", bool(unity_result.get("success")), unity_result))

    report.success = all(s.success for s in report.steps)
    return report


async def list_pipeline_staging(staging_dir: Path | None = None) -> dict[str, Any]:
    return list_staging_files(staging_dir or DEFAULT_STAGING_DIR)
