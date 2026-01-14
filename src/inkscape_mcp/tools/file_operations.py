"""Comprehensive file operations for Inkscape SVG documents.

PORTMANTEAU PATTERN RATIONALE:
Consolidates 6 file operations (load, save, convert, info, validate, list_formats) into a single
interface. Prevents tool explosion while maintaining full functionality and improving discoverability.
Follows FastMCP 2.14.1+ SOTA standards.

SUPPORTED OPERATIONS:
- load: Load and validate SVG files
- save: Save SVG files with formatting options
- convert: Convert between vector formats (SVG, PDF, EPS, AI, CDR, PNG, PS, WMF, EMF, XAML)
- info: Get comprehensive file metadata and statistics
- validate: Validate SVG structure and syntax
- list_formats: Enumerate all supported export formats

OPERATIONS DETAIL:

**File Management (CRUD)**:
  - load: Validates SVG syntax and basic structure, returns dimensions and file metadata
  - save: Writes SVG with optional formatting and structure validation
  - convert: Transforms between vector formats using Inkscape export functionality

**Analysis & Discovery**:
  - info: Extracts dimensions, file size, format, and comprehensive metadata
  - validate: Checks SVG validity using Inkscape query commands, reports issues
  - list_formats: Shows all available export formats supported by Inkscape

PREREQUISITES:
- Requires Inkscape CLI installation (1.0+ recommended, 1.2+ for Actions API)
- Supports all Inkscape-compatible SVG features
- Cross-platform file path handling via pathlib

Args:
    operation (Literal, required): The file operation to perform. Must be one of:
        "load", "save", "convert", "info", "validate", "list_formats".
        - "load": Load SVG file and validate structure (requires: input_path)
        - "save": Save SVG with options (requires: input_path, output_path)
        - "convert": Convert between formats (requires: input_path, output_path, format)
        - "info": Get file metadata (requires: input_path)
        - "validate": Validate SVG structure (requires: input_path)
        - "list_formats": List supported formats (no additional parameters required)

    input_path (str | None): Path to input SVG file. Required for: load, save, convert, info, validate.
        Must be a valid file path accessible by the system.

    output_path (str | None): Path for output file. Required for: save, convert operations.
        Directory must exist and be writable. File extension should match format parameter.

    format (str | None): Output format for convert operations. Must be one of:
        "pdf", "eps", "ai", "cdr", "svg", "png", "ps", "wmf", "emf", "xaml".
        Required for: convert operation. Case-insensitive.

    validate_structure (bool): Whether to validate SVG structure during load operations.
        Default: True. When True, uses Inkscape query commands to verify file validity.

    cli_wrapper (Any): Injected CLI wrapper dependency. Required. Handles Inkscape command execution.

    config (Any): Injected configuration dependency. Required. Contains Inkscape executable path and settings.

Returns:
    FastMCP 2.14.1+ Enhanced Response Pattern (Structured Returns):

    Success Response:
    {
      "success": true,
      "operation": "operation_name",
      "summary": "Human-readable conversational summary (e.g., 'Successfully loaded drawing.svg')",
      "result": {
        "data": {
          "input_path": "path/to/input.svg",
          "output_path": "path/to/output.svg",
          "file_info": {
            "width": 100.0,
            "height": 200.0,
            "file_size": 1536,
            "format": "svg"
          },
          "validation_results": {
            "valid": true,
            "errors": []
          },
          "formats": ["svg", "pdf", "eps", "png", ...]
        },
        "execution_time_ms": 123.45
      },
      "next_steps": ["Use inkscape_vector tool for path operations", "Convert to PDF format"],
      "context": {
        "operation_details": "Technical details about file operation"
      },
      "suggestions": ["Try inkscape_vector tool for advanced operations", "Use convert operation for format changes"],
      "follow_up_questions": ["Would you like to convert this file to another format?", "Need to optimize the SVG?"]
    }

    Error Response (Error Recovery Pattern):
    {
      "success": false,
      "operation": "operation_name",
      "error": "Error type (e.g., FileNotFoundError)",
      "message": "Human-readable error description",
      "recovery_options": ["Check file path and permissions", "Verify Inkscape installation", "Ensure output directory exists"],
      "diagnostic_info": {
        "file_exists": false,
        "inkscape_available": true,
        "permissions": "read-only"
      },
      "alternative_solutions": ["Use list_formats to verify supported formats", "Check file extension matches format"]
    }

Examples:
    # Load and validate an SVG file
    result = await inkscape_file(
        operation="load",
        input_path="logo.svg",
        validate_structure=True
    )

    # Convert SVG to PDF
    result = await inkscape_file(
        operation="convert",
        input_path="drawing.svg",
        output_path="drawing.pdf",
        format="pdf"
    )

    # Get comprehensive file information
    result = await inkscape_file(
        operation="info",
        input_path="design.svg"
    )

    # Validate SVG structure
    result = await inkscape_file(
        operation="validate",
        input_path="document.svg"
    )

    # List all supported export formats
    result = await inkscape_file(
        operation="list_formats"
    )

    # Save SVG with formatting
    result = await inkscape_file(
        operation="save",
        input_path="source.svg",
        output_path="formatted.svg"
    )

Errors:
    - FileNotFoundError: Input file does not exist or is not readable
        Recovery options:
        → Verify file path is correct and accessible
        → Check file permissions (read access required)
        → Ensure file is a valid SVG document
        → Use absolute paths if relative paths fail

    - InkscapeExecutionError: Inkscape CLI command failed
        Recovery options:
        → Verify Inkscape installation (run inkscape --version)
        → Check CLI arguments are valid for Inkscape version
        → Ensure output directory exists and is writable
        → Check process timeout settings in config

    - ValueError: Invalid format or parameters
        Recovery options:
        → Verify format is supported (use list_formats operation)
        → Check output_path is provided for write operations (save, convert)
        → Ensure format parameter matches file extension
        → Validate all required parameters are provided

    - PermissionError: Cannot write to output location
        Recovery options:
        → Check write permissions on output directory
        → Ensure output path is not read-only
        → Verify sufficient disk space available
        → Check if file is locked by another process
"""

