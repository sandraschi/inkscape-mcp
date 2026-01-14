# Inkscape MCP Server - Configuration Guide

## Configuration Architecture

The Inkscape MCP Server supports multiple configuration methods depending on your MCP client:

- **Claude Desktop (MCPB)**: Configuration through Claude Desktop UI or environment variables
- **Glama**: Standard MCP configuration with enhanced `glama.json` discovery
- **Other MCP Clients**: Standard MCP configuration methods

## Configuration Options

### Core Settings

#### Inkscape Executable Path
**Key**: `inkscape_path`
**Default**: Auto-detected
**Description**: Full path to Inkscape executable
```
# Auto-detection (recommended)
inkscape_path: auto

# Windows explicit path
inkscape_path: "C:\Program Files\Inkscape\bin\inkscape.exe"

# Linux/Mac explicit path
inkscape_path: "/usr/bin/inkscape"
```

#### Operation Timeout
**Key**: `process_timeout`
**Default**: 60 seconds
**Description**: Maximum time for individual operations
```
# Fast operations
process_timeout: 30

# Complex operations (recommended)
process_timeout: 120

# Very complex batch processing
process_timeout: 300
```

#### Concurrent Operations Limit
**Key**: `max_concurrent_processes`
**Default**: 4
**Description**: Maximum parallel Inkscape processes
```
# Resource-constrained systems
max_concurrent_processes: 1

# Standard desktop (recommended)
max_concurrent_processes: 4

# High-performance workstation
max_concurrent_processes: 8
```

#### Directory Restrictions
**Key**: `allowed_directories`
**Default**: Unrestricted
**Description**: Comma-separated list of allowed working directories
```
# Single directory
allowed_directories: "/home/user/projects"

# Multiple directories
allowed_directories: "/home/user/projects,/home/user/designs,/tmp"

# Unrestricted (default)
allowed_directories: ""
```

### Quality and Performance Settings

#### Default Export DPI
**Key**: `default_export_dpi`
**Default**: 300
**Description**: Default resolution for raster exports
```
# Screen/web use
default_export_dpi: 96

# Print quality (recommended)
default_export_dpi: 300

# High-end printing
default_export_dpi: 600
```

#### Path Simplification Threshold
**Key**: `path_simplify_threshold`
**Default**: 0.1
**Description**: Default simplification aggressiveness (0.01-1.0)
```
# Conservative (preserves detail)
path_simplify_threshold: 0.01

# Balanced (recommended)
path_simplify_threshold: 0.1

# Aggressive (maximum simplification)
path_simplify_threshold: 0.5
```

#### SVG Optimization Level
**Key**: `svg_optimization_level`
**Default**: standard
**Description**: Optimization aggressiveness for SVG processing
```
# Minimal optimization
svg_optimization_level: minimal

# Standard optimization (recommended)
svg_optimization_level: standard

# Aggressive optimization
svg_optimization_level: aggressive
```

## Client-Specific Configuration

### Claude Desktop (MCPB) Configuration

#### UI-Based Configuration
1. Open Claude Desktop settings
2. Navigate to MCP servers
3. Select "Inkscape MCP Server"
4. Configure options in the UI panel

#### Environment Variable Configuration
```bash
# Set before starting Claude Desktop
export MCP_INKSCAPE_PATH="/custom/path/inkscape"
export MCP_TIMEOUT="120"
export MCP_MAX_PROCESSES="2"
```

### Glama Configuration

#### glama.json Structure
```json
{
  "mcpServers": {
    "inkscape-mcp": {
      "command": "python",
      "args": ["-m", "src.inkscape_mcp.main"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "INKSCAPE_PATH": "/custom/path/inkscape",
        "INKSCAPE_TIMEOUT": "120"
      },
      "description": "Professional vector graphics automation",
      "capabilities": {
        "tools": {"enabled": true},
        "resources": {"enabled": true},
        "prompts": {"enabled": true}
      },
      "timeout": {
        "initialize": 30000,
        "message": 120000
      }
    }
  }
}
```

#### Glama Environment Variables
```bash
# Project-specific configuration
INKSCAPE_PATH=/opt/inkscape/bin/inkscape
INKSCAPE_TIMEOUT=180
INKSCAPE_MAX_PROCESSES=6
INKSCAPE_ALLOWED_DIRS=/workspace/projects,/workspace/assets
```

### Other MCP Clients Configuration

#### Standard MCP Configuration
```json
{
  "mcpServers": {
    "inkscape": {
      "command": "python",
      "args": ["-m", "inkscape_mcp.main"],
      "env": {
        "PYTHONPATH": "/path/to/inkscape_mcp/src",
        "INKSCAPE_PATH": "/usr/bin/inkscape"
      }
    }
  }
}
```

## Performance Tuning

### System Resource Optimization

#### Memory Management
```bash
# Limit memory usage
INKSCAPE_MAX_MEMORY=512MB

# Enable memory monitoring
INKSCAPE_MEMORY_MONITOR=true
```

#### CPU Optimization
```bash
# CPU affinity (Linux)
INKSCAPE_CPU_AFFINITY=0-3

# Process priority
INKSCAPE_NICE_LEVEL=10
```

### Operation-Specific Tuning

#### Batch Processing
```bash
# Batch size for large operations
INKSCAPE_BATCH_SIZE=10

# Parallel processing limit
INKSCAPE_MAX_PARALLEL=4
```

