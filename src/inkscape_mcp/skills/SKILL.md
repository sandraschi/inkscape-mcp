# inkscape-mcp skills

## generate_svg
Generate a complete SVG file from a natural language description using SEP-1577 multi-step sampling.

**When to use:** User wants to create a new SVG from a description — "make a heraldic crest", "generate a QR code", "draw a geometric logo".

**Key params:**
- `description`: natural language (e.g. "royal crest with two lions rampant on a blue field")
- `style_preset`: geometric | organic | technical | heraldic | abstract
- `dimensions`: "800x600", "500x500", etc.
- `quality`: draft | standard | high | ultra
- `max_steps`: default 5, increase for complex compositions

**Requires sampling host** (Antigravity, not Claude Desktop). Returns `svg_path` + full `svg_content`.

---

## agentic_inkscape_workflow
Multi-step autonomous workflow planning via SEP-1577 — the LLM probes capabilities then produces a concrete ordered plan.

**When to use:** Complex multi-operation tasks — "optimise all SVGs in this folder for web", "convert every layer to a separate file and export as PNG".

**Key params:**
- `workflow_prompt`: natural language goal
- `available_operations`: optional constraint list
- `max_steps`: default 5

---

## inkscape_file
Load, convert, export, validate SVG and other vector files via Inkscape CLI.

**Operations:** load | save | convert | info | validate | list_formats

**Common pattern:**
1. `inkscape_file(operation="validate", input_path="...")` — check before editing
2. `inkscape_file(operation="convert", input_path="...", output_path="...", format="pdf")` — export

---

## inkscape_vector
Vector editing, boolean ops, tracing, path manipulation, barcode/QR generation.

**Key operations:** trace_image | generate_barcode_qr | apply_boolean | path_simplify | optimize_svg | scour_svg | render_preview | export_dxf | layers_to_files | text_to_path

---

## inkscape_analysis
Read-only inspection of SVG structure, quality, dimensions. Always call before mutating.

**Operations:** quality | statistics | validate | objects | dimensions | structure

---

## inkscape_system
Server/Inkscape status, help, diagnostics, version, extension listing.

**Operations:** status | help | diagnostics | version | config | list_extensions

---

## Environment
- Transport: `MCP_TRANSPORT=stdio` for Claude Desktop, `MCP_TRANSPORT=http` + `MCP_PORT=10847` for webapp
- Inkscape not required for sampling-based tools; CLI tools degrade gracefully with a warning
- Skills are loaded via `resource://inkscape/skills`
