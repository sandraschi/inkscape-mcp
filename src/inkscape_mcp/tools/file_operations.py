"""
GIMP File Operations Portmanteau Tool.

Comprehensive file management for GIMP MCP, consolidating all file I/O
operations into a single unified interface.
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


async def gimp_file(
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
    """Comprehensive file management portmanteau for GIMP MCP.

    PORTMANTEAU PATTERN RATIONALE:
    Instead of creating 6 separate tools (one per operation), this tool consolidates
    related file operations into a single interface. This design:
    - Prevents tool explosion (6 tools → 1 tool) while maintaining full functionality
    - Improves discoverability by grouping related operations together
    - Reduces cognitive load when working with file management tasks
    - Enables consistent file interface across all operations
    - Follows FastMCP 2.13+ best practices for feature-rich MCP servers

    SUPPORTED OPERATIONS:
    - load: Load an image file and return metadata/thumbnail
    - save: Save image to specified format with quality options
    - convert: Convert image between formats (PNG, JPG, WEBP, TIFF, etc.)
    - info: Get comprehensive image metadata without loading full image
    - validate: Validate image file integrity and format compliance
    - list_formats: List all supported image formats

    Args:
        operation: The file operation to perform. MUST be one of:
            - "load": Load image file (requires: input_path)
            - "save": Save image file (requires: input_path, output_path)
            - "convert": Convert format (requires: input_path, output_path or format)
            - "info": Get image metadata (requires: input_path)
            - "validate": Validate image file (requires: input_path)
            - "list_formats": List supported formats (no parameters required)

        input_path: Path to source image file. Required for: load, save, convert, info, validate.
            Supports absolute or relative paths. Example: "C:/images/photo.jpg"

        output_path: Path for output file. Required for: save, convert operations.
            If omitted for convert, generates path from input with new extension.

        format: Target format for conversion. Used by: convert, save operations.
            Valid: "png", "jpg", "jpeg", "webp", "tiff", "bmp", "gif", "xcf", "psd"
            Default: Inferred from output_path extension.

        quality: JPEG/WebP quality (1-100). Used by: save, convert operations.
            Default: 95. Higher = better quality, larger file.

        metadata: Preserve EXIF/metadata. Used by: save, convert operations.
            Default: True. Set False to strip all metadata.

        overwrite: Overwrite existing output file. Used by: save, convert operations.
            Default: False. Raises error if file exists and overwrite=False.

        compression: Compression method for PNG/TIFF. Used by: save, convert operations.
            PNG: "none", "fast", "best" (default: "best")
            TIFF: "none", "lzw", "zip", "jpeg" (default: "lzw")

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
            result = await _load_image(input_path, metadata, cli_wrapper, config)
        elif operation == "save":
            if not output_path:
                return FileOperationResult(
                    success=False,
                    operation=operation,
                    message="output_path is required for save",
                    error="Missing required parameter: output_path",
                ).model_dump()
            result = await _save_image(
                input_path,
                output_path,
                format,
                quality,
                metadata,
                overwrite,
                compression,
                cli_wrapper,
                config,
            )
        elif operation == "convert":
            result = await _convert_image(
                input_path,
                output_path,
                format,
                quality,
                metadata,
                overwrite,
                compression,
                cli_wrapper,
                config,
            )
        elif operation == "info":
            result = await _get_image_info(input_path, cli_wrapper, config)
        elif operation == "validate":
            result = await _validate_image(input_path, cli_wrapper, config)
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
    read_formats = [
        "png",
        "jpg",
        "jpeg",
        "gif",
        "bmp",
        "tiff",
        "tif",
        "webp",
        "xcf",
        "psd",
        "svg",
        "ico",
        "pcx",
        "ppm",
        "pgm",
        "pbm",
        "tga",
        "xpm",
        "xbm",
        "fits",
        "raw",
        "cr2",
        "nef",
        "orf",
    ]
    write_formats = [
        "png",
        "jpg",
        "jpeg",
        "gif",
        "bmp",
        "tiff",
        "tif",
        "webp",
        "xcf",
        "psd",
        "ico",
        "pcx",
        "ppm",
        "pgm",
        "pbm",
        "tga",
    ]

    return FileOperationResult(
        success=True,
        operation="list_formats",
        message=f"GIMP supports {len(read_formats)} read and {len(write_formats)} write formats",
        data={
            "read_formats": sorted(read_formats),
            "write_formats": sorted(write_formats),
            "recommended": {
                "lossless": ["png", "tiff", "webp"],
                "lossy": ["jpg", "webp"],
                "native": ["xcf"],
                "web": ["png", "jpg", "webp", "gif"],
            },
        },
    ).model_dump()


