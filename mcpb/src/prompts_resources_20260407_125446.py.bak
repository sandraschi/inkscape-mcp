"""FastMCP 3.1+ prompts and resources for inkscape-mcp (fleet SOTA alignment).

Registers MCP prompts (prompt://inkscape/...) and resources (resource://inkscape/...)
so clients that list prompts/resources see real entries, not only MCPB bundle text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_prompts_and_resources(mcp: FastMCP) -> None:
    """Attach prompts and resources to the given FastMCP instance."""

    @mcp.prompt("prompt://inkscape/svg-file-workflow")
    def prompt_svg_file_workflow() -> str:
        """Guide file-level SVG workflows (load, convert, validate)."""
        return """Guide the user through Inkscape MCP file operations.
1. Call inkscape_system(operation="status") or operation="version" to confirm Inkscape is reachable.
2. Use inkscape_file(operation="info", input_path="...") for format and basic metadata.
3. Use inkscape_file(operation="validate", input_path="...") before heavy edits.
4. Use inkscape_file(operation="convert", input_path="...", output_path="...", format="pdf|png|...") for exports.
5. Prefer absolute paths the server is allowed to read; respect allowed_directories in config."""

    @mcp.prompt("prompt://inkscape/vector-editing-workflow")
    def prompt_vector_editing_workflow() -> str:
        """Guide vector edits via inkscape_vector."""
        return """Guide vector editing with inkscape_vector (Inkscape CLI --actions).
1. Start from inkscape_analysis(operation="dimensions", input_path="...") or "statistics" for context.
2. Typical flows: path_simplify, path_clean, apply_boolean (union/intersect with operation_type), trace_image for raster sources.
3. For barcodes/QR: inkscape_vector(operation="generate_barcode_qr", output_path="...", barcode_data="...") via kwargs your client passes through.
4. Always pass input_path and output_path when the operation writes a file; verify success in the tool response dict."""

    @mcp.prompt("prompt://inkscape/analysis-workflow")
    def prompt_analysis_workflow() -> str:
        """Guide document analysis before editing."""
        return """Use inkscape_analysis to understand an SVG before changing it.
1. inkscape_analysis(operation="statistics", input_path="...")
2. inkscape_analysis(operation="objects", input_path="...") for structure
3. inkscape_analysis(operation="validate", input_path="...")
4. inkscape_analysis(operation="dimensions", input_path="...")
5. Summarize findings and propose the smallest set of inkscape_vector / inkscape_file calls to meet the user goal."""

    @mcp.prompt("prompt://inkscape/sampling-agentic-workflow")
    def prompt_sampling_agentic_workflow() -> str:
        """Explain SEP-1577 / ctx.sample agentic tools."""
        return """When the MCP host supports sampling (FastMCP 3.1 SEP-1577):
- generate_svg: client LLM produces SVG via multi-step sampling; requires ctx.
- agentic_inkscape_workflow, intelligent_vector_processing, conversational_inkscape_assistant: orchestration helpers (see docs/AI_SAMPLING.md).

If the tool returns "Sampling context unavailable", switch to explicit inkscape_* tool calls instead of agentic tools.
Optional: list_local_models() to see Ollama/LM Studio; REST /api/generate-svg uses Ollama when configured (dashboard docs)."""

    @mcp.prompt("prompt://inkscape/heraldry-workflow")
    def prompt_heraldry_workflow() -> str:
        """Heraldry-specific generation."""
        return """For heraldic assets use generate_heraldry(operation="trumponia", output_path="...") when registered.
Confirm output path is under an allowed directory. Combine with inkscape_file / inkscape_vector for post-processing if needed."""

    @mcp.resource("resource://inkscape/capabilities")
    def resource_capabilities() -> str:
        """Static capability summary for indexers and clients."""
        return """inkscape-mcp (FastMCP 3.1+)
Tools: inkscape_file, inkscape_vector, inkscape_analysis, inkscape_system, list_local_models, generate_heraldry
Optional (sampling): generate_svg, agentic_inkscape_workflow, intelligent_vector_processing, conversational_inkscape_assistant
Transports: stdio (MCP_TRANSPORT=stdio), HTTP (MCP_TRANSPORT=http, MCP_PORT default 10847, path /mcp)
REST (when HTTP + fastapi extra): /api/health, /api/help, /api/logs, /api/chat (no local LLM), /api/generate-svg (Ollama)
Web UI dev: Vite proxy to backend (see web_sota; fleet ports 10846/10847).
Prompts: prompt://inkscape/svg-file-workflow, vector-editing-workflow, analysis-workflow, sampling-agentic-workflow, heraldry-workflow
Resources: resource://inkscape/capabilities, resource://inkscape/skills"""

    @mcp.resource("resource://inkscape/skills")
    def resource_skills() -> str:
        """LLM-oriented skill reference (mirrors fleet skill:// style content)."""
        return """# inkscape-mcp — skills reference

## inkscape_file
- load, save, convert, info, validate, list_formats

## inkscape_vector
- trace_image, generate_barcode_qr, create_mesh_gradient, text_to_path, construct_svg,
  apply_boolean, path_inset_outset, path_simplify, path_clean, path_combine, path_break_apart,
  object_to_path, optimize_svg, scour_svg, measure_object, query_document, count_nodes,
  export_dxf, layers_to_files, fit_canvas_to_drawing, render_preview, generate_laser_dot,
  object_raise, object_lower, set_document_units

## inkscape_analysis
- quality, statistics, validate, objects, dimensions, structure

## inkscape_system
- status, help, diagnostics, version, config, list_extensions, execute_extension (if enabled)

## Other
- list_local_models: Ollama / LM Studio discovery
- generate_heraldry: heraldic SVG (trumponia)

## Agentic (sampling hosts only)
- generate_svg, agentic_inkscape_workflow, intelligent_vector_processing, conversational_inkscape_assistant

See docs/USAGE.md, docs/AI_SAMPLING.md, and llms-full.txt in the repository root for environment variables and run commands.
"""
