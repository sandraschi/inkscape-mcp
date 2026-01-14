# Inkscape MCP Server

**By FlowEngineer sandraschi**

Professional vector graphics and SVG editing through Model Context Protocol (MCP) using Inkscape.

[![FastMCP](https://img.shields.io/badge/FastMCP-2.13%2B-blue)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## Overview

Inkscape-MCP provides Claude and other AI agents with professional vector graphics capabilities through Inkscape (the premier open-source SVG editor). This MCP server enables powerful SVG creation, manipulation, and conversion operations via a clean, standardized interface.

## v1.0.0 - Portmanteau Architecture

**New in v1.0.0:** Instead of 50+ individual tools, Inkscape MCP consolidates related operations into **8 master portmanteau tools**. This design:

- 🎯 **Reduces cognitive load** - 8 tools instead of 50+
- 🔍 **Improves discoverability** - Related operations grouped together
- ⚡ **Follows FastMCP 2.13+ best practices** - Modern MCP architecture
- 📚 **Better documentation** - Each tool is self-documenting with comprehensive docstrings

### Portmanteau Tools

| Tool | Operations | Description |
|------|------------|-------------|
| `inkscape_file` | 6 | File operations: load, save, convert, info, validate |
| `inkscape_transform` | 7 | Transforms: resize, crop, rotate, flip, scale, perspective |
| `inkscape_object` | 8 | Objects: create, duplicate, delete, group, ungroup, align |
| `inkscape_path` | 6 | Paths: edit, simplify, boolean operations, stroke/fill |
| `inkscape_text` | 5 | Text: create, edit, style, convert to path |
| `inkscape_export` | 8 | Export: PNG, PDF, PS, EPS, SVG variants |
| `inkscape_analysis` | 6 | Analysis: quality, statistics, validation |
| `inkscape_system` | 8 | System: status, help, diagnostics, cache, config |

## Features

### Core Vector Operations
- **File Management**: Load, save, and convert between vector formats (SVG, PDF, EPS, etc.)
- **Object Manipulation**: Create, edit, group, and transform vector objects
- **Path Editing**: Advanced path operations, boolean operations, stroke/fill controls
- **Text Handling**: Typography controls, text-to-path conversion
- **Export Options**: Multiple output formats with quality controls
- **SVG Optimization**: Clean, standards-compliant SVG output

### Technical Highlights
- **Cross-platform**: Windows, macOS, and Linux support
- **Performance optimized**: Async operations with process management
- **Robust error handling**: Comprehensive validation and recovery
- **Flexible configuration**: YAML-based settings with sensible defaults
- **Security focused**: File validation and access controls
- **FastMCP 2.13+**: Modern MCP architecture with portmanteau tools

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

## Development Status

**Current Phase**: v1.0.0 Portmanteau Architecture (IN DEVELOPMENT)
- ✅ FastMCP 2.13+ integration
- ✅ 8 portmanteau tools consolidating 40+ operations
- ✅ Comprehensive docstrings with examples
- 🔄 Core CLI wrapper implementation
- 🔄 Basic file operations
- 🔄 Object manipulation tools
- 📋 Path editing operations (planned)
- 📋 Export functionality (planned)

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