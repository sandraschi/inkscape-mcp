"""Shared SVG pack audit helpers for validation and sim-art tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .svg_pack_presets import detect_svg_icons
from .svg_pack_presets import validate_svg_pack_layout


async def audit_svg_pack_directory(input_dir: Path) -> dict[str, Any]:
    """Audit all SVG icons in a directory for fleet handoff readiness."""
    from ..tools.validation_tools import inkscape_validation

    icons = detect_svg_icons(input_dir)
    layout_issues = validate_svg_pack_layout(icons)
    per_file: list[dict[str, Any]] = []
    for _stem, path in icons.items():
        audit = await inkscape_validation("audit_web_svg", str(path))
        passed = bool(audit.get("success"))
        issues = list(audit.get("issues") or [])
        if not passed and not issues:
            issues = [str(audit.get("message") or audit.get("error") or "validation failed")]
        per_file.append(
            {
                "path": str(path),
                "passed": passed,
                "issues": issues,
            }
        )
    file_issues = [f"{entry['path']}: {issue}" for entry in per_file for issue in entry["issues"]]
    all_issues = layout_issues + file_issues
    passed = len(all_issues) == 0 and all(entry["passed"] for entry in per_file)
    return {
        "success": True,
        "passed": passed,
        "icon_count": len(icons),
        "layout_issues": layout_issues,
        "files": per_file,
        "issues": all_issues,
    }
