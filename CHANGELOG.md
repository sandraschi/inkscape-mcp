# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-14 - Complete Vibe Architect Workflow

### 🎉 **Major Release: Complete Implementation**

This release transforms Inkscape-MCP into a comprehensive "vibe architect" workflow tool, implementing all 23 advanced vector operations across 5 specialized categories as requested by Gemini's AG specifications.

### ✨ **Added**

#### 🎨 **Vibe-to-Vector Tools (Generative)**
- **`construct_svg`**: Build complex SVGs from text descriptions (Polish royal crest demo)
- **`generate_barcode_qr`**: Create QR codes and barcodes using Inkscape extensions
- **`create_mesh_gradient`**: Generate complex organic color gradients with multiple stops
- **`text_to_path`**: Convert text strings to editable Bezier curves with font selection
- **`trace_image`**: Enhanced raster-to-vector conversion using Potrace with multiple modes

#### 🔧 **Geometric Logic (Boolean Operations)**
- **`apply_boolean`**: Complete boolean operations suite (Union, Difference, Intersection, Exclusion, Division)
- **`path_inset_outset`**: Shrink or grow shapes for borders and halo effects

#### ⚙️ **Path Engineering (LDDO Prevention)**
- **`path_operations`**: Advanced path manipulation (simplify, reverse, boolean ops)
- **`path_clean`**: Remove empty groups, unused defs, and hidden metadata
- **`path_combine`**: Merge separate paths into compound objects
- **`path_break_apart`**: Split compound objects into separate paths
- **`object_to_path`**: Convert primitives (rectangles, circles) to editable Bezier curves
- **`optimize_svg`**: Clean and optimize SVG for web deployment
- **`scour_svg`**: Remove "LDDO" (Low-Density Derivative Output) metadata

#### 👁️ **Query & Analysis (AI's "Eyes")**
- **`measure_object`**: Query object dimensions using `--query-x`, `--query-width`, `--query-height`
- **`query_document`**: Get comprehensive document statistics and object enumeration
- **`count_nodes`**: Analyze path complexity for optimization decisions

#### 🎮 **Specialized VRChat/Resonite Workflows**
- **`export_dxf`**: Export paths for CAD and 3D modeling tools (R14 format)
- **`layers_to_files`**: Export each layer as separate PNG/SVG files for texture atlases
- **`fit_canvas_to_drawing`**: Snap document boundaries to actual artwork for clean Unity imports

#### 🎯 **Entertainment & Easter Eggs**
- **`generate_laser_dot`**: Animated green laser pointer SVG for Benny (Easter egg)
- **Benny Test**: Laser dot generation with proper node counting and animation

### 🔧 **Enhanced**

#### **Inkscape Actions API Integration**
- Complete `--batch-process` implementation with action chaining
- Object ID addressing: `select-by-id:rect123;path-reverse`
- Complex operation pipelines without GUI flickering
- Inkscape 1.2+ modern actions system support

#### **CLI Wrapper Improvements**
- Enhanced error handling and timeout management
- Cross-platform Inkscape detection and validation
- Process isolation and resource management
- Support for all Inkscape CLI query functions

#### **Performance & Reliability**
- Async operation support for all vector tools
- Configurable timeouts and resource limits
- Comprehensive error recovery mechanisms
- Optimized file size reduction (LDDO prevention)

### 📚 **Documentation**
- Complete README rewrite with all 23 operations documented
- Category-based organization (Vibe-to-Vector, Geometric Logic, Path Engineering, etc.)
- Usage examples for all major operations
- Architecture documentation with portmanteau tool explanations

### 🧪 **Testing**
- Comprehensive test suite with Polish royal crest construction
- Mesh gradient generation verification
- Laser dot animation testing
- Path complexity analysis validation

### 🎯 **Compatibility**
- **Inkscape 1.2+** with Actions API support (preferred)
- **Inkscape 1.0+** backward compatibility
- **Cross-platform**: Windows, macOS, Linux with auto-detection
- **Python 3.10+** with modern async patterns

## [1.0.0] - 2025-01-13 - Initial Portmanteau Architecture

### ✨ **Added**
- FastMCP 2.13+ integration with modern portmanteau architecture
- Basic Inkscape CLI wrapper with cross-platform detection
- 8 portmanteau tools consolidating 40+ operations
- File operations (load, save, convert, validate)
- Basic vector operations (trace, boolean, optimize)
- Document analysis and system tools
- YAML-based configuration with environment variable support
- Comprehensive error handling and validation

### 🔧 **Technical Foundation**
- Async operation support with configurable timeouts
- Process management and resource isolation
- Security-focused file validation
- Modern Python type annotations
- Cross-platform compatibility layer

---

## Development Notes

### Version Numbering
- **Major**: Breaking changes to API or core architecture
- **Minor**: New features and operations (backward compatible)
- **Patch**: Bug fixes and optimizations

### Categories
- 🎨 **Vibe-to-Vector**: Generative tools bridging ideas to assets
- 🔧 **Geometric Logic**: Boolean operations and shape manipulation
- ⚙️ **Path Engineering**: Optimization and LDDO prevention
- 👁️ **Query & Analysis**: AI vision and measurement tools
- 🎮 **VR/Unity Pipeline**: Specialized export workflows
- 🎯 **Entertainment**: Easter eggs and fun features

### Testing
- **Benny Test**: Laser dot generation with proper complexity analysis
- **Polish Crest Test**: Complex SVG construction from text descriptions
- **LDDO Test**: File size reduction and metadata removal validation

---

**Legend:**
- ✅ Implemented and tested
- 🔄 In development
- 📋 Planned for future release
- 🎯 Key achievement/milestone