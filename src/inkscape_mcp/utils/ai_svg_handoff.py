"""Agent handoff manifest for SVG refine loops (inkscape + gimp fleet QA)."""

from __future__ import annotations

import os
from typing import Any


def _env_flag(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def build_ai_svg_handoff(*, goal: str = "", svg_issues: list[str] | None = None) -> dict[str, Any]:
    """Return agent-facing handoff manifest for iterative SVG icon/UI pipelines."""
    ollama = _env_flag("OLLAMA_BASE_URL") or _env_flag("OLLAMA_HOST")
    openai = _env_flag("OPENAI_API_KEY")

    backends: list[dict[str, Any]] = []
    if ollama:
        backends.append(
            {
                "backend": "ollama",
                "mcp_tool": "construct_svg",
                "repo": "inkscape-mcp",
                "env": ["OLLAMA_BASE_URL", "OLLAMA_MODEL"],
                "hint": "Regenerate or refine SVG via agentic construct_svg sampling loop.",
            }
        )
    if openai:
        backends.append(
            {
                "backend": "openai",
                "mcp_tool": "construct_svg",
                "repo": "inkscape-mcp",
                "env": ["OPENAI_API_KEY"],
            }
        )

    refine_steps = [
        "Run inkscape_validation audit_svg_pack on the icon directory.",
        "Normalize with inkscape_sim_art svg_pack_batch to a fleet template (ui_icon_128).",
        "Layout with build_icon_sheet (margin/bleed) and export PNG via inkscape_fleet push_gimp_raster.",
        "Re-run audit_svg_pack until issue_count is 0, then push_unity_sprite or stage_resonite_ui.",
    ]
    if backends:
        refine_steps.insert(
            0,
            "Use construct_svg / agentic sampling to refine vector paths from agent feedback.",
        )
    else:
        refine_steps.insert(
            0,
            "Set OLLAMA_BASE_URL for local SVG generation; manual inkscape_vector edits still work.",
        )

    return {
        "goal": goal or "Fleet-ready SVG icon pack",
        "svg_issues": svg_issues or [],
        "available_backends": backends,
        "backends_configured": bool(backends),
        "refine_loop": refine_steps,
        "inkscape_mcp_url": os.getenv("INKSCAPE_MCP_URL", "http://127.0.0.1:10900"),
        "gimp_mcp_url": os.getenv("GIMP_MCP_URL", "http://127.0.0.1:10773"),
        "sim_art_operation": "svg_pack_batch",
        "validation_operation": "audit_svg_pack",
    }
