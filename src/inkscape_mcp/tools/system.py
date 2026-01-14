"""
GIMP System Operations Portmanteau Tool.

Comprehensive system management for GIMP MCP.
"""

from __future__ import annotations

import os
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class SystemResult(BaseModel):
    """Result model for system operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: Optional[str] = None


async def gimp_system(
    operation: Literal[
        "status",
        "help",
        "diagnostics",
        "cache",
        "config",
        "performance",
        "tools",
        "version",
    ],
    # Help parameters
    topic: Optional[str] = None,
    level: str = "basic",
    # Cache parameters
    cache_action: str = "status",
    cache_type: str = "all",
    # Config parameters
    config_key: Optional[str] = None,
    config_value: Optional[Any] = None,
    # Performance parameters
    operation_type: Optional[str] = None,
    time_range_hours: int = 24,
    # Dependencies
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Comprehensive system management portmanteau for GIMP MCP.

    PORTMANTEAU PATTERN RATIONALE:
    Instead of creating 8+ separate tools (one per system operation), this tool
    consolidates related system operations into a single interface. This design:
    - Prevents tool explosion (8 tools → 1 tool) while maintaining full functionality
    - Improves discoverability by grouping related operations together
    - Reduces cognitive load when working with system management
    - Enables consistent system interface across all operations
    - Follows FastMCP 2.13+ best practices for feature-rich MCP servers

    SUPPORTED OPERATIONS:
    - status: Get server and GIMP status
    - help: Get help on tools and usage
    - diagnostics: Run diagnostic checks
    - cache: Manage caches (status, clear)
    - config: View/modify configuration
    - performance: Get performance metrics
    - tools: List available tools
    - version: Get version information

    Args:
        operation: System operation to perform. MUST be one of:
            - "status": Server/GIMP status (no params needed)
            - "help": Get help (optional: topic, level)
            - "diagnostics": Run diagnostics (no params needed)
            - "cache": Cache management (requires: cache_action)
            - "config": Configuration (optional: config_key, config_value)
            - "performance": Performance metrics (optional: operation_type, time_range_hours)
            - "tools": List tools (no params needed)
            - "version": Version info (no params needed)

        topic: Help topic. Used by: help.
            Valid: "overview", "file", "transform", "color", "filter", "batch", "analysis"

        level: Help detail level. Used by: help.
            Valid: "basic" (default), "intermediate", "advanced", "expert"

        cache_action: Cache operation. Used by: cache.
            Valid: "status" (default), "clear", "optimize"

        cache_type: Cache to manage. Used by: cache.
            Valid: "all" (default), "thumbnails", "temp", "results"

        config_key: Configuration key. Used by: config.
            If None, returns all config. If set with config_value, updates config.

        config_value: New config value. Used by: config.
            Used with config_key to update configuration.

        operation_type: Filter metrics by operation. Used by: performance.

        time_range_hours: Time range for metrics. Used by: performance. Default: 24

    Returns:
        Dict containing system operation results.

    Examples:
        # Get server status
        gimp_system("status")

        # Get help on transforms
        gimp_system("help", topic="transform", level="intermediate")

        # Run diagnostics
        gimp_system("diagnostics")

        # Clear all caches
        gimp_system("cache", cache_action="clear")

        # Get performance metrics
        gimp_system("performance", time_range_hours=1)

        # List available tools
        gimp_system("tools")

        # Get version info
        gimp_system("version")
    """
    start_time = time.time()

    try:
        if operation == "status":
            result = await _get_status(cli_wrapper, config)
        elif operation == "help":
            result = _get_help(topic, level)
        elif operation == "diagnostics":
            result = await _run_diagnostics(cli_wrapper, config)
        elif operation == "cache":
            result = _manage_cache(cache_action, cache_type, config)
        elif operation == "config":
            result = _manage_config(config_key, config_value, config)
        elif operation == "performance":
            result = _get_performance(operation_type, time_range_hours)
        elif operation == "tools":
            result = _list_tools()
        elif operation == "version":
            result = _get_version()
        else:
            return SystemResult(
                success=False,
                operation=operation,
                message=f"Unknown operation: {operation}",
                error="Invalid operation",
            ).model_dump()

        execution_time = (time.time() - start_time) * 1000
        result["execution_time_ms"] = round(execution_time, 2)
        return result

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return SystemResult(
            success=False,
            operation=operation,
            message=f"System operation failed: {str(e)}",
            error=str(e),
            execution_time_ms=round(execution_time, 2),
        ).model_dump()


