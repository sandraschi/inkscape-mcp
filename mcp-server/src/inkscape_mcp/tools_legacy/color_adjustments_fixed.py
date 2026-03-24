from __future__ import annotations

"""
Fixed Color Adjustment Tools for GIMP MCP Server.

Provides color manipulation operations including brightness, contrast,
hue, saturation, and advanced color grading.

FIXES APPLIED:
- Removed 'self' parameter from @app.tool() decorated functions
- Fixed parameter binding to use class instance methods
"""

import logging
import sys
from typing import Any, Dict, Tuple

from fastmcp import FastMCP

# Optional numpy import with type checking
try:
    import numpy as np
    import numpy.typing as npt

    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore
    npt = None  # type: ignore
    HAS_NUMPY = False

from .base import BaseToolCategory

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

logger = logging.getLogger(__name__)

# Type aliases for better type hints
FilePath: TypeAlias = str
ColorValue: TypeAlias = float  # 0.0 to 1.0
ColorTuple: TypeAlias = Tuple[float, float, float]
AdjustmentResult: TypeAlias = Dict[str, Any]


class ColorAdjustmentTools(BaseToolCategory):
    """
    Color adjustment and manipulation tools.

    Provides comprehensive color correction and enhancement operations
    including brightness/contrast, hue/saturation, color balance, levels,
    curves, and other color grading functions.
    """

    def register_tools(self, app: FastMCP) -> None:
        """Register all color adjustment tools with FastMCP."""

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

                # Execute brightness/contrast adjustment using GIMP CLI
                result = await self.cli_wrapper.adjust_brightness_contrast(
                    input_path=input_path,
                    output_path=output_path,
                    brightness=brightness,
                    contrast=contrast,
                    preserve_colors=preserve_colors,
                )

                if result:
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
                        },
                        "Brightness and contrast adjusted successfully",
                    )
                else:
                    return self.create_error_response("Brightness/contrast adjustment failed")

            except Exception as e:
                self.logger.error(f"Brightness/contrast adjustment failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Adjustment operation failed: {str(e)}")

        @app.tool()
        async def adjust_hue_saturation(
            input_path: str,
            output_path: str,
            hue: float = 0.0,
            saturation: float = 0.0,
            lightness: float = 0.0,
            overlap: float = 0.0,
            colorize: bool = False,
        ) -> Dict[str, Any]:
            """
            Adjust hue, saturation, and lightness of an image.

            Args:
                input_path: Source image path
                output_path: Destination path
                hue: Hue shift in degrees (-180 to 180)
                saturation: Saturation adjustment (-100 to 100)
                lightness: Lightness adjustment (-100 to 100)
                overlap: Overlap amount (0.0 to 1.0)
                colorize: Whether to colorize the image

            Returns:
                Dict with operation results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")

                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response(f"Invalid output path: {output_path}")

                # Validate parameter ranges
                if not (-180 <= hue <= 180):
                    return self.create_error_response("Hue must be between -180 and 180 degrees")

                if not (-100 <= saturation <= 100):
                    return self.create_error_response("Saturation must be between -100 and 100")

                if not (-100 <= lightness <= 100):
                    return self.create_error_response("Lightness must be between -100 and 100")

                if not (0.0 <= overlap <= 1.0):
                    return self.create_error_response("Overlap must be between 0.0 and 1.0")

                # Execute hue/saturation adjustment using GIMP CLI
                result = await self.cli_wrapper.adjust_hue_saturation(
                    input_path=input_path,
                    output_path=output_path,
                    hue=hue,
                    saturation=saturation,
                    lightness=lightness,
                    overlap=overlap,
                    colorize=colorize,
                )

                if result:
                    return self.create_success_response(
                        {
                            "operation": "hue_saturation_adjustment",
                            "input_path": input_path,
                            "output_path": output_path,
                            "settings": {
                                "hue": hue,
                                "saturation": saturation,
                                "lightness": lightness,
                                "overlap": overlap,
                                "colorize": colorize,
                            },
                        },
                        "Hue and saturation adjusted successfully",
                    )
                else:
                    return self.create_error_response("Hue/saturation adjustment failed")

            except Exception as e:
                self.logger.error(f"Hue/saturation adjustment failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Hue/saturation adjustment failed: {str(e)}")

        # Apply the same fix pattern to other tools...
        @app.tool()
        async def desaturate(
            input_path: str, output_path: str, mode: str = "luminosity"
        ) -> Dict[str, Any]:
            """
            Desaturate an image (convert to grayscale).

            Args:
                input_path: Source image path
                output_path: Destination path
                mode: Desaturation mode (luminosity, average, lightness, max, min)

            Returns:
                Dict with operation results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")

                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response(f"Invalid output path: {output_path}")

                # Validate mode
                valid_modes = ["luminosity", "average", "lightness", "max", "min"]
                if mode not in valid_modes:
                    return self.create_error_response(
                        f"Invalid mode. Must be one of: {', '.join(valid_modes)}"
                    )

                # Execute desaturation using GIMP CLI
                result = await self.cli_wrapper.desaturate(
                    input_path=input_path, output_path=output_path, mode=mode
                )

                if result:
                    return self.create_success_response(
                        {
                            "operation": "desaturate",
                            "input_path": input_path,
                            "output_path": output_path,
                            "settings": {"mode": mode},
                        },
                        "Image desaturated successfully",
                    )
                else:
                    return self.create_error_response("Desaturation failed")

            except Exception as e:
                self.logger.error(f"Desaturation failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Desaturation failed: {str(e)}")
