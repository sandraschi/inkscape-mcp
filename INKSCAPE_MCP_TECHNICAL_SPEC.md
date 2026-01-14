# Inkscape MCP Server - Technical Specification

## Overview

The Inkscape MCP (Model Context Protocol) Server provides comprehensive vector graphics editing capabilities through a standardized API. Unlike traditional image editors that work with pixels, Inkscape is a vector graphics editor that uses mathematical equations to define shapes, allowing for infinite scalability and professional-quality graphics.

**Key Architecture:**
- **FastMCP 2.14.1+ Framework**: Modern MCP implementation with portmanteau design pattern
- **4 Portmanteau Tools + Extension System**: Consolidated operations + 200+ Inkscape extensions
- **39 Core Operations + Unlimited Extensions**: Comprehensive vector graphics workflow coverage
- **Stdio-based Communication**: JSON-RPC over stdin/stdout for AI agent integration
- **4 Specialized Unity/VRChat Extensions**: AG Series for game development pipelines

## Portmanteau Tool Architecture

Instead of 50+ individual tools, operations are consolidated into 4 master tools based on functional domains:

### 1. inkscape_file - File Operations
**Category**: File Management
**Operations**: 6 total
**Purpose**: Load, save, convert, and validate SVG files

#### Operations:
- `load`: Load SVG file and validate structure
- `save`: Save SVG with specific options
- `convert`: Convert between vector formats (SVG, PDF, EPS, AI, CDR)
- `info`: Get file metadata and statistics
- `validate`: Validate SVG structure and syntax
- `list_formats`: Show supported export formats

#### Technical Implementation:
```python
# Example CLI usage
inkscape --query-width input.svg  # Get width
inkscape --export-filename=output.pdf --export-type=pdf input.svg
```

### 2. inkscape_vector - Advanced Vector Operations
**Category**: Vector Graphics Processing
**Operations**: 23 total
**Purpose**: Professional vector editing and generation

#### Core Operations (with Prerequisites):

**🔍 PREREQUISITE**: For operations requiring `object_id`, the AI **MUST** first call `inkscape_analysis("objects")` to discover actual object IDs. AI agents often hallucinate IDs like "path1" or "rect1".

- `trace_image`: Convert raster images to vector paths using potrace
- `generate_barcode_qr`: Create QR codes and barcodes
- `create_mesh_gradient`: Generate complex gradient meshes
- `text_to_path`: Convert text to editable vector paths
- `construct_svg`: Generate SVG from text descriptions (AI-powered)
- `apply_boolean`: Boolean operations (union, difference, intersection, exclusion) - **REQUIRES object_ids OR select_all=true**
- `path_inset_outset`: Dynamic path offset for borders/shadows - **REQUIRES object_ids**
- `path_simplify`: Reduce path complexity while preserving shape - **REQUIRES object_ids OR select_all=true**
- `path_clean`: Remove unnecessary elements and metadata
- `path_combine`: Merge multiple paths into compound paths - **REQUIRES object_ids**
- `path_break_apart`: Separate compound paths into individual elements - **REQUIRES object_ids**
- `object_to_path`: Convert primitive shapes to editable Bezier curves - **REQUIRES object_ids OR select_all=true**
- `optimize_svg`: Clean and optimize SVG XML structure
- `scour_svg`: Remove metadata and optimize for web deployment
- `measure_object`: Query object dimensions and properties - **REQUIRES object_ids from inkscape_analysis.objects**
- `query_document`: Get comprehensive document statistics
- `count_nodes`: Count nodes in paths for complexity analysis - **REQUIRES object_ids**
- `export_dxf`: Export to CAD formats (DXF for AutoCAD, SolidWorks)
- `layers_to_files`: Export each layer as separate SVG file
- `fit_canvas_to_drawing`: Resize canvas to match content bounds
- `render_preview`: Generate PNG previews of SVG content
- `generate_laser_dot`: Create animated laser pointer (entertainment feature)

#### Technical Implementation (CORRECTED):
```bash
# ✅ CORRECT: Boolean operations with complete action chain
inkscape --actions="select-all;selection-union;export-filename:output.svg;export-do" input.svg

# ✅ CORRECT: Path simplification (uses document threshold, no direct parameter)
inkscape --actions="select-by-id:path1;selection-simplify;export-filename:output.svg;export-do" input.svg

# ❌ WRONG: selection-simplify does not take numeric parameter directly
# inkscape --actions="select-by-id:path1;selection-simplify:0.1" input.svg

# ✅ CORRECT: DXF export with proper flags
inkscape --export-filename=output.dxf --export-type=dxf input.svg

# ✅ CORRECT: Layer export (requires --export-layers flag)
inkscape --export-layers --export-filename-base=output_ input.svg
```