async def _get_status(cli_wrapper, config) -> Dict[str, Any]:
    """Get server and GIMP status."""
    import psutil

    # System info
    status_data = {
        "server": {
            "status": "running",
            "pid": os.getpid(),
            "uptime_seconds": time.time() - psutil.Process().create_time(),
        },
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "memory_available_gb": round(
                psutil.virtual_memory().available / (1024**3), 2
            ),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        },
        "gimp": {
            "available": False,
            "version": None,
            "path": None,
        },
    }

    # Check GIMP availability
    if cli_wrapper:
        try:
            gimp_path = getattr(config, "gimp_executable", None)
            if gimp_path and Path(gimp_path).exists():
                status_data["gimp"]["available"] = True
                status_data["gimp"]["path"] = gimp_path
        except Exception:
            pass

    return SystemResult(
        success=True,
        operation="status",
        message="Server running"
        + (
            " with GIMP" if status_data["gimp"]["available"] else " (GIMP not detected)"
        ),
        data=status_data,
    ).model_dump()


def _get_help(topic: Optional[str], level: str) -> Dict[str, Any]:
    """Get help information."""
    help_topics = {
        "overview": {
            "basic": "GIMP MCP Server provides image editing capabilities through MCP protocol.",
            "intermediate": """
GIMP MCP Server v3.0.0 - Portmanteau Architecture

This server exposes GIMP's image editing capabilities through 8 consolidated tools:
- gimp_file: Load, save, convert images
- gimp_transform: Resize, crop, rotate, flip
- gimp_color: Brightness, contrast, levels, curves
- gimp_filter: Blur, sharpen, noise, artistic effects
- gimp_layer: Layer management (requires GIMP)
- gimp_analysis: Quality analysis, statistics, comparison
- gimp_batch: Batch processing multiple images
- gimp_system: Server status, help, diagnostics
            """,
            "advanced": "Full API documentation available at https://github.com/sandraschi/gimp-mcp",
        },
        "file": {
            "basic": "Use gimp_file for loading, saving, and converting images.",
            "intermediate": """
gimp_file operations:
- load: Load image and get metadata
- save: Save image with format options
- convert: Convert between formats (PNG, JPG, WebP, TIFF)
- info: Get image metadata without loading
- validate: Check image integrity
- list_formats: Show supported formats
            """,
        },
        "transform": {
            "basic": "Use gimp_transform for resizing, cropping, and rotating images.",
            "intermediate": """
gimp_transform operations:
- resize: Change dimensions with aspect ratio control
- crop: Extract rectangular region
- rotate: Rotate by angle with fill options
- flip: Mirror horizontally or vertically
- scale: Scale by factor
- autocrop: Remove transparent/uniform borders
            """,
        },
        "color": {
            "basic": "Use gimp_color for color adjustments and corrections.",
            "intermediate": """
gimp_color operations:
- brightness_contrast: Adjust brightness and contrast
- levels: Tonal range adjustment
- curves: Fine-tune with control points
- hue_saturation: HSL adjustments
- colorize: Apply color tint
- threshold/posterize: Special effects
- desaturate: Convert to grayscale
- invert: Invert colors
- auto_levels/auto_color: Automatic corrections
            """,
        },
        "filter": {
            "basic": "Use gimp_filter for blur, sharpen, and artistic effects.",
            "intermediate": """
gimp_filter operations:
- blur: Gaussian, motion, zoom, pixelize
- sharpen: Unsharp mask, high pass
- noise: Add or reduce noise
- edge_detect: Sobel, Canny, Laplace
- artistic: Oilify, cartoon, pencil, emboss
- enhance: Sharpen, detail, smooth
- distort: Ripple, wave, twirl
- light_shadow: Vignette effects
            """,
        },
        "batch": {
            "basic": "Use gimp_batch for processing multiple images at once.",
            "intermediate": """
gimp_batch operations:
- resize: Batch resize to dimensions
- convert: Batch format conversion
- process: Apply chain of operations
- watermark: Add watermark to all images
- rename: Batch rename with patterns
- optimize: Optimize for web
            """,
        },
        "analysis": {
            "basic": "Use gimp_analysis for image quality assessment and statistics.",
            "intermediate": """
gimp_analysis operations:
- quality: Sharpness, noise, exposure analysis
- statistics: Mean, std, histogram
- histogram: Per-channel histogram data
- compare: PSNR, SSIM comparison
- detect_issues: Find overexposure, blur, noise
- report: Comprehensive analysis report
- metadata: Extract EXIF and other metadata
            """,
        },
    }

    if topic and topic in help_topics:
        help_content = help_topics[topic].get(
            level, help_topics[topic].get("basic", "")
        )
    else:
        # List all topics
        help_content = help_topics.get("overview", {}).get(
            level, help_topics["overview"]["basic"]
        )

    return SystemResult(
        success=True,
        operation="help",
        message=f"Help: {topic or 'overview'} ({level})",
        data={
            "topic": topic or "overview",
            "level": level,
            "content": help_content.strip(),
            "available_topics": list(help_topics.keys()),
        },
    ).model_dump()


