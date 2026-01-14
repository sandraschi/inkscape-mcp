"""
Inkscape MCP Tools - FastMCP 2.13+ Portmanteau Architecture.

Consolidated tools for vector graphics operations with reduced cognitive load and better discoverability.

Instead of 50+ individual tools, Inkscape MCP consolidates related operations into 8
master tools. Each tool handles a specific domain with multiple operations.

TOOLS:
- inkscape_file: File operations (load, save, convert, info)
- inkscape_object: Object management (create, group, align, transform)
- inkscape_path: Path operations (edit, boolean, stroke/fill)
- inkscape_text: Text handling (create, edit, style, convert to path)
- inkscape_transform: Geometric transforms (scale, rotate, translate)
- inkscape_export: Export operations (PNG, PDF, EPS, SVG variants)
- inkscape_analysis: Document analysis (quality, statistics, validation)
- inkscape_system: System operations (status, help, diagnostics)
"""

from .file_operations import inkscape_file
from .transform import inkscape_transform
from .analysis import inkscape_analysis
from .system import inkscape_system

# Placeholder imports for tools to be implemented
# from .object_operations import inkscape_object
# from .path_operations import inkscape_path
# from .text_operations import inkscape_text
# from .export_operations import inkscape_export

__all__ = [
    "inkscape_file",
    "inkscape_transform",
    "inkscape_analysis",
    "inkscape_system",
    # "inkscape_object",
    # "inkscape_path",
    # "inkscape_text",
    # "inkscape_export",
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
]


def get_all_tools():
    """Return all portmanteau tool functions for registration."""
    return [tool["function"] for tool in PORTMANTEAU_TOOLS]


def get_tool_metadata():
    """Return metadata for all portmanteau tools."""
    return PORTMANTEAU_TOOLS
