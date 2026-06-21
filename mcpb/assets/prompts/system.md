# Inkscape MCP Server — Complete Capabilities

## Server Overview
Inkscape MCP Server provides AI agents with complete programmatic access to Inkscape,
the premier open-source vector graphics editor. Through the Model Context Protocol,
this server enables SVG creation, editing, analysis, conversion, and optimization
using Inkscape's powerful CLI and Actions API. The server uses an industrial portmanteau
architecture: instead of 50+ individual tools, related operations are grouped into 7 master
portmanteau tools (file, system, vector, analysis, render, fab_art, sim_art) plus a
heraldry generator and a fleet cross-repo handoff tool. This reduces cognitive load
while maintaining full functional breadth.

## Tool Reference

### inkscape_file (File Operations)
Portmanteau for file I/O. Operations:
- **load**: Read and validate an SVG file path for editing workflows
- **save**: Persist changes to disk (requires allowed directories)
- **convert**: Export SVG to PDF, PNG, or other formats via Inkscape CLI
- **info**: Return metadata including dimensions, layer count, and element statistics
- **validate**: Structural check via Inkscape CLI query
- **list_formats**: Return the list of supported export formats
Parameters: operation (required Literal), input_path, output_path, format.
Returns: success, operation, message, data, execution_time_ms.

### inkscape_system (System Operations)
Portmanteau for server/Inkscape introspection. Operations:
- **status**: Check Inkscape CLI availability, version, and connection health
- **execution_mode**: Report whether server routes through CLI or shell
- **help**: Return structured help for this server
- **diagnostics**: Comprehensive system health including config, paths, extensions
- **version**: Return Inkscape version string
- **config**: Return current server configuration
- **list_extensions**: List installed Inkscape extensions
- **execute_extension**: Run a specific Inkscape extension with parameters
Parameters: operation (required Literal), extension_id, extension_params, input_file, output_file.
Returns: success, message, data, execution_time_ms.

### inkscape_vector (Vector Operations)
Portmanteau for advanced SVG manipulation (23+ operations). Operations:
- **trace_image**: Convert raster images to SVG vector paths using potrace
- **generate_barcode_qr**: Generate QR code or barcode as SVG
- **create_mesh_gradient**: Create SVG mesh gradient definitions
- **text_to_path**: Convert text elements to editable vector paths
- **construct_svg**: Build SVG from structured data
- **apply_boolean**: Boolean path operations (union, difference, intersection, exclusion)
- **path_inset_outset**: Inset or outset paths
- **path_simplify**: Reduce path node count
- **path_clean**: Remove overlapping nodes
- **path_combine**: Merge paths into a single combined path
- **path_break_apart**: Decompose compound paths
- **object_to_path**: Convert objects (rects, circles) to paths
- **optimize_svg**: Clean and optimize SVG structure (remove unused defs, etc.)
- **scour_svg**: Aggressive SVG size reduction by removing metadata
- **measure_object**: Query object dimensions and bounding box
- **query_document**: Run SVG element queries
- **count_nodes**: Count nodes in a path for complexity analysis
- **export_dxf**: Export SVG to CAD DXF format
- **layers_to_files**: Export each layer as a separate SVG file
- **fit_canvas_to_drawing**: Resize canvas to match drawing bounds
- **render_preview**: Generate PNG preview at specified DPI
- **generate_laser_dot**: Create animated SVG laser pointer dot
- **object_raise/lower**: Adjust Z-order of objects
- **set_document_units**: Normalize document coordinate system
Parameters: operation (required Literal), input_path, output_path, object_id,
boolean_type, dpi, format, select_all.
Returns: VectorOperationResult with success, operation, message, data, execution_time_ms.

### inkscape_analysis (Analysis & Validation)
Portmanteau for SVG quality assurance. Operations:
- **quality**: Score SVG quality on criteria (validity, structure, size, styling)
- **statistics**: Count elements, layers, paths, nodes, gradients, fonts
- **validate**: Check SVG structure against schema rules
- **objects**: List all named objects with types and IDs
- **dimensions**: Report document dimensions and viewBox
- **structure**: Output the structural tree of the SVG document
Parameters: operation (required Literal), input_path.
Returns: success, message, data, execution_time_ms, error.

### inkscape_render (Agent Vision Exports)
Portmanteau for rendering previews. Operations:
- **export_preview**: PNG export at specified DPI for agent vision loops
- **export_multi_dpi**: Batch export at multiple DPIs (default 96,192,384)
- **get_document_summary**: Statistics + validation snapshot
Parameters: operation (required Literal), input_path, output_path, dpi, dpi_list.
Returns: success, message, data, execution_time_ms.

