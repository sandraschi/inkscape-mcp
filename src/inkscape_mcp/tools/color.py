"""
GIMP Color Adjustments Portmanteau Tool.

Comprehensive color manipulation operations for GIMP MCP.
"""

from __future__ import annotations

import colorsys
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from pydantic import BaseModel, Field


class ColorResult(BaseModel):
    """Result model for color operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: Optional[str] = None


async def inkscape_color(
    operation: Literal[
        "brightness_contrast",
        "levels",
        "curves",
        "color_balance",
        "hue_saturation",
        "colorize",
        "threshold",
        "posterize",
        "desaturate",
        "invert",
        "auto_levels",
        "auto_color",
    ],
    input_path: str,
    output_path: str,
    # Brightness/Contrast
    brightness: float = 0.0,
    contrast: float = 0.0,
    # Levels
    input_black: float = 0.0,
    input_white: float = 1.0,
    gamma: float = 1.0,
    output_black: float = 0.0,
    output_white: float = 1.0,
    channel: str = "value",
    # Curves
    control_points: Optional[List[Tuple[float, float]]] = None,
    # Color Balance
    cyan_red: Tuple[float, float, float] = (0, 0, 0),
    magenta_green: Tuple[float, float, float] = (0, 0, 0),
    yellow_blue: Tuple[float, float, float] = (0, 0, 0),
    preserve_luminosity: bool = True,
    # Hue/Saturation
    hue: float = 0.0,
    saturation: float = 0.0,
    lightness: float = 0.0,
    # Colorize
    colorize_hue: float = 0.0,
    colorize_saturation: float = 50.0,
    colorize_lightness: float = 0.0,
    # Threshold/Posterize
    threshold_value: float = 0.5,
    posterize_levels: int = 4,
    # Desaturate
    desaturate_mode: str = "luminosity",
    # Common
    overwrite: bool = False,
    # Dependencies
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Comprehensive color adjustment portmanteau for GIMP MCP.

    PORTMANTEAU PATTERN RATIONALE:
    Instead of creating 12+ separate tools (one per color operation), this tool
    consolidates related color operations into a single interface. This design:
    - Prevents tool explosion (12 tools → 1 tool) while maintaining full functionality
    - Improves discoverability by grouping related operations together
    - Reduces cognitive load when working with color adjustments
    - Enables consistent color interface across all operations
    - Follows FastMCP 2.13+ best practices for feature-rich MCP servers

    SUPPORTED OPERATIONS:
    - brightness_contrast: Adjust brightness and contrast
    - levels: Adjust tonal range with input/output levels
    - curves: Fine-tune tones with control points
    - color_balance: Adjust color balance for shadows/midtones/highlights
    - hue_saturation: Adjust HSL values
    - colorize: Apply color tint to image
    - threshold: Convert to black/white at threshold
    - posterize: Reduce color levels
    - desaturate: Convert to grayscale
    - invert: Invert colors
    - auto_levels: Automatic levels adjustment
    - auto_color: Automatic color correction

    Args:
        operation: Color operation to perform. MUST be one of:
            - "brightness_contrast": Adjust brightness/contrast (requires: brightness, contrast)
            - "levels": Tonal adjustment (requires: input_black, input_white, gamma)
            - "curves": Curve adjustment (requires: control_points)
            - "color_balance": Color balance (requires: cyan_red, magenta_green, yellow_blue)
            - "hue_saturation": HSL adjustment (requires: hue, saturation, lightness)
            - "colorize": Apply color tint (requires: colorize_hue, colorize_saturation)
            - "threshold": Black/white threshold (requires: threshold_value)
            - "posterize": Reduce levels (requires: posterize_levels)
            - "desaturate": Grayscale conversion (requires: desaturate_mode)
            - "invert": Invert colors (no extra params)
            - "auto_levels": Auto levels (no extra params)
            - "auto_color": Auto color (no extra params)

        input_path: Path to source image. Required for all operations.

        output_path: Path for output image. Required for all operations.

        brightness: Brightness adjustment (-100 to 100). Used by: brightness_contrast.
            Negative = darker, positive = brighter. Default: 0

        contrast: Contrast adjustment (-100 to 100). Used by: brightness_contrast.
            Negative = less contrast, positive = more contrast. Default: 0

        input_black: Input black point (0.0-1.0). Used by: levels. Default: 0.0

        input_white: Input white point (0.0-1.0). Used by: levels. Default: 1.0

        gamma: Gamma correction (0.1-10.0). Used by: levels. Default: 1.0
            <1 = darker midtones, >1 = lighter midtones

        output_black: Output black point (0.0-1.0). Used by: levels. Default: 0.0

        output_white: Output white point (0.0-1.0). Used by: levels. Default: 1.0

        channel: Channel to adjust. Used by: levels, curves.
            Valid: "value" (all), "red", "green", "blue", "alpha"

        control_points: Curve control points. Used by: curves.
            Format: [(x1,y1), (x2,y2), ...] where x,y are 0.0-1.0
            Example: [(0,0), (0.25,0.3), (0.75,0.7), (1,1)]

        cyan_red: Cyan-Red balance (shadows, midtones, highlights). Used by: color_balance.
            Each value -100 to 100. Default: (0, 0, 0)

        magenta_green: Magenta-Green balance. Used by: color_balance.

        yellow_blue: Yellow-Blue balance. Used by: color_balance.

        preserve_luminosity: Keep luminosity constant. Used by: color_balance. Default: True

        hue: Hue shift (-180 to 180 degrees). Used by: hue_saturation. Default: 0

        saturation: Saturation adjustment (-100 to 100). Used by: hue_saturation. Default: 0

        lightness: Lightness adjustment (-100 to 100). Used by: hue_saturation. Default: 0

        colorize_hue: Hue for colorize (0-360). Used by: colorize. Default: 0

        colorize_saturation: Saturation for colorize (0-100). Used by: colorize. Default: 50

        threshold_value: Threshold point (0.0-1.0). Used by: threshold. Default: 0.5

        posterize_levels: Number of levels (2-255). Used by: posterize. Default: 4

        desaturate_mode: Grayscale method. Used by: desaturate.
            Valid: "luminosity", "average", "lightness", "luma"

    Returns:
        Dict containing color adjustment results.

    Examples:
        # Increase brightness and contrast
        gimp_color("brightness_contrast", "photo.jpg", "bright.jpg", brightness=20, contrast=10)

        # Auto-levels
        gimp_color("auto_levels", "photo.jpg", "auto.jpg")

        # Desaturate to grayscale
        gimp_color("desaturate", "photo.jpg", "bw.jpg", desaturate_mode="luminosity")

        # Apply sepia tint
        gimp_color("colorize", "photo.jpg", "sepia.jpg", colorize_hue=30, colorize_saturation=40)

        # Posterize effect
        gimp_color("posterize", "photo.jpg", "poster.jpg", posterize_levels=4)
    """
    start_time = time.time()

    try:
        input_path_obj = Path(input_path)
        output_path_obj = Path(output_path)

        if not input_path_obj.exists():
            return ColorResult(
                success=False,
                operation=operation,
                message=f"Input file not found: {input_path}",
                error="FileNotFoundError",
            ).model_dump()

        if output_path_obj.exists() and not overwrite:
            return ColorResult(
                success=False,
                operation=operation,
                message=f"Output file exists: {output_path}",
                error="Set overwrite=True to replace",
            ).model_dump()

        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(input_path_obj) as img:
            if img.mode == "P":
                img = img.convert("RGB")

            if operation == "brightness_contrast":
                result = _brightness_contrast(img, brightness, contrast)
            elif operation == "levels":
                result = _levels(
                    img,
                    input_black,
                    input_white,
                    gamma,
                    output_black,
                    output_white,
                    channel,
                )
            elif operation == "curves":
                result = _curves(img, control_points, channel)
            elif operation == "color_balance":
                result = _color_balance(
                    img, cyan_red, magenta_green, yellow_blue, preserve_luminosity
                )
            elif operation == "hue_saturation":
                result = _hue_saturation(img, hue, saturation, lightness)
            elif operation == "colorize":
                result = _colorize(
                    img, colorize_hue, colorize_saturation, colorize_lightness
                )
            elif operation == "threshold":
                result = _threshold(img, threshold_value)
            elif operation == "posterize":
                result = _posterize(img, posterize_levels)
            elif operation == "desaturate":
                result = _desaturate(img, desaturate_mode)
            elif operation == "invert":
                result = ImageOps.invert(img.convert("RGB"))
            elif operation == "auto_levels":
                result = ImageOps.autocontrast(img)
            elif operation == "auto_color":
                result = _auto_color(img)
            else:
                return ColorResult(
                    success=False,
                    operation=operation,
                    message=f"Unknown operation: {operation}",
                    error="Invalid operation",
                ).model_dump()

            # Save
            save_kwargs = {}
            if output_path_obj.suffix.lower() in (".jpg", ".jpeg"):
                save_kwargs["quality"] = 95
                if result.mode == "RGBA":
                    result = result.convert("RGB")

            result.save(output_path_obj, **save_kwargs)

        execution_time = (time.time() - start_time) * 1000

        return ColorResult(
            success=True,
            operation=operation,
            message=f"Color adjustment '{operation}' applied successfully",
            data={
                "input_path": str(input_path_obj.resolve()),
                "output_path": str(output_path_obj.resolve()),
                "operation_applied": operation,
                "output_size_bytes": output_path_obj.stat().st_size,
            },
            execution_time_ms=round(execution_time, 2),
        ).model_dump()

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return ColorResult(
            success=False,
            operation=operation,
            message=f"Color adjustment failed: {str(e)}",
            error=str(e),
            execution_time_ms=round(execution_time, 2),
        ).model_dump()