async def _run_diagnostics(cli_wrapper, config) -> Dict[str, Any]:
    """Run diagnostic checks."""
    checks = []

    # Python check
    checks.append(
        {
            "name": "Python Version",
            "status": "pass" if sys.version_info >= (3, 10) else "warn",
            "message": f"Python {platform.python_version()}",
        }
    )

    # Required packages
    required_packages = ["PIL", "numpy", "pydantic", "fastmcp"]
    for pkg in required_packages:
        try:
            __import__(pkg.lower().replace("pil", "PIL"))
            checks.append(
                {"name": f"Package: {pkg}", "status": "pass", "message": "Installed"}
            )
        except ImportError:
            checks.append(
                {
                    "name": f"Package: {pkg}",
                    "status": "fail",
                    "message": "Not installed",
                }
            )

    # Disk space
    import shutil

    total, used, free = shutil.disk_usage("/")
    free_gb = free / (1024**3)
    checks.append(
        {
            "name": "Disk Space",
            "status": "pass" if free_gb > 1 else "warn",
            "message": f"{free_gb:.1f} GB free",
        }
    )

    # Memory
    import psutil

    mem = psutil.virtual_memory()
    checks.append(
        {
            "name": "Memory",
            "status": "pass" if mem.percent < 90 else "warn",
            "message": f"{mem.available / (1024**3):.1f} GB available ({100 - mem.percent:.0f}% free)",
        }
    )

    # GIMP check
    gimp_found = False
    if cli_wrapper:
        gimp_path = getattr(config, "gimp_executable", None)
        if gimp_path and Path(gimp_path).exists():
            gimp_found = True
    checks.append(
        {
            "name": "GIMP Installation",
            "status": "pass" if gimp_found else "warn",
            "message": "Found"
            if gimp_found
            else "Not detected (some features limited)",
        }
    )

    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")

    return SystemResult(
        success=failed == 0,
        operation="diagnostics",
        message=f"Diagnostics: {passed}/{len(checks)} passed",
        data={
            "checks": checks,
            "passed": passed,
            "failed": failed,
            "warnings": len(checks) - passed - failed,
        },
    ).model_dump()


def _manage_cache(action: str, cache_type: str, config) -> Dict[str, Any]:
    """Manage caches."""
    import tempfile

    temp_dir = Path(tempfile.gettempdir()) / "gimp_mcp"

    if action == "status":
        cache_size = 0
        cache_files = 0
        if temp_dir.exists():
            for f in temp_dir.rglob("*"):
                if f.is_file():
                    cache_size += f.stat().st_size
                    cache_files += 1

        return SystemResult(
            success=True,
            operation="cache",
            message=f"Cache: {cache_files} files, {cache_size / (1024 * 1024):.1f} MB",
            data={
                "action": "status",
                "cache_directory": str(temp_dir),
                "exists": temp_dir.exists(),
                "file_count": cache_files,
                "size_bytes": cache_size,
                "size_mb": round(cache_size / (1024 * 1024), 2),
            },
        ).model_dump()

    elif action == "clear":
        cleared = 0
        if temp_dir.exists():
            for f in list(temp_dir.rglob("*")):
                if f.is_file():
                    try:
                        f.unlink()
                        cleared += 1
                    except OSError:
                        pass

        return SystemResult(
            success=True,
            operation="cache",
            message=f"Cleared {cleared} cached files",
            data={"action": "clear", "files_cleared": cleared},
        ).model_dump()

    return SystemResult(
        success=False,
        operation="cache",
        message=f"Unknown cache action: {action}",
        error="Invalid action",
    ).model_dump()


