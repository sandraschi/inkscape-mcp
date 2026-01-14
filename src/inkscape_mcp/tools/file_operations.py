"""
Inkscape File Operations Portmanteau Tool.

Comprehensive file management for Inkscape MCP, consolidating all file I/O
operations into a single unified interface for SVG and vector graphics files.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class FileOperationResult(BaseModel):
    """Result model for file operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: Optional[str] = None


async def inkscape_file(
    operation: Literal["load", "save", "convert", "info", "validate", "list_formats"],
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    format: Optional[str] = None,
    quality: int = 95,
    metadata: bool = True,
    overwrite: bool = False,
    compression: Optional[str] = None,
    # Injected dependencies
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Comprehensive file management portmanteau for Inkscape MCP.

    PORTMANTEAU PATTERN RATIONALE:
    Instead of creating 6 separate tools (one per operation), this tool consolidates
    related file operations into a single interface. This design:
    - Prevents tool explosion (6 tools → 1 tool) while maintaining full functionality
    - Improves discoverability by grouping related operations together
    - Reduces cognitive load when working with file management tasks
    - Enables consistent file interface across all operations
    - Follows FastMCP 2.13+ best practices for feature-rich MCP servers

    SUPPORTED OPERATIONS:
    - load: Load an SVG/vector file and return basic metadata
    - save: Save SVG file with optional optimization
    - convert: Convert between vector formats (SVG, PDF, EPS, AI, CDR)
    - info: Get comprehensive SVG metadata (dimensions, objects, layers)
    - validate: Validate SVG file structure and compliance
    - list_formats: List all supported vector graphics formats

    Args:
        operation: The file operation to perform. MUST be one of:
            - "load": Load image file (requires: input_path)
            - "save": Save image file (requires: input_path, output_path)
            - "convert": Convert format (requires: input_path, output_path or format)
            - "info": Get image metadata (requires: input_path)
            - "validate": Validate image file (requires: input_path)
            - "list_formats": List supported formats (no parameters required)

        input_path: Path to source SVG/vector file. Required for: load, save, convert, info, validate.
            Supports absolute or relative paths. Example: "C:/designs/logo.svg"

        output_path: Path for output file. Required for: save, convert operations.
            If omitted for convert, generates path from input with new extension.

        format: Target format for conversion. Used by: convert, save operations.
            Valid: "svg", "pdf", "eps", "ai", "cdr", "odg", "plt"
            Default: Inferred from output_path extension.

        quality: Export quality for raster conversions (1-100). Used by: convert operations.
            Default: 95. Only applies when converting to raster formats like PNG.

        metadata: Preserve SVG metadata. Used by: save, convert operations.
            Default: True. Set False to strip metadata and comments.

        overwrite: Overwrite existing output file. Used by: save, convert operations.
            Default: False. Raises error if file exists and overwrite=False.

        compression: Compression level for PDF/EPS. Used by: convert operations.
            Range: 0-9 (0=none, 9=maximum). Default: 6.

    Returns:
        Dict containing operation results:
        {
            "success": bool,           # Whether operation succeeded
            "operation": str,          # Operation that was performed
            "message": str,            # Human-readable result message
            "data": {                  # Operation-specific data
                # For load/info:
                "width": int,          # Image width in pixels
                "height": int,         # Image height in pixels
                "format": str,         # Image format (png, jpg, etc.)
                "color_mode": str,     # RGB, RGBA, Grayscale, etc.
                "bit_depth": int,      # Bits per channel
                "file_size_bytes": int,# File size
                "has_alpha": bool,     # Has transparency
                "metadata": dict,      # EXIF and other metadata

                # For save/convert:
                "output_path": str,    # Path to saved file
                "output_size_bytes": int,
                "compression_ratio": float,

                # For list_formats:
                "read_formats": list,  # Formats that can be loaded
                "write_formats": list, # Formats that can be saved
            },
            "execution_time_ms": float,# Operation duration
            "error": str | None        # Error message if failed
        }

    Examples:
        # Load image and get metadata
        gimp_file("load", input_path="photo.jpg")

        # Convert PNG to WebP with quality setting
        gimp_file("convert", input_path="image.png", format="webp", quality=85)

        # Save with specific compression
        gimp_file("save", input_path="edited.xcf", output_path="final.png", compression="best")

        # Get image info without loading
        gimp_file("info", input_path="large_image.tiff")

        # Validate image file
        gimp_file("validate", input_path="suspect.jpg")

        # List supported formats
        gimp_file("list_formats")

    Errors:
        - FileNotFoundError: Input file does not exist
        - FileExistsError: Output file exists and overwrite=False
        - ValueError: Invalid format or quality value
        - PermissionError: Cannot read/write to specified path
        - RuntimeError: GIMP processing failed
    """
    start_time = time.time()

    try:
        # Validate operation
        valid_operations = [
            "load",
            "save",
            "convert",
            "info",
            "validate",
            "list_formats",
        ]
        if operation not in valid_operations:
            return FileOperationResult(
                success=False,
                operation=operation,
                message=f"Invalid operation: {operation}",
                error=f"Operation must be one of: {valid_operations}",
            ).model_dump()

        # Handle list_formats - no input needed
        if operation == "list_formats":
            return _list_formats(config)

        # Validate input_path for operations that need it
        if operation in ["load", "save", "convert", "info", "validate"]:
            if not input_path:
                return FileOperationResult(
                    success=False,
                    operation=operation,
                    message="input_path is required",
                    error="Missing required parameter: input_path",
                ).model_dump()

            input_path_obj = Path(input_path)
            if not input_path_obj.exists():
                return FileOperationResult(
                    success=False,
                    operation=operation,
                    message=f"File not found: {input_path}",
                    error=f"Input file does not exist: {input_path}",
                ).model_dump()

        # Dispatch to specific operation handlers
        if operation == "load":
            result = await _load_svg(input_path, cli_wrapper, config)
        elif operation == "save":
            if not output_path:
                return FileOperationResult(
                    success=False,
                    operation=operation,
                    message="output_path is required for save",
                    error="Missing required parameter: output_path",
                ).model_dump()
            result = await _save_svg(input_path, output_path, overwrite, cli_wrapper, config)
        elif operation == "convert":
            result = await _convert_svg(
                input_path,
                output_path,
                format,
                quality,
                overwrite,
                compression,
                cli_wrapper,
                config,
            )
        elif operation == "info":
            result = await _get_svg_info(input_path, cli_wrapper, config)
        elif operation == "validate":
            result = await _validate_svg(input_path, cli_wrapper, config)
        else:
            result = FileOperationResult(
                success=False,
                operation=operation,
                message=f"Operation not implemented: {operation}",
                error="Operation handler not found",
            )

        # Add execution time
        execution_time = (time.time() - start_time) * 1000
        if isinstance(result, dict):
            result["execution_time_ms"] = round(execution_time, 2)
        else:
            result.execution_time_ms = round(execution_time, 2)
            result = result.model_dump()

        return result

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return FileOperationResult(
            success=False,
            operation=operation,
            message=f"Operation failed: {str(e)}",
            error=str(e),
            execution_time_ms=round(execution_time, 2),
        ).model_dump()


def _list_formats(config: Any) -> Dict[str, Any]:
    """List supported image formats."""
    # Inkscape primarily works with SVG but can export to various formats
    read_formats = [
        "svg",      # Native SVG format
        "svgz",     # Compressed SVG
        "ai",       # Adobe Illustrator
        "cdr",      # CorelDRAW
        "vsd",      # Microsoft Visio
        "odg",      # OpenDocument Graphics
        "pdf",      # PDF (import only)
    ]
    export_formats = [
        "svg",      # Optimized SVG
        "svgz",     # Compressed SVG
        "png",      # Raster PNG
        "pdf",      # PDF document
        "eps",      # Encapsulated PostScript
        "ps",       # PostScript
        "ai",       # Adobe Illustrator
        "odg",      # OpenDocument Graphics
        "plt",      # HPGL plotter
        "dxf",      # AutoCAD DXF
    ]

    return FileOperationResult(
        success=True,
        operation="list_formats",
        message=f"Inkscape supports {len(read_formats)} import and {len(export_formats)} export formats",
        data={
            "read_formats": sorted(read_formats),
            "export_formats": sorted(export_formats),
            "recommended": {
                "lossless": ["png", "tiff", "webp"],
                "lossy": ["jpg", "webp"],
                "native": ["xcf"],
                "web": ["png", "jpg", "webp", "gif"],
            },
        },
    ).model_dump()


async def _load_svg(
    input_path: str, cli_wrapper: Any, config: Any
) -> Dict[str, Any]:
    """Load SVG file and return basic metadata using Inkscape."""
    import time
    start_time = time.time()

    try:
        # Use Inkscape to get document information
        result = await cli_wrapper.get_document_info(input_path)

        input_path_obj = Path(input_path)

        # Parse Inkscape output for dimensions and object count
        # This is a simplified implementation - in practice you'd parse the actual output
        data = {
            "file_size_bytes": input_path_obj.stat().st_size,
            "file_size_mb": round(input_path_obj.stat().st_size / (1024 * 1024), 2),
            "path": str(input_path_obj.resolve()),
            "format": "SVG",
            "is_vector": True,
            "inkscape_output": result,
        }

        return {
            "success": True,
            "message": f"Successfully loaded SVG: {Path(input_path).name}",
            "data": data,
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to load SVG: {e}",
            "error": str(e),
            "execution_time_ms": (time.time() - start_time) * 1000,
        }
            "HSV": 8,
            "I": 32,
            "F": 32,
            "LA": 8,
            "PA": 8,
            "I;16": 16,
            "I;16L": 16,
            "I;16B": 16,
        }
        data["bit_depth"] = mode_depths.get(img.mode, 8)

        # Include metadata if requested
        if include_metadata:
            metadata = {}
            if hasattr(img, "_getexif") and img._getexif():
                from PIL.ExifTags import TAGS

                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if isinstance(value, bytes):
                        value = value.decode("utf-8", errors="ignore")
                    metadata[tag] = str(value)
            data["metadata"] = metadata

    return FileOperationResult(
        success=True,
        operation="load",
        message=f"Loaded {data['width']}x{data['height']} {data['format']} image",
        data=data,
    ).model_dump()


async def _save_svg(
    input_path: str,
    output_path: str,
    overwrite: bool,
    cli_wrapper: Any,
    config: Any,
) -> Dict[str, Any]:
    """Save SVG file to specified path."""
    import time
    import shutil
    start_time = time.time()

    input_path_obj = Path(input_path)
    output_path_obj = Path(output_path)

    try:
        # Check overwrite
        if output_path_obj.exists() and not overwrite:
            return {
                "success": False,
                "message": f"Output file exists and overwrite=False: {output_path}",
                "error": "File exists",
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        # For SVG files, we can simply copy them
        # In a more advanced implementation, we could use Inkscape to optimize/cleanup
        shutil.copy2(input_path_obj, output_path_obj)

        output_size = output_path_obj.stat().st_size

        return {
            "success": True,
            "message": f"Successfully saved SVG to {output_path}",
            "data": {
                "output_path": str(output_path_obj.resolve()),
                "file_size_bytes": output_size,
                "file_size_mb": round(output_size / (1024 * 1024), 2),
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to save SVG: {e}",
            "error": str(e),
            "execution_time_ms": (time.time() - start_time) * 1000,
        }


async def _convert_svg(
    input_path: str,
    output_path: str,
    format: Optional[str],
    quality: int,
    overwrite: bool,
    cli_wrapper: Any,
    config: Any,
) -> Dict[str, Any]:
    """Convert SVG to other formats using Inkscape export."""
    import time
    start_time = time.time()

    input_path_obj = Path(input_path)
    output_path_obj = Path(output_path)

    try:
        # Check overwrite
        if output_path_obj.exists() and not overwrite:
            return {
                "success": False,
                "message": f"Output file exists and overwrite=False: {output_path}",
                "error": "File exists",
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        # Determine format from output path if not specified
        if not format:
            format = output_path_obj.suffix.lstrip(".").lower()

        # Use Inkscape's export functionality
        result = await cli_wrapper.export_file(
            input_path=input_path,
            output_path=output_path,
            export_type=format,
            dpi=quality if format in ["png", "jpg", "jpeg"] else 300,
            export_area="drawing"
        )

        output_size = output_path_obj.stat().st_size
        input_size = input_path_obj.stat().st_size

        return {
            "success": True,
            "message": f"Successfully converted SVG to {format}",
            "data": {
                "input_path": str(input_path_obj.resolve()),
                "output_path": str(output_path_obj.resolve()),
                "format": format,
                "quality": quality,
                "input_size_bytes": input_size,
                "output_size_bytes": output_size,
                "compression_ratio": round(output_size / input_size, 3) if input_size > 0 else 0,
                "inkscape_output": result,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to convert SVG: {e}",
            "error": str(e),
            "execution_time_ms": (time.time() - start_time) * 1000,
        }


async def _get_svg_info(
    input_path: str, cli_wrapper: Any, config: Any
) -> Dict[str, Any]:
    """Get SVG document information using Inkscape."""
    import time
    start_time = time.time()

    try:
        # Use Inkscape to get document information
        result = await cli_wrapper.get_document_info(input_path)

        input_path_obj = Path(input_path)

        # Parse basic file info
        data = {
            "file_size_bytes": input_path_obj.stat().st_size,
            "file_size_mb": round(input_path_obj.stat().st_size / (1024 * 1024), 2),
            "path": str(input_path_obj.resolve()),
            "format": "SVG",
            "is_vector": True,
            "inkscape_info": result,
        }

        return {
            "success": True,
            "message": f"Successfully retrieved SVG info for {Path(input_path).name}",
            "data": data,
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get SVG info: {e}",
            "error": str(e),
            "execution_time_ms": (time.time() - start_time) * 1000,
        }


async def _validate_svg(
    input_path: str, cli_wrapper: Any, config: Any
) -> Dict[str, Any]:
    """Validate SVG file by checking if Inkscape can process it."""
    import time
    start_time = time.time()

    input_path_obj = Path(input_path)
    issues = []
    warnings = []

    try:
        # Basic file checks first
        if not input_path_obj.exists():
            issues.append("File does not exist")
            valid = False
        elif input_path_obj.stat().st_size == 0:
            issues.append("File is empty")
            valid = False
        else:
            # Try to get document info with Inkscape
            result = await cli_wrapper.get_document_info(input_path)

            # If we get here without exception, the file is valid
            valid = True

            # Check file size
            file_size = input_path_obj.stat().st_size
            if file_size > 50 * 1024 * 1024:  # 50MB
                warnings.append(f"Very large SVG file: {round(file_size / (1024*1024), 1)}MB")

        return {
            "success": True,
            "message": "SVG is valid" if valid else f"SVG has {len(issues)} issue(s)",
            "data": {
                "valid": valid,
                "issues": issues,
                "warnings": warnings,
                "path": str(input_path_obj.resolve()),
                "file_size_bytes": input_path_obj.stat().st_size if input_path_obj.exists() else 0,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"SVG validation failed: {e}",
            "error": str(e),
            "data": {
                "valid": False,
                "issues": [str(e)],
                "warnings": warnings,
                "path": str(input_path_obj.resolve()) if input_path_obj.exists() else input_path,
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }
            error=str(e),
        ).model_dump()