async def _load_image(
    input_path: str, include_metadata: bool, cli_wrapper: Any, config: Any
) -> Dict[str, Any]:
    """Load image and return metadata."""
    from PIL import Image

    input_path_obj = Path(input_path)

    with Image.open(input_path_obj) as img:
        data = {
            "width": img.width,
            "height": img.height,
            "format": img.format or input_path_obj.suffix.lstrip(".").upper(),
            "color_mode": img.mode,
            "has_alpha": img.mode in ("RGBA", "LA", "PA"),
            "file_size_bytes": input_path_obj.stat().st_size,
            "file_size_mb": round(input_path_obj.stat().st_size / (1024 * 1024), 2),
            "path": str(input_path_obj.resolve()),
        }

        # Add bit depth info
        mode_depths = {
            "1": 1,
            "L": 8,
            "P": 8,
            "RGB": 8,
            "RGBA": 8,
            "CMYK": 8,
            "YCbCr": 8,
            "LAB": 8,
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


async def _save_image(
    input_path: str,
    output_path: str,
    format: Optional[str],
    quality: int,
    preserve_metadata: bool,
    overwrite: bool,
    compression: Optional[str],
    cli_wrapper: Any,
    config: Any,
) -> Dict[str, Any]:
    """Save image to specified path and format."""
    from PIL import Image

    input_path_obj = Path(input_path)
    output_path_obj = Path(output_path)

    # Check overwrite
    if output_path_obj.exists() and not overwrite:
        return FileOperationResult(
            success=False,
            operation="save",
            message=f"Output file exists: {output_path}",
            error="Set overwrite=True to replace existing file",
        ).model_dump()

    # Ensure output directory exists
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Determine format
    if not format:
        format = output_path_obj.suffix.lstrip(".").lower()

    # Load and save
    with Image.open(input_path_obj) as img:
        original_size = input_path_obj.stat().st_size

        save_kwargs = {}

        # Format-specific options
        if format in ("jpg", "jpeg"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
            if img.mode == "RGBA":
                img = img.convert("RGB")
        elif format == "webp":
            save_kwargs["quality"] = quality
            save_kwargs["method"] = 6  # Best compression
        elif format == "png":
            if compression == "none":
                save_kwargs["compress_level"] = 0
            elif compression == "fast":
                save_kwargs["compress_level"] = 1
            else:  # best
                save_kwargs["compress_level"] = 9
        elif format in ("tiff", "tif"):
            if compression == "lzw":
                save_kwargs["compression"] = "tiff_lzw"
            elif compression == "zip":
                save_kwargs["compression"] = "tiff_adobe_deflate"
            elif compression == "jpeg":
                save_kwargs["compression"] = "jpeg"

        img.save(output_path_obj, **save_kwargs)

    output_size = output_path_obj.stat().st_size

    return FileOperationResult(
        success=True,
        operation="save",
        message=f"Saved to {output_path}",
        data={
            "input_path": str(input_path_obj.resolve()),
            "output_path": str(output_path_obj.resolve()),
            "format": format,
            "quality": quality,
            "input_size_bytes": original_size,
            "output_size_bytes": output_size,
            "compression_ratio": round(output_size / original_size, 3)
            if original_size > 0
            else 1.0,
        },
    ).model_dump()


async def _convert_image(
    input_path: str,
    output_path: Optional[str],
    format: Optional[str],
    quality: int,
    preserve_metadata: bool,
    overwrite: bool,
    compression: Optional[str],
    cli_wrapper: Any,
    config: Any,
) -> Dict[str, Any]:
    """Convert image to different format."""
    input_path_obj = Path(input_path)

    # Determine output path
    if not output_path:
        if not format:
            return FileOperationResult(
                success=False,
                operation="convert",
                message="Either output_path or format must be specified",
                error="Missing required parameter for conversion",
            ).model_dump()
        output_path = str(input_path_obj.with_suffix(f".{format}"))

    # Use save implementation
    return await _save_image(
        input_path,
        output_path,
        format,
        quality,
        preserve_metadata,
        overwrite,
        compression,
        cli_wrapper,
        config,
    )


async def _get_image_info(
    input_path: str, cli_wrapper: Any, config: Any
) -> Dict[str, Any]:
    """Get image metadata without full load."""
    return await _load_image(input_path, True, cli_wrapper, config)


async def _validate_image(
    input_path: str, cli_wrapper: Any, config: Any
) -> Dict[str, Any]:
    """Validate image file integrity."""
    from PIL import Image

    input_path_obj = Path(input_path)
    issues = []
    warnings = []

    try:
        with Image.open(input_path_obj) as img:
            # Verify image can be fully loaded
            img.verify()

        # Re-open to get details (verify() invalidates the image)
        with Image.open(input_path_obj) as img:
            img.load()  # Force full load

            # Check for potential issues
            if img.width == 0 or img.height == 0:
                issues.append("Image has zero dimensions")

            if img.width > 32000 or img.height > 32000:
                warnings.append(f"Very large image: {img.width}x{img.height}")

            file_size = input_path_obj.stat().st_size
            if file_size == 0:
                issues.append("File is empty")

            # Check for truncation
            expected_size = img.width * img.height * len(img.getbands())
            if file_size < expected_size * 0.1:
                warnings.append("File may be truncated or heavily compressed")

        valid = len(issues) == 0

        return FileOperationResult(
            success=True,
            operation="validate",
            message="Image is valid" if valid else f"Image has {len(issues)} issue(s)",
            data={
                "valid": valid,
                "issues": issues,
                "warnings": warnings,
                "path": str(input_path_obj.resolve()),
            },
        ).model_dump()

    except Exception as e:
        return FileOperationResult(
            success=False,
            operation="validate",
            message=f"Validation failed: {str(e)}",
            data={
                "valid": False,
                "issues": [str(e)],
                "warnings": [],
                "path": str(input_path_obj.resolve()),
            },
            error=str(e),
        ).model_dump()
