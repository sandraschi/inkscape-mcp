"""Filesystem staging helpers for inkscape fleet handoff."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_STAGING_DIR = Path("D:/Temp/fleet_pipeline/inkscape_staging")
DEFAULT_BLENDER_DROP_DIR = Path("D:/Temp/fleet_pipeline/inkscape_staging/blender_drop")
DEFAULT_UNITY_SPRITES_SUBDIR = "InkscapeSprites"


def list_staging_files(staging_dir: Path, *, subdir: str = "") -> dict[str, Any]:
    root = staging_dir / subdir if subdir else staging_dir
    if not root.is_dir():
        return {"success": True, "files": [], "staging_dir": str(staging_dir)}
    files = sorted(str(p) for p in root.rglob("*") if p.is_file())
    return {"success": True, "files": files, "staging_dir": str(staging_dir), "scan_root": str(root)}


async def stage_file(
    *,
    source_path: str,
    staging_dir: Path,
    subdir: str = "incoming",
) -> dict[str, Any]:
    src = Path(source_path)
    if not src.is_file():
        return {"success": False, "error": f"Source not found: {source_path}"}

    dest_dir = staging_dir / subdir
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
    except OSError as exc:
        logger.exception("Staging copy failed for %s", source_path)
        return {"success": False, "error": str(exc)}

    return {
        "success": True,
        "source_path": str(src.resolve()),
        "staged_path": str(dest.resolve()),
        "staging_dir": str(staging_dir),
    }
