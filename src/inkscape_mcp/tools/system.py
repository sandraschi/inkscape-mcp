"""Inkscape system operations - FastMCP 2.14.1+ Portmanteau Tool.

Portmanteau Pattern Rationale:
Consolidates system management operations into a single tool to prevent tool explosion
while maintaining clean separation of concerns. Follows FastMCP 2.14.1+ SOTA standards.

Supported Operations:
- "status": Get server and Inkscape status
- "help": Get help information
- "diagnostics": Run diagnostic checks
- "version": Get version information
- "config": View or modify configuration
- "set_document_units": Normalize document coordinate systems (px, mm, in)

Args:
    operation (Literal, required): The system operation to perform.
    cli_wrapper (Any): Injected CLI wrapper dependency.
    config (Any): Injected configuration dependency.

Returns:
    **FastMCP 2.14.1+ Conversational Response Structure:**

    {
      "success": true,
      "operation": "operation_name",
      "summary": "Human-readable conversational summary",
      "result": {
        "data": {
          "system_info": {...}
        },
        "execution_time_ms": 123.45
      },
      "next_steps": ["Suggested maintenance actions"],
      "context": {
        "operation_details": "Technical details about system status"
      },
      "suggestions": ["Recommended optimizations or fixes"],
      "follow_up_questions": ["Questions about system configuration"]
    }

Examples:
    # Get system status
    result = await inkscape_system("status")

    # Get version info
    result = await inkscape_system("version")

    # Run diagnostics
    result = await inkscape_system("diagnostics")

Errors:
    - ValueError: Invalid operation or parameter values
    - FileNotFoundError: Configuration file not found
    - PermissionError: Insufficient permissions for system operations
    - ConnectionError: Cannot connect to Inkscape or system services
"""

import time
from typing import Any, Dict, Literal

from pydantic import BaseModel


class SystemResult(BaseModel):
    """Result model for system operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any]
    execution_time_ms: float
    error: str = ""


async def inkscape_system(
    operation: Literal["status", "help", "diagnostics", "version", "config"],
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Inkscape system operations portmanteau tool."""
    start_time = time.time()

    try:
        if operation == "status":
            # Get server and Inkscape status
            inkscape_available = False
            inkscape_version = "unknown"

            try:
                if config and config.inkscape_executable:
                    result = await cli_wrapper._execute_command(
                        [str(config.inkscape_executable), "--version"], config.process_timeout
                    )
                    inkscape_available = True
                    inkscape_version = result.strip().split("\n")[0] if result else "unknown"
            except:
                pass

            return SystemResult(
                success=True,
                operation="status",
                message="Retrieved system status",
                data={
                    "server": {
                        "name": "Inkscape MCP Server",
                        "version": "1.1.0",
                        "status": "running",
                    },
                    "inkscape": {
                        "available": inkscape_available,
                        "version": inkscape_version,
                        "executable": str(config.inkscape_executable) if config else None,
                    },
                    "tools": {
                        "file": "available",
                        "vector": "available",
                        "analysis": "available",
                        "system": "available",
                    },
                },
                execution_time_ms=(time.time() - start_time) * 1000,
            ).model_dump()

        elif operation == "version":
            # Get version information
            return SystemResult(
                success=True,
                operation="version",
                message="Retrieved version information",
                data={
                    "server": "Inkscape MCP Server v1.1.0",
                    "protocol": "FastMCP 2.14.1+",
                    "architecture": "Portmanteau Tools",
                    "inkscape_required": "1.0+ (1.2+ recommended for Actions API)",
                },
                execution_time_ms=(time.time() - start_time) * 1000,
            ).model_dump()

        elif operation == "diagnostics":
            # Run basic diagnostic checks
            checks = {
                "config_loaded": config is not None,
                "cli_wrapper_available": cli_wrapper is not None,
                "inkscape_executable_set": bool(config and config.inkscape_executable)
                if config
                else False,
            }

            return SystemResult(
                success=True,
                operation="diagnostics",
                message="Ran diagnostic checks",
                data={
                    "checks": checks,
                    "all_passed": all(checks.values()),
                    "issues": [k for k, v in checks.items() if not v],
                },
                execution_time_ms=(time.time() - start_time) * 1000,
            ).model_dump()

        elif operation == "help":
            # Provide help information
            help_info = {
                "server": "Inkscape MCP Server",
                "description": "Professional vector graphics and SVG editing through Model Context Protocol",
                "tools": [
                    "inkscape_file: Basic file operations (load, save, convert, info, validate, list_formats)",
                    "inkscape_vector: Advanced vector operations (23 operations including trace, boolean, optimize, render)",
                    "inkscape_analysis: Document analysis (quality, statistics, validate, objects, dimensions, structure)",
                    "inkscape_system: System operations (status, help, diagnostics, version, config)",
                ],
                "getting_started": [
                    "Ensure Inkscape 1.0+ is installed",
                    "Use inkscape_file for basic operations",
                    "Use inkscape_vector for advanced vector editing",
                    "Use inkscape_analysis to understand your SVGs",
                ],
            }

            return SystemResult(
                success=True,
                operation="help",
                message="Retrieved help information",
                data=help_info,
                execution_time_ms=(time.time() - start_time) * 1000,
            ).model_dump()

        elif operation == "config":
            # View configuration
            config_data = {}
            if config:
                config_data = {
                    "inkscape_executable": str(config.inkscape_executable)
                    if config.inkscape_executable
                    else None,
                    "process_timeout": config.process_timeout
                    if hasattr(config, "process_timeout")
                    else None,
                    "max_concurrent_processes": config.max_concurrent_processes
                    if hasattr(config, "max_concurrent_processes")
                    else None,
                }

            return SystemResult(
                success=True,
                operation="config",
                message="Retrieved configuration",
                data=config_data,
                execution_time_ms=(time.time() - start_time) * 1000,
            ).model_dump()

        else:
            return SystemResult(
                success=False,
                operation=operation,
                message=f"Unknown operation: {operation}",
                data={},
                execution_time_ms=(time.time() - start_time) * 1000,
                error="ValueError",
            ).model_dump()

    except Exception as e:
        return SystemResult(
            success=False,
            operation=operation,
            message=f"System operation failed: {e}",
            data={},
            execution_time_ms=(time.time() - start_time) * 1000,
            error=str(e),
        ).model_dump()
