# Inkscape MCP — User Guide and Tutorials

## Getting Started

Inkscape MCP Server gives an AI agent complete access to Inkscape's vector graphics
capabilities. Before using any tool, check the Inkscape connection by calling
inkscape_system with operation "status". This returns the Inkscape version, installation
path, and confirms the CLI is reachable. If Inkscape is not found, the server attempts
auto-detection on standard install paths. On Windows it checks Program Files and
the PATH. On Linux it checks common snap, flatpak, and apt locations.

## File Operations Tutorial

Loading an SVG file for analysis: call inkscape_file with operation "info" and the
input_path set to your SVG file. This returns the document dimensions, viewBox, layer
count, element count, and basic metadata. For a deeper analysis, use inkscape_analysis
with operation "statistics" to get a full breakdown of element types, path counts,
node counts, gradient and font usage.

To convert an SVG to PNG: use inkscape_file with operation "convert", set format to "png",
and provide an input_path and output_path. The default DPI is 96 for screen resolution.
For print quality, set dpi to 300. For web display, 72 DPI is sufficient. The conversion
routes through Inkscape's command-line export which supports SVG 1.1 full feature set
including filters, masks, gradients, and text.

To save an edited SVG: use inkscape_file with operation "save". This persists in-memory
or buffered changes to disk. The output_path must be within the configured allowed
directories for security.

## Vector Editing Tutorial

The inkscape_vector portmanteau is the most feature-rich tool with 23+ operations.
Here is a guide to common workflows:

Raster to Vector Conversion: Use operation "trace_image" with input_path pointing to a
PNG or JPEG bitmap. Inkscape uses potrace internally for single-bitmap tracing. The
output is a clean SVG with filled paths representing the image content. This is ideal
for converting logos, signatures, and line art to scalable vector format.

Boolean Path Operations: Use operation "apply_boolean" with boolean_type set to one of
"union", "difference", "intersection", or "exclusion". Provide an input_path to an SVG
with multiple overlapping paths. The server selects all editable paths in the document
and applies the boolean operation via Inkscape's path-union, path-difference,
path-intersection, or path-exclusion actions. Results are saved to the output_path.

Path Simplification: Use operation "path_simplify" to reduce node count on complex paths.
This is useful before laser cutting or CNC routing where too many nodes cause jerky
machine motion. The simplification threshold is managed by Inkscape's internal algorithm.
Use operation "count_nodes" before and after to measure the reduction.

Object Measurement: Use operation "measure_object" with object_id set to the SVG element
id. Returns the bounding box dimensions, position, rotation, and path length if applicable.
This is useful for verifying layout constraints before fabrication.

Canvas Fitting: Use operation "fit_canvas_to_drawing" to resize the document canvas to
match the exact bounding box of all content. This eliminates excess white space before
export. After fitting, use inkscape_analysis with operation "dimensions" to verify.

## Analysis and Validation Tutorial

For quality assurance workflows, use inkscape_analysis. Operation "quality" scores an
SVG document on a 0-100 scale across five criteria: structural validity, file size
efficiency, element organization, styling consistency, and metadata quality. Each
criterion is scored independently and the overall score is the weighted average.

Operation "validate" checks the SVG against structural rules: valid XML syntax,
correct namespace declarations, properly closed tags, valid viewBox attribute, and
non-zero dimensions. This catches common export issues from other tools.

Operation "structure" outputs the hierarchical tree of the SVG document showing
the parent-child relationships of groups, layers, and elements. Use this to understand
document organization before making structural edits.

## Fabrication Art Tutorial

For laser cutting and CNC workflows, use inkscape_fab_art. Operation "list_presets"
shows available fabrication presets including material types (plywood, acrylic, cardboard)
and corresponding power/speed settings. Operation "batch_dxf_export" converts multiple
SVG files to DXF format for import into LightBurn, LaserGRBL, or other laser software.
Each SVG is processed individually and output files are named to match inputs.

Operation "batch_laser_dots" generates alignment and calibration grids. These are small
laser-fired dots used for material alignment, focus distance calibration, and bed
levelling checks. The output is a single SVG with a grid of circle elements at
configurable spacing.

Operation "gazebo_schematic" generates a schematic overlay SVG suitable for the Gazebo
simulator's visual layers. This bridges 2D vector design with robotic simulation
environments.

## Simulation Art Tutorial

