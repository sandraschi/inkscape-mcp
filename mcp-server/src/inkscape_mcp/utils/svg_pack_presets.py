"""SVG icon pack presets and layout catalog for fleet UI pipelines."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from typing import TypedDict


class SvgIconTemplate(TypedDict):
    id: str
    label: str
    width: int
    height: int
    view_box: str
    target: str


class AtlasLayout(TypedDict):
    id: str
    label: str
    columns: int
    rows: int


SVG_ICON_TEMPLATES: tuple[SvgIconTemplate, ...] = (
    {
        "id": "ui_icon_64",
        "label": "Unity UI icon 64px",
        "width": 64,
        "height": 64,
        "view_box": "0 0 64 64",
        "target": "unity",
    },
    {
        "id": "ui_icon_128",
        "label": "Unity UI icon 128px",
        "width": 128,
        "height": 128,
        "view_box": "0 0 128 128",
        "target": "unity",
    },
    {
        "id": "vrchat_badge_256",
        "label": "VRChat badge 256px",
        "width": 256,
        "height": 256,
        "view_box": "0 0 256 256",
        "target": "vrchat",
    },
    {
        "id": "resonite_panel_512",
        "label": "Resonite UI panel tile 512px",
        "width": 512,
        "height": 512,
        "view_box": "0 0 512 512",
        "target": "resonite",
    },
)

ATLAS_LAYOUTS: dict[str, tuple[int, int]] = {
    "2x2": (2, 2),
    "3x3": (3, 3),
    "4x4": (4, 4),
    "4x2": (4, 2),
}

DEFAULT_SIM_STAGING = "D:/Temp/fleet_pipeline/inkscape_sim_art"

_SVG_SUFFIX = ".svg"


def list_svg_pack_presets() -> dict[str, Any]:
    """Return icon templates and atlas layouts for agents."""
    return {
        "icon_templates": list(SVG_ICON_TEMPLATES),
        "atlas_layouts": [
            {"id": key, "label": key.replace("x", " x "), "columns": cols, "rows": rows}
            for key, (cols, rows) in ATLAS_LAYOUTS.items()
        ],
        "default_staging": DEFAULT_SIM_STAGING,
        "naming_hint": "Inputs: icon_home.svg, badge_crew.svg; outputs: icon_home_ui_icon_128.svg",
    }


def resolve_icon_template(template_id: str) -> SvgIconTemplate | None:
    for template in SVG_ICON_TEMPLATES:
        if template["id"] == template_id:
            return template
    return None


def _stem_tokens(stem: str) -> list[str]:
    return [part.lower() for part in re.split(r"[_\-.]+", stem) if part]


def detect_svg_icons(input_dir: Path) -> dict[str, Path]:
    """Detect SVG icon files in a directory (flat scan)."""
    found: dict[str, Path] = {}
    if not input_dir.is_dir():
        return found
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() != _SVG_SUFFIX:
            continue
        found[path.stem] = path.resolve()
    return found


def validate_svg_pack_layout(
    icons: dict[str, Path],
    *,
    min_count: int = 1,
    max_count: int = 64,
) -> list[str]:
    """Return layout issues for an SVG icon pack directory."""
    issues: list[str] = []
    count = len(icons)
    if count < min_count:
        issues.append(f"Expected at least {min_count} SVG icon(s), found {count}")
    if count > max_count:
        issues.append(f"Pack exceeds max icon count {max_count} ({count} found)")
    seen_stems: set[str] = set()
    for stem in icons:
        lowered = stem.lower()
        if lowered in seen_stems:
            issues.append(f"Duplicate icon stem (case-insensitive): {stem}")
        seen_stems.add(lowered)
    return issues