**CRITICAL**: All `--actions` chains MUST end with `export-filename:output.svg;export-do` or changes are lost to RAM only.

### 3. inkscape_analysis - Document Analysis
**Category**: Quality Assurance & Inspection
**Operations**: 6 total
**Purpose**: Analyze and validate SVG documents

#### Operations:
- `quality`: Assess SVG quality metrics (complexity, optimization potential)
- `statistics`: Generate comprehensive document statistics
- `validate`: Check SVG syntax and structure compliance
- `objects`: List all objects in document with properties
- `dimensions`: Get document and viewport dimensions
- `structure`: Analyze document hierarchy and relationships

#### Technical Implementation:
```bash
# Query document dimensions
inkscape --query-width input.svg     # Canvas width
inkscape --query-height input.svg    # Canvas height
inkscape --query-x input.svg         # Viewport X offset
inkscape --query-y input.svg         # Viewport Y offset
```

### 4. inkscape_system - System Management
**Category**: Server Administration
**Operations**: 5 total
**Purpose**: Manage server state and configuration

#### Operations:
- `status`: Get server and Inkscape installation status
- `help`: Display available operations and usage
- `diagnostics`: Run health checks and performance tests
- `version`: Show version information
- `config`: View/modify server configuration

## CLI Integration Details

### Inkscape Actions API (--actions flag) - CRITICAL STATEFUL BEHAVIOR
**⚠️ CRITICAL**: Inkscape's `--actions` API is **stateful within a single command execution**. Operations must follow a strict "Select → Modify → Persist" chain or they will silently fail.

**🚀 PERFORMANCE CRITICAL**: Always use `--batch-process` flag to maintain 50MB memory footprint. Without it, Inkscape initializes full GTK/display context, bloating memory to 500MB+ and potentially hanging in server environments (GitHub Actions, headless VPS, containers).

#### The Action-Chain Pattern (MANDATORY)
Every vector modification MUST follow this internal protocol:

1. **Targeting**: `select-by-id:object_id` or `select-all` (establishes selection state)
2. **Modification**: The actual operation (e.g., `selection-union`, `selection-simplify`)
3. **Persistence**: `export-filename:output.svg` followed by `export-do` (saves changes to disk)

```bash
# ❌ WRONG - Stateless assumption (will silently do nothing)
inkscape --actions="selection-union" input.svg

# ✅ CORRECT - Stateful chain (selection → operation → save)
inkscape --actions="select-all;selection-union;export-filename:output.svg;export-do" input.svg

# ✅ CORRECT - Specific object selection
inkscape --actions="select-by-id:rect1,path2;selection-union;export-filename:output.svg;export-do" input.svg

# Syntax: --actions="action1:param1,param2;action2:param1;action3"
```

#### Common Actions Used:
- **Selection Management**:
  - `select-by-id:object_id`        # Select specific SVG objects (comma-separated)
  - `select-all`                    # Select everything in document
  - `select-clear`                  # Clear current selection

- **Boolean Operations**:
  - `selection-union`               # Boolean union of selected objects
  - `selection-difference`          # Boolean difference operation
  - `selection-intersection`        # Boolean intersection
  - `selection-exclusion`           # Boolean exclusion (XOR)

- **Path Operations**:
  - `selection-simplify`            # Simplify selected paths (uses document threshold)
  - `object-to-path`                # Convert shapes to editable paths
  - `selection-break-apart`         # Break compound paths into individual paths

- **Export Operations** (MANDATORY for persistence):
  - `export-filename:output.png`    # Set export destination (REQUIRED)
  - `export-dpi:300`               # Set export resolution
  - `export-do`                    # Execute the export (REQUIRED)

### Query Functions (--query-* flags)
Real-time property inspection:

```bash
inkscape --query-width input.svg           # Object/SVG width
inkscape --query-height input.svg          # Object/SVG height
inkscape --query-x input.svg               # Object X position
inkscape --query-y input.svg               # Object Y position
inkscape --query-id input.svg              # Object ID
inkscape --query-all input.svg             # All object properties
```

