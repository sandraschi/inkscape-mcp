"""Robotics and fab art portmanteau (DXF, laser paths, Gazebo schematics)."""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from ..utils.fab_art_presets import DEFAULT_FAB_STAGING
from ..utils.fab_art_presets import DEFAULT_ROBOTICS_URL
from ..utils.fab_art_presets import list_fab_presets
from ..utils.fab_art_presets import resolve_laser_preset
from ..utils.fab_art_presets import resolve_schematic_preset
from ..utils.fleet_handoff import push_raster_to_gimp
from ..utils.fleet_http import check_http_health
from ..utils.fleet_staging import stage_file
from .render_tools import inkscape_render
from .vector_operations import inkscape_vector

logger = logging.getLogger(__name__)

FabArtOperation = Literal[
    "list_presets",
    "batch_dxf_export",
    "batch_laser_dots",
    "gazebo_schematic",
    "stage_for_robotics",
    "run_fab_pipeline",
]


class FabArtResult(BaseModel):
    success: bool
    operation: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    files: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    error: str = ""


def _iter_svgs(input_dir: Path) -> list[Path]:
    return sorted({p.resolve() for p in input_dir.rglob("*.svg") if p.is_file()})


async def _batch_dxf_export(
    *,
    input_dir: Path,
    output_dir: Path,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    sources = _iter_svgs(input_dir)
    if not sources:
        return {"success": False, "error": f"No SVG files in {input_dir}"}

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, str]] = []
    failed = 0

    for src in sources:
        dest = output_dir / f"{src.stem}.dxf"
        export = await inkscape_vector(
            operation="export_dxf",
            input_path=str(src),
            output_path=str(dest),
            cli_wrapper=cli_wrapper,
            config=config,
        )
        if export.get("success"):
            results.append({"source": str(src), "output": str(dest), "status": "success"})
        else:
            failed += 1
            results.append(
                {
                    "source": str(src),
                    "status": "failed",
                    "error": export.get("error") or export.get("message", ""),
                }
            )

    return {
        "success": failed == 0,
        "count": len(results),
        "failed": failed,
        "output_dir": str(output_dir),
        "results": results,
    }


