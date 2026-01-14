# Inkscape MCP Server - Quick Start Guide

## 🚀 Get Started in 5 Minutes

Welcome to the Inkscape MCP Server! This guide will get you up and running with professional vector graphics automation in under 5 minutes.

## Prerequisites

### Required Software
- **Inkscape 1.0+** (1.2+ recommended for best Actions API support)
- **Python 3.10+** (automatically provided by MCP client)
- **MCP-compatible client** (Claude Desktop, Cursor, or Glama)

### Installation Verification

**Check Inkscape Installation:**
```bash
inkscape --version
# Should show: Inkscape 1.2.x or higher
```

**Test MCPB Installation (Claude Desktop):**
1. Download the `.mcpb` file
2. Drag it into Claude Desktop settings
3. Look for "Inkscape MCP Server" in the tools list

**Test Glama Installation:**
1. Install via standard MCP methods
2. Place `glama.json` in your project root
3. Glama will automatically discover the server

## Your First Operations

### 1. Basic File Operations

**Load and check an SVG:**
```
"Load this SVG file and tell me about it"
```
→ Returns file info, dimensions, and validation status

**Convert formats:**
```
"Convert logo.svg to PDF format"
```
→ Creates high-quality PDF with vector scaling

### 2. Vector Editing Operations

**Simplify complex paths:**
```
"Simplify the paths in this detailed drawing"
```
→ Reduces file size while preserving quality

**Convert text to paths:**
```
"Convert all text to editable paths"
```
→ Makes typography fully editable

### 3. Creative Operations

**Generate QR codes:**
```
"Create a QR code for https://example.com"
```
→ Generates scannable QR code

**AI-powered design:**
```
"Create an SVG of a geometric logo"
```
→ AI generates professional SVG from description

### 4. Quality Assurance

**Validate designs:**
```
"Check if this SVG is valid"
```
→ Comprehensive structure validation

**Get statistics:**
```
"Analyze the quality of this design"
```
→ Detailed metrics and optimization suggestions

## Common Workflows

### Logo Creation Pipeline
1. **Design**: "Create a professional logo with clean geometric shapes"
2. **Refine**: "Convert text to paths and simplify curves"
3. **Optimize**: "Clean up the SVG and optimize for web"
4. **Export**: "Convert to multiple formats (PNG, PDF, EPS)"

### Technical Illustration
1. **Import**: "Load this scanned blueprint"
2. **Vectorize**: "Trace the bitmap to clean vector paths"
3. **Refine**: "Simplify paths and convert objects to paths"
4. **Export**: "Save as DXF for CAD software"

### Web Graphics Optimization
1. **Load**: "Open this SVG icon set"
2. **Optimize**: "Simplify paths and scour metadata"
3. **Validate**: "Check quality and generate preview"
4. **Deploy**: "Compress for web delivery"

## Configuration Basics

### Default Settings (Usually Work Out-of-Box)
- **Inkscape Path**: Auto-detected
- **Timeout**: 60 seconds
- **Concurrent Operations**: 4 max
- **Allowed Directories**: Unrestricted

### Custom Configuration
```
"Configure Inkscape path to /custom/path/inkscape"
"Set operation timeout to 120 seconds"
"Limit concurrent operations to 2"
```

## Troubleshooting Quick Fixes

### Server Won't Start
- ✅ Check Inkscape installation: `inkscape --version`
- ✅ Verify MCPB installation in Claude Desktop
- ✅ Check Glama configuration file placement

### Operations Fail
- ✅ Verify file paths and permissions
- ✅ Check file formats (must be valid SVG)
- ✅ Try simpler operations first

### Performance Issues
- ✅ Close other memory-intensive applications
- ✅ Process large files individually
- ✅ Use path simplification for complex drawings

## Success Indicators

### ✅ Server Working Correctly
- Commands respond within seconds
- File operations complete successfully
- Vector operations produce expected results

### ✅ Quality Operations
- Path simplification reduces node counts
- Boolean operations create clean results
- Export operations maintain quality

### ✅ Performance Metrics
- File operations: <500ms
- Vector operations: <2000ms
- Memory usage: <50MB baseline

## Next Steps

### Explore Advanced Features
- Try boolean operations on complex shapes
- Experiment with mesh gradients
- Create custom automation workflows

### Build Workflows
- Combine multiple operations in sequences
- Create template-based processing
- Integrate with your design pipeline

### Customize Configuration
- Set up project-specific settings
- Configure performance optimizations
- Establish quality standards

## Get Help

### Built-in Help
```
"Show me system help"
"Get server status"
"Run diagnostics"
```

### Community Resources
- Check the technical specification document
- Review the user interaction guide
- Explore the examples collection

---

**🎯 Pro Tip**: Start simple, then build complexity. The server is designed to grow with your needs from basic file operations to sophisticated vector automation workflows.