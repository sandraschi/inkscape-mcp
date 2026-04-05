# Inkscape MCP Server — user interaction guide

## What you can ask for

This MCP server drives **Inkscape from the command line**. You describe the outcome (export PDF, trace PNG, simplify paths, check SVG health); the assistant maps that to `inkscape_file`, `inkscape_vector`, `inkscape_analysis`, or `inkscape_system`. **Install Inkscape** on the same machine as the MCP server.

If a tool returns `success: false`, read `message` / `error` and adjust paths, permissions, or timeouts before retrying.

## Getting Started - Your First Vector Graphics Operations

### Quick Start Examples

**Loading and Validating SVG Files:**
- "Load this SVG file and check if it's valid"
- "Open my logo design and show me its dimensions"
- "Validate the SVG structure of this drawing"

**Basic File Operations:**
- "Convert this SVG to PDF format"
- "Save a copy of this design as an EPS file"
- "Get detailed information about this SVG file"

**Simple Vector Editing:**
- "Simplify the paths in this complex drawing"
- "Convert all text to paths in this design"
- "Clean up unnecessary elements in this SVG"

## Understanding Vector Graphics Operations

### File Management - The Foundation

#### Loading and Validating Files
**"Load and validate this SVG file"**
→ The server loads your SVG and checks for structural integrity, reporting any issues found.

**"Check if this drawing is valid SVG"**
→ Performs comprehensive validation including XML syntax, SVG compliance, and path data integrity.

**"Get information about this design file"**
→ Returns file size, dimensions, object count, and basic statistics.

#### Format Conversion
**"Convert this SVG to a high-quality PDF"**
→ Exports to PDF with proper vector scaling and embedded fonts.

**"Export this design as EPS for print production"**
→ Creates EPS file optimized for professional printing workflows.

**"Save this as a compressed SVG"**
→ Optimizes and compresses SVG while preserving all visual elements.

### Vector Editing - The Creative Core

#### Path Operations - The Heart of Vector Graphics

**Path Simplification:**
- "Make this complex illustration web-friendly by simplifying paths"
- "Reduce the file size by simplifying these detailed curves"
- "Optimize this technical drawing for faster loading"

**Path Cleaning:**
- "Remove construction lines and temporary elements"
- "Clean up imported graphics with unnecessary artifacts"
- "Fix corrupted paths in this imported file"

**Path Combination:**
- "Merge these separate shapes into a single path"
- "Combine all the elements in this layer"
- "Unite overlapping shapes for cleaner design"

#### Boolean Operations - Shape Logic

**Union Operations:**
- "Combine these two overlapping circles"
- "Merge the logo elements into a single shape"
- "Unite all the selected objects"

**Difference Operations:**
- "Cut a hole in this shape using that circle"
- "Subtract the inner shape from the outer one"
- "Create a ring by removing the center"

**Intersection:**
- "Keep only the overlapping parts of these shapes"
- "Find the common area between these two designs"
- "Create a new shape from the intersection"

#### Object to Path Conversion

**"Convert all text to editable paths"**
→ Transforms text objects into Bézier curves for full manipulation.

**"Convert these rectangles to paths"**
→ Changes primitive shapes to editable path data.

**"Make this design fully editable by converting everything to paths"**
→ Ensures complete control over all design elements.

### Advanced Vector Operations

#### Bitmap to Vector Conversion

**"Convert this scanned sketch to vector paths"**
→ Uses potrace algorithm to create clean vector outlines.

**"Trace this photograph into vector art"**
→ Intelligent tracing with adjustable parameters for different image types.

**"Create a technical drawing from this blueprint scan"**
→ Optimized for line art and technical illustrations.

#### Barcode and QR Generation

**"Generate a QR code for this URL"**
→ Creates scannable QR code with customizable size and error correction.

**"Make a barcode for product identification"**
→ Generates various barcode formats for inventory and labeling.

**"Create a data matrix code for this information"**
→ Produces 2D barcode for compact data storage.

#### Mesh Gradients

**"Create a complex gradient fill for this background"**
→ Builds multi-stop mesh gradients for photorealistic effects.

**"Add realistic shading to this 3D object"**
→ Applies advanced gradient meshes for depth and dimension.

#### AI-Powered SVG Construction

**"Create an SVG of a professional logo with geometric shapes"**
→ Generates complete SVG from natural language descriptions.

