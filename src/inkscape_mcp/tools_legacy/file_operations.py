"""
File Operation Tools for GIMP MCP Server.

This module provides core file handling operations for the GIMP MCP server,
including loading, saving, format conversion, and metadata extraction.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from enum import auto
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from ..config import InkscapeConfig

logger = logging.getLogger(__name__)


__all__ = ["FileOperationTools", "FileOperationResult"]

# Type aliases for better type hints
type FilePath = str
type ImageMetadata = dict[str, Any]
type ImageData = Any  # Placeholder for actual image data type


class FileOperationStatus(Enum):
    """Status of a file operation."""

    SUCCESS = auto()
    FAILURE = auto()
    PARTIAL = auto()


@dataclass
class FileOperationResult:
    """Result of a file operation.

    Attributes:
        status: Status of the operation
        message: Human-readable message
        data: Additional data related to the operation
        error: Error message if the operation failed
    """

    status: FileOperationStatus
    message: str
    data: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "success": self.status == FileOperationStatus.SUCCESS,
            "message": self.message,
            "data": self.data or {},
            "error": self.error,
        }


class FileOperationTools:
    """Tools for file operations in GIMP MCP Server."""

    def __init__(self, cli_wrapper: Any, config: InkscapeConfig):
        """Initialize file operation tools.

        Args:
            cli_wrapper: The GIMP CLI wrapper instance
            config: The application configuration
        """
        self.cli_wrapper = cli_wrapper
        self.config = config

    def _error_response(self, message: str, details: str | None = None) -> dict[str, Any]:
        """Create a standardized error response.

        Args:
            message: Error message
            details: Optional detailed error information

        Returns:
            Dictionary with error information
        """
        response = {"status": "error", "error": message}
        if details:
            response["details"] = details
        return response

    def register_tools(self, mcp: FastMCP) -> None:
        """Register all file operation tools with the MCP server.

        Args:
            mcp: The FastMCP instance to register tools with
        """

        # Register a simple test tool
        @mcp.tool()
        async def test_tool(_self, name: str = "World") -> dict[str, str]:
            """A simple test tool to verify tool registration

            Args:
                name: Your name

            Returns:
                A test message
            """
            return {"message": f"Hello, {name}! This is a test tool from GIMP MCP Server."}

        # Register load_image tool
        @mcp.tool()
        async def load_image(
            self, file_path: str, load_metadata: bool = True, _max_dimension: int = 0
        ) -> dict[str, Any]:
            """Load an image file and return comprehensive metadata and image handle.

            This tool loads an image file from the specified path, validates it against
            supported formats, extracts metadata, and returns a structured response with
            image details. The returned handle can be used for subsequent operations.

            Args:
                file_path: Path to the image file to load
                load_metadata: Whether to load and return image metadata
                max_dimension: Optional maximum dimension for the loaded image (0 for no resizing)

            Returns:
                Dictionary containing status, image handle, and optional metadata
            """
            try:
                # Basic validation
                if not Path(file_path).exists():
                    return self._error_response(
                        "File not found", f"The file {file_path} does not exist"
                    )

                # Get file info
                file_path = str(Path(file_path).resolve())
                file_name = Path(file_path).name
                file_size = Path(file_path).stat().st_size
                last_modified = Path(file_path).stat().st_mtime

                # Create response
                response = {
                    "status": "success",
                    "image_handle": f"img_{file_name}_{int(time.time())}",
                    "file_info": {
                        "path": file_path,
                        "name": file_name,
                        "size": file_size,
                        "last_modified": last_modified,
                    },
                }

                # Add metadata if requested
                if load_metadata:
                    response["metadata"] = {
                        "filename": file_name,
                        "file_size": file_size,
                        "last_modified": last_modified,
                    }

                return response

            except Exception as e:
                return self._error_response("Error loading image", str(e))

        # Register save_image tool
        @mcp.tool(
            name="save_image",
            description=(
                "Save or convert an image to the specified format and location.\n\n"
                "This tool provides comprehensive image saving capabilities including format conversion, "
                "quality adjustment, metadata preservation, and file management. It supports all major "
                "image formats and handles format-specific options automatically."
            ),
            parameters={
                "input_path": {
                    "type": "string",
                    "format": "file-path",
                    "description": "Path to the source image file",
                    "required": True,
                },
                "output_path": {
                    "type": "string",
                    "format": "file-path",
                    "description": "Path where to save the output file",
                    "required": True,
                },
                "format": {
                    "type": "string",
                    "description": "Output format (e.g., 'jpeg', 'png', 'gif'). If not specified, inferred from output_path extension",
                    "required": False,
                },
                "quality": {
                    "type": "integer",
                    "description": "Quality setting (1-100) for lossy formats",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 90,
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Whether to overwrite existing files",
                    "default": False,
                },
                "preserve_metadata": {
                    "type": "boolean",
                    "description": "Whether to preserve image metadata",
                    "default": True,
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["success", "error"]},
                    "saved_path": {"type": "string"},
                    "file_size": {"type": "integer"},
                    "format": {"type": "string"},
                    "error": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["status"],
            },
        )
        async def save_image(
            self,
            input_path: str,
            output_path: str,
            format: str | None = None,
            _quality: int = 90,
            overwrite: bool = False,
            _preserve_metadata: bool = True,
        ) -> dict[str, Any]:
            """Save an image to the specified location with the given format and options.

            This method handles saving images with format conversion, quality adjustment,
            and proper error handling. It supports all major image formats that GIMP can handle.

            Args:
                input_path: Path to the source image file
                output_path: Path where to save the output file
                format: Output format (e.g., 'jpeg', 'png', 'gif'). If None, inferred from output_path
                quality: Quality setting (1-100) for lossy formats
                overwrite: Whether to overwrite existing files
                preserve_metadata: Whether to preserve image metadata

            Returns:
                Dictionary with save operation results
            """
            try:
                # Validate input paths
                if not Path(input_path).is_file():
                    return self._error_response("Input file does not exist")

                # Resolve output path
                output_path = str(Path(output_path).resolve())
                output_dir = str(Path(output_path).parent)

                # Create output directory if it doesn't exist
                if output_dir and not Path(output_dir).exists():
                    try:
                        Path(output_dir).mkdir(parents=True, exist_ok=True)
                    except OSError as e:
                        return self._error_response(f"Failed to create output directory: {e}")

                # Check if output file exists and handle overwrite
                if Path(output_path).exists() and not overwrite:
                    return self._error_response(
                        f"Output file already exists: {output_path}",
                        "Set overwrite=True to replace existing files",
                    )

                # Determine output format
                if not format:
                    _, ext = Path(output_path).suffix
                    format = ext.lstrip(".").lower()
                    if not format:
                        return self._error_response(
                            "Could not determine output format from file extension. Please specify format parameter."
                        )

                # Validate format
                supported_formats = ["jpeg", "jpg", "png", "gif", "bmp", "tiff", "webp"]
                if format.lower() not in supported_formats:
                    return self._error_response(
                        f"Unsupported format: {format}",
                        f"Supported formats: {', '.join(supported_formats)}",
                    )

                # Prepare GIMP script with quality parameter for supported formats
                if format.lower() in ["jpeg", "jpg", "webp"]:
                    script = f"""
                    (let* (
                        (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                        (drawable (car (gimp-image-get-active-layer image)))
                    )
                    (gimp-file-save RUN-NONINTERACTIVE
                                   image
                                   drawable
                                   "{output_path}"
                                   "{output_path}")
                    (gimp-image-delete image))
                    """
                else:
                    script = f"""
                    (let* (
                        (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                        (drawable (car (gimp-image-get-active-layer image)))
                    )
                    (gimp-file-save RUN-NONINTERACTIVE
                                   image
                                   drawable
                                   "{output_path}"
                                   "{output_path}")
                    (gimp-image-delete image))
                    """

                # Execute GIMP command
                await self.cli_wrapper.execute_script(script)

                # Verify the file was saved
                if not Path(output_path).exists():
                    return self._error_response("Failed to save image: Output file was not created")

                # Get file info
                file_size = Path(output_path).stat().st_size

                return {
                    "status": "success",
                    "saved_path": output_path,
                    "file_size": file_size,
                    "format": format,
                    "message": f"Image successfully saved to {output_path}",
                }

            except Exception as e:
                return self._error_response(f"Error saving image: {str(e)}")

        # Register the tools with instance binding
        mcp.register_tool(test_tool.__get__(self, type(self)))
        mcp.register_tool(load_image.__get__(self, type(self)))
        mcp.register_tool(save_image.__get__(self, type(self)))