def _manage_config(key: Optional[str], value: Optional[Any], config) -> Dict[str, Any]:
    """View or modify configuration."""
    if key is None:
        # Return all config
        config_data = {
            "gimp_executable": getattr(config, "gimp_executable", "auto"),
            "temp_directory": getattr(config, "temp_directory", "auto"),
            "max_file_size_mb": getattr(config, "max_file_size_mb", 500),
            "default_quality": getattr(config, "default_quality", 95),
            "log_level": getattr(config, "log_level", "INFO"),
        }

        return SystemResult(
            success=True,
            operation="config",
            message="Current configuration",
            data={"config": config_data},
        ).model_dump()

    # Config modification not implemented for safety
    return SystemResult(
        success=False,
        operation="config",
        message="Configuration modification not supported via API",
        error="Read-only",
    ).model_dump()


def _get_performance(
    operation_type: Optional[str], time_range_hours: int
) -> Dict[str, Any]:
    """Get performance metrics."""
    import psutil

    process = psutil.Process()

    metrics = {
        "process": {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / (1024**2),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage("/").percent,
        },
    }

    return SystemResult(
        success=True,
        operation="performance",
        message="Performance metrics",
        data=metrics,
    ).model_dump()


def _list_tools() -> Dict[str, Any]:
    """List available tools."""
    tools = [
        {
            "name": "gimp_file",
            "description": "File operations: load, save, convert, info, validate",
            "operations": [
                "load",
                "save",
                "convert",
                "info",
                "validate",
                "list_formats",
            ],
        },
        {
            "name": "gimp_transform",
            "description": "Geometric transforms: resize, crop, rotate, flip, scale",
            "operations": [
                "resize",
                "crop",
                "rotate",
                "flip",
                "scale",
                "perspective",
                "autocrop",
            ],
        },
        {
            "name": "gimp_color",
            "description": "Color adjustments: brightness, contrast, levels, curves, HSL",
            "operations": [
                "brightness_contrast",
                "levels",
                "curves",
                "color_balance",
                "hue_saturation",
                "colorize",
                "threshold",
                "posterize",
                "desaturate",
                "invert",
                "auto_levels",
                "auto_color",
            ],
        },
        {
            "name": "gimp_filter",
            "description": "Filters: blur, sharpen, noise, edge detection, artistic effects",
            "operations": [
                "blur",
                "sharpen",
                "noise",
                "edge_detect",
                "artistic",
                "enhance",
                "distort",
                "light_shadow",
            ],
        },
        {
            "name": "gimp_layer",
            "description": "Layer management: create, duplicate, merge, flatten (requires GIMP)",
            "operations": [
                "create",
                "duplicate",
                "delete",
                "merge",
                "flatten",
                "reorder",
                "properties",
                "info",
            ],
        },
        {
            "name": "gimp_analysis",
            "description": "Image analysis: quality, statistics, histogram, compare",
            "operations": [
                "quality",
                "statistics",
                "histogram",
                "compare",
                "detect_issues",
                "report",
                "metadata",
            ],
        },
        {
            "name": "gimp_batch",
            "description": "Batch processing: resize, convert, watermark, optimize",
            "operations": [
                "resize",
                "convert",
                "process",
                "watermark",
                "rename",
                "optimize",
            ],
        },
        {
            "name": "gimp_system",
            "description": "System: status, help, diagnostics, cache, config",
            "operations": [
                "status",
                "help",
                "diagnostics",
                "cache",
                "config",
                "performance",
                "tools",
                "version",
            ],
        },
    ]

    return SystemResult(
        success=True,
        operation="tools",
        message=f"{len(tools)} portmanteau tools available",
        data={
            "tools": tools,
            "total_tools": len(tools),
            "total_operations": sum(len(t["operations"]) for t in tools),
        },
    ).model_dump()


def _get_version() -> Dict[str, Any]:
    """Get version information."""
    return SystemResult(
        success=True,
        operation="version",
        message="GIMP MCP Server v3.0.0",
        data={
            "server_version": "3.0.0",
            "architecture": "portmanteau",
            "fastmcp_version": "2.13+",
            "python_version": platform.python_version(),
            "platform": platform.system(),
        },
    ).model_dump()