**"Design a technical diagram showing data flow"**
→ Creates structured illustrations from conceptual descriptions.

**"Generate an icon set for a mobile application"**
→ Produces consistent icon families based on themes.

### Document Analysis - Understanding Your Designs

#### Quality Assessment

**"Analyze the quality of this SVG file"**
→ Comprehensive quality metrics including complexity, optimization potential, and performance indicators.

**"Check for potential issues in this design"**
→ Identifies corrupted paths, missing elements, and optimization opportunities.

**"Evaluate this file for web deployment"**
→ Assesses file size, path complexity, and browser compatibility.

#### Statistical Analysis

**"Get detailed statistics about this drawing"**
→ Object counts, path lengths, color usage, and structural metrics.

**"Analyze the complexity of this illustration"**
→ Node counts, path types, layer organization, and editing difficulty assessment.

#### Dimension and Measurement

**"Measure the dimensions of this design"**
→ Canvas size, viewport settings, and coordinate system information.

**"Check the bounding box of this object"**
→ Precise measurements of individual elements and groups.

### System Management - Keeping Everything Running

#### Status and Diagnostics

**"Check if the Inkscape server is working"**
→ System health, Inkscape installation status, and capability verification.

**"Run diagnostics on the vector processing system"**
→ Performance tests, configuration validation, and error detection.

#### Configuration Management

**"Show me the current server settings"**
→ Active configuration, timeouts, and operational parameters.

**"Configure the system for high-performance processing"**
→ Optimize settings for speed, quality, or resource usage.

## Workflow Examples - Real-World Applications

### Logo Design Workflow

**Starting with a Concept:**
1. "Create an SVG logo with geometric shapes and clean lines"
2. "Add text to the logo saying 'TechCorp Solutions'"
3. "Convert the text to paths for consistency"

**Refining the Design:**
4. "Apply boolean operations to combine the shapes"
5. "Simplify the paths to reduce file size"
6. "Clean up any construction artifacts"

**Finalizing for Production:**
7. "Optimize the SVG for web use"
8. "Export to various formats (PNG, PDF, EPS)"
9. "Validate the final design quality"

### Technical Illustration Creation

**Planning the Diagram:**
1. "Create a basic flowchart layout"
2. "Add technical symbols and connectors"
3. "Organize elements into logical groups"

**Detailing the Content:**
4. "Convert all shapes to paths for precision"
5. "Add measurement annotations"
6. "Apply consistent styling across elements"

**Quality Assurance:**
7. "Check path complexity and optimize where needed"
8. "Validate all measurements and alignments"
9. "Export to DXF for CAD integration"

### Web Graphics Optimization

**Preparing Graphics:**
1. "Load the SVG icon set"
2. "Simplify paths for better performance"
3. "Remove unnecessary metadata"

**Optimization Process:**
4. "Apply scour optimization to reduce file size"
5. "Validate SVG structure and fix issues"
6. "Generate preview images at multiple sizes"

**Deployment Preparation:**
7. "Compress SVG files for web delivery"
8. "Check browser compatibility"
9. "Create fallbacks for older browsers"

### Print Production Preparation

**Pre-Press Setup:**
1. "Load the design and check dimensions"
2. "Convert all elements to CMYK color space"
3. "Ensure proper bleed and safe areas"

**Quality Control:**
4. "Validate vector integrity and path data"
5. "Check for hairline strokes and thin elements"
6. "Optimize for the target printing process"

**Final Output:**
7. "Export to PDF/X standard for print"
8. "Generate color proofs and validation reports"
9. "Create cutting paths and registration marks"

## Understanding Server Responses

### Successful Operation Results

When operations complete successfully, you'll receive detailed information:

```json
{
  "success": true,
  "operation": "path_simplify",
  "message": "Successfully simplified paths in drawing.svg",
  "data": {
    "input_path": "drawing.svg",
    "output_path": "drawing_simplified.svg",
    "original_nodes": 1247,
    "simplified_nodes": 423,
    "reduction_percentage": 66.1,
    "processing_time_ms": 890
  },
  "next_steps": ["Consider cleaning the simplified paths", "Validate the result"],
  "context": {
    "operation_details": "Applied 0.1 threshold simplification",
    "quality_preserved": "High"
  }
}
```

### Performance Metrics

