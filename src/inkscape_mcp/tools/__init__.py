"""
Inkscape MCP Tools - FastMCP 2.13+ Portmanteau Architecture.

Consolidated tools for vector graphics operations with reduced cognitive load and better discoverability.

Instead of 50+ individual tools, Inkscape MCP consolidates related operations into 8
master tools. Each tool handles a specific domain with multiple operations.

TOOLS:
- inkscape_file: File operations (load, save, convert, info)
- : Object management (create, group, align, transform)
- inkscape_path: Path operations (edit, boolean, stroke/fill)
- inkscape_text: Text handling (create, edit, style, convert to path)
- inkscape_transform: Geometric transforms (scale, rotate, translate)
- inkscape_export: Export operations (PNG, PDF, EPS, SVG variants)
- inkscape_analysis: Document analysis (quality, statistics, validation)
- inkscape_system: System operations (status, help, diagnostics)
"""

from .file_operations import inkscape_file
from .vector_operations import inkscape_vector
from .analysis import inkscape_analysis
from .system import inkscape_system
from .transform import inkscape_transform
from .color import inkscape_color
from .filter import inkscape_filter
from .layer import inkscape_layer
from .batch import inkscape_batch

__all__ = [
    "inkscape_file",
    "inkscape_vector",
    "inkscape_analysis",
    "inkscape_system",
    "inkscape_transform",
    "inkscape_color",
    "inkscape_filter",
    "inkscape_layer",
    "inkscape_batch",
]

# Tool metadata for discovery
PORTMANTEAU_TOOLS = [
    {
        "name": "inkscape_file",
        "function": inkscape_file,
        "category": "file_operations",
        "operations": ["load", "save", "convert", "info", "validate", "list_formats"],
    },
    {
        "name": "inkscape_vector",
        "function": inkscape_vector,
        "category": "vector_operations",
        "operations": [
            "trace_image",
            "apply_boolean",
            "optimize_svg",
            "render_preview",
        ],
    },
    {
        "name": "inkscape_analysis",
        "function": inkscape_analysis,
        "category": "document_analysis",
        "operations": [
            "quality",
            "statistics",
            "validate",
            "objects",
            "dimensions",
            "structure",
        ],
    },
    {
        "name": "inkscape_system",
        "function": inkscape_system,
        "category": "system",
        "operations": [
            "status",
            "help",
            "diagnostics",
            "version",
            "config",
        ],
    },
    {
        "name": "inkscape_transform",
        "function": inkscape_transform,
        "category": "transforms",
        "operations": [
            "scale",
            "rotate",
            "translate",
            "skew",
            "matrix",
            "reset",
        ],
    },
    {
        "name": "inkscape_color",
        "function": inkscape_color,
        "category": "color_adjustments",
        "operations": [
            "brightness",
            "contrast",
            "hue",
            "saturation",
            "levels",
            "curves",
            "hsl",
        ],
    },
    {
        "name": "inkscape_filter",
        "function": inkscape_filter,
        "category": "filters",
        "operations": [
            "blur",
            "sharpen",
            "noise",
            "artistic",
            "distort",
            "lighting",
        ],
    },
    {
        "name": "inkscape_layer",
        "function": inkscape_layer,
        "category": "layer_management",
        "operations": [
            "create",
            "delete",
            "duplicate",
            "merge",
            "flatten",
            "reorder",
        ],
    },
    {
        "name": "inkscape_batch",
        "function": inkscape_batch,
        "category": "batch_processing",
        "operations": [
            "resize",
            "convert",
            "watermark",
            "optimize",
            "rename",
            "process",
        ],
    },
]


def get_all_tools():
    """Return all portmanteau tool functions for registration."""
    return [tool["function"] for tool in PORTMANTEAU_TOOLS]


def get_tool_metadata():
    """Return metadata for all portmanteau tools."""
    return PORTMANTEAU_TOOLS
