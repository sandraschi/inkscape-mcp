"""Inkscape MCP Tools — FastMCP 3.1+ portmanteau surface.

Consolidated tools for vector graphics operations with reduced cognitive load and better discoverability.

Instead of 50+ individual tools, Inkscape MCP consolidates related operations into 4
master tools. Each tool handles a specific domain with multiple operations.

TOOLS:
- inkscape_file: File operations (load, save, convert, info, validate, list_formats)
- inkscape_vector: Advanced vector operations (23 operations: trace, boolean, optimize, render, etc.)
- inkscape_analysis: Document analysis (quality, statistics, validate, objects, dimensions, structure)
- inkscape_system: System operations (status, help, diagnostics, version, config)
"""

from typing import Any

from .file_operations import inkscape_file
from .vector_operations import inkscape_vector
from .analysis import inkscape_analysis
from .system import inkscape_system
from .heraldry import register_heraldry_tools
from .llm_discovery import list_local_models

__all__ = [
    "inkscape_file",
    "inkscape_vector",
    "inkscape_analysis",
    "inkscape_system",
    "register_heraldry_tools",
    "list_local_models",
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
        "operations": ["status", "help", "diagnostics", "version", "config"],
    },
]


def get_all_tools():
    """Return all portmanteau tool functions for registration."""
    return [tool["function"] for tool in PORTMANTEAU_TOOLS]


def get_tool_metadata():
    """Return metadata for all portmanteau tools."""
    return PORTMANTEAU_TOOLS


def register_all_tools(mcp: Any, cli_wrapper: Any, config: Any) -> None:
    """Register all portmanteau tools with the MCP server."""
    # Register core portmanteau tools
    for tool_info in PORTMANTEAU_TOOLS:
        mcp.tool()(tool_info["function"])

    # Register specialized tools
    register_heraldry_tools(mcp, cli_wrapper, config)

    # Register individual utility tools
    mcp.tool()(list_local_models)