def _brightness_contrast(
    img: Image.Image, brightness: float, contrast: float
) -> Image.Image:
    """Adjust brightness and contrast.

    Args:
        img: Source image
        brightness: -100 to 100 (0 = no change)
        contrast: -100 to 100 (0 = no change)
    """
    # Brightness: convert -100..100 to 0..2 factor
    b_factor = 1 + (brightness / 100)
    enhancer = ImageEnhance.Brightness(img)
    result = enhancer.enhance(b_factor)

    # Contrast: convert -100..100 to 0..2 factor
    c_factor = 1 + (contrast / 100)
    enhancer = ImageEnhance.Contrast(result)
    return enhancer.enhance(c_factor)


def _levels(
    img: Image.Image,
    input_black: float,
    input_white: float,
    gamma: float,
    output_black: float,
    output_white: float,
    channel: str,
) -> Image.Image:
    """Apply levels adjustment.

    Args:
        img: Source image
        input_black: Input black point (0.0-1.0)
        input_white: Input white point (0.0-1.0)
        gamma: Gamma correction (0.1-10.0)
        output_black: Output black point (0.0-1.0)
        output_white: Output white point (0.0-1.0)
        channel: Channel to adjust ("value", "red", "green", "blue")
    """
    arr = np.array(img, dtype=np.float32) / 255.0

    # Prevent division by zero
    input_range = max(input_white - input_black, 0.001)

    def apply_levels(data: np.ndarray) -> np.ndarray:
        # Input levels
        result = (data - input_black) / input_range
        result = np.clip(result, 0, 1)
        # Gamma
        result = np.power(result, 1 / gamma)
        # Output levels
        result = result * (output_white - output_black) + output_black
        return result

    if channel == "value" or len(arr.shape) == 2:
        arr = apply_levels(arr)
    else:
        channel_map = {"red": 0, "green": 1, "blue": 2, "alpha": 3}
        ch_idx = channel_map.get(channel, None)
        if ch_idx is not None and ch_idx < arr.shape[2]:
            arr[:, :, ch_idx] = apply_levels(arr[:, :, ch_idx])
        else:
            # Apply to all color channels
            for i in range(min(3, arr.shape[2])):
                arr[:, :, i] = apply_levels(arr[:, :, i])

    arr = np.clip(arr * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode=img.mode)