async def _batch_laser_dots(
    *,
    output_dir: Path,
    preset_id: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    preset = resolve_laser_preset(preset_id)
    if preset is None:
        return {"success": False, "error": f"Unknown laser preset: {preset_id}"}

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []
    failures: list[dict[str, str]] = []

    for index, dot in enumerate(preset["dots"], start=1):
        dest = output_dir / f"{preset_id}_{index:02d}.svg"
        result = await inkscape_vector(
            operation="generate_laser_dot",
            output_path=str(dest),
            cli_wrapper=cli_wrapper,
            config=config,
            x=dot["x"],
            y=dot["y"],
            preset_id=preset_id,
        )
        if result.get("success"):
            outputs.append(str(dest))
        else:
            failures.append({"index": str(index), "error": result.get("error", "failed")})

    return {
        "success": not failures,
        "preset_id": preset_id,
        "output_dir": str(output_dir),
        "files": outputs,
        "failures": failures,
    }


async def inkscape_fab_art(
    operation: FabArtOperation,
    *,
    input_dir: str = "",
    output_dir: str = "",
    svg_path: str = "",
    png_path: str = "",
    preset_id: str = "gazebo_model_doc_192",
    laser_preset_id: str = "fab_calibration_grid",
    staging_dir: str = "",
    robotics_url: str = "",
    gimp_url: str = "",
    dpi: int = 0,
    push_gimp: bool = False,
    cli_wrapper: Any = None,
    config: Any = None,
) -> dict[str, Any]:
    """Robotics fab art: DXF batch, laser dots, Gazebo schematics, robotics staging."""
    start = time.time()
    stage = Path(staging_dir) if staging_dir else Path(DEFAULT_FAB_STAGING)
    r_url = robotics_url or DEFAULT_ROBOTICS_URL

    try:
        if operation == "list_presets":
            payload = list_fab_presets()
            return FabArtResult(
                success=True,
                operation=operation,
                message="Fab art preset catalog",
                data=payload,
            ).model_dump()

        if operation == "batch_dxf_export":
            if not input_dir:
                return FabArtResult(
                    success=False,
                    operation=operation,
                    message="input_dir required",
                    error="input_dir required",
                ).model_dump()
            out = Path(output_dir) if output_dir else stage / "dxf"
            batch = await _batch_dxf_export(
                input_dir=Path(input_dir),
                output_dir=out,
                cli_wrapper=cli_wrapper,
                config=config,
            )
            files = [
                row["output"]
                for row in batch.get("results", [])
                if row.get("status") == "success" and row.get("output")
            ]
            return FabArtResult(
                success=bool(batch.get("success")),
                operation=operation,
                message=f"DXF batch: {batch.get('count', 0) - batch.get('failed', 0)}/{batch.get('count', 0)}",
                data=batch,
                files=files,
                error=batch.get("error") or "",
            ).model_dump()

        if operation == "batch_laser_dots":
            out = Path(output_dir) if output_dir else stage / "laser_dots"
            batch = await _batch_laser_dots(
                output_dir=out,
                preset_id=laser_preset_id,
                cli_wrapper=cli_wrapper,
                config=config,
            )
            return FabArtResult(
                success=bool(batch.get("success")),
                operation=operation,
                message=f"Laser dots preset={laser_preset_id}: {len(batch.get('files', []))} file(s)",
                data=batch,
                files=list(batch.get("files") or []),
                error="" if batch.get("success") else str(batch.get("failures") or ""),
            ).model_dump()

        if operation == "gazebo_schematic":
            if not svg_path:
                return FabArtResult(
                    success=False,
                    operation=operation,
                    message="svg_path required",
                    error="svg_path required",
                ).model_dump()
            schematic = resolve_schematic_preset(preset_id) or resolve_schematic_preset("gazebo_model_doc_192")
            use_dpi = dpi or (schematic["dpi"] if schematic else 192)
            png_out = png_path or str(stage / "schematics" / f"{Path(svg_path).stem}_{use_dpi}dpi.png")
            Path(png_out).parent.mkdir(parents=True, exist_ok=True)

            render = await inkscape_render(
                operation="export_preview",
                input_path=svg_path,
                output_path=png_out,
                dpi=use_dpi,
                cli_wrapper=cli_wrapper,
                config=config,
            )
            if not render.get("success"):
                return FabArtResult(
                    success=False,
                    operation=operation,
                    message="Schematic PNG export failed",
                    data=render,
                    error=render.get("error", "RenderError"),
                ).model_dump()

            staged = await stage_file(source_path=png_out, staging_dir=stage, subdir="gazebo_schematics")
            gimp_result = None
            if push_gimp:
                gimp_result = await push_raster_to_gimp(
                    png_path=png_out,
                    gimp_url=gimp_url or None,
                    target_platform="gazebo",
                )

            data = {
                "svg_path": svg_path,
                "png_path": png_out,
                "dpi": use_dpi,
                "preset_id": preset_id,
                "staged": staged,
                "gimp_handoff": gimp_result,
            }
            return FabArtResult(
                success=True,
                operation=operation,
                message=f"Gazebo schematic exported at {use_dpi} DPI",
                data=data,
                files=[png_out],
            ).model_dump()

        if operation == "stage_for_robotics":
            src_dir = Path(input_dir) if input_dir else stage / "dxf"
            if svg_path and Path(svg_path).is_file():
                staged = await stage_file(source_path=svg_path, staging_dir=stage, subdir="robotics_staging")
                files = [staged.get("staged_path", "")]
            elif src_dir.is_dir():
                dest = stage / "robotics_staging"
                dest.mkdir(parents=True, exist_ok=True)
                copied: list[str] = []
                for pattern in ("*.dxf", "*.svg", "*.png"):
                    for src in src_dir.glob(pattern):
                        target = dest / src.name
                        shutil.copy2(src, target)
                        copied.append(str(target))
                staged = {"success": bool(copied), "files": copied, "staging_dir": str(dest)}
                files = copied
            else:
                return FabArtResult(
                    success=False,
                    operation=operation,
                    message="Provide input_dir with fab outputs or svg_path",
                    error="ValueError",
                ).model_dump()

            robotics_online = await check_http_health(r_url, health_path="/api/v1/health")
            if not robotics_online:
                robotics_online = await check_http_health(r_url, health_path="/health")

            return FabArtResult(
                success=bool(staged.get("success", True)),
                operation=operation,
                message="Staged fab art for robotics-mcp",
                data={
                    "staging": staged,
                    "robotics_url": r_url,
                    "robotics_reachable": robotics_online,
                },
                files=[f for f in files if f],
            ).model_dump()

        if operation == "run_fab_pipeline":
            if not svg_path:
                return FabArtResult(
                    success=False,
                    operation=operation,
                    message="svg_path required",
                    error="svg_path required",
                ).model_dump()
            work = stage / Path(svg_path).stem
            work.mkdir(parents=True, exist_ok=True)
            svg_copy = work / Path(svg_path).name
            if not svg_copy.exists():
                shutil.copy2(svg_path, svg_copy)

            dxf = await _batch_dxf_export(
                input_dir=work,
                output_dir=work / "dxf",
                cli_wrapper=cli_wrapper,
                config=config,
            )
            schematic = await inkscape_fab_art(
                "gazebo_schematic",
                svg_path=str(svg_copy),
                png_path=str(work / "schematics" / f"{svg_copy.stem}_schematic.png"),
                preset_id=preset_id,
                staging_dir=str(stage),
                push_gimp=push_gimp,
                gimp_url=gimp_url,
                cli_wrapper=cli_wrapper,
                config=config,
            )
            staged = await inkscape_fab_art(
                "stage_for_robotics",
                input_dir=str(work / "dxf"),
                staging_dir=str(stage),
                robotics_url=r_url,
                cli_wrapper=cli_wrapper,
                config=config,
            )
            success = bool(dxf.get("success")) and schematic.get("success") and staged.get("success")
            return FabArtResult(
                success=success,
                operation=operation,
                message="Fab pipeline complete" if success else "Fab pipeline partial failure",
                data={"dxf": dxf, "schematic": schematic.get("data"), "robotics_stage": staged.get("data")},
                files=(schematic.get("files") or []) + (staged.get("files") or []),
            ).model_dump()

        return FabArtResult(
            success=False,
            operation=operation,
            message=f"Unknown operation: {operation}",
            error="ValueError",
        ).model_dump()
    except Exception as exc:
        logger.exception("inkscape_fab_art failed operation=%s", operation)
        return FabArtResult(
            success=False,
            operation=operation,
            message=f"Fab art operation failed: {exc}",
            error=str(exc),
            execution_time_ms=(time.time() - start) * 1000,
        ).model_dump()
