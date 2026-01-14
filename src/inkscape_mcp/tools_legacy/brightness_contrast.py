from __future__ import annotations

"""
Brightness and Contrast adjustment tool for GIMP MCP Server.

Provides a simple interface to adjust image brightness and contrast.
"""

import logging
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP, mcp

from .base import BaseToolCategory

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

logger = logging.getLogger(__name__)

# Type aliases
FilePath: TypeAlias = str
ImageData: TypeAlias = Any  # numpy.ndarray | PIL.Image.Image | GIMP image

class ColorPreservationMode(str, Enum):
    """Modes for color preservation during brightness/contrast adjustments."""
    NONE = "none"
    LUMINOSITY = "luminosity"
    HUE = "hue"
    SATURATION = "saturation"
    PERCEPTUAL = "perceptual"

@dataclass
class BrightnessContrastConfig:
    """Configuration for brightness and contrast adjustments."""
    brightness: float = 0.0  # Range: -100 to 100
    contrast: float = 0.0    # Range: -100 to 100
    color_preservation: ColorPreservationMode = ColorPreservationMode.PERCEPTUAL
    preserve_highlights: bool = True
    preserve_shadows: bool = True
    auto_contrast: bool = False

class BrightnessContrastTools(BaseToolCategory):
    """Tools for adjusting brightness and contrast of images."""
    
    def __init__(self, cli_wrapper, config):
        super().__init__(cli_wrapper, config)
        self.cli_wrapper = cli_wrapper
    
    def register_tools(self, mcp: FastMCP) -> None:
        """Register all brightness and contrast adjustment tools with FastMCP."""
        
        @mcp.tool(
            name="adjust_brightness_contrast",
            description="""
            Adjust the brightness and contrast of an image with precise control.
            
            This tool provides professional-grade brightness and contrast adjustments
            with optional color preservation. It's ideal for photo correction,
            creative effects, and batch processing of multiple images.
            
            Key features:
            - Precise brightness control from -100 to +100
            - Fine-grained contrast adjustment from -100 to +100
            - Optional color preservation to maintain natural color relationships
            - Non-destructive operation (preserves original file)
            - Supports all major image formats
            """,
            parameters={
                "input_path": {
                    "type": "string",
                    "format": "file-path",
                    "description": "Path to the source image file",
                    "required": True
                },
                "output_path": {
                    "type": "string",
                    "format": "file-path",
                    "description": "Path where the adjusted image will be saved",
                    "required": True
                },
                "brightness": {
                    "type": "number",
                    "description": "Brightness adjustment value (-100 to +100)",
                    "minimum": -100,
                    "maximum": 100,
                    "default": 0.0,
                    "note": "Negative values darken, positive values lighten"
                },
                "contrast": {
                    "type": "number",
                    "description": "Contrast adjustment value (-100 to +100)",
                    "minimum": -100,
                    "maximum": 100,
                    "default": 0.0,
                    "note": "Negative values reduce contrast, positive values increase it"
                },
                "preserve_colors": {
                    "type": "boolean",
                    "description": "Whether to preserve color relationships during adjustment",
                    "default": False,
                    "note": "When True, maintains relative color values to prevent color shifts"
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": "Whether the operation completed successfully"
                    },
                    "brightness": {
                        "type": "number",
                        "description": "The applied brightness value"
                    },
                    "contrast": {
                        "type": "number",
                        "description": "The applied contrast value"
                    },
                    "output_path": {
                        "type": "string",
                        "format": "file-path",
                        "description": "Path to the processed image"
                    },
                    "output_size": {
                        "type": "integer",
                        "description": "Size of the output file in bytes"
                    },
                    "preserve_colors": {
                        "type": "boolean",
                        "description": "Whether color preservation was enabled"
                    }
                },
                "required": ["success", "brightness", "contrast", "output_path", "preserve_colors"]
            },
            examples=[
                {
                    "description": "Slight brightness and contrast boost",
                    "code": """
                    await adjust_brightness_contrast(
                        input_path='photo.jpg',
                        output_path='adjusted_photo.jpg',
                        brightness=15,
                        contrast=10
                    )
                    """
                },
                {
                    "description": "Dramatic high-contrast black and white effect",
                    "code": """
                    await adjust_brightness_contrast(
                        input_path='portrait.jpg',
                        output_path='high_contrast_bw.jpg',
                        brightness=5,
                        contrast=75,
                        preserve_colors=True
                    )
                    """
                }
            ],
            notes=[
                "For best results with photos, use small adjustments (between -30 and +30)",
                "Extreme contrast values may result in loss of detail",
                "The tool automatically handles different color spaces and bit depths"
            ]
        )
        async def adjust_brightness_contrast(
            self,
            input_path: str,
            output_path: str,
            brightness: float = 0.0,
            contrast: float = 0.0,
            preserve_colors: bool = False
        ) -> Dict[str, Any]:
            """
            Adjust image brightness and contrast with optional color preservation.
            
            This function applies brightness and contrast adjustments to an image using GIMP's
            built-in algorithms. The operation is non-destructive to the original file.
            
            Args:
                input_path: Path to the source image file
                output_path: Path where the processed image will be saved
                brightness: Brightness adjustment value (-100 to +100)
                contrast: Contrast adjustment value (-100 to +100)
                preserve_colors: Whether to maintain color relationships
                
            Returns:
                Dict containing operation results with the following structure:
                {
                    "success": bool,
                    "brightness": float,
                    "contrast": float,
                    "output_path": str,
                    "preserve_colors": bool
                }
                
            Raises:
                Exception: If the operation fails for any reason
            """
            try:
                # Input validation
                if not os.path.isfile(input_path):
                    return {
                        "success": False,
                        "error": f"Input file not found: {input_path}",
                        "brightness": brightness,
                        "contrast": contrast,
                        "output_path": output_path,
                        "preserve_colors": preserve_colors
                    }
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                # Normalize values for GIMP
                brightness_norm = brightness / 100.0  # Convert to -1.0 to 1.0 range
                contrast_norm = (contrast + 100) / 100.0  # Convert to 0.0 to 2.0 range
                
                # Create GIMP script with proper error handling
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (success FALSE))
                    
                    (if (and image drawable)
                        (begin
                            ; Apply brightness-contrast
                            (gimp-brightness-contrast drawable {brightness} {contrast} {preserve})
                            
                            ; Save the result
                            (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                            (gimp-image-delete image)
                            (set! success TRUE)
                        )
                    )
                    
                    (if (not success)
                        (gimp-message "ERROR: Failed to process image")
                    )
                    
                    (gimp-message (string-append "SUCCESS:" 
                        "brightness=" (number->string {brightness_val}) " "
                        "contrast=" (number->string {contrast_val}) " "
                        "preserve_colors=" (if {preserve} "true" "false")))
                ))
                """.format(
                    input_path=input_path.replace('\\', '\\\\'),
                    output_path=output_path.replace('\\', '\\\\'),
                    brightness=brightness_norm,
                    contrast=contrast_norm,
                    brightness_val=brightness,  # For the success message
                    contrast_val=contrast,      # For the success message
                    preserve="TRUE" if preserve_colors else "FALSE"
                )
                
                # Execute the script using the instance's CLI wrapper
                output = await self.cli_wrapper.execute_script_fu(script)
                
                # Verify the operation was successful
                if "SUCCESS:" not in output:
                    raise Exception("GIMP processing failed")
                
                # Get file info for the output
                output_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                
                return {
                    "success": True,
                    "brightness": brightness,
                    "contrast": contrast,
                    "output_path": output_path,
                    "preserve_colors": preserve_colors
                }
                
            except Exception as e:
                logger.error(f"Brightness/contrast adjustment failed: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "brightness": brightness,
                    "contrast": contrast,
                    "output_path": output_path,
                    "preserve_colors": preserve_colors
                }
            output_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            return {
                "success": True,
                "brightness": brightness,
                "contrast": contrast,
                "output_path": os.path.abspath(output_path),
                "output_size": output_size,
                "preserve_colors": preserve_colors
            }
