from __future__ import annotations

"""
Filter and Effects Tools for GIMP MCP Server.

Provides image filtering operations including blur, sharpen,
noise reduction, and artistic effects.
"""

import logging
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

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

# Type aliases
FilePath: TypeAlias = str
Kernel: TypeAlias = Any  # numpy.ndarray | List[List[float]]
FilterResult: TypeAlias = Dict[str, Any]

# Constants for filters
DEFAULT_KERNEL_SIZE = 3
MAX_KERNEL_SIZE = 15


class BlurMethod(str, Enum):
    """Available blur methods."""

    GAUSSIAN = "gaussian"
    MOTION = "motion"
    ZOOM = "zoom"
    PIXELIZE = "pixelize"
    TILE = "tile"
    LENS = "lens"
    SELECTIVE_GAUSSIAN = "selective_gaussian"


class EdgeDetectMethod(str, Enum):
    """Available edge detection methods."""

    SOBEL = "sobel"
    PREWITT = "prewitt"
    LAPLACIAN = "laplacian"
    CANNY = "canny"
    SCHARR = "scharr"


@dataclass
class FilterConfig:
    """Configuration for image filters."""

    radius: float = 1.0
    method: str = BlurMethod.GAUSSIAN
    threshold: float = 0.5
    amount: float = 1.0
    iterations: int = 1


