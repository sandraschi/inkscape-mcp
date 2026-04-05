# Architecture

## Overview

**inkscape-mcp** is a **FastMCP 3.1+** server. Tools are implemented in Python; heavy work is delegated to the **Inkscape CLI** (queries and `--actions` chains). The package lives under `src/inkscape_mcp/`.

## Core components

### FastMCP layer

- **MCP** tool surface (portmanteau tools + optional agentic registrations)
- **Transports:** stdio / HTTP / dual — see `transport.py` and CLI flags on `inkscape_mcp.main`
- **Responses:** JSON-friendly dicts (`success`, `message`, `data`, errors)

### CLI integration

### CLI Wrapper Architecture
- **Cross-platform Detection**: Automatic Inkscape installation discovery
- **Process Management**: Isolated execution with timeout controls
- **Action Chaining**: Stateful operation sequences using Inkscape's Actions API
- **Output Processing**: JSON-RPC response cleaning and validation

### Extension System
- **Discovery**: Automatic scanning of Inkscape extension directories
- **Parameter Mapping**: Conversion between MCP and extension parameter formats
- **Execution**: Sandboxed extension execution with resource limits
- **Integration**: Extension tools appear as standard MCP operations

## Data Flow

1. **Request Processing**: FastMCP routes requests to appropriate tools
2. **Parameter Validation**: Pydantic models ensure data integrity
3. **Execution**: Isolated Inkscape processes with proper CLI arguments
4. **Result Processing**: Output parsing and MCP response formatting
5. **Cleanup**: Automatic temporary file management and resource release

## Security Model

- **Input Validation**: File type verification and path sanitization
- **Process Isolation**: Separate Inkscape instances for each operation
- **Resource Limits**: CPU and memory constraints per operation
- **Access Controls**: Configurable file system restrictions

## Performance

Depends on Inkscape startup, file size, and path complexity. Tune `process_timeout` and concurrency in config when batching.

## Platform Support

### Operating Systems
- **Windows**: Full support with auto-detection
- **macOS**: Native support with Homebrew integration
- **Linux**: Ubuntu and other distributions

### Inkscape Versions
- **1.4+**: Full Actions API support (recommended)
- **1.2+**: Basic operations with limitations
- **1.0+**: Legacy compatibility mode

### Python

- **3.12+** per `pyproject.toml`

## Configuration System

YAML-based configuration with environment variable support:

```yaml
# Inkscape settings
inkscape_executable: auto  # Auto-detected
working_directory: "/tmp/inkscape-mcp"

# Performance tuning
max_concurrent_processes: 3
process_timeout: 30
max_file_size_mb: 100

# Extensions
extension_directories:
  - "~/.config/inkscape/extensions"
  - "/usr/share/inkscape/extensions"
```

## Errors

Tools return structured failure payloads (messages, error types). Timeouts and Inkscape stderr propagate through the CLI wrapper — see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