### Export Formats Supported
- **SVG**: Native Inkscape format (compressed/uncompressed)
- **PDF**: Vector PDF with layers and text preservation
- **EPS**: Encapsulated PostScript for print workflows
- **AI**: Adobe Illustrator format compatibility
- **CDR**: CorelDRAW format support
- **DXF**: CAD exchange format (AutoCAD, SolidWorks)
- **PNG**: Raster preview with configurable DPI
- **PS**: PostScript for legacy printing
- **WMF/EMF**: Windows vector formats
- **XAML**: Microsoft XAML for WPF/Silverlight

## AI Agent Integration

### Conversational Response Structure
All operations return structured responses following FastMCP 2.14.1+ standards:

```json
{
  "success": true,
  "operation": "trace_image",
  "summary": "Successfully traced bitmap to vector paths",
  "result": {
    "data": {
      "input_path": "sketch.png",
      "output_path": "vector.svg",
      "method": "potrace",
      "nodes_created": 247
    },
    "execution_time_ms": 1250.50
  },
  "next_steps": ["Consider simplifying the path for web optimization"],
  "context": {
    "operation_details": "Used potrace algorithm with default parameters"
  },
  "suggestions": ["optimize_svg", "render_preview"],
  "follow_up_questions": ["What DPI should the preview be?"]
}
```

### Error Handling
Comprehensive error reporting with recovery suggestions:

```json
{
  "success": false,
  "operation": "trace_image",
  "message": "Bitmap tracing failed: invalid image format",
  "data": {},
  "execution_time_ms": 45.20,
  "error": "ValueError",
  "recovery_options": [
    "Ensure input is a valid PNG/JPG/BMP file",
    "Check file permissions",
    "Try with a different image format"
  ]
}
```

## Inkscape Extension System

### Overview

**v1.2.0 Enhancement**: Complete integration with Inkscape's extension ecosystem. The server now provides access to the 200+ Inkscape extensions that power professional vector workflows, including specialized tools for Unity/VRChat development.

### Extension Architecture

#### Extension Discovery
- **Cross-platform directories**: Automatic scanning of standard Inkscape extension locations
- **XML parsing**: Robust `.inx` file parsing for extension metadata and parameter schemas
- **Dynamic registration**: Runtime extension loading with parameter validation
- **Hot-reload support**: Extensions can be added/removed without server restart

#### Extension Execution
- **CLI integration**: Native `--extension=extension_id` parameter support
- **Parameter injection**: Automatic mapping from MCP parameters to extension format
- **Async processing**: Non-blocking execution with configurable timeouts
- **Error isolation**: Sandboxed execution with comprehensive error reporting

### MCP Extension Tools

#### inkscape_system Extension Operations

**list_extensions**: Discover available extensions
```python
result = inkscape_system("list_extensions")
# Returns: [{"id": "org.project_ag.batch_trace", "name": "AG Batch Trace", "category": "project_ag", "parameters": [...]}]
```

**execute_extension**: Execute any Inkscape extension
```python
result = inkscape_system("execute_extension",
                        extension_id="org.project_ag.batch_trace",
                        extension_params={"input_dir": "/path/to/images", "colors": 8},
                        input_file="input.svg",
                        output_file="output.svg")
```

### Built-in Unity/VRChat Extensions (AG Series)

#### AG Batch Trace (`org.project_ag.batch_trace`)
**Purpose**: Convert AI-generated bitmaps to optimized SVG vectors
**Parameters**:
- `input_dir`: Source directory containing bitmap files
- `output_dir`: Destination directory for SVG output
- `colors`: Maximum colors for quantization (2-256)
- `simplify`: Enable path simplification (boolean)

**CLI Execution**:
```bash
inkscape --extension=org.project_ag.batch_trace --input_dir=/input --output_dir=/output --colors=8 --simplify=true
```

#### AG Unity Prep (`org.project_ag.unity_prep`)
**Purpose**: Prepare SVGs for Unity UI import with coordinate normalization
**Parameters**:
- `flatten_groups`: Remove all group nesting (boolean)
- `reset_coordinates`: Reset viewBox to origin (boolean)
- `optimize_paths`: Simplify path complexity (boolean)
- `remove_metadata`: Strip Inkscape-specific metadata (boolean)

**CLI Execution**:
```bash
inkscape --extension=org.project_ag.unity_prep --flatten_groups=true --reset_coordinates=true --optimize_paths=true --remove_metadata=true input.svg
```

#### AG Layer Animation (`org.project_ag.layer_animation`)
**Purpose**: Create CSS-animated SVGs from layers for Unity web UI
**Parameters**:
- `duration`: Animation cycle duration in seconds (0.1-60.0)
- `loop`: Enable infinite looping (boolean)
- `easing`: CSS easing function (ease, linear, ease-in, ease-out, ease-in-out)