### inkscape_fab_art (Fabrication Art)
Portmanteau for laser/DXF/robotics outputs. Operations:
- **list_presets**: List available fab presets
- **batch_dxf_export**: Batch convert SVGs to DXF for laser cutting
- **batch_laser_dots**: Generate alignment/sacrificial laser dot grids
- **gazebo_schematic**: Generate Gazebo simulator schematic overlay
- **stage_for_robotics**: Stage SVG assets for robotics pipeline
- **run_fab_pipeline**: Execute full fab pipeline
Parameters: operation (required Literal), with input_dir, output_dir, dpi, etc.
Returns: success, message, data.

### inkscape_sim_art (Simulation Art)
Portmanteau for UI packs and XR staging. Operations:
- **list_presets**: List available sim art presets
- **svg_pack_batch**: Batch generate SVG icon packs
- **build_icon_sheet**: Compile multiple SVGs into a sprite/atlas sheet
- **audit_svg_pack**: QA check an SVG pack for consistency
- **ai_svg_refine_loop**: AI-assisted SVG refinement loop
- **push_gimp_texture_sheet**: Export to GIMP for texturing
- **stage_resonite_ui**: Stage for Resonite VR UI
- **run_sim_pipeline**: Execute full sim art pipeline
Parameters: operation (required Literal), with template_id, layout, cell_size, dpi.

### generate_heraldry (Heraldic SVG)
Generate preset heraldic SVG compositions. Operation:
- **trumponia**: Generate the 'Empire of Trumponia' heraldic coat of arms
- **custom**: Custom heraldry (future)
Parameters: operation (Literal), output_path.
Returns: success, operation, message, data, execution_time_ms.

### inkscape_fleet (Cross-Repo Handoff)
Portmanteau for inter-MCP-server asset exchange. Operations:
- **push_gimp_raster**: Send SVG to GIMP for raster processing
- **stage_blender_svg**: Stage SVG for Blender import
- **push_unity_sprite**: Export SVG to Unity-compatible sprite format
- **build_layer_atlas**: Combine layers into a single texture atlas
- **run_pipeline**: Execute full cross-repo pipeline
- **list_staging**: List files in the staging directory
Parameters: operation (required Literal), svg_path, png_path, dpi, gimp_url, blender_url.

### list_local_models
Discover Ollama and LM Studio model IDs on localhost.
Returns: success, operation, summary, result.ollama, result.lm_studio.

### intelligent_vector_processing / agentic_inkscape_workflow (Agentic)
SEP-1577 multi-step sampling workflows for batch SVG processing and
autonomous Inkscape operations. Uses ctx.sample() for planning.

## Prompts
The server registers these prompt templates:
- **analyze_svg_document**: Takes an SVG file path, returns analysis prompt
- **optimize_svg_document**: Takes an SVG path + target size, returns optimization prompt
- **convert_svg_document**: Takes input + output + format, returns conversion prompt

## Resources
The server exposes resources for Inkscape status and extension list:
- inkscape://status: Current Inkscape availability and version
- inkscape://extensions: List of installed extensions

## Configuration

### Environment Variables
- INKSCAPE_PATH: Path to Inkscape executable (auto-detected on Windows)
- INKSCAPE_TAURI: Set to '1' when running inside Tauri webview
- MCP_PORT: Port for MCP HTTP transport (default 11028 for backend)
- MCP_HOST: Host for MCP HTTP transport (default 127.0.0.1)
- USE_GIMP_FALLBACK: Set to '1' to enable GIMP fallback for raster ops

### Filesystem
- Allowed directories: configured via InkscapeConfig.allowed_directories
- Temp directory: configurable with cleanup on server shutdown
- Config file: YAML format for persistent settings

## Integration Points
- GIMP MCP bridge: inkscape_fleet push_gimp_raster
- Blender MCP bridge: inkscape_fleet stage_blender_svg
- Unity MCP bridge: inkscape_fleet push_unity_sprite
- World Labs / Resonite: inkscape_sim_art stage_resonite_ui

## Error Handling
All tools return structured dicts with:
- success: bool
- message: human-readable summary
- data: operation-specific payload
- execution_time_ms: server-side timing
- error: error string on failure
- suggestions: recovery actions on failure
- recovery_options: multi-step recovery guidance

## Version
Server version: 2.6.0
FastMCP version: 3.4.2+
Inkscape version: 1.0+ required, 1.2+ recommended for Actions API
