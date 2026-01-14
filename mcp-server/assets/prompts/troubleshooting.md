# Inkscape MCP Server - Troubleshooting Guide

## Quick Diagnosis

### Is the Server Running?
```bash
# Check server status
"Check server status"

# Expected response includes:
# - Server version and health
# - Inkscape installation status
# - Available tools count
# - System resource information
```

### Basic Connectivity Test
```bash
# Test basic operation
"List supported export formats"

# Should return: svg, pdf, eps, png, etc.
```

## Installation Issues

### Claude Desktop (MCPB) Installation

#### MCPB Won't Install
**Symptoms:**
- Drag-and-drop fails
- "Invalid package" error
- Claude Desktop doesn't recognize the file

**Solutions:**
1. **Verify file integrity:**
   ```bash
   # Check file size (should be > 1MB)
   ls -lh inkscape-mcp-v1.1.0.mcpb

   # Try re-downloading if corrupted
   ```

2. **Check Claude Desktop version:**
   - Must be recent version with MCPB support
   - Update Claude Desktop if needed

3. **Alternative installation:**
   - Try installing via Glama instead
   - Use standard MCP installation methods

#### Tools Not Appearing
**Symptoms:**
- Server installs but no tools available
- "No tools found" in Claude Desktop

**Solutions:**
1. **Restart Claude Desktop completely**
2. **Check server logs:**
   ```bash
   # Enable debug logging
   export MCP_DEBUG=true
   # Restart Claude Desktop
   ```

3. **Verify manifest:**
   ```bash
   # Check manifest.json syntax
   cat mcp-server/manifest.json | jq .
   ```

### Glama Installation

#### Server Not Discovered
**Symptoms:**
- `glama.json` exists but server not found
- "Server unavailable" errors

**Solutions:**
1. **Verify `glama.json` location:**
   ```bash
   # Must be in repository root
   ls -la glama.json
   pwd  # Should be project root
   ```

2. **Check JSON syntax:**
   ```bash
   # Validate JSON
   jq . glama.json
   ```

3. **Restart Glama client**
4. **Check MCP server path:**
   ```bash
   # Verify server location
   python -c "import inkscape_mcp; print(inkscape_mcp.__file__)"
   ```

## Inkscape Integration Issues

### Inkscape Not Found

#### Auto-Detection Failing
**Symptoms:**
- "Inkscape executable not found" errors
- Operations fail immediately

**Solutions:**
1. **Verify Inkscape installation:**
   ```bash
   # Check if installed
   which inkscape
   inkscape --version
   ```

2. **Set explicit path:**
   ```bash
   # Configure custom path
   export INKSCAPE_PATH=/usr/bin/inkscape
   # Or on Windows:
   # set INKSCAPE_PATH="C:\Program Files\Inkscape\bin\inkscape.exe"
   ```

3. **Check PATH environment:**
   ```bash
   # Add to PATH if needed
   export PATH=$PATH:/path/to/inkscape/bin
   ```

#### Permission Issues
**Symptoms:**
- "Permission denied" when accessing Inkscape
- Operations fail with access errors

**Solutions:**
1. **Check executable permissions:**
   ```bash
   ls -la $(which inkscape)
   # Should be executable by user
   ```

2. **Run as appropriate user:**
   ```bash
   # Check current user
   whoami
   id
   ```

3. **Fix permissions if needed:**
   ```bash
   sudo chmod +x /path/to/inkscape
   ```

### Version Compatibility

#### Outdated Inkscape
**Symptoms:**
- Operations fail with "unknown option" errors
- Actions API not working

**Solutions:**
1. **Check version:**
   ```bash
   inkscape --version
   # Need 1.0+ , prefer 1.2+
   ```

2. **Upgrade Inkscape:**
   - Download latest version from inkscape.org
   - Use package manager: `sudo apt update && sudo apt install inkscape`

3. **Feature detection:**
   ```bash
   # Test Actions API
   inkscape --actions="help" 2>/dev/null && echo "Actions API available" || echo "Actions API missing"
   ```