**Understanding Timing:**
- **File Operations**: Typically 10-500ms for I/O-bound tasks
- **Vector Operations**: 100-2000ms for computationally intensive work
- **Analysis Operations**: 50-300ms for measurement and validation
- **System Operations**: Under 10ms for status checks

**Resource Usage Indicators:**
- Memory usage for large file processing
- CPU utilization for complex operations
- Disk I/O for file-intensive workflows

### Quality Assessments

**Path Complexity Metrics:**
- Node count reduction after simplification
- File size changes after optimization
- Rendering performance improvements

**Validation Results:**
- Structural integrity checks
- SVG specification compliance
- Cross-browser compatibility scores

## Error Handling and Recovery

### Common Issues and Solutions

#### File Access Problems

**"File not found" errors:**
- Verify the file path is correct
- Check file permissions and accessibility
- Ensure the file isn't locked by another application

**"Permission denied" errors:**
- Check write permissions for output directories
- Verify the application has access to the specified locations
- Consider running with elevated privileges if necessary

#### Inkscape Integration Issues

**"Inkscape not found" errors:**
- Verify Inkscape is installed and in PATH
- Provide explicit path in configuration
- Check Inkscape version compatibility (1.0+ required)

**"Operation timeout" errors:**
- Increase timeout settings for complex operations
- Simplify the operation or break into smaller steps
- Check system resources and close other applications

#### Vector Operation Failures

**"Invalid path data" errors:**
- Validate SVG structure before operations
- Clean corrupted paths first
- Use path repair tools for damaged files

**"Object not found" errors:**
- Verify object IDs exist in the SVG
- Check object naming and selection
- Ensure proper SVG structure and namespaces

### Recovery Strategies

#### Automatic Recovery
The server implements intelligent recovery for common issues:
- **Temporary File Cleanup**: Automatic removal of failed operation artifacts
- **Rollback Operations**: Revert to original state on critical failures
- **Alternative Methods**: Fallback approaches when primary methods fail

#### Manual Recovery Steps

**For Failed Conversions:**
1. Validate input file integrity
2. Try alternative export formats
3. Check Inkscape version compatibility
4. Use manual Inkscape GUI for complex cases

**For Path Operation Issues:**
1. Clean and validate paths first
2. Break complex operations into steps
3. Use path repair tools
4. Simplify complex geometries

## Advanced Usage Patterns

### Batch Processing Workflows

**Processing Multiple Files:**
1. "Process all SVG files in this directory"
2. "Apply path simplification to these 10 drawings"
3. "Convert this folder of SVGs to PDF format"

**Quality Assurance Pipelines:**
1. "Validate all files in the project"
2. "Generate quality reports for the asset library"
3. "Optimize all web graphics for performance"

### Template-Based Operations

**Design Templates:**
1. "Create a new logo based on the company template"
2. "Generate icons using the established style guide"
3. "Apply the brand color scheme to this design"

**Workflow Templates:**
1. "Run the standard web optimization pipeline"
2. "Apply the print production preparation workflow"
3. "Execute the technical illustration quality checks"

### Integration with Other Tools

**Development Workflows:**
- "Prepare SVG icons for the web application"
- "Generate technical diagrams for documentation"
- "Create UI mockups with consistent styling"

**Content Management:**
- "Optimize all SVG assets for the CMS"
- "Generate multiple sizes for responsive design"
- "Create accessibility-compliant graphics"

## Configuration and Customization

### Basic Configuration

**Inkscape Path Setup:**
- "Configure the server to use Inkscape at this path"
- "Auto-detect Inkscape installation"
- "Set custom Inkscape executable location"

**Performance Tuning:**
- "Increase timeout for complex operations"
- "Limit concurrent operations to 2"
- "Optimize for memory-constrained environments"

### Advanced Settings

**Quality Presets:**
- "Use high-quality settings for print production"
- "Apply web optimization defaults"
- "Set technical drawing precision standards"

**Workflow Customization:**
- "Create a custom processing pipeline"
- "Define quality thresholds for different projects"
- "Set up automated backup and versioning"

## Troubleshooting Guide

### Performance Issues

**Slow Operations:**
- Check system resources (CPU, memory)
- Reduce concurrent operation limits
- Break large files into smaller operations
- Use simpler algorithms for draft work

**Memory Problems:**
- Process files individually instead of batch
- Close other memory-intensive applications
- Increase system RAM if possible
- Use streaming processing for large files

### Quality Issues

