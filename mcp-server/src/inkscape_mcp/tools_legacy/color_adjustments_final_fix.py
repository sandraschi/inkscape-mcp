from __future__ import annotations

"""
PROPERLY Fixed Color Adjustment Tools for GIMP MCP Server.

CRITICAL FIX: The @app.tool() decorated functions must NOT include 'self' parameter,
but they need to access the class instance methods. This is done by capturing 'self'
in the closure and calling the actual implementation methods.
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


class ColorAdjustmentTools(BaseToolCategory):
    """Color adjustment and manipulation tools."""

    async def _adjust_brightness_contrast_impl(
        self,
        input_path: str,
        output_path: str,
        brightness: float = 0.0,
        contrast: float = 0.0,
        preserve_colors: bool = False,
    ) -> Dict[str, Any]:
        """Implementation of brightness/contrast adjustment."""
        try:
            # Validate inputs
            if not self.validate_file_path(input_path, must_exist=True):
                return self.create_error_response(f"Invalid input file: {input_path}")

            if not self.validate_file_path(output_path, must_exist=False):
                return self.create_error_response(f"Invalid output path: {output_path}")

            # Validate parameter ranges
            if not (-100 <= brightness <= 100):
                return self.create_error_response("Brightness must be between -100 and 100")

            if not (-100 <= contrast <= 100):
                return self.create_error_response("Contrast must be between -100 and 100")

            # For now, use basic CLI wrapper operations
            # TODO: Implement proper brightness/contrast adjustment in CLI wrapper
            logger.info(f"Adjusting brightness/contrast: {input_path} -> {output_path}")
            logger.info(
                f"Settings: brightness={brightness}, contrast={contrast}, preserve_colors={preserve_colors}"
            )

            # Placeholder implementation - copy file for now
            import shutil

            shutil.copy2(input_path, output_path)

            return self.create_success_response(
                {
                    "operation": "brightness_contrast_adjustment",
                    "input_path": input_path,
                    "output_path": output_path,
                    "settings": {
                        "brightness": brightness,
                        "contrast": contrast,
                        "preserve_colors": preserve_colors,
                    },
                    "note": "Placeholder implementation - actual GIMP processing to be implemented",
                },
                "Brightness and contrast adjustment placeholder completed",
            )

        except Exception as e:
            logger.error(f"Brightness/contrast adjustment failed: {str(e)}", exc_info=True)
            return self.create_error_response(f"Adjustment operation failed: {str(e)}")

    def register_tools(self, app: FastMCP) -> None:
        """Register all color adjustment tools with FastMCP."""

        # CORRECT FIX: Capture 'self' in closure and call implementation method
        @app.tool()
        async def adjust_brightness_contrast(
            input_path: str,
            output_path: str,
            brightness: float = 0.0,
            contrast: float = 0.0,
            preserve_colors: bool = False,
        ) -> Dict[str, Any]:
            """
            Adjust image brightness and contrast with optional color preservation.

            Args:
                input_path: Source image file path
                output_path: Destination file path
                brightness: Brightness adjustment (-100 to +100)
                contrast: Contrast adjustment (-100 to +100)
                preserve_colors: Whether to preserve color relationships

            Returns:
                Dict containing adjustment operation results
            """
            return await self._adjust_brightness_contrast_impl(
                input_path, output_path, brightness, contrast, preserve_colors
            )
