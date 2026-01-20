# Inkscape MCP Server

**By FlowEngineer sandraschi**

Professional vector graphics, SVG editing, and extension ecosystem through Model Context Protocol (MCP) using Inkscape.

[![CI/CD](https://img.shields.io/github/actions/workflow/status/sandraschi/inkscape-mcp/ci.yml?branch=master&label=CI%2FCD)](https://github.com/sandraschi/inkscape-mcp/actions)
[![PyPI Version](https://img.shields.io/pypi/v/inkscape-mcp?color=blue)](https://pypi.org/project/inkscape-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/inkscape-mcp)](https://pypi.org/project/inkscape-mcp/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Code Quality](https://img.shields.io/github/actions/workflow/status/sandraschi/inkscape-mcp/code-quality.yml?branch=master&label=Code%20Quality)](https://github.com/sandraschi/inkscape-mcp/actions)
[![Security](https://img.shields.io/github/actions/workflow/status/sandraschi/inkscape-mcp/security.yml?branch=master&label=Security)](https://github.com/sandraschi/inkscape-mcp/actions)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://hub.docker.com)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.14.3%2B-blue)](https://github.com/jlowin/fastmcp)
[![Inkscape](https://img.shields.io/badge/Inkscape-1.2%2B-orange)](https://inkscape.org)
[![Development Status](https://img.shields.io/badge/Status-Beta-orange)](https://github.com/sandraschi/inkscape-mcp)

> ⚠️ **BETA STATUS**: This software is feature-complete but may contain bugs. APIs are stable but minor changes may occur. Suitable for testing and non-critical production use.

## Overview

Inkscape-MCP provides Claude and other AI agents with professional vector graphics and universal format translation capabilities through Inkscape. This MCP server enables powerful SVG operations, raster-to-vector conversion, boolean geometry operations, and format translation via a clean, standardized interface.

## 🚀 **AI SVG Generation System (Now Available!)**

**Transform natural language into professional SVG vector graphics.** Tell Claude "create a coat of arms with a lion rampant and medieval shield" and watch it generate production-ready SVG files automatically.

### 🎯 **Now Available in v1.3.0!**
- **🤖 AI-Powered SVG Generation**: Natural language to professional vector graphics
- **🎨 Style Presets**: geometric, organic, technical, heraldic, abstract styles
- **⚡ Quality Levels**: draft, standard, high, ultra with intelligent optimization
- **🛡️ Enterprise Security**: Validated SVG generation with comprehensive safety measures
- **🔄 Inkscape Post-Processing**: Automatic application of professional vector operations
- **📚 SVG Repository**: Versioned asset management with metadata and search
- **🎯 Conversational Refinement**: Iterative improvement cycles with user feedback

### Quick Example
```python
# Generate a heraldic coat of arms
generate_svg(
    description="coat of arms with lions rampant and a golden crown",
    style_preset="heraldic",
    dimensions="600x800",
    model="flux-dev",
    quality="high",
    post_processing=["simplify", "optimize"]
)
```

See [AI SVG Generation Documentation](docs/USAGE.md#ai-svg-generation) for complete usage guide.

## 🚀 Installation

**State-of-the-Art (SOTA) Installation Methods**

### Quick Install (Recommended)
```bash
# Install from PyPI with uv (recommended)
uv pip install inkscape-mcp

# Or with pip
pip install inkscape-mcp

# Verify installation
inkscape-mcp --help
```

### One-Shot Execution
```bash
# Run without installation
uvx inkscape-mcp

# Run from GitHub source
uvx git+https://github.com/sandraschi/inkscape-mcp
```

### MCPB Configuration (Claude Desktop & Windsurf)

**Claude Desktop**: Copy `claude_desktop_config.json` to your Claude config directory
**Windsurf**: Copy `windsurf_config.json` to your Windsurf config directory

📖 **[Complete Installation Guide](INSTALL.md)** - Comprehensive documentation covering all installation methods, configuration, troubleshooting, and production deployment.

## 🦀 Zed IDE Integration

This repository includes a **Zed Extension** that allows you to run the Inkscape MCP server directly within the Zed IDE. The extension provides seamless integration with Zed's AI assistant for vector graphics workflows.

### Installation in Zed

1. **Prerequisites**: Install Rust toolchain and ensure `wasm32-wasip1` target is available:
   ```bash
   rustup target add wasm32-wasip1
   ```

2. **Build the extension**:
   ```bash
   ./build.sh
   ```

3. **Install in Zed**:
   - Open Zed and run the command palette (`Cmd+Shift+P`)
   - Type `zed: extensions` and select "Install Dev Extension"
   - Select this repository root folder

4. **Usage**: The "Inkscape Vector Tools" context server will be available in Zed's AI assistant panel.

### Development

The Zed extension uses a Rust bridge compiled to WebAssembly for security and performance. The bridge spawns your local Python MCP server when activated in Zed.

See the extension files:
- `extension.toml` - Extension manifest
- `Cargo.toml` - Rust dependencies
- `src/lib.rs` - Bridge implementation
- `build.sh` - Build automation

### 🎯 **v1.2.0-beta - Complete Extension Ecosystem**

**New in v1.2.0-beta:** **Full Inkscape extension system support** - Access the entire Inkscape extension ecosystem (200+ extensions) directly through MCP. Includes specialized Unity/VRChat workflow extensions for professional game development pipelines.

## v1.1.1 - Production-Ready Robustness & Critical Fixes

**New in v1.1.1:** **Complete implementation of all Gemini-identified critical gaps** - Production-ready with bulletproof stateful execution, proper prerequisites, and technical accuracy.

### ✅ **Critical Robustness Fixes (Gemini Analysis)**
- **Stateful Action Chains**: Fixed Inkscape's `--actions` API stateful execution with proper "Select → Modify → Persist" patterns
- **Object ID Prerequisites**: `inkscape_analysis("objects")` now mandatory prerequisite for ID-requiring operations (prevents hallucination failures)
- **Headless Mode**: `--batch-process` and `--no-remote-resources` prevent GUI flashes and hanging on missing images
- **Output Filtering**: Proper JSON-RPC response handling prevents parsing failures and ontological drift
- **CLI Syntax Corrections**: All examples now use correct Inkscape 1.2+ syntax with proper action chains
- **Z-Order Management**: Added `object-raise` and `object-lower` operations for layering control
- **Document Units**: Added `set_document_units` for coordinate system normalization

### ✅ **23 Advanced Vector Operations** (Now Robust & Reliable)

### 🎨 **Vibe-to-Vector Tools (Generative)**
- **`trace_image`**: Convert raster sketches to clean SVG paths using Potrace
- **`generate_barcode_qr`**: Create QR codes and barcodes
- **`create_mesh_gradient`**: Generate complex organic color gradients
- **`text_to_path`**: Convert text strings to editable Bezier curves
- **`construct_svg`**: Build complex SVGs from text descriptions (Polish crest demo!)

### 🔧 **Geometric Logic (Boolean Operations)**
- **`apply_boolean`**: Union, Difference, Intersection, Exclusion, Division
- **`path_inset_outset`**: Shrink/grow shapes for borders and halo effects

### ⚙️ **Path Engineering (Optimization)**
- **`path_operations`**: Simplify, reverse, boolean ops on paths
- **`path_clean`**: Remove empty groups, unused defs, hidden metadata
- **`path_combine`**: Merge separate paths into compound objects
- **`path_break_apart`**: Split compound objects into separate paths
- **`object_to_path`**: Convert primitives to editable Bezier curves
- **`optimize_svg`**: Clean and optimize SVG for web deployment
- **`scour_svg`**: Remove "LDDO" metadata and optimize SVG

### 👁️ **Query & Analysis (AI's "Eyes")**
- **`measure_object`**: Query dimensions with `--query-x`, `--query-width`, etc.
- **`query_document`**: Get comprehensive document statistics
- **`count_nodes`**: Analyze path complexity for optimization decisions

### 🎮 **Specialized VRChat/Resonite Workflows**
- **`export_dxf`**: Export paths for CAD and 3D modeling tools
- **`layers_to_files`**: Export each layer as separate PNG/SVG files
- **`fit_canvas_to_drawing`**: Snap document boundaries to artwork

### 🎯 **Entertainment & Z-Order Control**
- **`generate_laser_dot`**: Frantic animated green laser pointer (SVG `<animate>` tags, LDDO-compliant)
- **`object_raise`**: Move objects up in Z-order/layering
- **`object_lower`**: Move objects down in Z-order/layering

### 🔒 **System Management & Document Control**
- **`set_document_units`**: Normalize coordinate systems (Bottom-Left UI to Top-Left SVG) for consistent workflows

### Portmanteau Tools

| Tool | Operations | Description |
|------|------------|-------------|
| `generate_svg` | 1 | **AI SVG Generation**: Create vector graphics from natural language descriptions |
| `inkscape_file` | 6 | File operations: load, save, convert, info, validate, list_formats |
| `inkscape_vector` | **23** | **Complete vector operations suite** - all categories above |
| `inkscape_analysis` | 6 | Document analysis: quality, statistics, validate, objects, dimensions |
| `inkscape_system` | 5 | System operations: status, help, diagnostics, version, config |
| `inkscape_transform` | 6 | Geometric transforms: scale, rotate, translate, skew, matrix, reset |
| `inkscape_color` | 7 | Color adjustments: brightness, contrast, hue, saturation, levels, curves, hsl |
| `inkscape_filter` | 6 | Filters: blur, sharpen, noise, artistic, distort, lighting |
| `inkscape_layer` | 7 | Layer management: create, delete, duplicate, merge, flatten, reorder |
| `inkscape_batch` | 7 | Batch processing: resize, convert, watermark, optimize, rename, process |

## Advanced Capabilities

### Universal Vector Translator
Inkscape serves as a "universal translator" for vector graphics:
- **Imports**: Adobe Illustrator (.ai), CorelDRAW (.cdr), PDF, EPS, PostScript, DXF, WMF/EMF
- **Exports**: PDF, PNG, G-Code (CNC/plotting), XAML (Windows UI), optimized SVG

### Universal Vector Translator
Inkscape serves as a "universal translator" for vector and raster data:
- **Imports**: Adobe Illustrator (.ai), CorelDRAW (.cdr), PDF, EPS, PostScript, DXF, WMF/EMF
- **Exports**: PDF, PNG, G-Code (CNC/plotting), XAML (Windows UI), optimized SVG
- **Raster-to-Vector**: Convert PNG/JPG sketches to clean SVG paths using Potrace

### Complete Vibe Architect Workflow
**23 Operations** across 5 specialized categories:

#### 🎨 **Vibe-to-Vector (Generative)**
- `construct_svg`: Build complex graphics from text descriptions
- `generate_barcode_qr`: Create QR codes and barcodes
- `create_mesh_gradient`: Organic color flows with multiple stops
- `text_to_path`: Typography to editable vector paths
- `trace_image`: Hand-drawn sketches to vector paths

#### 🔧 **Geometric Logic (Boolean Operations)**
- `apply_boolean`: Union, Difference, Intersection, Exclusion, Division
- `path_inset_outset`: Borders and halo effects through shape manipulation

#### ⚙️ **Path Engineering (LDDO Prevention)**
- `path_simplify`: Reduce node count while maintaining shape
- `path_clean`: Remove empty groups and hidden metadata
- `path_combine`/`path_break_apart`: Manage compound object structure
- `object_to_path`: Convert primitives to editable curves
- `scour_svg`: Remove Adobe/Inkscape metadata for clean output

#### 👁️ **Query & Analysis (AI Vision)**
- `measure_object`: `--query-x`, `--query-width`, `--query-height`
- `count_nodes`: Path complexity analysis for optimization
- `query_document`: Comprehensive document statistics

#### 🎮 **VR/Unity Pipeline**
- `export_dxf`: CAD and 3D modeling compatibility
- `layers_to_files`: Texture atlases and UI elements
- `fit_canvas_to_drawing`: Clean Unity imports with proper pivot points

### Actions System (Inkscape 1.2+)
Advanced CLI actions chaining with `--batch-process`:
- Object ID addressing: `select-by-id:rect123;path-reverse`
- Complex operation pipelines: Open → Select → Transform → Export
- Chained commands without GUI flickering

## Features

### Complete Vector Graphics Suite
- **Universal Translation**: Import AI/CDR/PDF/EPS, export PDF/PNG/G-Code/XAML
- **23 Advanced Operations**: Full vibe architect workflow implementation
- **Object ID Addressing**: Precision manipulation with `select-by-id:object123`
- **Measurement Tools**: `--query-x`, `--query-width`, `--query-height` for AI vision
- **Path Complexity Analysis**: Node counting for optimization decisions
- **LDDO Prevention**: Remove metadata and optimize output size
- **VR/Unity Pipeline**: DXF export, layer separation, canvas fitting

### Technical Excellence
- **Cross-platform**: Windows, macOS, and Linux support with auto-detection
- **Performance optimized**: Async operations with configurable timeouts
- **Robust error handling**: Comprehensive validation and recovery mechanisms
- **Flexible configuration**: YAML-based settings with environment variable support
- **Security focused**: File validation, access controls, and process isolation
- **FastMCP 2.14.3+**: Modern MCP architecture with portmanteau tools
- **Actions API**: Inkscape 1.2+ `--batch-process` chaining for complex workflows

### Specialized Capabilities
- **Mesh Gradients**: Complex organic color flows with multiple gradient stops
- **Barcode/QR Generation**: Built-in barcode and QR code creation
- **Text-to-Path**: Typography conversion to editable vector curves
- **Boolean Operations**: Professional geometric set operations
- **Path Optimization**: Node reduction while maintaining visual fidelity
- **Layer Management**: Export layers as separate files for texture atlases
- **Easter Eggs**: Benny's laser dot generator with animation

## Installation

### Prerequisites
- Python 3.10 or higher
- Inkscape 1.0+ (Inkscape 1.4+ recommended)

### Quick Install
```bash
# Clone the repository
git clone https://github.com/sandraschi/inkscape-mcp.git
cd inkscape-mcp

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Verify Installation
```bash
# Check Inkscape detection
inkscape-mcp --validate-only
```

## Configuration

Inkscape-MCP works out of the box with automatic Inkscape detection and sensible defaults.

### Custom Configuration
Create `config.yaml` in your working directory:

```yaml
# Inkscape Configuration
inkscape_executable: "/custom/path/to/inkscape"  # Optional: auto-detected

# Performance Settings
max_concurrent_processes: 3
process_timeout: 30

# File Handling
temp_directory: "/tmp/inkscape-mcp"
max_file_size_mb: 100
preserve_metadata: true
```

## Usage

### Start the Server
```bash
inkscape-mcp --host localhost --port 8000
```

### Claude Desktop Integration
Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "inkscape-mcp": {
      "command": "inkscape-mcp",
      "args": []
    }
  }
}
```

## Available Tools (v1.0.0 Portmanteau)

### inkscape_file - File Operations
```python
inkscape_file(operation="load", input_path="drawing.svg")
inkscape_file(operation="save", input_path="drawing.svg", output_path="output.svg", format="svg")
inkscape_file(operation="convert", input_path="drawing.ai", output_path="drawing.svg", format="svg")
inkscape_file(operation="info", input_path="drawing.svg")
```
**Operations**: `load`, `save`, `convert`, `info`, `validate`, `list_formats`

### inkscape_object - Object Management
```python
inkscape_object(operation="create", object_type="rectangle", x=100, y=100, width=200, height=150)
inkscape_object(operation="duplicate", input_path="drawing.svg", object_id="rect123")
inkscape_object(operation="group", input_path="drawing.svg", output_path="grouped.svg", object_ids=["obj1", "obj2"])
```
**Operations**: `create`, `duplicate`, `delete`, `group`, `ungroup`, `align`, `distribute`

### inkscape_path - Path Operations
```python
inkscape_path(operation="edit", input_path="drawing.svg", path_id="path123", action="simplify")
inkscape_path(operation="boolean", input_path="drawing.svg", output_path="combined.svg", operation="union", paths=["path1", "path2"])
inkscape_path(operation="stroke_fill", input_path="drawing.svg", output_path="styled.svg", stroke_color="#000000", fill_color="#ffffff")
```
**Operations**: `edit`, `simplify`, `boolean`, `stroke_fill`, `convert_shape`, `offset`

### inkscape_export - Export Operations
```python
inkscape_export(operation="png", input_path="drawing.svg", output_path="drawing.png", dpi=300)
inkscape_export(operation="pdf", input_path="drawing.svg", output_path="drawing.pdf")
inkscape_export(operation="eps", input_path="drawing.svg", output_path="drawing.eps")
```
**Operations**: `png`, `pdf`, `ps`, `eps`, `svg_plain`, `svg_inkscape`, `optimize_svg`

### inkscape_analysis - Document Analysis
```python
inkscape_analysis(operation="quality", input_path="drawing.svg")
inkscape_analysis(operation="statistics", input_path="drawing.svg", include_objects=True)
inkscape_analysis(operation="validate", input_path="drawing.svg")
```
**Operations**: `quality`, `statistics`, `validate`, `objects`, `layers`, `dimensions`

### inkscape_system - System Operations & Extensions

```python
# Extension discovery and execution
inkscape_system(operation="list_extensions")
inkscape_system(operation="execute_extension", extension_id="org.project_ag.batch_trace",
                extension_params={"input_dir": "/path/to/images", "colors": 8})

# Server status and diagnostics
inkscape_system(operation="status")
inkscape_system(operation="diagnostics")
```
**Operations**: `status`, `help`, `diagnostics`, `version`, `config`, `list_extensions`, `execute_extension`

## 🎨 **Inkscape Extension System**

Inkscape-MCP now provides **complete access to Inkscape's extension ecosystem** - the 200+ Python extensions that power professional vector workflows. Extensions are automatically discovered and can be executed directly through MCP tools.

### **Built-in Unity/VRChat Extensions (AG Series)**

#### **AG Batch Trace** - AI Art to Vector Pipeline
```python
# Convert entire folders of AI-generated images to optimized SVGs
inkscape_system("execute_extension",
               extension_id="org.project_ag.batch_trace",
               extension_params={
                   "input_dir": "C:/ProjectAG/ConceptArt",
                   "output_dir": "C:/ProjectAG/Vectors",
                   "colors": 8,
                   "simplify": True
               })
```
**Perfect for**: Converting Midjourney/DALL-E outputs to Unity-ready vectors

#### **AG Unity Prep** - Game Engine Optimization
```python
# Prepare complex SVGs for Unity import
inkscape_system("execute_extension",
               extension_id="org.project_ag.unity_prep",
               extension_params={
                   "flatten_groups": True,
                   "reset_coordinates": True,
                   "optimize_paths": True,
                   "remove_metadata": True
               })
```
**Perfect for**: Cleaning up intricate SVGs before Unity import

#### **AG Layer Animation** - CSS Animations for UI
```python
# Create animated SVGs from layers for Unity web UI
inkscape_system("execute_extension",
               extension_id="org.project_ag.layer_animation",
               extension_params={
                   "duration": 2.0,
                   "loop": True,
                   "easing": "ease-in-out"
               })
```
**Perfect for**: Animated UI elements without heavy video files

#### **AG Color Quantize** - Performance Optimization
```python
# Reduce color palettes while maintaining brand consistency
inkscape_system("execute_extension",
               extension_id="org.project_ag.color_quantize",
               extension_params={
                   "max_colors": 8,
                   "palette": "#FF0000,#00FF00,#0000FF,#FFFF00,#FF00FF,#00FFFF,#000000,#FFFFFF"
               })
```
**Perfect for**: Optimizing textures for mobile/VR performance

### **Extension Discovery & Management**

```python
# Discover all available extensions
extensions = inkscape_system("list_extensions")
# Returns: [{"id": "org.inkscape.render.barcode", "name": "Barcode", "category": "render"}, ...]

# Execute any Inkscape extension
result = inkscape_system("execute_extension",
                        extension_id="org.inkscape.render.barcode.qr",
                        extension_params={"text": "Hello World"})
```

### **Extension Architecture**

- **Automatic Discovery**: Scans standard Inkscape extension directories
- **Parameter Mapping**: Converts MCP parameters to extension format
- **Async Execution**: Non-blocking extension execution with timeouts
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Security**: Sandboxed execution with resource limits

## Development Status

**Current Phase**: v1.2.0 Complete Extension Ecosystem ✅

### ✅ **Fully Implemented**
- ✅ FastMCP 2.14.3+ integration with modern portmanteau architecture
- ✅ **Complete Inkscape extension system** with 200+ extension support
- ✅ **4 specialized Unity/VRChat extensions** (AG Series) for game development
- ✅ **23 advanced vector operations** across 5 specialized categories
- ✅ Complete Inkscape Actions API with `--batch-process` chaining
- ✅ Universal vector translator (AI/CDR/PDF/EPS import, multi-format export)
- ✅ Object ID addressing and measurement tools (`--query-x`, `--query-width`)
- ✅ Path complexity analysis and LDDO prevention
- ✅ VR/Unity pipeline support (DXF export, layer separation, canvas fitting)
- ✅ Comprehensive CLI wrapper with error handling and cross-platform support
- ✅ All 9 portmanteau tools with 60+ consolidated operations + extensions

### 🎯 **Key Achievements**
- **Benny Test Passed**: Laser dot generation with proper node counting
- **Polish Crest Demo**: Complex SVG construction from text descriptions
- **Zero LDDO**: Optimized output with metadata removal and file size reduction
- **Universal Compatibility**: Import/export across Adobe, Corel, and open formats

## Architecture

The server uses a modular architecture with:
- **FastMCP Integration**: Standard MCP protocol implementation
- **CLI Wrapper**: Robust Inkscape command-line interface
- **Tool Categories**: Organized by functionality for maintainability
- **Error Handling**: Comprehensive validation and recovery
- **Cross-platform**: Windows, macOS, and Linux support

## Contributing

See the detailed implementation plan in `docs/IMPLEMENTATION_ROADMAP.md` for development guidelines and current status.

## License

MIT License - see LICENSE file for details.