**Poor Tracing Results:**
- Adjust tracing parameters for image type
- Pre-process images (contrast, cleaning)
- Use different tracing algorithms
- Manual cleanup for critical results

**Export Problems:**
- Check target format compatibility
- Verify color space and profiles
- Ensure proper DPI settings
- Test with different export options

### Compatibility Issues

**Browser Display Problems:**
- Validate SVG structure and namespaces
- Remove Inkscape-specific extensions
- Use scour optimization for web deployment
- Test across target browsers

**Application Import Issues:**
- Check version compatibility
- Export to intermediary formats
- Simplify complex path data
- Remove advanced features not supported

## Best Practices and Tips

### File Organization

**Project Structure:**
- Keep source SVGs in dedicated directories
- Use consistent naming conventions
- Maintain backup copies of important files
- Organize by project and asset type

**Version Control:**
- Commit SVG files to Git repositories
- Use meaningful commit messages
- Track changes to critical designs
- Maintain design history and evolution

### Performance Optimization

**File Size Management:**
- Simplify paths regularly during development
- Remove unnecessary metadata and comments
- Use efficient grouping and layering
- Optimize before final deployment

**Workflow Efficiency:**
- Plan operations to minimize file I/O
- Use batch processing for repetitive tasks
- Automate quality checks and validations
- Maintain consistent processing pipelines

### Quality Assurance

**Regular Validation:**
- Check file integrity after major operations
- Validate before important exports
- Test compatibility across target platforms
- Maintain quality standards throughout projects

**Testing Strategies:**
- Test operations on sample files first
- Validate results against requirements
- Compare automated vs manual results
- Document successful workflows for reuse

## Integration Examples

### Development Workflow Integration

**Web Development:**
- "Optimize all SVG icons for the React application"
- "Generate multiple sizes for responsive images"
- "Create sprite sheets from individual icons"

**Documentation:**
- "Generate technical diagrams for the API docs"
- "Create flowcharts for process documentation"
- "Optimize illustrations for PDF generation"

### Content Management Systems

**Asset Preparation:**
- "Process all uploaded SVG files for the CMS"
- "Generate preview thumbnails for the media library"
- "Validate and optimize user-uploaded graphics"

**Automated Processing:**
- "Apply branding to all marketing graphics"
- "Generate localized versions of graphics"
- "Create accessibility-compliant alternatives"

### Design System Maintenance

**Consistency Enforcement:**
- "Apply the design system colors to all icons"
- "Ensure consistent stroke widths across components"
- "Validate spacing and alignment standards"

**Asset Generation:**
- "Generate icon variations for different states"
- "Create component library graphics"
- "Produce documentation examples automatically"

## Long-form tutorials (step patterns)

### Tutorial A — Inspect an SVG before editing

1. Ask to **load** or **validate** the file (`inkscape_file`, `operation`: `load` or `validate`, `input_path`: absolute or workspace path).
2. If valid, ask for **info** to capture width/height and size.
3. Optionally run **statistics** (`inkscape_analysis`) to summarize the document.
4. Only then request **convert** or **path_simplify** so failures are easier to attribute.

### Tutorial B — Raster logo to PDF handoff

1. Put the PNG/JPEG on disk; call **trace_image** (`inkscape_vector`) with `input_path` and `output_path` ending in `.svg`.
2. Open-result check: **validate** the new SVG.
3. **convert** to PDF (`inkscape_file`) with explicit `format`: `pdf` and a new `output_path`.
4. If the PDF is empty or clipped, re-run **info** on the SVG and adjust canvas in Inkscape manually once, then automate again.

### Tutorial C — Batch-style prompts (sequential, not parallel unless user confirms)

1. List targets: e.g. `icons/*.svg`.
2. For each file: **validate** → **path_simplify** (if needed) → **render_preview** for a quick raster sanity check.
3. Aggregate success/failure tables for the user; do not hide stderr-equivalent messages returned in JSON.

### Tutorial D — QR code asset

1. Choose payload (URL or text); call **generate_barcode_qr** with `barcode_data` and `output_path` `.svg`.
2. **convert** to PNG if a raster deliverable is required.

### Tutorial E — When Inkscape is missing

1. Ask the user to install Inkscape or provide the full path to `inkscape.exe` / binary.
2. Retry **status** (`inkscape_system`) until `success` shows Inkscape available.
3. If the host blocks subprocesses, stop: MCP cannot drive Inkscape without CLI access.

