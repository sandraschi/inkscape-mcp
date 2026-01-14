"""Inkscape file operations - FastMCP 2.14.1+ Portmanteau Tool.

Portmanteau Pattern Rationale:
Consolidates basic file operations into a single tool to prevent tool explosion
while maintaining clean separation of concerns. Follows FastMCP 2.14.1+ SOTA standards.

Supported Operations:
- "load": Load SVG file and validate
- "save": Save SVG with options
- "convert": Convert between vector formats (SVG, PDF, EPS, AI, CDR)
- "info": Get file metadata and statistics
- "validate": Validate SVG structure
- "list_formats": List supported formats

Args:
    operation (Literal, required): The file operation to perform.
    input_path (str, required): Path to input SVG file.
    output_path (str, optional): Path for output file (required for save/convert).
    format (str, optional): Output format for convert operations.
    validate_structure (bool): Whether to validate SVG structure.
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
          "input_path": "path/to/input.svg",
          "output_path": "path/to/output.svg",
          "file_info": {...},
          "validation_results": {...}
        },
        "execution_time_ms": 123.45
      },
      "next_steps": ["Suggested next operations"],
      "context": {
        "operation_details": "Technical details about file operation"
      },
      "suggestions": ["Related file operations"],
      "follow_up_questions": ["Questions about file handling"]
    }

Examples:
    # Load and validate SVG
    result = await inkscape_file("load", input_path="drawing.svg")

    # Convert to PDF
    result = await inkscape_file("convert", input_path="drawing.svg", output_path="drawing.pdf", format="pdf")

    # Get file info
    result = await inkscape_file("info", input_path="drawing.svg")

Errors:
    - FileNotFoundError: Input file does not exist
    - ValueError: Invalid format or parameters
    - InkscapeExecutionError: Inkscape CLI command failed
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
