"""Cross-fleet handoff helpers (gimp, blender, unity)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from ..tools.render_tools import inkscape_render
from ..tools.validation_tools import inkscape_validation
from ..tools.vector_operations import inkscape_vector
from .fleet_http import DEFAULT_BLENDER_URL
from .fleet_http import DEFAULT_GIMP_URL
from .fleet_http import DEFAULT_UNITY_URL
from .fleet_http import call_http_tool
from .fleet_http import check_http_health
from .fleet_staging import DEFAULT_BLENDER_DROP_DIR
from .fleet_staging import DEFAULT_UNITY_SPRITES_SUBDIR
from .fleet_staging import stage_file

logger = logging.getLogger(__name__)


async def export_png_preview(
    *,
    svg_path: str,
    output_path: str,
    dpi: int,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    return await inkscape_render(
        operation="export_preview",
        input_path=svg_path,
        output_path=output_path,
        dpi=dpi,
        cli_wrapper=cli_wrapper,
        config=config,
    )


async def push_raster_to_gimp(
    *,
    png_path: str,
    gimp_url: str | None = None,
    target_platform: str = "unity",
) -> dict[str, Any]:
    """Validate raster via gimp-mcp HTTP (texture QA after inkscape export)."""
    url = gimp_url or DEFAULT_GIMP_URL
    if not Path(png_path).is_file():
        return {"success": False, "error": f"PNG not found: {png_path}"}

    if not await check_http_health(url):
        return {
            "success": False,
            "error": f"gimp-mcp not reachable at {url}",
            "hint": "Start gimp-mcp webapp or pass reachable gimp_url",
        }

    result = await call_http_tool(
        url,
        "gimp_validation_tool",
        {
            "operation": "audit_texture",
            "input_path": png_path,
            "target_platform": target_platform,
        },
    )
    passed = bool(result.get("success")) and not result.get("issues")
    if "passed" in result.get("data", {}):
        passed = bool(result["data"]["passed"])
    return {
        "success": passed,
        "png_path": png_path,
        "gimp_url": url,
        "gimp_response": result,
        "error": None if passed else result.get("error") or "GIMP validation failed",
    }


async def stage_svg_for_blender(
    *,
    svg_path: str,
    drop_dir: Path | None = None,
    blender_url: str | None = None,
    import_to_blender: bool = False,
) -> dict[str, Any]:
    """Copy SVG to blender drop folder; optionally call blender_import over HTTP."""
    drop = drop_dir or DEFAULT_BLENDER_DROP_DIR
    staged = await stage_file(source_path=svg_path, staging_dir=drop.parent, subdir=drop.name)
    if not staged.get("success"):
        return staged

    payload: dict[str, Any] = {
        "success": True,
        "svg_path": svg_path,
        "staged_path": staged["staged_path"],
        "blender_drop_dir": str(drop),
        "import_to_blender": import_to_blender,
    }

    if not import_to_blender:
        return payload

    burl = blender_url or DEFAULT_BLENDER_URL
    if not await check_http_health(burl, health_path="/api/v1/health"):
        if not await check_http_health(burl, health_path="/health"):
            payload["success"] = False
            payload["error"] = f"blender-mcp not reachable at {burl}"
            return payload

    import_result = await call_http_tool(
        burl,
        "blender_import",
        {
            "operation": "import_svg",
            "filepath": staged["staged_path"],
            "file_format": "SVG",
        },
    )
    ok = bool(import_result.get("success", True))
    payload["blender_import"] = import_result
    payload["success"] = ok
    if not ok:
        payload["error"] = import_result.get("error") or "Blender SVG import failed"
    return payload


async def push_sprite_to_unity(
    *,
    png_path: str,
    project_path: str,
    unity_url: str | None = None,
    assets_subdir: str = DEFAULT_UNITY_SPRITES_SUBDIR,
    texture_type: str = "sprite",
) -> dict[str, Any]:
    """Copy PNG into Unity Assets and notify unity3d-mcp import_texture."""
    src = Path(png_path)
    if not src.is_file():
        return {"success": False, "error": f"Sprite PNG not found: {png_path}"}

    project = Path(project_path)
    if not project.is_dir():
        return {"success": False, "error": f"Unity project not found: {project_path}"}

    dest_dir = project / "Assets" / assets_subdir
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
    except OSError as exc:
        logger.exception("Unity sprite copy failed")
        return {"success": False, "error": str(exc)}

    uurl = unity_url or DEFAULT_UNITY_URL
    if not await check_http_health(uurl, health_path="/api/v1/health"):
        return {
            "success": dest.is_file(),
            "source_path": str(src),
            "destination_path": str(dest),
            "project_path": project_path,
            "warning": f"unity3d-mcp not reachable at {uurl}; file copied only",
        }

    unity_result = await call_http_tool(
        uurl,
        "import_texture",
        {
            "texture_path": str(dest),
            "project_path": project_path,
            "texture_type": texture_type,
        },
    )
    success = dest.is_file() and unity_result.get("success", True)
    return {
        "success": success,
        "source_path": str(src),
        "destination_path": str(dest),
        "project_path": project_path,
        "texture_type": texture_type,
        "unity_response": unity_result,
        "error": None if success else unity_result.get("error") or "Unity sprite handoff failed",
    }


async def build_layer_atlas(
    *,
    svg_path: str,
    output_dir: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Export SVG layers as separate PNG/SVG files for UI sprite atlases."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return await inkscape_vector(
        operation="layers_to_files",
        input_path=svg_path,
        output_path=str(out),
        cli_wrapper=cli_wrapper,
        config=config,
    )


async def validate_svg_for_handoff(
    svg_path: str,
    *,
    cli_wrapper: Any = None,
    config: Any = None,
) -> dict[str, Any]:
    return await inkscape_validation(
        operation="audit_web_svg",
        input_path=svg_path,
        cli_wrapper=cli_wrapper,
        config=config,
    )
