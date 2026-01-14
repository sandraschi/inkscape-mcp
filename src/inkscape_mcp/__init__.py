"""
Inkscape MCP Server - Professional Vector Graphics through Model Context Protocol

This package provides a FastMCP 2.13+ server that enables AI agents like Claude
to perform professional vector graphics operations using Inkscape (the premier
open-source SVG editor).

v1.0.0 - Portmanteau Architecture:
Instead of 50+ individual tools, Inkscape MCP consolidates related operations into 8
master portmanteau tools for reduced cognitive load and better discoverability.

Portmanteau Tools:
- inkscape_file: File operations (load, save, convert, info)
- inkscape_transform: Geometric transforms (resize, rotate, scale)
- inkscape_object: Object management (create, group, align)
- inkscape_path: Path operations (edit, boolean, stroke/fill)
- inkscape_text: Text handling (create, edit, style)
- inkscape_export: Export operations (PNG, PDF, EPS, SVG variants)
- inkscape_analysis: Document analysis (quality, statistics, validation)
- inkscape_system: System operations (status, help, diagnostics)

Author: Sandra Schipal
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Sandra Schipal"
__email__ = "sandra@sandraschi.dev"

from .server import InkscapeMcpServer

# Export portmanteau tools for direct use
from .tools import (
    inkscape_file,
    inkscape_transform,
    inkscape_object,
    inkscape_path,
    inkscape_text,
    inkscape_export,
    inkscape_analysis,
    inkscape_system,
    PORTMANTEAU_TOOLS,
)

__all__ = [
    "InkscapeMcpServer",
    # Portmanteau tools
    "inkscape_file",
    "inkscape_transform",
    "inkscape_object",
    "inkscape_path",
    "inkscape_text",
    "inkscape_export",
    "inkscape_analysis",
    "inkscape_system",
    "PORTMANTEAU_TOOLS",
]
