from __future__ import annotations

"""
Color Adjustment Tools for GIMP MCP Server.

Provides color manipulation operations including brightness, contrast,
hue, saturation, and advanced color grading.
"""

import logging
import math
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union, cast

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

from .base import BaseToolCategory, tool

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

logger = logging.getLogger(__name__)

# Type aliases for better type hints
FilePath: TypeAlias = str
ColorValue: TypeAlias = Union[float, int]
ColorRGB: TypeAlias = Tuple[float, float, float]
ColorRGBA: TypeAlias = Tuple[float, float, float, float]
Color = Union[ColorRGB, ColorRGBA]

# Constants for color operations
DEFAULT_GAMMA = 2.2
MAX_8BIT = 255.0
MAX_16BIT = 65535.0

@dataclass
class ColorAdjustment:
    """Configuration for color adjustments."""
    brightness: float = 0.0  # -1.0 to 1.0
    contrast: float = 0.0    # -1.0 to 1.0
    saturation: float = 0.0  # -1.0 to 1.0
    hue: float = 0.0         # 0.0 to 360.0
    gamma: float = 1.0
    temperature: float = 0.0  # in kelvin
    tint: float = 0.0        # -1.0 to 1.0

class ColorAdjustmentTools(BaseToolCategory):
    """
    Comprehensive color manipulation and adjustment tools.
    Provides a wide range of color correction and grading operations.
    """
    
    def register_tools(self, app: FastMCP) -> None:
        """Register all color adjustment tools with FastMCP."""
        
        @app.tool()
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
                
                # Validate adjustment values
                if not (-100 <= brightness <= 100):
                    return self.create_error_response("Brightness must be between -100 and +100")
                
                if not (-100 <= contrast <= 100):
                    return self.create_error_response("Contrast must be between -100 and +100")
                
                # Normalize values for GIMP
                brightness = brightness / 100.0  # Convert to -1.0 to 1.0 range
                contrast = (contrast + 100) / 100.0  # Convert to 0.0 to 2.0 range
                
                # Create GIMP script
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image))))
                    
                    ; Apply brightness-contrast
                    (gimp-brightness-contrast drawable {brightness} {contrast} {preserve_colors})
                    
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message=f"Brightness/contrast adjustment completed",
                    details={
                        "brightness": brightness * 100,
                        "contrast": (contrast * 100) - 100,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Brightness/contrast adjustment failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Adjustment operation failed: {str(e)}")
        
        @app.tool()
        async def adjust_hue_saturation(
            self, input_path: str,
            output_path: str,
            hue: float = 0.0,
            saturation: float = 0.0,
            lightness: float = 0.0,
            overlap: float = 0.0,
            colorize: bool = False
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
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")
                    
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")
                
                # Normalize values for GIMP
                hue = max(-180, min(180, hue)) / 180.0  # Convert to -1.0 to 1.0
                saturation = max(-100, min(100, saturation)) / 100.0  # -1.0 to 1.0
                lightness = max(-100, min(100, lightness)) / 100.0  # -1.0 to 1.0
                overlap = max(0.0, min(1.0, overlap))
                
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (hue {hue})
                    (saturation {saturation})
                    (lightness {lightness})
                    (overlap {overlap}))
                    
                    ; Apply hue-saturation
                    (gimp-hue-saturation 
                        (if (eq? (car (gimp-drawable-is-rgb drawable)) FALSE)
                            (gimp-image-convert-rgb image))
                        drawable 
                        ALL-HUES 
                        hue 
                        saturation 
                        lightness 
                        overlap)
                    
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """
                
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message="Hue/saturation adjustment completed",
                    details={
                        "hue_shift": hue * 180,
                        "saturation": saturation * 100,
                        "lightness": lightness * 100,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Hue/saturation adjustment failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Hue/saturation adjustment failed: {str(e)}")
        
        @app.tool()
        async def adjust_color_balance(
            self, input_path: str,
            output_path: str,
            cyan_red: Tuple[float, float, float] = (0, 0, 0),
            magenta_green: Tuple[float, float, float] = (0, 0, 0),
            yellow_blue: Tuple[float, float, float] = (0, 0, 0),
            preserve_luminosity: bool = True,
            range_type: str = "midtones"
        ) -> Dict[str, Any]:
            """
            Adjust color balance of an image.
            
            Args:
                input_path: Source image path
                output_path: Destination path
                cyan_red: Cyan-Red balance for shadows, midtones, highlights (-100 to 100)
                magenta_green: Magenta-Green balance for shadows, midtones, highlights (-100 to 100)
                yellow_blue: Yellow-Blue balance for shadows, midtones, highlights (-100 to 100)
                preserve_luminosity: Whether to preserve image luminosity
                range_type: Adjustment range (shadows, midtones, highlights)
                
            Returns:
                Dict with operation results
            """
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")
                    
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")
                
                # Validate range type
                valid_ranges = {"shadows": 0, "midtones": 1, "highlights": 2}
                if range_type not in valid_ranges:
                    return self.create_error_response(
                        f"Invalid range type. Must be one of: {list(valid_ranges.keys())}")
                
                range_idx = valid_ranges[range_type]
                
                # Normalize values
                def clamp(value, min_val=-100, max_val=100):
                    return max(min_val, min(max_val, value))
                
                # Get the specific range values
                cr = clamp(cyan_red[range_idx]) / 100.0
                mg = clamp(magenta_green[range_idx]) / 100.0
                yb = clamp(yellow_blue[range_idx]) / 100.0
                
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (preserve-luminosity {'TRUE' if preserve_luminosity else 'FALSE'}))
                    
                    ; Convert to RGB if needed
                    (if (eq? (car (gimp-drawable-is-rgb drawable)) FALSE)
                        (gimp-image-convert-rgb image))
                    
                    ; Apply color balance
                    (gimp-color-balance 
                        drawable 
                        {range_idx}  ; 0=shadows, 1=midtones, 2=highlights
                        preserve-luminosity
                        {cr} {mg} {yb})
                    
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """
                
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message=f"Color balance adjustment completed for {range_type}",
                    details={
                        "range": range_type,
                        "cyan_red": cr * 100,
                        "magenta_green": mg * 100,
                        "yellow_blue": yb * 100,
                        "preserve_luminosity": preserve_luminosity,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Color balance adjustment failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Color balance adjustment failed: {str(e)}")
        
        @app.tool()
        async def adjust_levels(
            self, input_path: str,
            output_path: str,
            channel: str = "value",
            in_min: float = 0.0,
            in_max: float = 1.0,
            gamma: float = 1.0,
            out_min: float = 0.0,
            out_max: float = 1.0
        ) -> Dict[str, Any]:
            """
            Adjust image levels (tonal range and gamma).
            
            Args:
                input_path: Source image path
                output_path: Destination path
                channel: Channel to adjust (value, red, green, blue, alpha)
                in_min: Input black point (0.0-1.0)
                in_max: Input white point (0.0-1.0)
                gamma: Gamma correction (0.1-10.0)
                out_min: Output black point (0.0-1.0)
                out_max: Output white point (0.0-1.0)
                
            Returns:
                Dict with operation results
            """
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")
                    
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")
                
                # Validate channel
                valid_channels = {
                    "value": 0, "red": 1, "green": 2, 
                    "blue": 3, "alpha": 4
                }
                if channel.lower() not in valid_channels:
                    return self.create_error_response(
                        f"Invalid channel. Must be one of: {list(valid_channels.keys())}")
                
                channel_idx = valid_channels[channel.lower()]
                
                # Clamp values
                in_min = max(0.0, min(1.0, in_min))
                in_max = max(0.0, min(1.0, in_max))
                gamma = max(0.1, min(10.0, gamma))
                out_min = max(0.0, min(1.0, out_min))
                out_max = max(0.0, min(1.0, out_max))
                
                # Ensure in_min < in_max
                if in_min >= in_max:
                    in_min = min(in_max - 0.01, 0.99) if in_max > 0.01 else 0.0
                
                # Ensure out_min < out_max
                if out_min >= out_max:
                    out_min = min(out_max - 0.01, 0.99) if out_max > 0.01 else 0.0
                
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (channel {channel_idx})  ; 0=value, 1=red, 2=green, 3=blue, 4=alpha
                    (in-min {in_min})
                    (in-max {in_max})
                    (gamma {gamma})
                    (out-min {out_min})
                    (out-max {out_max}))
                    
                    ; Convert to RGB if needed and not alpha channel
                    (if (and (eq? (car (gimp-drawable-is-rgb drawable)) FALSE)
                             (< channel 4))  ; Not alpha channel
                        (gimp-image-convert-rgb image))
                    
                    ; Apply levels
                    (gimp-levels drawable channel in-min in-max gamma out-min out-max)
                    
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """
                
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message="Levels adjustment completed",
                    details={
                        "channel": channel,
                        "input_range": [in_min, in_max],
                        "gamma": gamma,
                        "output_range": [out_min, out_max],
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Levels adjustment failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Levels adjustment failed: {str(e)}")
        
        @app.tool()
        async def adjust_curves(
            self, input_path: str,
            output_path: str,
            channel: str = "value",
            control_points: Optional[List[Tuple[float, float]]] = None,
            curve_type: str = "smooth"
        ) -> Dict[str, Any]:
            """
            Adjust image using curves.
            
            Args:
                input_path: Source image path
                output_path: Destination path
                channel: Channel to adjust (value, red, green, blue, alpha)
                control_points: List of (x,y) control points (0.0-1.0)
                curve_type: Type of curve (smooth, free)
                
            Returns:
                Dict with operation results
            """
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")
                    
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")
                
                # Validate channel
                valid_channels = {
                    "value": 0, "red": 1, "green": 2, 
                    "blue": 3, "alpha": 4
                }
                if channel.lower() not in valid_channels:
                    return self.create_error_response(
                        f"Invalid channel. Must be one of: {list(valid_channels.keys())}")
                
                channel_idx = valid_channels[channel.lower()]
                
                # Default curve (linear)
                if not control_points or len(control_points) < 2:
                    control_points = [(0.0, 0.0), (1.0, 1.0)]
                
                # Sort and validate control points
                control_points = sorted(control_points, key=lambda x: x[0])
                control_points = [
                    (max(0.0, min(1.0, x)), max(0.0, min(1.0, y)))
                    for x, y in control_points
                ]
                
                # Create curve string for GIMP
                curve_str = ""
                for x, y in control_points:
                    curve_str += f" {x} {y}"
                
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (channel {channel_idx})  ; 0=value, 1=red, 2=green, 3=blue, 4=alpha
                    (curve-type (if (string=? "{curve_type}" "smooth") 0 1))  ; 0=smooth, 1=free
                    (n-points {len(control_points)})
                    (control-points (list {curve_str}))
                    (curve (cons-array 256 'byte)))
                    
                    ; Convert to RGB if needed and not alpha channel
                    (if (and (eq? (car (gimp-drawable-is-rgb drawable)) FALSE)
                             (< channel 4))  ; Not alpha channel
                        (gimp-image-convert-rgb image))
                    
                    ; Create curve from control points
                    (gimp-curves-explicit drawable channel n-points control-points)
                    
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """
                
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message="Curves adjustment completed",
                    details={
                        "channel": channel,
                        "curve_type": curve_type,
                        "control_points": control_points,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Curves adjustment failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Curves adjustment failed: {str(e)}")
        
        @app.tool()
        async def adjust_threshold(
            self, input_path: str,
            output_path: str,
            threshold: float = 0.5,
            channel: str = "value"
        ) -> Dict[str, Any]:
            """
            Apply threshold adjustment to an image.
            
            Args:
                input_path: Source image path
                output_path: Destination path
                threshold: Threshold value (0.0-1.0)
                channel: Channel to threshold (value, red, green, blue, alpha)
                
            Returns:
                Dict with operation results
            """
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")
                    
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")
                
                # Validate channel
                valid_channels = {
                    "value": 0, "red": 1, "green": 2, 
                    "blue": 3, "alpha": 4
                }
                if channel.lower() not in valid_channels:
                    return self.create_error_response(
                        f"Invalid channel. Must be one of: {list(valid_channels.keys())}")
                
                channel_idx = valid_channels[channel.lower()]
                
                # Clamp threshold
                threshold = max(0.0, min(1.0, threshold))
                
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (channel {channel_idx})  ; 0=value, 1=red, 2=green, 3=blue, 4=alpha
                    (threshold {threshold}))
                    
                    ; Convert to grayscale for value threshold
                    (if (and (eq? channel 0)  ; Value channel
                             (eq? (car (gimp-drawable-is-rgb drawable)) TRUE))
                        (begin
                            (gimp-image-convert-grayscale image)
                            (set! drawable (car (gimp-image-get-active-layer image)))))
                    
                    ; Apply threshold
                    (gimp-threshold drawable channel threshold 1.0)
                    
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """
                
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message="Threshold adjustment completed",
                    details={
                        "channel": channel,
                        "threshold": threshold,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Threshold adjustment failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Threshold adjustment failed: {str(e)}")
        
        @app.tool()
        async def adjust_posterize(
            self, input_path: str,
            output_path: str,
            levels: int = 2,
            dither: bool = True
        ) -> Dict[str, Any]:
            """
            Apply posterize effect to an image.
            
            Args:
                input_path: Source image path
                output_path: Destination path
                levels: Number of brightness levels (2-255)
                dither: Whether to apply dithering
                
            Returns:
                Dict with operation results
            """
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")
                    
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")
                
                # Clamp levels
                levels = max(2, min(255, int(levels)))
                
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image))))
                    
                    ; Apply posterize
                    (gimp-posterize drawable {levels} {1 if dither else 0})
                    
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """
                
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message="Posterize adjustment completed",
                    details={
                        "levels": levels,
                        "dither": dither,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Posterize adjustment failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Posterize adjustment failed: {str(e)}")
        
        @app.tool()
        async def desaturate(
            self, input_path: str,
            output_path: str,
            mode: str = "luminosity"
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
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")
                    
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")
                
                # Map mode to GIMP's desaturate type
                mode_map = {
                    "luminosity": 0,  # Luminance
                    "average": 1,     # Average
                    "lightness": 2,   # Lightness
                    "max": 3,         # Maximum
                    "min": 4,         # Minimum
                }
                
                if mode.lower() not in mode_map:
                    return self.create_error_response(
                        f"Invalid mode. Must be one of: {list(mode_map.keys())}")
                
                desaturate_type = mode_map[mode.lower()]
                
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image))))
                    
                    ; Convert to grayscale using specified method
                    (gimp-desaturate-full drawable {desaturate_type})
                    
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """
                
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message="Desaturation completed",
                    details={
                        "mode": mode,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Desaturation failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Desaturation failed: {str(e)}")
        
        # Tools are automatically registered via @app.tool() decorators