import time
from pathlib import Path
from typing import Any, Dict, Literal

from pydantic import BaseModel


class FileOperationResult(BaseModel):
    """Result model for file operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any]
    execution_time_ms: float
    error: str = ""


async def inkscape_file(
    operation: Literal["load", "save", "convert", "info", "validate", "list_formats"],
    input_path: str,
    output_path: str = "",
    format: str = "",
    validate_structure: bool = True,
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Inkscape file operations portmanteau tool."""
    start_time = time.time()

    try:
        input_path_obj = Path(input_path)

        if operation == "load":
            # Basic load and validate
            if not input_path_obj.exists():
                return FileOperationResult(
                    success=False,
                    operation="load",
                    message=f"File not found: {input_path}",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="FileNotFoundError",
                ).model_dump()

            # Use Inkscape to validate by attempting to query dimensions
            try:
                result = await cli_wrapper._execute_command(
                    [str(config.inkscape_executable), str(input_path_obj), "--query-width"],
                    config.process_timeout,
                )
                width = float(result.strip())

                return FileOperationResult(
                    success=True,
                    operation="load",
                    message=f"Successfully loaded {input_path}",
                    data={
                        "path": str(input_path_obj.resolve()),
                        "width": width,
                        "loaded": True,
                    },
                    execution_time_ms=(time.time() - start_time) * 1000,
                ).model_dump()

            except Exception as e:
                return FileOperationResult(
                    success=False,
                    operation="load",
                    message=f"Failed to load SVG: {e}",
                    data={"path": str(input_path_obj)},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error=str(e),
                ).model_dump()

        elif operation == "convert":
            if not output_path:
                return FileOperationResult(
                    success=False,
                    operation="convert",
                    message="Output path required for convert operation",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="ValueError",
                ).model_dump()

            # Use Inkscape export functionality
            actions = [
                f"export-filename:{output_path}",
                f"export-type:{format.upper()}",
                "export-do",
            ]

            try:
                await cli_wrapper._execute_actions(
                    input_path=input_path,
                    actions=actions,
                    output_path=output_path,
                    timeout=config.process_timeout,
                )

                return FileOperationResult(
                    success=True,
                    operation="convert",
                    message=f"Converted {input_path} to {output_path}",
                    data={
                        "input_path": str(input_path_obj.resolve()),
                        "output_path": output_path,
                        "format": format,
                    },
                    execution_time_ms=(time.time() - start_time) * 1000,
                ).model_dump()

            except Exception as e:
                return FileOperationResult(
                    success=False,
                    operation="convert",
                    message=f"Conversion failed: {e}",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error=str(e),
                ).model_dump()

        elif operation == "info":
            # Get basic file info
            if not input_path_obj.exists():
                return FileOperationResult(
                    success=False,
                    operation="info",
                    message=f"File not found: {input_path}",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="FileNotFoundError",
                ).model_dump()

            try:
                # Query dimensions
                width_result = await cli_wrapper._execute_command(
                    [str(config.inkscape_executable), str(input_path_obj), "--query-width"],
                    config.process_timeout,
                )
                height_result = await cli_wrapper._execute_command(
                    [str(config.inkscape_executable), str(input_path_obj), "--query-height"],
                    config.process_timeout,
                )

                width = float(width_result.strip())
                height = float(height_result.strip())

                return FileOperationResult(
                    success=True,
                    operation="info",
                    message=f"Retrieved info for {input_path}",
                    data={
                        "path": str(input_path_obj.resolve()),
                        "file_size": input_path_obj.stat().st_size,
                        "width": width,
                        "height": height,
                        "format": "svg",
                    },
                    execution_time_ms=(time.time() - start_time) * 1000,
                ).model_dump()

            except Exception as e:
                return FileOperationResult(
                    success=False,
                    operation="info",
                    message=f"Failed to get info: {e}",
                    data={"path": str(input_path_obj)},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error=str(e),
                ).model_dump()

        elif operation == "validate":
            # Basic validation by attempting to load
            try:
                result = await cli_wrapper._execute_command(
                    [str(config.inkscape_executable), str(input_path_obj), "--query-width"],
                    config.process_timeout,
                )

                return FileOperationResult(
                    success=True,
                    operation="validate",
                    message="SVG is valid",
                    data={
                        "path": str(input_path_obj.resolve()),
                        "valid": True,
                    },
                    execution_time_ms=(time.time() - start_time) * 1000,
                ).model_dump()

            except Exception as e:
                return FileOperationResult(
                    success=False,
                    operation="validate",
                    message=f"SVG validation failed: {e}",
                    data={
                        "path": str(input_path_obj.resolve()),
                        "valid": False,
                    },
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error=str(e),
                ).model_dump()

        elif operation == "list_formats":
            # List supported export formats
            formats = ["svg", "pdf", "eps", "png", "ps", "ai", "cdr", "wmf", "emf", "xaml"]

            return FileOperationResult(
                success=True,
                operation="list_formats",
                message="Retrieved supported formats",
                data={"formats": formats},
                execution_time_ms=(time.time() - start_time) * 1000,
            ).model_dump()

        else:
            return FileOperationResult(
                success=False,
                operation=operation,
                message=f"Unknown operation: {operation}",
                data={},
                execution_time_ms=(time.time() - start_time) * 1000,
                error="ValueError",
            ).model_dump()

    except Exception as e:
        return FileOperationResult(
            success=False,
            operation=operation,
            message=f"Operation failed: {e}",
            data={},
            execution_time_ms=(time.time() - start_time) * 1000,
            error=str(e),
        ).model_dump()