def _curves(
    img: Image.Image,
    control_points: Optional[List[Tuple[float, float]]],
    channel: str,
) -> Image.Image:
    """Apply curves adjustment with cubic interpolation.

    Args:
        img: Source image
        control_points: List of (x, y) tuples, x and y in 0.0-1.0 range
        channel: Channel to adjust ("value", "red", "green", "blue")
    """
    if not control_points:
        return img

    # Build lookup table from control points
    points = sorted(control_points, key=lambda p: p[0])

    # Ensure we have endpoints
    if points[0][0] > 0:
        points.insert(0, (0.0, points[0][1]))
    if points[-1][0] < 1:
        points.append((1.0, points[-1][1]))

    lut = np.zeros(256, dtype=np.uint8)

    for i in range(256):
        x = i / 255.0
        y = 0.0

        # Find surrounding points and interpolate
        for j in range(len(points) - 1):
            if points[j][0] <= x <= points[j + 1][0]:
                denom = points[j + 1][0] - points[j][0]
                if denom > 0:
                    t = (x - points[j][0]) / denom
                    y = points[j][1] + t * (points[j + 1][1] - points[j][1])
                else:
                    y = points[j][1]
                break
        else:
            # x is beyond last point
            y = points[-1][1]

        lut[i] = int(np.clip(y * 255, 0, 255))

    if img.mode in ("L", "LA"):
        return img.point(lut)

    channels = list(img.split())
    channel_map = {"red": 0, "green": 1, "blue": 2}

    if channel == "value":
        # Apply to all color channels
        for i in range(min(3, len(channels))):
            channels[i] = channels[i].point(lut)
    elif channel in channel_map:
        ch_idx = channel_map[channel]
        if ch_idx < len(channels):
            channels[ch_idx] = channels[ch_idx].point(lut)

    return Image.merge(img.mode, channels)