**CLI Execution**:
```bash
inkscape --extension=org.project_ag.layer_animation --duration=2.0 --loop=true --easing=ease-in-out input.svg
```

#### AG Color Quantize (`org.project_ag.color_quantize`)
**Purpose**: Reduce color palettes for performance while maintaining brand consistency
**Parameters**:
- `max_colors`: Maximum colors in palette (2-256)
- `palette`: Custom hex color palette (comma-separated)
- `dither`: Enable dithering (boolean)

**CLI Execution**:
```bash
inkscape --extension=org.project_ag.color_quantize --max_colors=8 --palette="#FF0000,#00FF00,#0000FF" input.svg
```

### Extension Development

#### Creating Custom Extensions
Extensions consist of two files in the extensions directory:

**extension_example.inx** (XML metadata):
```xml
<inkscape-extension xmlns="http://www.inkscape.org/namespace/inkscape/extension">
    <name>Custom Extension</name>
    <id>org.example.custom</id>
    <param name="param1" type="string" gui-text="Parameter 1">default</param>
    <effect>
        <object-type>all</object-type>
        <effects-menu><submenu>Project AG</submenu></effects-menu>
    </effect>
    <script>
        <command location="inx" interpreter="python">extension_example.py</command>
    </script>
</inkscape-extension>
```

**extension_example.py** (Python logic):
```python
import inkex

class CustomExtension(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--param1", type=str, help="Parameter 1")

    def effect(self):
        # Extension logic using inkex library
        param1 = self.options.param1
        # Process SVG document...

if __name__ == '__main__':
    CustomExtension().run()
```

### Configuration

Extensions are configured in `config.yaml`:
```yaml
extension_config:
  enable_extensions: true
  extension_dirs:
    - "~/.config/inkscape/extensions"
    - "./extensions"
  disabled_extensions:
    - "org.example.problematic"
  config:
    org.project_ag.batch_trace:
      default_colors: 8
      simplify_paths: true
```

### Performance Characteristics

- **Extension Discovery**: < 1 second for typical extension sets
- **Extension Execution**: Variable (depends on extension complexity)
- **Memory Overhead**: Minimal (< 5MB for extension registry)
- **Concurrent Extensions**: Limited by Inkscape CLI (typically 3-5 concurrent)

### Security Considerations

- **Sandboxed Execution**: Extensions run in isolated subprocesses
- **Timeout Protection**: Configurable execution timeouts (default: 60s)
- **Parameter Validation**: Strict parameter type checking and bounds validation
- **File Access Control**: Extensions operate within configured allowed directories

## Performance Characteristics

### Startup Time (with --batch-process enforced)
- **Cold Start**: < 2 seconds (headless mode, no background indexing)
- **Hot Reload**: < 0.5 seconds
- **Memory Footprint**: < 50MB baseline (vs 500MB+ with GUI context)

### Headless Mode Benefits
**🚀 CRITICAL**: `--batch-process` flag prevents GTK/display initialization:
- **Without --batch-process**: Full GUI context → 500MB+ RAM, hangs in server environments
- **With --batch-process**: Pure CLI processing → 50MB RAM, reliable in containers/GitHub Actions

### Operation Performance
- **File Operations**: 10-500ms (I/O bound)
- **Vector Operations**: 100-2000ms (computationally intensive)
- **Analysis Operations**: 50-300ms (query-based)
- **System Operations**: < 10ms (in-memory)

### Concurrent Processing
- **Max Concurrent Jobs**: Configurable (default: 4)
- **Queue Management**: FIFO with timeout handling
- **Resource Limits**: Automatic cleanup and memory management

## Workflow Examples

### Logo Creation Workflow
```python
# 1. Generate text-based logo
result1 = await inkscape_vector("text_to_path", input_path="logo.svg", text="ACME Corp", font="Arial Bold")

# 2. Apply boolean operations for design
result2 = await inkscape_vector("apply_boolean", input_path="logo.svg", operation_type="union", object_ids=["text", "icon"])

# 3. Optimize for web deployment
result3 = await inkscape_vector("optimize_svg", input_path="logo.svg", output_path="logo_optimized.svg")

# 4. Generate preview
result4 = await inkscape_vector("render_preview", input_path="logo_optimized.svg", output_path="logo_preview.png", dpi=150)
```

