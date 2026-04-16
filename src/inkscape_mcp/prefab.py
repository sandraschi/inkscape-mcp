"""
FastMCP 3.2 Prefab UI definitions for inkscape-mcp.

GenerativeUI provider: prefab-ui >= 0.14.0
Renders directly in Claude Desktop / supporting clients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_prefabs(mcp: "FastMCP") -> None:
    """Register Prefab UI components with the FastMCP instance."""

    try:
        from fastmcp.prefab import (
            Button,
            Column,
            Dropdown,
            Row,
            Slider,
            Text,
            TextInput,
            prefab,
        )
    except ImportError:
        import logging
        logging.getLogger(__name__).warning(
            "prefab-ui not installed — Prefab UI unavailable. "
            "Run: uv add 'prefab-ui>=0.14.0'"
        )
        return

    @prefab(mcp, tool="generate_svg")
    def generate_svg_prefab():
        """GenerativeUI panel for generate_svg — rendered in supporting clients."""
        return Column(
            children=[
                Text(value="SVG generator", style={"fontWeight": "500", "fontSize": "14px"}),
                TextInput(
                    param="description",
                    label="Description",
                    placeholder="e.g. heraldic crest with two lions rampant on azure field",
                ),
                Row(
                    children=[
                        Dropdown(
                            param="style_preset",
                            label="Style",
                            options=["geometric", "organic", "technical", "heraldic", "abstract"],
                            default="geometric",
                        ),
                        Dropdown(
                            param="quality",
                            label="Quality",
                            options=["draft", "standard", "high", "ultra"],
                            default="standard",
                        ),
                    ]
                ),
                Row(
                    children=[
                        TextInput(
                            param="dimensions",
                            label="Dimensions",
                            placeholder="800x600",
                            default="800x600",
                        ),
                        Slider(
                            param="max_steps",
                            label="Reasoning steps",
                            min=1,
                            max=10,
                            default=5,
                            step=1,
                        ),
                    ]
                ),
                Button(label="Generate SVG", action="submit"),
            ]
        )

    @prefab(mcp, tool="inkscape_system")
    def inkscape_system_prefab():
        """Quick status panel for inkscape_system."""
        return Column(
            children=[
                Text(value="Inkscape system", style={"fontWeight": "500", "fontSize": "14px"}),
                Dropdown(
                    param="operation",
                    label="Operation",
                    options=["status", "version", "diagnostics", "help", "config", "list_extensions"],
                    default="status",
                ),
                Button(label="Run", action="submit"),
            ]
        )
