"""
Fixed MCP Tool Registration for File Operations.

This module provides the corrected MCP tool registration for file operations,
fixing the missing _get_image_info method and other implementation issues.
"""

import time
import logging
from typing import Dict, Any, Callable, TypeVar
from pathlib import Path

from fastmcp import FastMCP
from ..cli_wrapper import InkscapeCliWrapper
from ..config import InkscapeConfig
from ..tool_utils import tool
from .file_operations_base import FileOperationBase

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Callable[..., Any])


class FileOperationTools(FileOperationBase):
    """Tools for file operations in GIMP MCP Server."""

    def __init__(self, cli_wrapper: "InkscapeCliWrapper", config: "InkscapeConfig"):
        """Initialize file operation tools.

        Args:
            cli_wrapper: The GIMP CLI wrapper instance
            config: The application configuration
        """
        super().__init__(cli_wrapper, config)

    async def _get_image_info(
        self, file_path: str, load_metadata: bool = True, max_dimension: int = 0
    ) -> Dict[str, Any]:
        """Get image information using GIMP CLI wrapper.

        Args:
            file_path: Path to the image file
            load_metadata: Whether to load image metadata
            max_dimension: Maximum dimension for thumbnails (0 = no thumbnail)

        Returns:
            Dictionary containing image information
        """
        try:
            # Use the CLI wrapper's load_image_info method
            image_info = await self.cli_wrapper.load_image_info(file_path)

            # Add additional metadata if requested
            if load_metadata:
                file_path_obj = Path(file_path)
                image_info.update(
                    {
                        "file_size": file_path_obj.stat().st_size,
                        "file_extension": file_path_obj.suffix.lower(),
                        "last_modified": file_path_obj.stat().st_mtime,
                    }
                )

            # TODO: Implement thumbnail generation if max_dimension > 0
            if max_dimension > 0:
                image_info["thumbnail"] = {"note": "Thumbnail generation not yet implemented"}

            return image_info

        except Exception as e:
            logger.error(f"Failed to get image info for {file_path}: {e}")
            raise

    @tool(
        name="test_tool",
        description="A simple test tool to verify tool registration.",
        parameters={
            "name": {
                "type": "string",
                "default": "World",
                "description": "Name to include in the greeting",
            }
        },
    )
    async def test_tool(self, name: str = "World") -> Dict[str, Any]:
        """Test tool that returns a greeting.

        Args:
            name: Name to include in the greeting

        Returns:
            Dictionary containing the greeting and timestamp
        """
        return {
            "greeting": f"Hello, {name}!",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    @tool(
        name="load_image",
        description="Load an image file using GIMP and return its information.",
        parameters={
            "file_path": {
                "type": "string",
                "format": "file-path",
                "description": "Path to the image file",
            },
            "load_metadata": {
                "type": "boolean",
                "default": True,
                "description": "Whether to load image metadata",
            },
            "max_dimension": {
                "type": "integer",
                "minimum": 0,
                "default": 0,
                "description": "Maximum dimension for thumbnails (0 = no thumbnail)",
            },
        },
    )
    async def load_image(
        self, file_path: str, load_metadata: bool = True, max_dimension: int = 0
    ) -> Dict[str, Any]:
        """Load an image file and return its information.

        Args:
            file_path: Path to the image file
            load_metadata: Whether to load image metadata
            max_dimension: Maximum dimension for thumbnails (0 = no thumbnail)

        Returns:
            Dictionary containing image information
        """
        try:
            # Basic file info
            file_path = Path(file_path).resolve()
            if not file_path.exists():
                return {"status": "error", "message": f"File not found: {file_path}"}

            result = {
                "status": "success",
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "modified_time": file_path.stat().st_mtime,
            }

            # Add image-specific info using the fixed method
            try:
                image_info = await self._get_image_info(
                    str(file_path), load_metadata, max_dimension
                )
                result["image_info"] = image_info
            except Exception as e:
                logger.warning(f"Could not get image info: {e}")
                result["image_info"] = {"error": str(e)}

            return result

        except Exception as e:
            logger.error(f"Error loading image: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def register_tools(self, app: FastMCP) -> None:
        """Register all file operation tools with FastMCP."""

        @app.tool()
        async def test_tool(self, name: str = "World") -> Dict[str, Any]:
            """Test tool that returns a greeting.

            Args:
                name: Name to include in the greeting

            Returns:
                Dictionary containing the greeting and timestamp
            """
            return await self.test_tool(name)

        @app.tool()
        async def load_image(
            self, file_path: str, load_metadata: bool = True, max_dimension: int = 0
        ) -> Dict[str, Any]:
            """Load an image file and return its information.

            Args:
                file_path: Path to the image file
                load_metadata: Whether to load image metadata
                max_dimension: Maximum dimension for thumbnails (0 = no thumbnail)

            Returns:
                Dictionary containing image information
            """
            return await self.load_image(file_path, load_metadata, max_dimension)
