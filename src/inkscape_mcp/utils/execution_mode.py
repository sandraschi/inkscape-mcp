"""Dual-mode execution helpers (Hands-In GUI watch vs Hands-Off batch CLI)."""

from __future__ import annotations

from typing import Any

from ..config import InkscapeConfig
from .inkscape_runtime import cli_available
from .inkscape_runtime import detect_inkscape_gui_process
from .inkscape_runtime import gui_watch_enabled


async def describe_execution_mode(
    *,
    cli_wrapper: Any = None,
    config: InkscapeConfig | None = None,
) -> dict[str, Any]:
    """Return current Hands-In vs Hands-Off mode for agents and webapp."""
    cfg = config or InkscapeConfig.load_default()
    gui_active = gui_watch_enabled() or detect_inkscape_gui_process()
    batch_ok = await cli_available(cli_wrapper, cfg)

    if gui_active:
        return {
            "success": True,
            "mode": "hands_in",
            "label": "Hands-In (GUI watch)",
            "gui_watch": True,
            "cli_available": batch_ok,
            "live_capabilities": [
                "User edits SVG interactively in Inkscape while agent runs CLI exports",
                "inkscape_render export_preview for agent vision loops",
                "inkscape_analysis objects/structure before mutating paths",
                "Re-export after manual tweaks without restarting the MCP server",
            ],
            "batch_note": (
                "CLI batch exports still run in isolated --batch-process instances; "
                "save the open document before expecting preview parity."
            ),
        }

    return {
        "success": True,
        "mode": "hands_off",
        "label": "Hands-Off (Batch CLI)",
        "gui_watch": False,
        "cli_available": batch_ok,
        "available_capabilities": [
            "inkscape_file / inkscape_vector disk pipelines via Inkscape CLI",
            "inkscape_render export_preview and export_multi_dpi for vision",
            "inkscape_analysis validate/statistics before destructive ops",
            "Fleet HTTP webapp backend on :10900 (Vite :10899)",
        ],
        "live_gui_hint": (
            "Open the SVG in Inkscape GUI for interactive editing, optionally set "
            "INKSCAPE_GUI_WATCH=1, then inkscape_system operation=execution_mode "
            "should report hands_in."
        ),
    }