def _color_balance(
    img: Image.Image,
    cyan_red: Tuple[float, float, float],
    magenta_green: Tuple[float, float, float],
    yellow_blue: Tuple[float, float, float],
    preserve_luminosity: bool,
) -> Image.Image:
    """Adjust color balance for shadows, midtones, and highlights.

    Args:
        img: Source image
        cyan_red: (shadows, midtones, highlights) adjustment for cyan-red axis (-100 to 100)
        magenta_green: (shadows, midtones, highlights) for magenta-green axis
        yellow_blue: (shadows, midtones, highlights) for yellow-blue axis
        preserve_luminosity: Keep overall luminosity constant
    """
    arr = np.array(img.convert("RGB"), dtype=np.float32)

    # Calculate luminosity for preservation
    if preserve_luminosity:
        lum_orig = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]

    # Create tonal masks (shadows, midtones, highlights)
    gray = np.mean(arr, axis=2) / 255.0

    # Soft masks with smooth transitions
    shadows = np.clip(1.0 - gray * 4, 0, 1)  # 0-64 range
    highlights = np.clip(gray * 4 - 3, 0, 1)  # 192-255 range
    midtones = 1.0 - shadows - highlights
    midtones = np.clip(midtones, 0, 1)

    # Apply adjustments per tonal range
    for i, (cr, mg, yb) in enumerate([(cyan_red, magenta_green, yellow_blue)]):
        for j, (adj, mask) in enumerate(
            zip([cr[0], cr[1], cr[2]], [shadows, midtones, highlights])
        ):
            # cr affects R, mg affects G, yb affects B
            if i == 0:  # cyan_red -> R channel
                arr[:, :, 0] += adj * 2.55 * mask
            elif i == 1:  # magenta_green -> G channel
                arr[:, :, 1] += adj * 2.55 * mask
            else:  # yellow_blue -> B channel
                arr[:, :, 2] += adj * 2.55 * mask

    # Simpler approach: apply each axis to its corresponding channel
    for j, mask in enumerate([shadows, midtones, highlights]):
        arr[:, :, 0] += cyan_red[j] * 2.55 * mask
        arr[:, :, 1] += magenta_green[j] * 2.55 * mask
        arr[:, :, 2] += yellow_blue[j] * 2.55 * mask

    # Preserve luminosity
    if preserve_luminosity:
        lum_new = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        lum_ratio = np.where(lum_new > 0, lum_orig / (lum_new + 1e-6), 1.0)
        for c in range(3):
            arr[:, :, c] *= lum_ratio

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