class FilterTools(BaseToolCategory):
    """
    Comprehensive image filter and effects tools.
    Provides a wide range of image processing filters and effects.
    """

    def register_tools(self, app: FastMCP) -> None:
        """Register all filter tools with FastMCP."""

        # ===== Blur Filters =====

        @app.tool()
        async def apply_blur(
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
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")

                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")

                # Validate parameters
                if radius <= 0 or radius > 100:
                    return self.create_error_response("Blur radius must be between 0.1 and 100")

                valid_methods = [
                    "gaussian",
                    "motion",
                    "radial",
                    "pixelize",
                    "tile",
                    "lens",
                    "selective_gaussian",
                ]
                if method.lower() not in valid_methods:
                    return self.create_error_response(
                        f"Invalid blur method. Must be one of: {valid_methods}"
                    )

                # Get image info for relative positioning
                img_info = await self.cli_wrapper.load_image_info(input_path)
                if not img_info or "width" not in img_info or "height" not in img_info:
                    return self.create_error_response("Could not get image dimensions")

                width = img_info["width"]
                height = img_info["height"]

                # Calculate absolute center coordinates
                center_x_abs = int(center_x * width)
                center_y_abs = int(center_y * height)

                # Build the GIMP script
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (radius {radius})
                    (angle {angle})
                    (center-x {center_x_abs})
                    (center-y {center_y_abs}))
                """

                # Add the appropriate blur operation
                if method == "gaussian":
                    script += """
                        ; Apply Gaussian blur
                        (plug-in-gauss-rle2 RUN-NONINTERACTIVE
                            image drawable radius radius)
                    """
                elif method == "motion":
                    script += f"""
                        ; Apply motion blur
                        (plug-in-mblur RUN-NONINTERACTIVE
                            image drawable
                            {1 if horizontal else 0}  ; horizontal
                            {1 if vertical else 0}    ; vertical
                            angle
                            radius)
                    """
                elif method == "radial":
                    script += """
                        ; Apply radial blur
                        (plug-in-radial-blur RUN-NONINTERACTIVE
                            image drawable
                            8  ; number of segments
                            TRUE  ; no-horiz
                            TRUE  ; no-vert
                            center-x center-y)
                    """
                elif method == "pixelize":
                    script += """
                        ; Apply pixelize effect
                        (plug-in-pixelize2 RUN-NONINTERACTIVE
                            image drawable (max 1 (round radius)))
                    """
                elif method == "zoom":
                    script += f"""
                        ; Apply zoom blur
                        (plug-in-zoom-motion RUN-NONINTERACTIVE
                            image drawable
                            radius
                            center-x center-y
                            {angle}  ; direction
                            0)      ; fade out
                    """
                elif method == "lens":
                    script += """
                        ; Apply lens blur
                        (plug-in-lens-distortion RUN-NONINTERACTIVE
                            image drawable
                            0 0  ; main, edge, zoom, xshift, yshift
                            radius  ; brighten
                            0)     ; wrap
                    """
                elif method == "selective_gaussian":
                    script += """
                        ; Apply selective Gaussian blur
                        (plug-in-sel-gauss RUN-NONINTERACTIVE
                            image drawable radius 0.1)
                    """

                # Complete the script
                script += f"""
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """

                # Execute the script
                await self.cli_wrapper.execute_script_fu(script)

                return self.create_success_response(
                    message=f"{method.replace('_', ' ').title()} blur applied",
                    details={"radius": radius, "method": method, "output_path": output_path},
                )

            except Exception as e:
                self.logger.error(f"Blur operation failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Blur operation failed: {str(e)}")

        # ===== Sharpening Filters =====

        @app.tool()
        async def apply_sharpen(
            self,
            input_path: str,
            output_path: str,
            method: str = "unsharp_mask",
            radius: float = 1.0,
            amount: float = 0.5,
            threshold: float = 0.0,
        ) -> Dict[str, Any]:
            """
            Apply sharpening to an image.

            Args:
                input_path: Source image path
                output_path: Destination path
                method: Sharpening method (unsharp_mask, high_pass, unsharp_mask_advanced)
                radius: Sharpening radius/amount (0.1-100)
                amount: Strength of effect (0.0-5.0)
                threshold: Threshold for edge detection (0.0-1.0)

            Returns:
                Dict with operation results
            """
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")

                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")

                # Clamp values
                radius = max(0.1, min(100.0, float(radius)))
                amount = max(0.0, min(5.0, float(amount)))
                threshold = max(0.0, min(1.0, float(threshold)))

                valid_methods = ["unsharp_mask", "high_pass", "unsharp_mask_advanced"]
                if method.lower() not in valid_methods:
                    return self.create_error_response(
                        f"Invalid sharpening method. Must be one of: {valid_methods}"
                    )

                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (radius {radius})
                    (amount {amount})
                    (threshold {threshold}))
                """

                if method == "unsharp_mask":
                    script += """
                        ; Apply unsharp mask
                        (plug-in-unsharp-mask RUN-NONINTERACTIVE
                            image drawable radius amount 0)
                    """
                elif method == "high_pass":
                    script += """
                        ; Apply high pass filter
                        (plug-in-high-pass RUN-NONINTERACTIVE
                            image drawable radius)
                        ; Invert and set to overlay mode for sharpening effect
                        (gimp-invert drawable)
                        (let* ((layer (car (gimp-layer-copy drawable TRUE))))
                            (gimp-image-insert-layer image layer 0 -1)
                            (gimp-layer-set-mode layer OVERLAY-MODE)
                            (gimp-image-flatten image))
                    """
                elif method == "unsharp_mask_advanced":
                    script += """
                        ; Apply advanced unsharp mask with threshold
                        (plug-in-unsharp-mask RUN-NONINTERACTIVE
                            image drawable radius amount threshold)
                    """

                # Complete the script
                script += f"""
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """

                await self.cli_wrapper.execute_script_fu(script)

                return self.create_success_response(
                    message=f"{method.replace('_', ' ').title()} sharpening applied",
                    details={
                        "method": method,
                        "radius": radius,
                        "amount": amount,
                        "threshold": threshold,
                        "output_path": output_path,
                    },
                )

            except Exception as e:
                self.logger.error(f"Sharpening failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Sharpening failed: {str(e)}")

        # ===== Edge Detection =====

        @app.tool()
        async def detect_edges(
            self,
            input_path: str,
            output_path: str,
            method: str = "sobel",
            amount: float = 1.0,
            threshold: float = 0.2,
            invert: bool = False,
        ) -> Dict[str, Any]:
            """
            Detect edges in an image.

            Args:
                input_path: Source image path
                output_path: Destination path
                method: Edge detection method (sobel, prewitt, laplace, canny, neon)
                amount: Effect strength (0.1-5.0)
                threshold: Edge threshold (0.0-1.0)
                invert: Invert the result

            Returns:
                Dict with operation results
            """
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")

                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")

                # Clamp values
                amount = max(0.1, min(5.0, float(amount)))
                threshold = max(0.0, min(1.0, float(threshold)))

                valid_methods = ["sobel", "prewitt", "laplace", "canny", "neon"]
                if method.lower() not in valid_methods:
                    return self.create_error_response(
                        f"Invalid edge detection method. Must be one of: {valid_methods}"
                    )

                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (amount {amount})
                    (threshold {threshold}))

                    ; Convert to grayscale for edge detection
                    (gimp-image-convert-grayscale image)
                    (set! drawable (car (gimp-image-get-active-layer image)))
                """

                if method == "sobel":
                    script += """
                        ; Apply Sobel edge detection
                        (plug-in-edge RUN-NONINTERACTIVE
                            image drawable amount 0 0)
                    """
                elif method == "prewitt":
                    script += """
                        ; Apply Prewitt edge detection
                        (plug-edge RUN-NONINTERACTIVE
                            image drawable 0)  ; 0=Prewitt
                    """
                elif method == "laplace":
                    script += """
                        ; Apply Laplace edge detection
                        (plug-in-laplace RUN-NONINTERACTIVE
                            image drawable 0)  ; 0=8-neighbor
                    """
                elif method == "canny":
                    script += """
                        ; Apply Canny edge detection
                        (plug-in-canny RUN-NONINTERACTIVE
                            image drawable
                            amount  ; sigma
                            (* 0.4 threshold)  ; low threshold
                            (* 0.8 threshold))  ; high threshold
                    """
                elif method == "neon":
                    script += """
                        ; Apply neon edge detection
                        (plug-in-neon RUN-NONINTERACTIVE
                            image drawable
                            amount  ; radius
                            threshold)
                    """

                if invert:
                    script += """
                        ; Invert the result if requested
                        (gimp-invert drawable)
                    """

                # Complete the script
                script += f"""
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """

                await self.cli_wrapper.execute_script_fu(script)

                return self.create_success_response(
                    message=f"{method.title()} edge detection applied",
                    details={
                        "method": method,
                        "amount": amount,
                        "threshold": threshold,
                        "inverted": invert,
                        "output_path": output_path,
                    },
                )

            except Exception as e:
                self.logger.error(f"Edge detection failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Edge detection failed: {str(e)}")

        # ===== Noise Filters =====

        @app.tool()
        async def apply_noise(
            self,
            input_path: str,
            output_path: str,
            method: str = "add",
            amount: float = 0.1,
            monochromatic: bool = True,
            seed: Optional[int] = None,
        ) -> Dict[str, Any]:
            """
            Add or reduce noise in an image.

            Args:
                input_path: Source image path
                output_path: Destination path
                method: Noise operation (add, reduce, spread, despeckle, hsv_noise)
                amount: Noise amount (0.0-1.0 for most methods)
                monochromatic: Apply noise to all channels equally
                seed: Random seed (None for random)

            Returns:
                Dict with operation results
            """
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")

                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")

                # Clamp values
                amount = max(0.0, min(1.0, float(amount)))

                valid_methods = ["add", "reduce", "spread", "despeckle", "hsv_noise"]
                if method.lower() not in valid_methods:
                    return self.create_error_response(
                        f"Invalid noise method. Must be one of: {valid_methods}"
                    )

                # Generate a random seed if none provided
                if seed is None:
                    import random

                    seed = random.randint(0, 65535)

                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (amount {amount})
                    (seed {seed})
                    (iterations (round (* amount 10))))
                """

                if method == "add":
                    script += f"""
                        ; Add noise
                        (plug-in-rgb-noise RUN-NONINTERACTIVE
                            image drawable
                            0  ; independent RGB
                            {"1" if monochromatic else "0"}  ; correlated RGB
                            (if monochromatic 1 0)  ; grayscale noise
                            seed
                            amount
                            amount
                            amount
                            0)  ; color model (0=RGB)
                    """
                elif method == "reduce":
                    script += """
                        ; Reduce noise (despeckle with iterations based on amount)
                        (let loop ((i 0))
                            (when (< i iterations)
                                (plug-in-despeckle RUN-NONINTERACTIVE
                                    image drawable
                                    3  ; radius
                                    0.5  ; black level
                                    0.5  ; white level
                                )
                                (loop (+ i 1))
                            )
                        )
                    """
                elif method == "spread":
                    script += """
                        ; Spread pixels (max 100px)
                        (plug-in-spread RUN-NONINTERACTIVE
                            image drawable
                            (* amount 100)  ; horizontal spread
                            (* amount 100)) ; vertical spread
                    """
                elif method == "despeckle":
                    script += """
                        ; Apply despeckle filter
                        (plug-in-despread RUN-NONINTERACTIVE
                            image drawable
                            (round (* amount 10))  ; radius
                            0.5  ; threshold
                            0.5)  ; black level
                    """
                elif method == "hsv_noise":
                    script += """
                        ; Add HSV noise
                        (plug-in-hsv-noise RUN-NONINTERACTIVE
                            image drawable
                            3  ; holdness
                            amount  ; hue distance
                            (* amount 0.5)  ; saturation distance
                            (* amount 0.2))  ; value distance
                    """

                # Complete the script
                script += f"""
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """

                await self.cli_wrapper.execute_script_fu(script)

                return self.create_success_response(
                    message=f"{method.replace('_', ' ').title()} noise operation applied",
                    details={
                        "method": method,
                        "amount": amount,
                        "monochromatic": monochromatic,
                        "seed": seed,
                        "output_path": output_path,
                    },
                )

            except Exception as e:
                self.logger.error(f"Noise operation failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Noise operation failed: {str(e)}")

        # ===== Artistic Filters =====

        @app.tool()
        async def apply_artistic(
            self,
            input_path: str,
            output_path: str,
            effect: str = "oilify",
            size: int = 3,
            exponent: float = 1.0,
            intensity: float = 0.5,
        ) -> Dict[str, Any]:
            """
            Apply artistic effects to an image.

            Args:
                input_path: Source image path
                output_path: Destination path
                effect: Effect to apply (oilify, cartoon, softglow, photocopy,
                        waterpixels, newsprint, clothify, coffee_stain, engrave,
                        jigsaw, mosaic, paper_tile, polar_coords, ripple,
                        small_tiles, tile, video, wind, whirl_pinch)
                size: Effect size/radius (1-100)
                exponent: Effect exponent (0.1-10.0)
                intensity: Effect intensity (0.0-1.0)

            Returns:
                Dict with operation results
            """
            try:
                # Input validation
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response("Invalid input file")

                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response("Invalid output path")

                # Clamp values
                size = max(1, min(100, int(size)))
                exponent = max(0.1, min(10.0, float(exponent)))
                intensity = max(0.0, min(1.0, float(intensity)))

                valid_effects = [
                    "oilify",
                    "cartoon",
                    "softglow",
                    "photocopy",
                    "waterpixels",
                    "newsprint",
                    "clothify",
                    "coffee_stain",
                    "engrave",
                    "jigsaw",
                    "mosaic",
                    "paper_tile",
                    "polar_coords",
                    "ripple",
                    "small_tiles",
                    "tile",
                    "video",
                    "wind",
                    "whirl_pinch",
                ]

                if effect.lower() not in valid_effects:
                    return self.create_error_response(
                        f"Invalid effect. Must be one of: {valid_effects}"
                    )

                effect = effect.lower()
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (size {size})
                    (exponent {exponent})
                    (intensity {intensity}))
                """

                # Apply the selected effect
                if effect == "oilify":
                    script += """
                        ; Apply oilify effect
                        (plug-in-oilify RUN-NONINTERACTIVE
                            image drawable size 0)
                    """
                elif effect == "cartoon":
                    script += """
                        ; Apply cartoon effect
                        (plug-ifw-cartoon RUN-NONINTERACTIVE
                            image drawable
                            size  ; mask radius
                            (* 0.1 intensity)  ; percent black
                            0)   ; no posterize
                    """
                elif effect == "softglow":
                    script += """
                        ; Apply softglow effect
                        (plug-in-softglow RUN-NONINTERACTIVE
                            image drawable
                            size  ; glow radius
                            (* 0.5 intensity)  ; brightness
                            0.8)  ; sharpness
                    """
                elif effect == "photocopy":
                    script += """
                        ; Apply photocopy effect
                        (plug-in-photocopy RUN-NONINTERACTIVE
                            image drawable
                            size  ; mask radius
                            (* 0.5 intensity)  ; sharpness
                            (* 0.5 intensity)  ; percent black
                            0.5)  ; percent white
                    """
                elif effect == "waterpixels":
                    script += """
                        ; Apply waterpixels effect
                        (plug-in-water RUN-NONINTERACTIVE
                            image drawable
                            size  ; radius
                            (* 10 intensity)  ; smoothness
                            1)   ; iterations
                    """
                elif effect == "whirl_pinch":
                    script += """
                        ; Apply whirl and pinch effect
                        (plug-in-whirl-pinch RUN-NONINTERACTIVE
                            image drawable
                            (* 360 intensity)  ; whirl
                            (* 1.0 intensity)  ; pinch
                            (* 1.0 intensity)  ; radius
                            0 0)  ; center x, y
                    """
                # Add more effects as needed...

                # Complete the script
                script += f"""
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """

                await self.cli_wrapper.execute_script_fu(script)

                return self.create_success_response(
                    message=f"{effect.replace('_', ' ').title()} effect applied",
                    details={
                        "effect": effect,
                        "size": size,
                        "exponent": exponent,
                        "intensity": intensity,
                        "output_path": output_path,
                    },
                )

            except Exception as e:
                self.logger.error(f"Artistic effect failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Artistic effect failed: {str(e)}")