### Tutorial F — Extension commands

1. **list_extensions** to discover IDs.
2. **execute_extension** only when the user explicitly wants that extension and understands side effects.
3. Log outputs verbatim for auditability.

### Tutorial G — Boolean cleanup

1. Ensure objects have stable IDs if the tool requires `object_ids`; otherwise use workflow guidance from the tool response.
2. Run **apply_boolean** with explicit `operation_type` (`union`, `difference`, `intersection`, etc.—match server expectations).
3. Save via **convert** or downstream pipeline; verify geometry with **dimensions**.

### Tutorial H — Document units for CNC / mm workflows

1. **set_document_units** with `units` such as `mm` when supported.
2. Re-query **info** / **dimensions** to confirm scale.

### Phrasing library (copy-friendly)

- "Run inkscape_system status and then inkscape_file validate on `X`."
- "If validate passes, inkscape_file convert `X` to `Y.pdf` with format pdf."
- "Trace `scan.png` to `out.svg` with inkscape_vector trace_image."
- "Simplify paths: inkscape_vector path_simplify on `busy.svg` with a reasonable threshold, write `busy.simple.svg`."

### Safety checklist

- Confirm overwrite targets.
- Use absolute paths when the client is unclear about cwd.
- Quote Windows paths with spaces when typing JSON parameters.

---

**Closing note**: Prefer small, verifiable steps. If the server returns `not implemented` for an operation, choose another approach or document the gap for manual Inkscape work.

## Scenario catalog (natural language → tools)

Each item below is a pattern you can paste or paraphrase. Replace paths with real files.

1. **Health check**: "Run inkscape_system with operation status; confirm Inkscape is available before we touch files."
2. **Quick SVG sanity**: "Use inkscape_file validate on `C:\work\ui.svg` and report success or errors."
3. **Dimensions only**: "inkscape_file info on `logo.svg` — I need pixel width and height."
4. **PDF export**: "Convert `diagram.svg` to `diagram.pdf` with inkscape_file convert; format pdf."
5. **EPS handoff**: "Export `sign.svg` to `sign.eps` if the server lists eps support; otherwise suggest an alternative."
6. **PNG preview**: "Generate a PNG preview of `mockup.svg` via inkscape_vector render_preview; pick a sensible dpi."
7. **Trace scan**: "Trace `scan.jpg` to `scan.svg` using trace_image; warn me if the output is huge."
8. **Simplify for web**: "path_simplify `hero.svg` to `hero.light.svg` with a moderate threshold."
9. **Clean imported art**: "path_clean on `imported.svg` saving to `imported.clean.svg`."
10. **QR for URL**: "Create `qr.svg` encoding `https://example.com` with generate_barcode_qr."
11. **Document stats**: "inkscape_analysis statistics on `poster.svg`."
12. **Validate before print**: "validate on `card.svg`, then convert to pdf if valid."
13. **Measure an object**: "measure_object on `tech.svg` for object id `path123` (adjust id to match file)."
14. **Count nodes**: "count_nodes for `ornament.svg` to see if simplification is warranted."
15. **Z-order tweak**: "Raise object `layer1` with object_raise; write to `raised.svg`."
16. **Lower background**: "object_lower for `bg_rect` in `scene.svg`."
17. **Set mm units**: "set_document_units to mm on `cnc.svg`, output `cnc.mm.svg`."
18. **List formats**: "list_formats — what can we export to?"
19. **Server version**: "inkscape_system version for debugging."
20. **Diagnostics**: "Run diagnostics when exports silently fail."
21. **Help text**: "inkscape_system help — summarize tools for the user in plain language."
22. **Show config**: "Display current MCP-related configuration via config operation."
23. **Extensions list**: "list_extensions — I need to know if a bundled extension exists."
24. **Run named extension**: "execute_extension only after I confirm the extension id and parameters."
25. **Dimensions analysis**: "inkscape_analysis dimensions on `banner.svg`."
26. **Re-validate after edit**: "After any boolean, validate the output svg again."
27. **Sequential batch**: "For each svg in this folder (user lists them), validate then render_preview to a sibling png."
28. **Failure triage**: "If convert fails, run diagnostics then status, then report the error field verbatim."
29. **Large file caution**: "Before simplify on a 5MB svg, warn about time and offer to proceed or split work."
30. **Local models**: "list_local_models — any local LLM for optional sampling workflows?"

