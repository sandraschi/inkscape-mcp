"""
Agentic Workflow Tools for Inkscape MCP - FastMCP 3.1

Real multi-step SEP-1577 sampling replaces the previous mock implementations.
The client LLM is borrowed via ctx.sample() in a loop, calling capability
probe tools to ground its decisions before producing a final SVG plan/script.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Capability probe tools — passed to ctx.sample so the LLM can query them
# ---------------------------------------------------------------------------


def get_inkscape_file_capabilities() -> str:
    """Return file I/O and format capabilities. Call to see supported formats and operations."""
    return (
        "File ops: load_svg, save_svg, save_as (pdf, png, emf, wmf, eps, ps, dxf, hpgl), "
        "convert_format, get_info (dimensions, elements, layers, viewBox), "
        "validate_svg, optimize_svg (scour), set_metadata (title, description, author), "
        "Supported input: svg, svgz, ai, pdf (single-page), wmf, emf, cdr (partial), "
        "Supported output: svg, svgz, png, pdf, eps, ps, emf, wmf, dxf, hpgl, gcode."
    )


def get_inkscape_vector_capabilities() -> str:
    """Return vector drawing and path manipulation capabilities."""
    return (
        "Drawing: draw_path (bezier/straight), draw_rect, draw_circle, draw_ellipse, "
        "draw_polygon (n-sides), draw_star (n-points, inner-ratio), draw_text (font, size, style), "
        "Path ops: union, difference, intersection, exclusion (xor), division, cut_path, "
        "combine, break_apart, flatten_beziers, simplify_path, reverse_path, "
        "path_effects: bend, envelope, interpolate, roughen, sketch, stitch, "
        "Calligraphy: dip_pen, marker, fill_between_paths."
    )


def get_inkscape_heraldic_capabilities() -> str:
    """Return heraldic/crest-specific design capabilities and conventional charges."""
    return (
        "Shield shapes: heater, lozenge, roundel, cartouche, escutcheon, bordure, "
        "Divisions: per-pale, per-fess, per-bend, quarterly, gyronny, barry, paly, "
        "Charges (ordinaries): chief, base, fess, pale, bend, chevron, cross, saltire, pile, "
        "Charges (subordinaries): canton, inescutcheon, gyron, "
        "Beasts rampant: lion, bear, eagle (displayed), griffin, dragon, unicorn, ASS (donkey), "
        "  - Rampant posture: upright on hind legs, facing dexter (right), forepaws raised, "
        "Tinctures: or (gold), argent (silver), gules (red), azure (blue), sable (black), "
        "  vert (green), purpure (purple), "
        "SVG heraldic paths: pre-built bezier paths for all standard charges, "
        "Supporters: flanking figures on either side of shield, "
        "Motto scroll: curved path with text, ribbon shape below shield, "
        "Crest: figure or device above helmet/wreath."
    )


def get_inkscape_style_capabilities() -> str:
    """Return fill, stroke, gradient, and pattern capabilities."""
    return (
        "Fill: solid_color (hex/rgb/hsl/named), linear_gradient, radial_gradient, "
        "mesh_gradient, pattern_fill (checkerboard, hatch, cross-hatch, dots), swatch_library, "
        "Stroke: solid, dashed (custom dash array), marker_start/end (arrow, dot, diamond, club), "
        "stroke_width, stroke_opacity, stroke_linecap (butt/round/square), linejoin (miter/round/bevel), "
        "Filters: blur, drop_shadow, bevel, glow, displacement, turbulence, "
        "Opacity: object_opacity, fill_opacity, stroke_opacity, "
        "Blend modes: normal, multiply, screen, overlay, darken, lighten, color-dodge/burn."
    )


def get_svg_generation_approach() -> str:
    """Return SVG generation strategy for complex descriptions. Call for multi-element compositions."""
    return (
        "SVG Generation Strategy: "
        "1. Parse description → identify main subject, style, elements, color scheme. "
        "2. Set viewBox and canvas (e.g. 800x600 for landscape, 600x800 for portrait, 500x500 square). "
        "3. Define <defs>: gradients, patterns, clipPaths, symbols, filters, reusable path data. "
        "4. Structure layers (Inkscape layers = SVG <g> with inkscape:label): "
        "   background → mid-ground → foreground → text/labels. "
        "5. For heraldic crests: background → shield → charges → supporters → motto → crest. "
        "6. Output complete valid SVG string with proper XML declaration and namespace. "
        "7. Use semantic IDs: id='shield-body', id='charge-lion-dexter', id='motto-text'. "
        "8. Two asses rampant = two donkey/ass figures each in rampant posture, one on each side."
    )


# ---------------------------------------------------------------------------
# Shared SEP-1577 multi-step loop
# ---------------------------------------------------------------------------

_CAPABILITY_TOOLS = [
    get_inkscape_file_capabilities,
    get_inkscape_vector_capabilities,
    get_inkscape_heraldic_capabilities,
    get_inkscape_style_capabilities,
    get_svg_generation_approach,
]


async def _run_sep1577_loop(
    ctx: Any,
    user_message: str,
    system_prompt: str,
    max_steps: int,
    max_tokens: int = 2500,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """
    Core SEP-1577 multi-step reasoning loop.

    Calls ctx.sample() with the full capability toolset, collects tool call history,
    and iterates until the LLM produces a final text response (stop_reason='end_turn')
    or max_steps is exhausted.
    """
    messages: list[Any] = [user_message]
    all_tool_calls: list[dict[str, Any]] = []
    final_text = ""
    step = 0

    while step < max_steps:
        step += 1
        result = await ctx.sample(
            messages=messages,
            system_prompt=system_prompt,
            tools=_CAPABILITY_TOOLS,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Collect tool calls from this step
        if hasattr(result, "tool_calls") and result.tool_calls:
            for tc in result.tool_calls:
                all_tool_calls.append(
                    {
                        "step": step,
                        "tool": getattr(tc, "name", str(tc)),
                        "result": getattr(tc, "result", None),
                    }
                )

        final_text = getattr(result, "text", None) or getattr(result, "content", "") or ""
        stop_reason = getattr(result, "stop_reason", None)

        if stop_reason in ("end_turn", "stop_sequence") or (
            final_text and not getattr(result, "tool_calls", None)
        ):
            break

        # Feed tool results + partial response back for next iteration
        if final_text:
            messages.append({"role": "assistant", "content": final_text})
        if all_tool_calls:
            tool_summary = "\n".join(
                f"[{tc['tool']}]: {tc['result']}" for tc in all_tool_calls[-5:]
            )
            messages.append(
                {
                    "role": "user",
                    "content": f"Tool results from step {step}:\n{tool_summary}\nContinue.",
                }
            )

    warning = (
        f"Reached max_steps={max_steps} without final stop signal."
        if step >= max_steps and not final_text
        else None
    )
    return {
        "output": final_text,
        "steps": step,
        "tool_calls": all_tool_calls,
        **({"warning": warning} if warning else {}),
    }


# ---------------------------------------------------------------------------
# Helper: save raw SVG string to file
# ---------------------------------------------------------------------------


def _save_svg(svg_content: str, description: str, style_preset: str) -> Path:
    """Write SVG content to a generated_svgs/ file and return the path."""
    output_dir = Path("generated_svgs")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    svg_hash = hashlib.md5(description.encode()).hexdigest()[:8]
    filename = f"ai_{style_preset}_{timestamp}_{svg_hash}.svg"
    svg_path = output_dir / filename
    svg_path.write_text(svg_content, encoding="utf-8")
    return svg_path


# ---------------------------------------------------------------------------
# Register agentic tools
# ---------------------------------------------------------------------------


def register_agentic_tools(mcp_instance=None):
    """Register agentic workflow tools with FastMCP 3.1 SEP-1577 sampling."""
    if mcp_instance is None:
        from .main import mcp as mcp_instance  # noqa: PLC0415

    @mcp_instance.tool()
    async def generate_svg(
        ctx: Any,
        description: str = "a simple geometric design",
        style_preset: str = "geometric",
        dimensions: str = "800x600",
        quality: str = "standard",
        reference_svgs: list[str] | None = None,
        post_processing: list[str] | None = None,
        max_steps: int = 5,
    ) -> dict[str, Any]:
        """Generate SVG files by prompting the client LLM with SEP-1577 multi-step sampling.

        The LLM probes Inkscape capabilities (heraldry, paths, styles, etc.) before
        producing a complete, valid SVG string for the requested description.

        Args:
            description: Natural language description (e.g. "royal crest with two asses rampant")
            style_preset: geometric | organic | technical | heraldic | abstract
            dimensions: Canvas size e.g. "800x600" or "500x500"
            quality: draft | standard | high | ultra
            reference_svgs: Optional list of reference SVG file paths
            post_processing: Inkscape ops to apply after generation (simplify, optimize, etc.)
            max_steps: Max SEP-1577 reasoning loops (default: 5)
            ctx: FastMCP context — injected when client supports sampling

        Returns:
            dict with success, svg_path, svg_content preview, and metadata
        """
        # --- parameter validation ---
        try:
            width, height = map(int, dimensions.split("x"))
            if not (64 <= width <= 8192 and 64 <= height <= 8192):
                raise ValueError
        except (ValueError, AttributeError):
            return {
                "success": False,
                "error": f"Invalid dimensions: '{dimensions}'. Use 'WIDTHxHEIGHT' (e.g. '800x600').",
            }

        valid_styles = ["geometric", "organic", "technical", "heraldic", "abstract"]
        if style_preset not in valid_styles:
            return {
                "success": False,
                "error": f"Invalid style_preset '{style_preset}'. Choose from: {valid_styles}",
            }

        if ctx is None:
            return {
                "success": False,
                "error": "Sampling context unavailable — client does not support SEP-1577.",
                "message": (
                    "Use a sampling-capable client (Claude Desktop, Antigravity) "
                    "to generate SVGs via this tool."
                ),
            }

        system_prompt = (
            "You are an expert SVG designer and Inkscape specialist using FastMCP 3.1 SEP-1577. "
            "Your job is to produce a COMPLETE, VALID SVG file as a string. "
            "Steps: (1) Call the relevant capability probes to understand available elements. "
            "(2) Plan the composition (layers, viewBox, elements, colours). "
            "(3) Output the FULL SVG XML as your final response — no truncation, no placeholders. "
            "For heraldic designs: use proper heraldic convention (tinctures, charges, postures). "
            "For 'asses rampant': draw donkey/ass figures in rampant posture (upright, hind legs only, "
            "forepaws raised, facing dexter). "
            "The SVG must be self-contained (no external resources) and render correctly in a browser."
        )

        ref_hint = (
            f"Reference SVGs to draw inspiration from: {reference_svgs}." if reference_svgs else ""
        )
        post_hint = (
            f"After generation, these Inkscape ops will be applied: {post_processing}."
            if post_processing
            else ""
        )
        user_message = (
            f"Generate a {style_preset} SVG ({width}x{height}px, {quality} quality).\n"
            f"Description: {description}\n"
            f"{ref_hint}\n{post_hint}\n"
            'Output ONLY the complete SVG XML string. Start with <?xml version="1.0"...>'
        )

        try:
            loop_result = await _run_sep1577_loop(
                ctx=ctx,
                user_message=user_message,
                system_prompt=system_prompt,
                max_steps=max_steps,
                max_tokens=4000,
                temperature=0.4,
            )
        except Exception as e:
            logger.exception("SEP-1577 SVG generation failed: %s", e)
            return {"success": False, "error": str(e), "message": "Sampling failed."}

        svg_content = loop_result["output"]

        # Extract SVG block if the LLM wrapped it in prose
        if "<svg" in svg_content and "</svg>" in svg_content:
            start = (
                svg_content.find("<?xml") if "<?xml" in svg_content else svg_content.find("<svg")
            )
            end = svg_content.rfind("</svg>") + len("</svg>")
            svg_content = svg_content[start:end]

        if not svg_content.strip():
            return {
                "success": False,
                "error": "LLM returned empty SVG content.",
                "steps_taken": loop_result["steps"],
                "tool_calls": loop_result["tool_calls"],
            }

        # Save to disk
        svg_path = _save_svg(svg_content, description, style_preset)
        file_size_kb = round(len(svg_content.encode()) / 1024, 2)
        svg_hash = hashlib.md5(svg_content.encode()).hexdigest()[:8]

        return {
            "success": True,
            "message": f"Generated {style_preset} SVG: '{description[:60]}'",
            "svg_path": str(svg_path),
            "svg_content": svg_content,  # full SVG for webapp preview
            "svg_hash": svg_hash,
            "dimensions": f"{width}x{height}",
            "style_preset": style_preset,
            "quality": quality,
            "file_size_kb": file_size_kb,
            "steps_taken": loop_result["steps"],
            "tool_calls": loop_result["tool_calls"],
            "next_steps": [
                "Use inkscape_vector to refine paths",
                "Use inkscape_file to export as PDF/PNG",
                "Use agentic_inkscape_workflow for further processing",
            ],
        }

    @mcp_instance.tool()
    async def agentic_inkscape_workflow(
        workflow_prompt: str,
        available_operations: list[str] | None = None,
        max_steps: int = 5,
        ctx: Any = None,
    ) -> dict[str, Any]:
        """Execute autonomous multi-step Inkscape workflows via FastMCP 3.1 SEP-1577.

        The client LLM plans and executes a vector graphics workflow step-by-step,
        autonomously querying Inkscape capability probes to inform each decision.

        Args:
            workflow_prompt: Natural language workflow goal
            available_operations: Optional list to constrain the plan
            max_steps: Maximum reasoning loops (default: 5)
            ctx: FastMCP context — injected when client supports sampling

        Returns:
            dict with success, message (final plan), steps_taken, tool_calls
        """
        if ctx is None:
            return {
                "success": False,
                "error": "Sampling context unavailable",
                "message": "Client does not support MCP sampling (SEP-1577).",
            }

        ops_hint = (
            f"Prefer these operations: {', '.join(available_operations)}."
            if available_operations
            else "Use any available Inkscape operation."
        )
        system_prompt = (
            "You are an expert Inkscape vector graphics workflow orchestrator using SEP-1577. "
            "Call the capability probes to discover available operations, then produce a "
            "concrete, ordered, step-by-step plan that maps precisely to real Inkscape operations. "
            "Be specific: name each operation, parameters, and expected output. "
            "Never hallucinate operations — only use what the probes confirm."
        )
        try:
            loop_result = await _run_sep1577_loop(
                ctx=ctx,
                user_message=f"Workflow goal: {workflow_prompt}\n{ops_hint}",
                system_prompt=system_prompt,
                max_steps=max_steps,
            )
            return {
                "success": True,
                "operation": "agentic_inkscape_workflow",
                "message": loop_result["output"],
                "steps_taken": loop_result["steps"],
                "tool_calls": loop_result["tool_calls"],
                "workflow_prompt": workflow_prompt,
                **({"warning": loop_result["warning"]} if "warning" in loop_result else {}),
            }
        except Exception as e:
            logger.exception("SEP-1577 workflow failed: %s", e)
            return {
                "success": False,
                "error": str(e),
                "message": "Multi-step sampling failed.",
            }

    @mcp_instance.tool()
    async def intelligent_vector_processing(
        documents: list[dict[str, Any]],
        processing_goal: str,
        available_operations: list[str],
        processing_strategy: str = "adaptive",
        max_steps: int = 5,
        ctx: Any = None,
    ) -> dict[str, Any]:
        """Intelligent batch SVG/vector processing via FastMCP 3.1 SEP-1577 multi-step sampling.

        Args:
            documents: List of document dicts (keys: path, format, purpose, etc.)
            processing_goal: What to achieve (e.g. "optimize all SVGs for web, max 50KB each")
            available_operations: Operations the LLM may use in the plan
            processing_strategy: "adaptive" | "parallel" | "sequential"
            max_steps: Maximum reasoning loops (default: 5)
            ctx: FastMCP context — injected when client supports sampling

        Returns:
            dict with success, message (processing plan), steps_taken, tool_calls
        """
        if ctx is None:
            return {
                "success": False,
                "error": "Sampling context unavailable",
                "message": "Client does not support MCP sampling.",
            }

        doc_count = len(documents) if documents else 0
        doc_names = [d.get("path", f"doc_{i}") for i, d in enumerate((documents or [])[:5])]

        system_prompt = (
            "You are a vector graphics pipeline engineer using FastMCP 3.1 SEP-1577. "
            "Call capability probes to understand available Inkscape operations, then design "
            "a precise processing pipeline for the batch. Output a numbered plan: "
            "operation, target file(s), parameters, expected outcome. "
            "Use only operations confirmed by the probes."
        )
        user_message = (
            f"Processing goal: {processing_goal}\n"
            f"Documents ({doc_count}): {doc_names}\n"
            f"Allowed ops: {available_operations}\n"
            f"Strategy: {processing_strategy}"
        )
        try:
            loop_result = await _run_sep1577_loop(
                ctx=ctx,
                user_message=user_message,
                system_prompt=system_prompt,
                max_steps=max_steps,
                max_tokens=1800,
            )
            return {
                "success": True,
                "operation": "intelligent_vector_processing",
                "message": loop_result["output"],
                "steps_taken": loop_result["steps"],
                "tool_calls": loop_result["tool_calls"],
                "processing_goal": processing_goal,
                "document_count": doc_count,
                "processing_strategy": processing_strategy,
                **({"warning": loop_result["warning"]} if "warning" in loop_result else {}),
            }
        except Exception as e:
            logger.exception("SEP-1577 batch processing failed: %s", e)
            return {
                "success": False,
                "error": str(e),
                "message": "Multi-step sampling failed.",
            }

    @mcp_instance.tool()
    async def conversational_inkscape_assistant(
        user_query: str,
        context_level: str = "comprehensive",
        max_steps: int = 3,
        ctx: Any = None,
    ) -> dict[str, Any]:
        """Conversational Inkscape assistant with SEP-1577 multi-step sampling.

        The LLM may probe capabilities to give accurate, operation-specific guidance.
        Falls back gracefully when sampling is unavailable.

        Args:
            user_query: Natural language question about Inkscape or vector graphics
            context_level: "basic" | "comprehensive" | "detailed"
            max_steps: Max reasoning loops (default: 3)
            ctx: FastMCP context — injected when client supports sampling

        Returns:
            dict with success, message, next_steps
        """
        _fallbacks = {
            "basic": "I can help you create vector graphics with Inkscape.",
            "comprehensive": (
                "I'm your Inkscape vector graphics assistant. I support SVG creation, "
                "path editing, heraldic design, batch processing, and agentic workflows."
            ),
            "detailed": (
                "Welcome to Inkscape MCP (FastMCP 3.1 SEP-1577). Capabilities: "
                "SVG generation via LLM sampling, path manipulation, boolean ops, "
                "heraldic/crest creation, style/gradient/filter application, "
                "batch conversion, and multi-step agentic workflows."
            ),
        }

        if ctx is None:
            return {
                "success": True,
                "operation": "conversational_assistance",
                "message": _fallbacks.get(context_level, _fallbacks["comprehensive"]),
                "user_query": user_query,
                "sampling_available": False,
                "next_steps": [
                    "Use generate_svg to create new SVGs via natural language",
                    "Use agentic_inkscape_workflow for multi-step workflows",
                    "Use inkscape_vector for direct path operations",
                ],
            }

        system_prompt = (
            "You are a helpful, expert Inkscape assistant. "
            "If the question is about specific ops, probe the relevant capability tool first "
            "so your answer references real available operations. Keep answers concise. "
            "Always suggest 2-3 concrete next steps (tool names or SVG operations)."
        )
        try:
            loop_result = await _run_sep1577_loop(
                ctx=ctx,
                user_message=user_query,
                system_prompt=system_prompt,
                max_steps=max_steps,
                max_tokens=900,
                temperature=0.4,
            )
            return {
                "success": True,
                "operation": "conversational_assistance",
                "message": loop_result["output"],
                "steps_taken": loop_result["steps"],
                "tool_calls": loop_result["tool_calls"],
                "user_query": user_query,
                "sampling_available": True,
                "next_steps": [
                    "Use generate_svg to create new SVGs via natural language",
                    "Use agentic_inkscape_workflow for multi-step workflows",
                    "Use inkscape_vector for direct path operations",
                ],
            }
        except Exception as e:
            logger.exception("Conversational assistant sampling failed: %s", e)
            return {
                "success": True,  # graceful degradation
                "operation": "conversational_assistance",
                "message": _fallbacks.get(context_level, _fallbacks["comprehensive"]),
                "user_query": user_query,
                "sampling_error": str(e),
                "sampling_available": False,
                "next_steps": [
                    "Use generate_svg with a sampling-capable client for AI SVG creation",
                ],
            }
