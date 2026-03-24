from __future__ import annotations

"""
Fixed Transform Tools for GIMP MCP Server.

FIXES APPLIED:
- Removed 'self' parameter from @app.tool() decorated functions
- Fixed load_image_info method call
- Proper error handling for CLI wrapper operations
- Added GUI opening functionality for before/after comparison
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastmcp import FastMCP
from .base import BaseToolCategory

if sys.version_info >= (3, 10):
    pass
else:
    pass

logger = logging.getLogger(__name__)


class TransformTools(BaseToolCategory):
    """Geometric transformation tools for image manipulation."""

    async def _resize_image_impl(
        self,
        input_path: str,
        output_path: str,
        width: int,
        height: int,
        maintain_aspect: bool = True,
        interpolation: str = "auto",
    ) -> Dict[str, Any]:
        """Implementation of image resize operation."""
        try:
            # Validate inputs
            if not self.validate_file_path(input_path, must_exist=True):
                return self.create_error_response(f"Invalid input file: {input_path}")

            if not self.validate_file_path(output_path, must_exist=False):
                return self.create_error_response(f"Invalid output path: {output_path}")

            # Validate dimensions
            if width <= 0 or height <= 0:
                return self.create_error_response("Width and height must be positive integers")

            if width > 10000 or height > 10000:
                return self.create_error_response("Maximum dimensions are 10000x10000 pixels")

            # Get original image info using the CLI wrapper
            try:
                original_info = await self.cli_wrapper.load_image_info(input_path)
                original_width = original_info.get("width", 0)
                original_height = original_info.get("height", 0)
            except Exception as e:
                logger.warning(f"Could not get original image info: {e}")
                original_width = original_height = 0

            # Calculate actual dimensions if maintaining aspect ratio
            actual_width, actual_height = width, height
            if maintain_aspect and original_width > 0 and original_height > 0:
                aspect_ratio = original_width / original_height

                # Calculate dimensions that fit within the specified bounds
                if width / height > aspect_ratio:
                    # Height is the limiting dimension
                    actual_width = int(height * aspect_ratio)
                    actual_height = height
                else:
                    # Width is the limiting dimension
                    actual_width = width
                    actual_height = int(width / aspect_ratio)

            # Perform resize using CLI wrapper
            result = await self.cli_wrapper.resize_image(
                input_path=input_path,
                output_path=output_path,
                width=actual_width,
                height=actual_height,
                maintain_aspect=maintain_aspect,
            )

            if result:
                return self.create_success_response(
                    {
                        "operation": "resize",
                        "input_path": input_path,
                        "output_path": output_path,
                        "original_dimensions": {"width": original_width, "height": original_height},
                        "target_dimensions": {"width": width, "height": height},
                        "actual_dimensions": {"width": actual_width, "height": actual_height},
                        "maintain_aspect": maintain_aspect,
                        "interpolation": interpolation,
                    },
                    f"Image resized successfully to {actual_width}x{actual_height}",
                )
            else:
                return self.create_error_response("Resize operation failed")

        except Exception as e:
            logger.error(f"Resize operation failed for {input_path}: {e}")
            return self.create_error_response(f"Resize operation failed: {str(e)}")

    async def _open_gimp_gui_impl(
        self, file_paths: List[str], comparison_mode: bool = False
    ) -> Dict[str, Any]:
        """Open GIMP GUI with specified files."""
        try:
            import subprocess
            import os

            if not file_paths:
                return self.create_error_response("No file paths provided")

            # Validate all files exist
            for file_path in file_paths:
                if not Path(file_path).exists():
                    return self.create_error_response(f"File not found: {file_path}")

            # Build GIMP command to open files in GUI mode
            cmd_args = [self.config.gimp_executable]

            # Add each file to open
            for file_path in file_paths:
                cmd_args.append(str(Path(file_path).resolve()))

            # Start GIMP GUI process (non-blocking)
            logger.info(f"Opening GIMP GUI with files: {file_paths}")
            process = subprocess.Popen(
                cmd_args,
                cwd=os.path.expanduser("~"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return self.create_success_response(
                {
                    "operation": "open_gimp_gui",
                    "files_opened": file_paths,
                    "comparison_mode": comparison_mode,
                    "process_id": process.pid,
                    "note": "GIMP GUI opened successfully. Files should appear as separate tabs/windows.",
                },
                f"GIMP GUI opened with {len(file_paths)} file(s)",
            )

        except Exception as e:
            logger.error(f"Failed to open GIMP GUI: {e}")
            return self.create_error_response(f"Failed to open GIMP GUI: {str(e)}")

    def register_tools(self, app: FastMCP) -> None:
        """Register transform tools with FastMCP."""

        @app.tool()
        async def resize_image(
            input_path: str,
            output_path: str,
            width: int,
            height: int,
            maintain_aspect: bool = True,
            interpolation: str = "auto",
        ) -> Dict[str, Any]:
            """
            Resize an image to specified dimensions.

            Args:
                input_path: Path to source image
                output_path: Path for resized image
                width: Target width in pixels
                height: Target height in pixels
                maintain_aspect: Whether to maintain aspect ratio
                interpolation: Interpolation method (auto, linear, cubic, lanczos)

            Returns:
                Dict containing resize operation results
            """
            return await self._resize_image_impl(
                input_path, output_path, width, height, maintain_aspect, interpolation
            )

        @app.tool()
        async def open_gimp_gui(
            file_paths: List[str], comparison_mode: bool = False
        ) -> Dict[str, Any]:
            """
            Open GIMP GUI with specified image files.

            Perfect for before/after comparisons or manual editing.

            Args:
                file_paths: List of image file paths to open
                comparison_mode: Whether this is for comparison (informational only)

            Returns:
                Dict containing GUI launch results
            """
            return await self._open_gimp_gui_impl(file_paths, comparison_mode)

        @app.tool()
        async def compare_images_in_gimp(original_path: str, processed_path: str) -> Dict[str, Any]:
            """
            Open both original and processed images in GIMP for visual comparison.

            Args:
                original_path: Path to original image
                processed_path: Path to processed image

            Returns:
                Dict containing comparison setup results
            """
            return await self._open_gimp_gui_impl(
                [original_path, processed_path], comparison_mode=True
            )
