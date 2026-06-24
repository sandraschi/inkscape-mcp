"""Fab art presets for laser paths, DXF export, and Gazebo schematics."""

from __future__ import annotations

from typing import Any
from typing import TypedDict


class LaserPreset(TypedDict):
    id: str
    label: str
    width: int
    height: int
    dots: list[dict[str, float]]


class SchematicPreset(TypedDict):
    id: str
    label: str
    dpi: int
    target: str


LASER_DOT_PRESETS: dict[str, LaserPreset] = {
    "presentation_single": {
        "id": "presentation_single",
        "label": "Single presentation laser dot",
        "width": 800,
        "height": 600,
        "dots": [{"x": 400.0, "y": 300.0}],
    },
    "fab_calibration_grid": {
        "id": "fab_calibration_grid",
        "label": "2x2 fab calibration grid",
        "width": 800,
        "height": 600,
        "dots": [
            {"x": 200.0, "y": 150.0},
            {"x": 600.0, "y": 150.0},
            {"x": 200.0, "y": 450.0},
            {"x": 600.0, "y": 450.0},
        ],
    },
    "robotics_marker_triplet": {
        "id": "robotics_marker_triplet",
        "label": "Three robotics alignment markers",
        "width": 1024,
        "height": 768,
        "dots": [
            {"x": 128.0, "y": 384.0},
            {"x": 512.0, "y": 128.0},
            {"x": 896.0, "y": 384.0},
        ],
    },
}

SCHEMATIC_PRESETS: dict[str, SchematicPreset] = {
    "gazebo_model_doc_192": {
        "id": "gazebo_model_doc_192",
        "label": "Gazebo model documentation PNG",
        "dpi": 192,
        "target": "gazebo",
    },
    "gazebo_model_doc_384": {
        "id": "gazebo_model_doc_384",
        "label": "High-res Gazebo schematic",
        "dpi": 384,
        "target": "gazebo",
    },
    "robotics_fab_sheet_256": {
        "id": "robotics_fab_sheet_256",
        "label": "Robotics fab reference sheet",
        "dpi": 256,
        "target": "robotics",
    },
}

DEFAULT_FAB_STAGING = "D:/Temp/fleet_pipeline/inkscape_fab_art"
DEFAULT_ROBOTICS_URL = "http://127.0.0.1:10821"


def list_fab_presets() -> dict[str, Any]:
    return {
        "laser_dot_presets": [
            {**preset, "dot_count": len(preset["dots"])} for preset in LASER_DOT_PRESETS.values()
        ],
        "schematic_presets": list(SCHEMATIC_PRESETS.values()),
        "default_staging": DEFAULT_FAB_STAGING,
        "robotics_url": DEFAULT_ROBOTICS_URL,
        "naming_hint": "SVG inputs: part_cut.svg, bracket.svg; DXF outputs: part_cut.dxf",
    }


def resolve_laser_preset(preset_id: str) -> LaserPreset | None:
    return LASER_DOT_PRESETS.get(preset_id)


def resolve_schematic_preset(preset_id: str) -> SchematicPreset | None:
    return SCHEMATIC_PRESETS.get(preset_id)
