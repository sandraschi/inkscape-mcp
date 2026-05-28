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

from .analysis import inkscape_analysis
from .file_operations import inkscape_file
from .heraldry import register_heraldry_tools
from .llm_discovery import list_local_models
from .fleet_tools import inkscape_fleet
from .render_tools import inkscape_render
from .system import inkscape_system
from .validation_tools import inkscape_validation
from .vector_operations import inkscape_vector

__all__ = [
    "inkscape_file",
    "inkscape_vector",
    "inkscape_analysis",
    "inkscape_render",
    "inkscape_validation",
    "inkscape_fleet",
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
        "name": "inkscape_render",
        "function": inkscape_render,
        "category": "agent_vision",
        "operations": ["export_preview", "export_multi_dpi", "get_document_summary"],
    },
    {
        "name": "inkscape_validation",
        "function": inkscape_validation,
        "category": "validation",
        "operations": [
            "validate_svg",
            "check_viewbox",
            "check_stroke_fill",
            "check_size_limits",
            "audit_web_svg",
        ],
    },
    {
        "name": "inkscape_system",
        "function": inkscape_system,
        "category": "system",
        "operations": [
            "status",
            "execution_mode",
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


def register_all_tools(mcp: Any, cli_wrapper: Any, config: Any) -> None:
    """Register all portmanteau tools with the MCP server."""
    # Register core portmanteau tools
    for tool_info in PORTMANTEAU_TOOLS:
        mcp.tool()(tool_info["function"])

    # Register specialized tools
    register_heraldry_tools(mcp, cli_wrapper, config)

    # Register individual utility tools
    mcp.tool()(list_local_models)
