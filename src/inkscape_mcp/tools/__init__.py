"""
GIMP MCP Tools - FastMCP 2.13+ Portmanteau Architecture.

Consolidated tools for reduced cognitive load and better discoverability.

Instead of 50+ individual tools, GIMP MCP consolidates related operations into 8
master tools. Each tool handles a specific domain with multiple operations.

TOOLS:
- gimp_file: File operations (load, save, convert, info)
- gimp_transform: Geometric transforms (resize, crop, rotate, flip)
- gimp_color: Color adjustments (brightness, levels, curves, HSL)
- gimp_filter: Filters (blur, sharpen, noise, artistic)
- gimp_layer: Layer management (create, merge, flatten)
- gimp_analysis: Image analysis (quality, statistics, compare)
- gimp_batch: Batch processing (resize, convert, watermark)
- gimp_system: System operations (status, help, cache)
"""

from .file_operations import gimp_file
from .transform import gimp_transform
from .color import gimp_color
from .filter import gimp_filter
from .layer import gimp_layer
from .analysis import gimp_analysis
from .batch import gimp_batch
from .system import gimp_system

__all__ = [
    "gimp_file",
    "gimp_transform",
    "gimp_color",
    "gimp_filter",
    "gimp_layer",
    "gimp_analysis",
    "gimp_batch",
    "gimp_system",
]

# Tool metadata for discovery
PORTMANTEAU_TOOLS = [
    {
        "name": "gimp_file",
        "function": gimp_file,
        "category": "file_operations",
        "operations": ["load", "save", "convert", "info", "validate", "list_formats"],
    },
    {
        "name": "gimp_transform",
        "function": gimp_transform,
        "category": "transforms",
        "operations": [
            "resize",
            "crop",
            "rotate",
            "flip",
            "scale",
            "perspective",
            "autocrop",
        ],
    },
    {
        "name": "gimp_color",
        "function": gimp_color,
        "category": "color_adjustments",
        "operations": [
            "brightness_contrast",
            "levels",
            "curves",
            "color_balance",
            "hue_saturation",
            "colorize",
            "threshold",
            "posterize",
            "desaturate",
            "invert",
            "auto_levels",
            "auto_color",
        ],
    },
    {
        "name": "gimp_filter",
        "function": gimp_filter,
        "category": "filters",
        "operations": [
            "blur",
            "sharpen",
            "noise",
            "edge_detect",
            "artistic",
            "enhance",
            "distort",
            "light_shadow",
        ],
    },
    {
        "name": "gimp_layer",
        "function": gimp_layer,
        "category": "layer_management",
        "operations": [
            "create",
            "duplicate",
            "delete",
            "merge",
            "flatten",
            "reorder",
            "properties",
            "info",
        ],
    },
    {
        "name": "gimp_analysis",
        "function": gimp_analysis,
        "category": "image_analysis",
        "operations": [
            "quality",
            "statistics",
            "histogram",
            "compare",
            "detect_issues",
            "report",
            "color_profile",
            "metadata",
        ],
    },
    {
        "name": "gimp_batch",
        "function": gimp_batch,
        "category": "batch_processing",
        "operations": [
            "resize",
            "convert",
            "process",
            "watermark",
            "rename",
            "optimize",
        ],
    },
    {
        "name": "gimp_system",
        "function": gimp_system,
        "category": "system",
        "operations": [
            "status",
            "help",
            "diagnostics",
            "cache",
            "config",
            "performance",
            "tools",
            "version",
        ],
    },
]


def get_all_tools():
    """Return all portmanteau tool functions for registration."""
    return [tool["function"] for tool in PORTMANTEAU_TOOLS]


def get_tool_metadata():
    """Return metadata for all portmanteau tools."""
    return PORTMANTEAU_TOOLS