## Parameter cheat sheet (user-facing)

- **input_path**: existing file the tool reads.
- **output_path**: where to write when the operation produces a file.
- **format**: export format string (e.g., `pdf`, `png`) for convert.
- **operation**: the portmanteau branch name; spelling must match server expectations.
- **operation_type**: for booleans, the boolean mode string supported by the server.
- **object_ids**: list of SVG id attributes when targeting specific elements.
- **threshold**: simplification aggressiveness; higher often removes more points.
- **dpi**: rasterization resolution for previews/exports that honor it.

## What not to expect

- The MCP server is not a full Inkscape GUI. Some niche dialog-only features may be unavailable.
- Perfect print color fidelity may still need human proofing.
- Automatic layout or brand-new illustration from vague prompts may require sampling tools or manual design work.

## Collaboration tips

Ask the user for: Inkscape version, OS, example file path, and the exact error JSON when something breaks. Offer minimal repro steps (one svg, one operation) before complex pipelines.

## Practice dialogue (assistant behavior)

User: "Make this svg smaller for web." Assistant: "I will run info to see dimensions and node complexity, then suggest path_simplify or scour steps with your approval." User: "OK." Assistant: *calls tools in order and reports file sizes before/after.*

## Kids gloves for destructive ops

Deleting, overwriting, or boolean-combining shared assets should be confirmed. Mention backups when touching production paths.

## After successful export

Suggest quick visual verification in a viewer (browser, Inkscape, or PDF reader) especially when fonts or clip paths are involved.

## If the assistant hallucinates a tool name

Correct to the four portmanteau tools plus `list_local_models` and any optional agentic tools the session actually registered. Use `help` output as ground truth when unsure.

## Desktop vs MCP

Remind users they can always finish edge cases in Inkscape interactively; MCP accelerates repeatable CLI-safe tasks.

## Revision hygiene

When sharing prompts or examples publicly, scrub personal paths and secrets from `barcode_data` or embedded URLs.

## Extra walkthrough — print shop handoff

Start with `validate` on the customer SVG. Run `info` to confirm physical size if `viewBox` and units are unclear. Export PDF with `convert`; if the client needs CMYK, state that Inkscape RGB workflows may require a prepress step outside MCP. Keep the original SVG alongside derived PDFs. If fonts are missing, stop and ask the customer to outline text in Inkscape before automation proceeds.

## Extra walkthrough — web icon pipeline

Validate each icon SVG. `path_simplify` only if file size is excessive. `render_preview` at 96 dpi to spot visual regressions. Prefer keeping SVG for delivery; generate PNG only when the target stack requires raster. Document which simplification threshold was used so the team can reproduce results.

## Extra walkthrough — recovering from a bad boolean

If the output looks empty, re-run `validate` on the source, check `object_ids`, and try a smaller selection set. Keep intermediate files (`before.svg`, `after.svg`) so you can diff in version control or Inkscape’s XML editor.

## Quick FAQ

**Q: Can MCP edit text content?**  
**A:** Only through operations exposed by the server; otherwise edit in Inkscape.

**Q: Does it run headless?**  
**A:** It uses the Inkscape CLI; a GUI is not required for supported actions.

**Q: Can I trust automatic measurements?**  
**A:** Cross-check critical dimensions manually for contractual work.

## Voice and tone

Ask for concrete paths, desired output format, and whether overwriting is acceptable. Short confirmations save time compared to long capability speeches. When unsure, run `help` or `list_formats` once instead of guessing operation names from memory.

## One-page summary

You have four main Inkscape tool groups plus optional helpers. File ops handle IO and export listing. Vector ops handle geometry and previews. Analysis reads metrics. System tells you whether Inkscape is wired up. Start with **status** and **validate**, end with **convert** or **render_preview** when delivering artifacts.

See `assets/prompts/examples.json` in the MCPB bundle for over one hundred worked parameter examples you can echo or adapt when training teammates on how to phrase requests.

Also read `configuration.md` and `troubleshooting.md` in the same folder when Claude Desktop surfaces configuration panes or when you need copy-paste env snippets for Inkscape path detection on Windows versus macOS versus Linux hosts. Keep screenshots in `assets/screenshots/` as visual anchors when onboarding designers who rarely read JSON or Markdown prompts without pictures in practice today.
