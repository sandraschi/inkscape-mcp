"""MCP-exposed Literal aliases for portmanteau `operation` params (ToolBench / fleet typing).

Keep in sync with `tools/file_operations.py`, `vector_operations.py`, `analysis.py`, `system.py`.
"""

from __future__ import annotations

from typing import Literal

InkscapeFileOperation = Literal[
    "load",
    "save",
    "convert",
    "info",
    "validate",
    "list_formats",
]

InkscapeVectorOperation = Literal[
    "trace_image",
    "generate_barcode_qr",
    "create_mesh_gradient",
    "text_to_path",
    "construct_svg",
    "apply_boolean",
    "path_inset_outset",
    "path_simplify",
    "path_clean",
    "path_combine",
    "path_break_apart",
    "object_to_path",
    "optimize_svg",
    "scour_svg",
    "measure_object",
    "query_document",
    "count_nodes",
    "export_dxf",
    "layers_to_files",
    "fit_canvas_to_drawing",
    "render_preview",
    "generate_laser_dot",
    "object_raise",
    "object_lower",
    "set_document_units",
]

InkscapeAnalysisOperation = Literal[
    "quality",
    "statistics",
    "validate",
    "objects",
    "dimensions",
    "structure",
]

InkscapeSystemOperation = Literal[
    "status",
    "help",
    "diagnostics",
    "version",
    "config",
    "execution_mode",
    "list_extensions",
    "execute_extension",
]

InkscapeRenderOperation = Literal[
    "export_preview",
    "export_multi_dpi",
    "get_document_summary",
]

InkscapeValidationOperation = Literal[
    "validate_svg",
    "check_viewbox",
    "check_stroke_fill",
    "check_size_limits",
    "audit_web_svg",
]

InkscapeFleetOperation = Literal[
    "push_gimp_raster",
    "stage_blender_svg",
    "push_unity_sprite",
    "build_layer_atlas",
    "run_pipeline",
    "list_staging",
]

InkscapeFabArtOperation = Literal[
    "list_presets",
    "batch_dxf_export",
    "batch_laser_dots",
    "gazebo_schematic",
    "stage_for_robotics",
    "run_fab_pipeline",
]