#### Quality vs Speed Trade-offs
```bash
# Fast mode (lower quality)
INKSCAPE_FAST_MODE=true

# Quality priority
INKSCAPE_QUALITY_PRIORITY=high
```

## Project-Specific Configuration

### Web Development Projects
```json
{
  "inkscape_path": "auto",
  "process_timeout": 30,
  "default_export_dpi": 96,
  "path_simplify_threshold": 0.2,
  "svg_optimization_level": "aggressive",
  "allowed_directories": "./src/assets,./public/images"
}
```

### Print Design Projects
```json
{
  "inkscape_path": "auto",
  "process_timeout": 120,
  "default_export_dpi": 300,
  "path_simplify_threshold": 0.05,
  "svg_optimization_level": "minimal",
  "allowed_directories": "./designs,./exports"
}
```

### Technical Illustration Projects
```json
{
  "inkscape_path": "auto",
  "process_timeout": 180,
  "default_export_dpi": 600,
  "path_simplify_threshold": 0.01,
  "svg_optimization_level": "minimal",
  "allowed_directories": "./drawings,./diagrams,./exports"
}
```

## Security Configuration

### File Access Control
```bash
# Restrict to specific directories only
INKSCAPE_ALLOWED_DIRS="/secure/designs,/secure/exports"

# Enable file type validation
INKSCAPE_VALIDATE_FILE_TYPES=true

# Disable network access
INKSCAPE_DISABLE_NETWORK=true
```

### Process Isolation
```bash
# Sandbox mode
INKSCAPE_SANDBOX_MODE=true

# Disable extensions
INKSCAPE_DISABLE_EXTENSIONS=true

# Limit subprocess capabilities
INKSCAPE_RESTRICT_SUBPROCESS=true
```

## Monitoring and Logging

### Log Configuration
```bash
# Log level
INKSCAPE_LOG_LEVEL=INFO

# Log file location
INKSCAPE_LOG_FILE=/var/log/inkscape-mcp.log

# Enable structured logging
INKSCAPE_STRUCTURED_LOGGING=true
```

### Performance Monitoring
```bash
# Enable metrics collection
INKSCAPE_METRICS_ENABLED=true

# Metrics export endpoint
INKSCAPE_METRICS_ENDPOINT=http://localhost:9090

# Operation profiling
INKSCAPE_PROFILE_OPERATIONS=true
```

## Troubleshooting Configuration

### Common Configuration Issues

#### Inkscape Not Found
```bash
# Check current path
which inkscape

# Set explicit path
export INKSCAPE_PATH=/usr/bin/inkscape

# Verify executable
$INKSCAPE_PATH --version
```

#### Permission Errors
```bash
# Check directory permissions
ls -la /path/to/working/directory

# Fix permissions
chmod 755 /path/to/working/directory

# Check user permissions
id
```

#### Timeout Issues
```bash
# Increase timeout for slow operations
export INKSCAPE_TIMEOUT=300

# Check system performance
top
free -h
```

### Configuration Validation

#### Test Configuration
```bash
# Validate Inkscape installation
python -c "
import subprocess
result = subprocess.run(['inkscape', '--version'], capture_output=True, text=True)
print('Inkscape version:', result.stdout.strip())
"

# Test MCP server startup
python -m inkscape_mcp.main --help
```

#### Debug Configuration Loading
```bash
# Enable debug logging
export INKSCAPE_LOG_LEVEL=DEBUG

# Check configuration loading
python -c "
from inkscape_mcp.config import InkscapeConfig
config = InkscapeConfig()
print('Configuration loaded:', config.model_dump())
"
```

## Advanced Configuration

### Custom Operation Profiles
```json
{
  "operation_profiles": {
    "web_optimization": {
      "timeout": 30,
      "simplify_threshold": 0.2,
      "optimization_level": "aggressive"
    },
    "print_quality": {
      "timeout": 120,
      "simplify_threshold": 0.05,
      "optimization_level": "minimal"
    }
  }
}
```

### Plugin Integration
```bash
# Enable custom plugins
INKSCAPE_PLUGINS_ENABLED=true

# Plugin directory
INKSCAPE_PLUGIN_DIR=/usr/share/inkscape/extensions

# Custom plugin path
INKSCAPE_CUSTOM_PLUGINS=/home/user/.config/inkscape/extensions
```

### Network and API Configuration
```bash
# Enable API access (if applicable)
INKSCAPE_API_ENABLED=false

# API endpoint (future feature)
INKSCAPE_API_ENDPOINT=http://localhost:8080

# Network timeout
INKSCAPE_NETWORK_TIMEOUT=30
```

## Migration and Upgrades

### Configuration Migration
```bash
# Backup current configuration
cp config.json config.backup.json

# Update to new format
python -m inkscape_mcp.tools.migration config.json

# Validate new configuration
python -m inkscape_mcp.tools.validation config.json
```

### Version Compatibility
```bash
# Check version compatibility
inkscape_mcp_version=$(python -c "import inkscape_mcp; print(inkscape_mcp.__version__)")
echo "Current version: $inkscape_mcp_version"

# Update configuration for new version
python -m inkscape_mcp.tools.upgrade_config
```

---

**Configuration Best Practices:**
1. Start with defaults and adjust based on your workflow
2. Test configurations on sample files before production use
3. Document your configuration choices for team consistency
4. Regularly review and optimize performance settings
5. Keep security restrictions appropriate for your environment