## Operation Failures

### File Operation Issues

#### File Not Found Errors
**Symptoms:**
- "File does not exist" for valid files
- Path resolution failures

**Solutions:**
1. **Check file path:**
   ```bash
   # Verify file exists
   ls -la /path/to/file.svg
   ```

2. **Check working directory:**
   ```bash
   # Server working directory
   pwd
   # File permissions
   ls -ld /path/to/directory
   ```

3. **Use absolute paths:**
   ```bash
   # Prefer absolute paths
   "Load file at /full/path/to/file.svg"
   ```

#### Invalid File Format
**Symptoms:**
- "Invalid SVG" errors
- Operations fail on valid-looking files

**Solutions:**
1. **Validate SVG structure:**
   ```bash
   # Use built-in validation
   "Validate this SVG file"
   ```

2. **Check file encoding:**
   ```bash
   # Should be UTF-8
   file /path/to/file.svg
   ```

3. **Repair corrupted files:**
   ```bash
   # Try cleaning first
   "Clean up this SVG file"
   ```

### Vector Operation Problems

#### Boolean Operations Failing
**Symptoms:**
- Union/difference operations fail
- "Invalid path data" errors

**Solutions:**
1. **Convert to paths first:**
   ```bash
   "Convert all objects to paths first"
   ```

2. **Clean paths:**
   ```bash
   "Clean the SVG before boolean operations"
   ```

3. **Check path validity:**
   ```bash
   "Validate path data in this file"
   ```

#### Path Simplification Issues
**Symptoms:**
- Simplification makes paths worse
- Operations take too long

**Solutions:**
1. **Adjust threshold:**
   ```bash
   # Try different values
   threshold: 0.05  # More conservative
   threshold: 0.2   # More aggressive
   ```

2. **Pre-clean paths:**
   ```bash
   "Clean paths before simplifying"
   ```

3. **Process in parts:**
   ```bash
   # Simplify individual objects
   "Simplify path with ID 'complex_shape'"
   ```

### Performance Issues

#### Operations Too Slow
**Symptoms:**
- Operations take >30 seconds
- System becomes unresponsive

**Solutions:**
1. **Check system resources:**
   ```bash
   # Monitor CPU/memory
   top
   free -h
   ```

2. **Reduce concurrent operations:**
   ```bash
   # Limit to 1-2 operations
   max_concurrent_processes: 2
   ```

3. **Increase timeout:**
   ```bash
   # Allow more time
   process_timeout: 120
   ```

4. **Optimize input files:**
   ```bash
   "Simplify this complex drawing first"
   ```

#### Memory Exhaustion
**Symptoms:**
- Operations fail with memory errors
- System swap file usage spikes

**Solutions:**
1. **Process smaller files:**
   ```bash
   # Split large files
   "Process individual layers separately"
   ```

2. **Increase system memory**
3. **Use streaming processing:**
   ```bash
   # Enable memory-efficient mode
   memory_efficient_mode: true
   ```

### Quality Issues

#### Export Quality Problems
**Symptoms:**
- PNG exports are pixelated
- PDF exports lose quality

**Solutions:**
1. **Adjust DPI settings:**
   ```bash
   # Higher DPI for better quality
   dpi: 300  # Instead of 96
   ```

2. **Check export format:**
   ```bash
   "Export as PDF instead of PNG"
   ```

3. **Verify Inkscape version:**
   ```bash
   # Newer versions have better export
   inkscape --version
   ```

#### Tracing Quality Issues
**Symptoms:**
- Bitmap tracing produces poor results
- Vector output doesn't match original

**Solutions:**
1. **Adjust tracing parameters:**
   ```bash
   # Pre-process image
   "Use higher contrast image for tracing"
   ```

2. **Try different algorithms:**
   ```bash
   # Different tracing methods
   method: "brightness"  # Alternative to default
   ```

3. **Clean source image:**
   ```bash
   # Remove noise first
   "Clean up the bitmap before tracing"
   ```

## Network and API Issues