For game UI and XR workflows, use inkscape_sim_art. Operation "svg_pack_batch" generates
multiple SVG icons from a template. Each icon is created with consistent canvas size,
stroke width, and color palette. Use the template_id parameter to select the base style.

Operation "build_icon_sheet" compiles individual SVG icons into a single sprite sheet
atlas. This is required for game engines (Unity, Godot) that batch UI elements into
a single texture. Set the layout parameter to "2x2", "4x4", etc. and cell_size to the
icon dimensions in pixels.

Operation "push_gimp_texture_sheet" sends the generated sheet to a GIMP MCP server for
texture baking. This requires gimp_url to be configured pointing to the GIMP server.
Operation "stage_resonite_ui" stages the assets for Resonite VR import.

## Cross-Repo Workflows

The inkscape_fleet tool enables inter-MCP-server handoffs. A typical workflow:
1. Create a design in Inkscape MCP as SVG
2. Call inkscape_fleet with operation "push_gimp_raster" to send SVG to GIMP for raster
   effects and texturing
3. Use inkscape_fleet operation "stage_blender_svg" to prepare the SVG for 3D extrusion
   in Blender
4. The final textured 3D model can be imported into Unity, Godot, or Resonite

For full pipeline execution, use operation "run_pipeline" which chains all steps.
Use operation "list_staging" to see all files in the cross-repo staging area.

## Heraldry Tutorial

The generate_heraldry tool creates preset heraldic SVG compositions. Use operation
"trumponia" to generate the 'Empire of Trumponia' coat of arms featuring two asses
rampant in a high-contrast SOTA heraldry style with gold, crimson, and cyan colours.
The output is a complete SVG file saved to the specified output_path.

## Using Agentic Workflows

For complex multi-step tasks, use the agentic_inkscape_workflow tool. This uses FastMCP
sampling (SEP-1577) to let the LLM plan and execute a sequence of tool calls
autonomously. Describe your goal in natural language: "Optimize all SVGs in the
designs folder to under 50KB each and export as PDF". The LLM will probe the server's
capabilities, plan the steps, and execute them.

For intelligent batch SVG processing, use intelligent_vector_processing with a
processing_goal and a list of documents to process. The LLM decides which operations
apply to each document based on its characteristics.

## Common Recipes

Recipe 1: Import a bitmap logo, trace it to SVG, and export as PDF for print.
Steps: inkscape_vector(operation="trace_image") to convert, then
inkscape_file(operation="convert", format="pdf") to export.

Recipe 2: Open an SVG, measure an element, simplify its path, then fit canvas.
Steps: inkscape_analysis(operation="statistics"),
inkscape_vector(operation="measure_object", object_id="..."),
inkscape_vector(operation="path_simplify"),
inkscape_vector(operation="fit_canvas_to_drawing"),
inkscape_file(operation="save").

Recipe 3: Batch convert all SVGs in a folder to DXF for laser cutting.
Steps: inkscape_fab_art(operation="batch_dxf_export", input_dir="...",
output_dir="..."), then inspect outputs in the output directory.

Recipe 4: Generate a QR code SVG, analyze its quality, and export PNG preview.
Steps: inkscape_vector(operation="generate_barcode_qr", barcode_data="..."),
inkscape_analysis(operation="quality"),
inkscape_render(operation="export_preview", dpi=192).

Recipe 5: Full cross-repo pipeline from SVG to GIMP to Blender.
Steps: inkscape_file(operation="save"),
inkscape_fleet(operation="push_gimp_raster"),
inkscape_fleet(operation="stage_blender_svg"),
inkscape_fleet(operation="run_pipeline").

## Troubleshooting

If Inkscape is not found: set the INKSCAPE_PATH environment variable to the full path
of the Inkscape executable. On Windows this is typically
C:\Program Files\Inkscape\bin\inkscape.exe. On Linux try /usr/bin/inkscape or
/snap/bin/inkscape.

If export fails: verify the output directory exists and is writable. Check that the
format is in the supported list from inkscape_file(operation="list_formats").
PDF export requires Inkscape 1.0+ with libcairo support.

If boolean operations fail: ensure the SVG contains at least two overlapping paths.
Text elements and groups must be converted to paths first using
inkscape_vector(operation="text_to_path" or "object_to_path").

If the Tauri desktop app shows a blank screen: check that the backend is running on
port 11028 and the CSP includes tauri://localhost and http://tauri.localhost in
connect-src. The INKSCAPE_TAURI environment variable should be set to "1".
