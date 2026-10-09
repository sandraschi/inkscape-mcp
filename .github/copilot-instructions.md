# Copilot Instructions — inkscape-mcp

## Session Context (Inkscape MCP)

Inkscape SVG vector editing and generation via FastMCP (portmanteau tools, `operation` enum param).

**Before starting work:**
1. Check server status: `inkscape_system(operation="status")`
2. Check execution mode: `inkscape_system(operation="execution_mode")`

**Key portmanteau tools:**
- `inkscape_file` — load, save, convert, info, validate, list_formats
- `inkscape_vector` — trace_image, boolean ops, path simplify, stroke/transform
- `inkscape_analysis` — document analysis, dimensions, element count
- `inkscape_render` — export PNG, render preview, batch render
- `inkscape_system` — status, help, diagnostics, version, config, list_extensions

**At end of work:**
- Save progress via `inkscape_file(operation="save", ...)`