def _hue_saturation(
    img: Image.Image,
    hue: float,
    saturation: float,
    lightness: float,
) -> Image.Image:
    """Adjust hue, saturation, and lightness.

    Args:
        img: Source image
        hue: Hue rotation in degrees (-180 to 180)
        saturation: Saturation adjustment (-100 to 100)
        lightness: Lightness adjustment (-100 to 100)
    """
    # Convert to RGB if needed
    rgb_img = img.convert("RGB")
    arr = np.array(rgb_img, dtype=np.float32) / 255.0

    # Convert RGB to HSV per-pixel
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin

    # Hue calculation
    h = np.zeros_like(r)
    mask_r = (cmax == r) & (delta > 0)
    mask_g = (cmax == g) & (delta > 0)
    mask_b = (cmax == b) & (delta > 0)

    h[mask_r] = 60 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6)
    h[mask_g] = 60 * (((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2)
    h[mask_b] = 60 * (((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4)

    # Saturation
    s = np.where(cmax > 0, delta / cmax, 0)

    # Value
    v = cmax

    # Apply adjustments
    h = (h + hue) % 360
    s = np.clip(s * (1 + saturation / 100), 0, 1)
    v = np.clip(v + lightness / 100, 0, 1)

    # Convert HSV back to RGB
    h_i = (h / 60).astype(int) % 6
    f = (h / 60) - h_i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    result = np.zeros_like(arr)

    for i in range(6):
        mask = h_i == i
        if i == 0:
            result[mask] = np.stack([v[mask], t[mask], p[mask]], axis=-1)
        elif i == 1:
            result[mask] = np.stack([q[mask], v[mask], p[mask]], axis=-1)
        elif i == 2:
            result[mask] = np.stack([p[mask], v[mask], t[mask]], axis=-1)
        elif i == 3:
            result[mask] = np.stack([p[mask], q[mask], v[mask]], axis=-1)
        elif i == 4:
            result[mask] = np.stack([t[mask], p[mask], v[mask]], axis=-1)
        else:
            result[mask] = np.stack([v[mask], p[mask], q[mask]], axis=-1)

    result = np.clip(result * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(result, mode="RGB")


def _colorize(
    img: Image.Image,
    hue: float,
    saturation: float,
    lightness: float,
) -> Image.Image:
    """Colorize image by applying a uniform hue while preserving luminosity.

    Args:
        img: Source image
        hue: Target hue (0-360 degrees)
        saturation: Saturation level (0-100)
        lightness: Lightness offset (-100 to 100)
    """
    # Convert to grayscale to get luminosity
    gray = img.convert("L")
    gray_arr = np.array(gray, dtype=np.float32) / 255.0

    # Apply lightness offset
    gray_arr = np.clip(gray_arr + lightness / 100, 0, 1)

    # Normalize hue and saturation
    h = (hue % 360) / 360.0
    s = np.clip(saturation / 100.0, 0, 1)

    # Create output array
    result = np.zeros((*gray_arr.shape, 3), dtype=np.float32)

    # Vectorized HSL to RGB conversion
    # Using the luminosity from grayscale as L, fixed H and S
    for y in range(gray_arr.shape[0]):
        for x in range(gray_arr.shape[1]):
            lum = gray_arr[y, x]
            r, g, b = colorsys.hls_to_rgb(h, lum, s)
            result[y, x] = [r, g, b]

    result = np.clip(result * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(result, mode="RGB")


def _threshold(img: Image.Image, threshold_value: float) -> Image.Image:
    """Apply threshold to convert image to black and white.

    Args:
        img: Source image
        threshold_value: Threshold point (0.0-1.0)
    """
    thresh = int(threshold_value * 255)
    return img.convert("L").point(lambda p: 255 if p > thresh else 0)


def _posterize(img: Image.Image, levels: int) -> Image.Image:
    """Posterize image by reducing color levels.

    Args:
        img: Source image
        levels: Number of output levels per channel (2-256)
    """
    # ImageOps.posterize takes bits (1-8), where bits determines levels as 2^bits
    # levels=2 -> 1 bit, levels=4 -> 2 bits, levels=256 -> 8 bits
    # Calculate bits needed: bits = ceil(log2(levels))
    levels = max(2, min(256, levels))
    bits = max(1, min(8, int(math.ceil(math.log2(levels)))))
    return ImageOps.posterize(img.convert("RGB"), bits)


def _desaturate(img: Image.Image, mode: str) -> Image.Image:
    """Desaturate image to grayscale using various methods.

    Args:
        img: Source image
        mode: Grayscale method - "luminosity" (Rec. 601), "luma" (Rec. 709),
              "average" (equal weights), "lightness" (HSL lightness)
    """
    rgb_img = img.convert("RGB")
    arr = np.array(rgb_img, dtype=np.float32)

    if mode == "average":
        gray = np.mean(arr[:, :, :3], axis=2)
    elif mode == "lightness":
        # HSL lightness: (max + min) / 2
        gray = (np.max(arr[:, :, :3], axis=2) + np.min(arr[:, :, :3], axis=2)) / 2
    elif mode == "luma":
        # Rec. 709 (HDTV)
        gray = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    else:  # luminosity (default) - Rec. 601 (SDTV)
        gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]

    return Image.fromarray(gray.astype(np.uint8), mode="L")


def _auto_color(img: Image.Image) -> Image.Image:
    """Automatic color correction via per-channel histogram equalization.

    Args:
        img: Source image
    """
    if img.mode == "RGB":
        channels = img.split()
        eq_channels = [ImageOps.equalize(ch) for ch in channels]
        return Image.merge("RGB", eq_channels)
    elif img.mode == "RGBA":
        r, g, b, a = img.split()
        eq_channels = [ImageOps.equalize(ch) for ch in (r, g, b)]
        eq_channels.append(a)
        return Image.merge("RGBA", eq_channels)
    else:
        return ImageOps.equalize(img.convert("L"))
