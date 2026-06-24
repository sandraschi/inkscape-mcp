"""Fleet handoff portmanteau for inkscape-mcp Phase 3."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from ..utils.fleet_handoff import build_layer_atlas
from ..utils.fleet_handoff import push_raster_to_gimp
from ..utils.fleet_handoff import push_sprite_to_unity
from ..utils.fleet_handoff import stage_svg_for_blender
from ..utils.fleet_pipeline import list_pipeline_staging
from ..utils.fleet_pipeline import run_fleet_pipeline
from ..utils.fleet_staging import DEFAULT_STAGING_DIR

logger = logging.getLogger(__name__)

FleetOperation = Literal[
    "push_gimp_raster",
    "stage_blender_svg",
    "push_unity_sprite",
    "build_layer_atlas",
    "run_pipeline",
    "list_staging",
]


class FleetResult(BaseModel):
    success: bool
    operation: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: str = ""


async def inkscape_fleet(
    operation: FleetOperation,
    *,
    svg_path: str = "",
    png_path: str = "",
    project_path: str = "",
    output_dir: str = "",
    staging_dir: str = "",
    dpi: int = 192,
    gimp_url: str = "",
    blender_url: str = "",
    unity_url: str = "",
    import_to_blender: bool = False,
    skip_validate: bool = False,
    skip_gimp: bool = False,
    skip_blender_stage: bool = True,
    skip_unity: bool = False,
    target_platform: str = "unity",
    cli_wrapper: Any = None,
    config: Any = None,
) -> dict[str, Any]:
    """Cross-fleet handoff operations for inkscape-mcp."""
    start = time.time()
    stage = Path(staging_dir) if staging_dir else DEFAULT_STAGING_DIR

    try:
        if operation == "push_gimp_raster":
            if not png_path and not svg_path:
                return FleetResult(
                    success=False,
                    operation=operation,
                    message="Provide png_path or svg_path",
                    error="ValueError",
                ).model_dump()

            resolved_png = png_path
            if not resolved_png:
                from .render_tools import inkscape_render

                out = stage / "processed" / f"{Path(svg_path).stem}_{dpi}dpi.png"
                export = await inkscape_render(
                    operation="export_preview",
                    input_path=svg_path,
                    output_path=str(out),
                    dpi=dpi,
                    cli_wrapper=cli_wrapper,
                    config=config,
                )
                if not export.get("success"):
                    return FleetResult(
                        success=False,
                        operation=operation,
                        message="PNG export failed before GIMP handoff",
                        data=export,
                        error=export.get("error", "ExportError"),
                    ).model_dump()
                resolved_png = str(out)

            gimp_result = await push_raster_to_gimp(
                png_path=resolved_png,
                gimp_url=gimp_url or None,
                target_platform=target_platform,
            )
            return FleetResult(
                success=bool(gimp_result.get("success")),
                operation=operation,
                message="GIMP raster validation complete" if gimp_result.get("success") else "GIMP handoff failed",
                data=gimp_result,
                execution_time_ms=(time.time() - start) * 1000,
                error="" if gimp_result.get("success") else str(gimp_result.get("error", "")),
            ).model_dump()

        if operation == "stage_blender_svg":
            if not svg_path:
                return FleetResult(
                    success=False,
                    operation=operation,
                    message="svg_path is required",
                    error="ValueError",
                ).model_dump()
            result = await stage_svg_for_blender(
                svg_path=svg_path,
                blender_url=blender_url or None,
                import_to_blender=import_to_blender,
            )
            return FleetResult(
                success=bool(result.get("success")),
                operation=operation,
                message="Blender SVG staged" if result.get("success") else "Blender stage failed",
                data=result,
                execution_time_ms=(time.time() - start) * 1000,
                error="" if result.get("success") else str(result.get("error", "")),
            ).model_dump()

        if operation == "push_unity_sprite":
            if not png_path or not project_path:
                return FleetResult(
                    success=False,
                    operation=operation,
                    message="png_path and project_path are required",
                    error="ValueError",
                ).model_dump()
            result = await push_sprite_to_unity(
                png_path=png_path,
                project_path=project_path,
                unity_url=unity_url or None,
            )
            return FleetResult(
                success=bool(result.get("success")),
                operation=operation,
                message="Unity sprite pushed" if result.get("success") else "Unity handoff failed",
                data=result,
                execution_time_ms=(time.time() - start) * 1000,
                error="" if result.get("success") else str(result.get("error", "")),
            ).model_dump()

        if operation == "build_layer_atlas":
            if not svg_path or not output_dir:
                return FleetResult(
                    success=False,
                    operation=operation,
                    message="svg_path and output_dir are required",
                    error="ValueError",
                ).model_dump()
            result = await build_layer_atlas(
                svg_path=svg_path,
                output_dir=output_dir,
                cli_wrapper=cli_wrapper,
                config=config,
            )
            return FleetResult(
                success=bool(result.get("success")),
                operation=operation,
                message="Layer atlas export complete" if result.get("success") else "Atlas export failed",
                data=result if isinstance(result, dict) else {"result": result},
                execution_time_ms=(time.time() - start) * 1000,
                error="" if result.get("success") else str(result.get("error", "")),
            ).model_dump()

        if operation == "run_pipeline":
            if not svg_path or not project_path:
                return FleetResult(
                    success=False,
                    operation=operation,
                    message="svg_path and project_path are required",
                    error="ValueError",
                ).model_dump()
            report = await run_fleet_pipeline(
                svg_path=svg_path,
                project_path=project_path,
                png_path=png_path or None,
                staging_dir=stage,
                dpi=dpi,
                gimp_url=gimp_url or None,
                blender_url=blender_url or None,
                unity_url=unity_url or None,
                skip_validate=skip_validate,
                skip_gimp=skip_gimp,
                skip_blender_stage=skip_blender_stage,
                import_to_blender=import_to_blender,
                skip_unity=skip_unity,
                target_platform=target_platform,
                cli_wrapper=cli_wrapper,
                config=config,
            )
            return FleetResult(
                success=report.success,
                operation=operation,
                message="Fleet pipeline complete" if report.success else "Fleet pipeline failed",
                data=report.to_dict(),
                execution_time_ms=(time.time() - start) * 1000,
                error="" if report.success else "PipelineError",
            ).model_dump()

        if operation == "list_staging":
            listing = await list_pipeline_staging(stage)
            return FleetResult(
                success=True,
                operation=operation,
                message=f"Listed {len(listing.get('files', []))} staged file(s)",
                data=listing,
                execution_time_ms=(time.time() - start) * 1000,
            ).model_dump()

        return FleetResult(
            success=False,
            operation=operation,
            message=f"Unknown operation: {operation}",
            error="ValueError",
        ).model_dump()

    except Exception as exc:
        logger.exception("inkscape_fleet failed operation=%s", operation)
        return FleetResult(
            success=False,
            operation=operation,
            message=f"Fleet operation failed: {exc}",
            error=str(exc),
            execution_time_ms=(time.time() - start) * 1000,
        ).model_dump()
