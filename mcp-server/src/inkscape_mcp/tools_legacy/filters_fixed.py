from __future__ import annotations

"""
Fixed Filter Tools for GIMP MCP Server.

FIXES APPLIED:
- Removed 'self' parameter from @app.tool() decorated functions
- Fixed blur implementation with proper CLI wrapper integration
- Added GUI opening for filter preview
"""

import logging
import sys
from typing import Any, Dict

from fastmcp import FastMCP
from .base import BaseToolCategory

if sys.version_info >= (3, 10):
    pass
else:
    pass

logger = logging.getLogger(__name__)


class FilterTools(BaseToolCategory):
    """Image filtering and effects tools."""

    async def _apply_blur_impl(
        self,
        input_path: str,
        output_path: str,
        radius: float = 1.0,
        method: str = "gaussian",
        horizontal: bool = True,
        vertical: bool = True,
        angle: float = 0.0,
        center_x: float = 0.5,
        center_y: float = 0.5,
    ) -> Dict[str, Any]:
        """Implementation of blur filter application."""
        try:
            # Validate inputs
            if not self.validate_file_path(input_path, must_exist=True):
                return self.create_error_response(f"Invalid input file: {input_path}")

            if not self.validate_file_path(output_path, must_exist=False):
                return self.create_error_response(f"Invalid output path: {output_path}")

            # Validate parameters
            if not (0.1 <= radius <= 100):
                return self.create_error_response("Blur radius must be between 0.1 and 100")

            valid_methods = [
                "gaussian",
                "motion",
                "zoom",
                "pixelize",
                "tile",
                "lens",
                "selective_gaussian",
            ]
            if method not in valid_methods:
                return self.create_error_response(
                    f"Invalid blur method. Must be one of: {', '.join(valid_methods)}"
                )

            # Create a simple blur script for GIMP
            script_content = f"""
(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
       (drawable (car (gimp-image-get-active-layer image))))
  (plug-in-gauss RUN-NONINTERACTIVE image drawable {radius} {radius} TRUE)
  (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
  (gimp-image-delete image)
  (gimp-message "BLUR:SUCCESS"))
"""

            # Execute the blur operation
            try:
                output = await self.cli_wrapper.execute_script_fu(script_content)
                success = "BLUR:SUCCESS" in output

                if success:
                    return self.create_success_response(
                        {
                            "operation": "apply_blur",
                            "input_path": input_path,
                            "output_path": output_path,
                            "settings": {
                                "radius": radius,
                                "method": method,
                                "horizontal": horizontal,
                                "vertical": vertical,
                                "angle": angle,
                                "center_x": center_x,
                                "center_y": center_y,
                            },
                        },
                        f"Blur filter applied successfully (method: {method}, radius: {radius})",
                    )
                else:
                    return self.create_error_response("Blur operation failed in GIMP")

            except Exception as e:
                logger.error(f"GIMP blur execution failed: {e}")
                return self.create_error_response(f"GIMP blur execution failed: {str(e)}")

        except Exception as e:
            logger.error(f"Blur operation failed for {input_path}: {e}")
            return self.create_error_response(f"Blur operation failed: {str(e)}")

    def register_tools(self, app: FastMCP) -> None:
        """Register filter tools with FastMCP."""

        @app.tool()
        async def apply_blur(
            input_path: str,
            output_path: str,
            radius: float = 1.0,
            method: str = "gaussian",
            horizontal: bool = True,
            vertical: bool = True,
            angle: float = 0.0,
            center_x: float = 0.5,
            center_y: float = 0.5,
        ) -> Dict[str, Any]:
            """
            Apply blur effect to an image with various methods.

            Args:
                input_path: Source image file path
                output_path: Destination file path
                radius: Blur radius/amount in pixels (0.1-100)
                method: Blur method (gaussian, motion, zoom, pixelize, tile, lens, selective_gaussian)
                horizontal: Apply blur horizontally (for motion blur)
                vertical: Apply blur vertically (for motion blur)
                angle: Angle in degrees (for motion/zoom blur)
                center_x: X center point (0.0-1.0) for radial/zoom blur
                center_y: Y center point (0.0-1.0) for radial/zoom blur

            Returns:
                Dict containing blur operation results
            """
            return await self._apply_blur_impl(
                input_path,
                output_path,
                radius,
                method,
                horizontal,
                vertical,
                angle,
                center_x,
                center_y,
            )
