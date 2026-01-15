# Inkscape MCP Installation Guide

**State-of-the-Art (SOTA) Installation Methods for Professional Deployments**

## 🎯 Installation Methods

### 1. **PyPI (Recommended for Production)**

```bash
# Install from PyPI
pip install inkscape-mcp

# Or with uv (recommended)
uv pip install inkscape-mcp

# Verify installation
inkscape-mcp --help
```

### 2. **uvx (One-Shot Execution)**

```bash
# Run without installation
uvx inkscape-mcp

# Run specific version
uvx inkscape-mcp==1.2.0

# Run from GitHub
uvx git+https://github.com/sandraschi/inkscape-mcp
```

### 3. **GitHub Source Installation**

```bash
# Clone repository
git clone https://github.com/sandraschi/inkscape-mcp
cd inkscape-mcp

# Install with uv (recommended)
uv sync
uv pip install -e .

# Or with pip
pip install -e .

# Or build and install
uv build
pip install dist/inkscape_mcp-1.2.0.tar.gz
```

### 4. **MCPB Configuration (Claude Desktop & Windsurf)**

#### Claude Desktop
Copy `claude_desktop_config.json` to:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Windsurf
Copy `windsurf_config.json` to:
- **macOS**: `~/Library/Application Support/Codeium/windsurf/mcp_config.json`
- **Windows**: `%USERPROFILE%\.codeium\windsurf\mcp_config.json`
- **Linux**: `~/.codeium/windsurf/mcp_config.json`

## 🔧 System Requirements

### Prerequisites

- **Python**: 3.10 - 3.13
- **Inkscape**: 1.2+ (with command-line support)
- **uv**: Latest version (recommended)

### Hardware Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for Inkscape + dependencies
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

## 🧪 Testing Installation

### Basic Functionality Test

```bash
# Test basic import
python -c "import inkscape_mcp; print('✅ Import successful')"

# Test CLI
inkscape-mcp --help

# Test MCP protocol
inkscape-mcp --test-mcp
```

### MCP Server Test

```bash
# Test with MCP inspector
uvx mcp-server-inspector inkscape-mcp

# Test with Claude Desktop
# 1. Add configuration to claude_desktop_config.json
# 2. Restart Claude Desktop
# 3. Check if "Inkscape Vector Tools" appears in tools
```

### Comprehensive Test Suite

```bash
# Run full test suite
uv run pytest

# Run with coverage
uv run pytest --cov=inkscape_mcp

# Run integration tests
uv run pytest tests/integration/
```

## 📋 Configuration

### Environment Variables

```bash
# Inkscape executable path (auto-detected if not set)
export INKSCAPE_PATH="/usr/bin/inkscape"

# Default SVG output directory
export INKSCAPE_OUTPUT_DIR="./output"

# Logging level
export INKSCAPE_LOG_LEVEL="INFO"

# Timeout for Inkscape operations (seconds)
export INKSCAPE_TIMEOUT="30"
```

### Configuration File

Create `config.yaml` in the working directory:

```yaml
inkscape:
  executable_path: "/usr/bin/inkscape"
  timeout: 30
  output_directory: "./output"

logging:
  level: "INFO"
  file: "inkscape_mcp.log"

mcp:
  server_name: "inkscape-mcp"
  version: "1.2.0"
```

## 🔄 Updating

### From PyPI

```bash
# Update to latest version
uv pip install --upgrade inkscape-mcp

# Update to specific version
uv pip install inkscape-mcp==1.2.1
```

### From Source

```bash
cd inkscape-mcp
git pull
uv sync
```

## 🐛 Troubleshooting

### Common Issues

#### "Command 'inkscape' not found"

**Solution**: Install Inkscape and ensure it's in PATH
```bash
# Ubuntu/Debian
sudo apt install inkscape

# macOS
brew install inkscape

# Windows: Download from inkscape.org
```

#### "Module 'inkscape_mcp' not found"

**Solution**: Install package correctly
```bash
# Reinstall with uv
uv pip uninstall inkscape-mcp
uv pip install inkscape-mcp

# Or reinstall from source
pip uninstall inkscape-mcp
pip install -e .
```

#### MCP Server Won't Start

**Solution**: Check MCPB configuration
```bash
# Test server directly
uvx inkscape-mcp

# Check logs
tail -f ~/.config/Claude/logs/mcp-server-inkscape-mcp.log
```

### Debug Mode

```bash
# Run with debug logging
INKSCAPE_LOG_LEVEL=DEBUG uvx inkscape-mcp

# Run MCP inspector in debug mode
uvx mcp-server-inspector --debug inkscape-mcp
```

## 📚 Verification Checklist

### Pre-Installation
- [ ] Python 3.10+ installed
- [ ] uv installed (`uv --version`)
- [ ] Inkscape 1.2+ installed

### Installation
- [ ] Package installs without errors
- [ ] CLI command works (`inkscape-mcp --help`)
- [ ] Import test passes

### MCPB Configuration
- [ ] Config file in correct location
- [ ] JSON syntax validated
- [ ] Claude Desktop/Windsurf restarted
- [ ] Tools appear in AI assistant

### Functionality
- [ ] Basic SVG operations work
- [ ] File I/O operations functional
- [ ] Error handling works correctly
- [ ] Performance acceptable

## 🎯 Performance Tuning

### For Production Use

```yaml
# config.yaml for production
inkscape:
  timeout: 60
  output_directory: "/tmp/inkscape_output"
  cleanup_temp_files: true

logging:
  level: "WARNING"
  file: "/var/log/inkscape-mcp.log"

mcp:
  max_concurrent_operations: 3
  cache_enabled: true
  cache_ttl: 3600
```

### Resource Optimization

- **Memory**: Monitor with `ps aux | grep inkscape`
- **Disk**: Enable temp file cleanup
- **CPU**: Limit concurrent operations
- **Network**: Use local file operations when possible

## 🔐 Security Considerations

- **File Access**: MCP server can read/write files - restrict to safe directories
- **Command Injection**: Input validation prevents shell injection
- **Sandboxing**: Run in isolated environment when possible
- **Updates**: Keep dependencies updated for security patches

## 📞 Support

### Getting Help

1. **Check Documentation**: This INSTALL.md and main README.md
2. **Run Diagnostics**: `uvx inkscape-mcp --diagnostics`
3. **Check Logs**: Review MCP server logs in Claude Desktop
4. **GitHub Issues**: Report bugs at https://github.com/sandraschi/inkscape-mcp/issues

### Community Resources

- **GitHub Discussions**: https://github.com/sandraschi/inkscape-mcp/discussions
- **Discord**: Join FastMCP community
- **MCP Protocol**: https://modelcontextprotocol.io/

---

**Installation verified on**: Windows 10/11, macOS 12+, Ubuntu 18.04+
**Last tested**: January 15, 2026
**Supported MCP clients**: Claude Desktop, Windsurf, Cline, other MCPB-compatible clients