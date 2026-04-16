# Troubleshooting Guide

## Installation Issues

### Inkscape Not Found

**Error:** `Inkscape executable not found`

**Solutions:**
1. Install Inkscape from the official website
2. Add Inkscape to your system PATH
3. Specify the full path in `config.yaml`:
   ```yaml
   inkscape_executable: "/path/to/inkscape.exe"
   ```

### Python Version Issues

**Error:** `Python version not supported`

**Solutions:**
- Use Python 3.10 or higher
- Check version with `python --version`
- Create virtual environment with correct Python version

### Dependency Installation Failed

**Error:** `pip install` fails

**Solutions:**
- Upgrade pip: `python -m pip install --upgrade pip`
- Use virtual environment
- Check network connectivity
- Install build dependencies (Linux/macOS)

## Runtime Issues

### Operation Timeout

**Error:** `Operation timed out`

**Solutions:**
- Increase timeout in config:
  ```yaml
  process_timeout: 60
  ```
- Check system resources (CPU/memory)
- Simplify the operation or reduce file size

### File Not Found

**Error:** `Input file not found`

**Solutions:**
- Use absolute paths
- Check file permissions
- Ensure file exists before operation
- Verify working directory

### Invalid SVG Format

**Error:** `Invalid or corrupted SVG file`

**Solutions:**
- Validate SVG with `inkscape_file(operation="validate")`
- Check SVG namespace declarations
- Repair with text editor if necessary
- Use well-formed SVG sources

## AI Generation Issues

### Generation Failed

**Error:** `AI model generation failed`

**Solutions:**
- Check network connectivity for AI services
- Verify API keys if required
- Try different model or quality settings
- Reduce description complexity

### Quality Issues

**Problem:** Generated SVG quality is poor

**Solutions:**
- Use higher quality settings
- Provide more detailed descriptions
- Use appropriate style presets
- Apply post-processing operations

### Style Not Applied

**Problem:** Style preset not working as expected

**Solutions:**
- Verify preset name spelling
- Try different style presets
- Provide style hints in description
- Check generation logs

## Extension Issues

### Extension Not Found

**Error:** `Extension not available`

**Solutions:**
- Install the extension in Inkscape
- Check extension directory permissions
- Restart the MCP server
- Verify extension ID

### Extension Execution Failed

**Error:** `Extension execution failed`

**Solutions:**
- Check extension parameters
- Verify input file compatibility
- Review extension documentation
- Try with simpler parameters

## Platform-Specific Issues

### Windows Issues

**Common Problems:**
- PATH environment variable not set
- Permission issues with temp directories
- Inkscape GUI conflicts

**Solutions:**
- Add Inkscape to system PATH
- Run as administrator if needed
- Use `--batch-process` flag

### macOS Issues

**Common Problems:**
- Homebrew installation conflicts
- Permission issues with system directories

**Solutions:**
- Install via Homebrew: `brew install inkscape`
- Check /usr/local permissions
- Use absolute paths

### Linux Issues

**Common Problems:**
- Missing system dependencies
- Display server conflicts
- Library version conflicts

**Solutions:**
- Install required packages: `sudo apt install inkscape`
- Use `--batch-process` flag
- Check library dependencies

## Performance Issues

### Slow Operations

**Causes:**
- Large file sizes
- Complex operations
- System resource constraints
- Network latency (for AI operations)

**Solutions:**
- Reduce file sizes
- Use simpler operations
- Increase system resources
- Cache frequent operations

### Memory Issues

**Error:** `Out of memory`

**Solutions:**
- Reduce concurrent operations in config
- Process files in smaller batches
- Close other applications
- Add more RAM or use smaller files

### High CPU Usage

**Causes:**
- Multiple concurrent operations
- Complex AI generation
- Large file processing

**Solutions:**
- Reduce `max_concurrent_processes`
- Use lower quality settings
- Process sequentially instead of parallel

## Configuration Issues

### Config Not Loaded

**Problem:** Configuration changes not applied

**Solutions:**
- Check YAML syntax
- Use absolute paths
- Restart the server
- Verify file permissions

### Invalid Configuration

**Error:** `Configuration validation failed`

**Solutions:**
- Check YAML indentation
- Verify parameter types
- Review documentation for valid values
- Use default configuration as template

## Network Issues

### Connection Refused

**Error:** `Connection to MCP server failed`

**Solutions:**
- Check if server is running
- Verify port configuration
- Check firewall settings
- Use correct server URL

### Timeout Issues

**Problem:** Network operations timeout

**Solutions:**
- Increase timeout values
- Check network connectivity
- Reduce request complexity
- Use local operations when possible

## Logging and Debugging

### Enable Debug Logging

Add to configuration:
```yaml
logging:
  level: DEBUG
  file: inkscape-mcp.log
```

### Check Logs

Common log locations:
- Console output (when running directly)
- System log files
- Application-specific log directory

### Common Debug Steps

1. Enable verbose logging
2. Check system resources
3. Verify file permissions
4. Test with minimal example
5. Check network connectivity
6. Review error messages carefully

## Getting Help

### Documentation Resources
- [README.md](README.md) - Basic usage
- [USAGE.md](USAGE.md) - Detailed usage examples
- [API.md](API.md) - Complete API reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details

### Community Support
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Documentation wiki for tutorials

### Diagnostic Information

When reporting issues, include:
- Operating system and version
- Python version
- Inkscape version
- Full error message and stack trace
- Configuration file (without sensitive data)
- Steps to reproduce the issue