### Connection Timeouts
**Symptoms:**
- Operations hang indefinitely
- "Connection timeout" errors

**Solutions:**
1. **Increase timeout settings:**
   ```bash
   process_timeout: 300  # 5 minutes
   ```

2. **Check network connectivity:**
   ```bash
   ping google.com
   ```

3. **Disable network features:**
   ```bash
   disable_network: true
   ```

### API Rate Limiting
**Symptoms:**
- Operations fail with rate limit errors
- "Too many requests" messages

**Solutions:**
1. **Reduce request frequency**
2. **Implement retry logic:**
   ```bash
   # Enable automatic retries
   retry_on_failure: true
   max_retries: 3
   ```

3. **Space out operations:**
   ```bash
   # Add delays between operations
   operation_delay: 1000  # milliseconds
   ```

## Configuration Problems

### Settings Not Applied
**Symptoms:**
- Configuration changes don't take effect
- Settings revert after restart

**Solutions:**
1. **Check configuration file location:**
   ```bash
   # Find config file
   find . -name "*.json" -exec grep -l "inkscape" {} \;
   ```

2. **Validate JSON syntax:**
   ```bash
   # Check for syntax errors
   jq . config.json
   ```

3. **Restart services:**
   ```bash
   # Restart MCP client
   # Restart MCP server
   ```

### Invalid Configuration Values
**Symptoms:**
- "Invalid configuration" errors
- Operations fail with config errors

**Solutions:**
1. **Check value ranges:**
   ```json
   {
     "timeout": 30,        // 1-3600
     "max_processes": 4,   // 1-16
     "dpi": 300           // 72-1200
   }
   ```

2. **Validate paths:**
   ```bash
   # Check path exists
   ls -la "$INKSCAPE_PATH"
   ```

3. **Reset to defaults:**
   ```bash
   # Clear custom config
   rm config.json
   # Restart with defaults
   ```

## Advanced Debugging

### Enable Debug Logging
```bash
# Maximum verbosity
export INKSCAPE_LOG_LEVEL=DEBUG
export MCP_DEBUG=true

# Restart server/client
```

### Collect Diagnostic Information
```bash
# System information
uname -a
python --version
inkscape --version

# Server logs
tail -f /var/log/inkscape-mcp.log

# Configuration dump
python -c "from inkscape_mcp.config import InkscapeConfig; print(InkscapeConfig().model_dump())"
```

### Performance Profiling
```bash
# Enable profiling
export INKSCAPE_PROFILE=true

# Run operation and check timing
time "Process this file"

# Check resource usage
ps aux | grep inkscape
```

## Common Error Patterns

### Error Code Reference
- **1001**: File not found - Check paths and permissions
- **1002**: Invalid format - Validate file structure
- **1003**: Permission denied - Check access rights
- **1004**: Timeout exceeded - Increase timeout or simplify
- **1005**: Memory limit - Reduce file size or increase RAM
- **1006**: Inkscape error - Check Inkscape installation
- **1007**: Invalid parameters - Verify operation arguments

### Recovery Procedures
1. **Isolate the problem:** Test with simple operations first
2. **Check prerequisites:** Verify Inkscape and file access
3. **Simplify inputs:** Use smaller, simpler files for testing
4. **Update software:** Ensure latest versions of all components
5. **Collect diagnostics:** Enable logging and gather system info

## Getting Help

### Self-Service Resources
- **Built-in help:** `"Show me system help"`
- **Status check:** `"Get server diagnostics"`
- **Version info:** `"What version is running?"`

### Community Support
- Check GitHub issues for similar problems
- Review documentation for configuration examples
- Test with sample files to isolate issues

### Professional Support
- Contact maintainers for complex issues
- Provide complete diagnostic information
- Include reproduction steps and environment details

---

**Prevention Best Practices:**
1. Test configurations on sample files before production use
2. Keep Inkscape and MCP client updated
3. Monitor system resources during intensive operations
4. Maintain backups of important configuration files
5. Document working setups for team consistency