### Technical Drawing Workflow
```python
# 1. Import CAD data or create from scratch
result1 = await inkscape_vector("construct_svg", description="Create isometric cube with dimensions")

# 2. Add measurements and annotations
result2 = await inkscape_vector("measure_object", input_path="drawing.svg", object_id="cube")

# 3. Export to CAD format
result3 = await inkscape_vector("export_dxf", input_path="drawing.svg", output_path="drawing.dxf")

# 4. Generate documentation
result4 = await inkscape_analysis("statistics", input_path="drawing.svg")
```

### Web Graphics Optimization
```python
# 1. Clean up imported graphics
result1 = await inkscape_vector("path_clean", input_path="imported.svg", output_path="clean.svg")

# 2. Simplify paths for web performance
result2 = await inkscape_vector("path_simplify", input_path="clean.svg", output_path="simple.svg", threshold=0.01)

# 3. Remove metadata and optimize
result3 = await inkscape_vector("scour_svg", input_path="simple.svg", output_path="optimized.svg")

# 4. Validate final result
result4 = await inkscape_analysis("quality", input_path="optimized.svg")
```

## Integration Points

### MCP Client Compatibility
- **Cursor IDE**: Native MCP support with tool discovery
- **Claude Desktop**: Full MCP protocol implementation
- **Custom Clients**: Stdio-based JSON-RPC interface
- **Web Interfaces**: HTTP gateway support

### File System Integration
- **Project Awareness**: Automatic project context detection
- **Path Resolution**: Cross-platform file path handling
- **Permission Management**: Secure file access controls
- **Backup System**: Automatic file versioning

### AI Agent Capabilities
- **Conversational Interface**: Natural language operation requests
- **Context Awareness**: Maintains conversation state across operations
- **Batch Processing**: Queue multiple operations efficiently
- **Error Recovery**: Intelligent retry and fallback strategies

## Security Model

### File Access Controls
- **Allowed Directories**: Configurable safe paths
- **Path Validation**: Prevent directory traversal attacks
- **Permission Checking**: File system permission verification
- **Temporary Files**: Secure temporary file management

### Process Isolation
- **Subprocess Execution**: Isolated Inkscape processes
- **Timeout Protection**: Automatic process termination
- **Resource Limits**: Memory and CPU usage controls
- **Cleanup Handling**: Proper process and file cleanup

## Critical Implementation Gaps (FIXED)

### ✅ 1. Action Verb vs Verb-Noun Gap - FIXED
**Issue**: Inkscape's `--actions` API is stateful - selection must precede operations
**Fix**: Server now enforces "Select → Modify → Persist" action chains internally

### ✅ 2. Object ID Hallucination Risk - FIXED
**Issue**: AI agents guess IDs like "path1" without discovery
**Fix**: `inkscape_analysis("objects")` promoted as prerequisite for ID-requiring operations

### ✅ 3. Verbosity/Header Problem - FIXED
**Issue**: Inkscape outputs headers that break JSON parsing
**Fix**: Server strips non-JSON noise and filters stderr GTK warnings

### ✅ 4. Technical Implementation Errors - FIXED
**Issue**: Incorrect CLI syntax (missing export-do, wrong simplify parameters)
**Fix**: All CLI examples corrected with proper action chains and parameters

### ✅ 5. Architectural Recommendations - IMPLEMENTED
**Potrace Tracing**: Black/white only by default, brightness threshold parameter added
**Coordinate System Clarity**: Inkscape UI uses Bottom-Left origin for ruler and coordinates display, but SVG standard (and --query flags) uses Top-Left origin. Server normalizes dimensions in analysis operations to prevent AI from "drawing off-canvas" by converting between coordinate systems automatically.
**Z-Order Management**: Added `object-raise` and `object-lower` operations
**Document Units**: Added `set_document_units` to `inkscape_system`
**Headless Mode**: `--batch-process` enforced to prevent GUI flashes
**Resource Handling**: `--no-remote-resources` flag prevents hanging on missing images

## Future Extensions

### Planned Enhancements
- **Live Preview**: Real-time SVG rendering in responses
- **Batch Operations**: Parallel processing for multiple files
- **Template System**: Reusable design templates
- **Collaboration**: Multi-user editing support
- **Version Control**: Git integration for design history

### API Expansions
- **WebSocket Support**: Real-time collaborative editing
- **REST API**: HTTP interface for web applications
- **Plugin System**: Extensible operation framework
- **Cloud Storage**: Integration with design asset libraries

---

**Server Version**: 1.1.0
**Protocol**: FastMCP 2.14.1+
**Inkscape Requirement**: 1.0+ (1.2+ recommended for Actions API)
**Platform**: Cross-platform (Windows, macOS, Linux)
**License**: MIT