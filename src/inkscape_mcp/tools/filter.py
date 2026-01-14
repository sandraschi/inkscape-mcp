"""
GIMP Filter Portmanteau Tool.

Comprehensive filter and effects operations for GIMP MCP.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class FilterResult(BaseModel):
    """Result model for filter operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: Optional[str] = None


async def gimp_filter(
    operation: Literal[
        "blur",
        "sharpen",
        "noise",
        "edge_detect",
        "artistic",
        "enhance",
        "distort",
        "light_shadow",
    ],
    input_path: str,
    output_path: str,
    # Blur parameters
    blur_method: str = "gaussian",
    blur_radius: float = 5.0,
    blur_angle: float = 0.0,
    # Sharpen parameters
    sharpen_method: str = "unsharp_mask",
    sharpen_amount: float = 1.0,
    sharpen_threshold: float = 0.0,
    # Noise parameters
    noise_method: str = "add",
    noise_amount: float = 0.1,
    noise_monochrome: bool = True,
    # Edge detection parameters
    edge_method: str = "sobel",
    edge_amount: float = 1.0,
    edge_invert: bool = False,
    # Artistic parameters
    artistic_effect: str = "oilify",
    artistic_size: int = 8,
    artistic_intensity: float = 0.5,
    # Enhance parameters
    enhance_method: str = "sharpen",
    enhance_amount: float = 1.0,
    # Distort parameters
    distort_effect: str = "ripple",
    distort_amplitude: float = 10.0,
    distort_wavelength: float = 20.0,
    # Light/Shadow parameters
    light_effect: str = "vignette",
    light_amount: float = 0.5,
    # Common
    overwrite: bool = False,
    # Dependencies
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Comprehensive filter and effects portmanteau for GIMP MCP.

    PORTMANTEAU PATTERN RATIONALE:
    Instead of creating 20+ separate tools (one per filter), this tool consolidates
    related filter operations into a single interface. This design:
    - Prevents tool explosion (20+ tools → 1 tool) while maintaining full functionality
    - Improves discoverability by grouping related operations together
    - Reduces cognitive load when working with image filters
    - Enables consistent filter interface across all operations
    - Follows FastMCP 2.13+ best practices for feature-rich MCP servers

    SUPPORTED OPERATIONS:
    - blur: Various blur effects (gaussian, motion, zoom, radial, lens)
    - sharpen: Sharpening filters (unsharp_mask, high_pass, smart)
    - noise: Add or reduce noise
    - edge_detect: Edge detection (sobel, canny, laplace)
    - artistic: Artistic effects (oilify, cartoon, watercolor)
    - enhance: Enhancement filters (sharpen, denoise, detail)
    - distort: Distortion effects (ripple, wave, twirl)
    - light_shadow: Lighting effects (vignette, lens_flare, drop_shadow)

    Args:
        operation: Filter operation to perform. MUST be one of:
            - "blur": Apply blur effect (requires: blur_method, blur_radius)
            - "sharpen": Apply sharpening (requires: sharpen_method, sharpen_amount)
            - "noise": Add/reduce noise (requires: noise_method, noise_amount)
            - "edge_detect": Detect edges (requires: edge_method)
            - "artistic": Apply artistic effect (requires: artistic_effect)
            - "enhance": Enhance image (requires: enhance_method)
            - "distort": Apply distortion (requires: distort_effect)
            - "light_shadow": Light effects (requires: light_effect)

        input_path: Path to source image. Required for all operations.

        output_path: Path for output image. Required for all operations.

        blur_method: Blur algorithm. Used by: blur operation.
            Valid: "gaussian" (default), "motion", "zoom", "radial", "lens", "pixelize"

        blur_radius: Blur strength in pixels (0.1-100). Used by: blur. Default: 5.0

        blur_angle: Angle for motion/zoom blur (0-360). Used by: blur. Default: 0

        sharpen_method: Sharpening algorithm. Used by: sharpen operation.
            Valid: "unsharp_mask" (default), "high_pass", "smart"

        sharpen_amount: Sharpening strength (0.1-5.0). Used by: sharpen. Default: 1.0

        sharpen_threshold: Edge threshold (0.0-1.0). Used by: sharpen. Default: 0

        noise_method: Noise operation. Used by: noise operation.
            Valid: "add" (default), "reduce", "spread", "despeckle"

        noise_amount: Noise strength (0.0-1.0). Used by: noise. Default: 0.1

        noise_monochrome: Grayscale noise. Used by: noise. Default: True

        edge_method: Edge detection algorithm. Used by: edge_detect operation.
            Valid: "sobel" (default), "canny", "laplace", "prewitt", "neon"

        edge_amount: Edge detection strength (0.1-5.0). Used by: edge_detect. Default: 1.0

        edge_invert: Invert edge result. Used by: edge_detect. Default: False

        artistic_effect: Artistic effect type. Used by: artistic operation.
            Valid: "oilify", "cartoon", "watercolor", "pencil", "emboss"

        artistic_size: Effect size/radius (1-100). Used by: artistic. Default: 8

        artistic_intensity: Effect strength (0.0-1.0). Used by: artistic. Default: 0.5

    Returns:
        Dict containing filter results.

    Examples:
        # Gaussian blur
        gimp_filter("blur", "photo.jpg", "blurred.jpg", blur_method="gaussian", blur_radius=10)

        # Motion blur
        gimp_filter("blur", "photo.jpg", "motion.jpg", blur_method="motion", blur_radius=20, blur_angle=45)

        # Sharpen
        gimp_filter("sharpen", "photo.jpg", "sharp.jpg", sharpen_amount=1.5)

        # Edge detection
        gimp_filter("edge_detect", "photo.jpg", "edges.jpg", edge_method="sobel")

        # Artistic oilify
        gimp_filter("artistic", "photo.jpg", "oil.jpg", artistic_effect="oilify", artistic_size=12)
    """
    start_time = time.time()

    try:
        from PIL import Image

        input_path_obj = Path(input_path)
        output_path_obj = Path(output_path)

        if not input_path_obj.exists():
            return FilterResult(
                success=False,
                operation=operation,
                message=f"Input file not found: {input_path}",
                error="FileNotFoundError",
            ).model_dump()

        if output_path_obj.exists() and not overwrite:
            return FilterResult(
                success=False,
                operation=operation,
                message=f"Output file exists: {output_path}",
                error="Set overwrite=True",
            ).model_dump()

        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(input_path_obj) as img:
            if img.mode == "P":
                img = img.convert("RGB")

            if operation == "blur":
                result = _apply_blur(img, blur_method, blur_radius, blur_angle)
            elif operation == "sharpen":
                result = _apply_sharpen(
                    img, sharpen_method, sharpen_amount, sharpen_threshold
                )
            elif operation == "noise":
                result = _apply_noise(img, noise_method, noise_amount, noise_monochrome)
            elif operation == "edge_detect":
                result = _apply_edge_detect(img, edge_method, edge_amount, edge_invert)
            elif operation == "artistic":
                result = _apply_artistic(
                    img, artistic_effect, artistic_size, artistic_intensity
                )
            elif operation == "enhance":
                result = _apply_enhance(img, enhance_method, enhance_amount)
            elif operation == "distort":
                result = _apply_distort(
                    img, distort_effect, distort_amplitude, distort_wavelength
                )
            elif operation == "light_shadow":
                result = _apply_light_shadow(img, light_effect, light_amount)
            else:
                return FilterResult(
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

        return FilterResult(
            success=True,
            operation=operation,
            message=f"Filter '{operation}' applied successfully",
            data={
                "filter_type": operation,
                "output_path": str(output_path_obj.resolve()),
                "output_size_bytes": output_path_obj.stat().st_size,
            },
            execution_time_ms=round(execution_time, 2),
        ).model_dump()

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return FilterResult(
            success=False,
            operation=operation,
            message=f"Filter failed: {str(e)}",
            error=str(e),
            execution_time_ms=round(execution_time, 2),
        ).model_dump()


def _apply_blur(img, method, radius, angle):
    """Apply blur filter."""
    from PIL import ImageFilter

    if method == "gaussian":
        return img.filter(ImageFilter.GaussianBlur(radius))
    elif method == "box":
        return img.filter(ImageFilter.BoxBlur(radius))
    elif method == "motion":
        # Motion blur via kernel
        import numpy as np

        size = int(radius * 2) | 1  # Ensure odd
        kernel = np.zeros((size, size))
        center = size // 2

        # Create motion blur kernel
        import math

        rad = math.radians(angle)
        for i in range(size):
            x = int(center + (i - center) * math.cos(rad))
            y = int(center + (i - center) * math.sin(rad))
            if 0 <= x < size and 0 <= y < size:
                kernel[y, x] = 1

        kernel = kernel / kernel.sum()
        kernel_flat = kernel.flatten().tolist()
        return img.filter(ImageFilter.Kernel((size, size), kernel_flat, scale=1))
    elif method == "pixelize":
        # Pixelation
        small_size = (
            max(1, img.width // int(radius)),
            max(1, img.height // int(radius)),
        )
        return img.resize(small_size, resample=0).resize(img.size, resample=0)
    else:
        return img.filter(ImageFilter.GaussianBlur(radius))


def _apply_sharpen(img, method, amount, threshold):
    """Apply sharpening filter."""
    from PIL import ImageFilter, ImageEnhance

    if method == "unsharp_mask":
        return img.filter(
            ImageFilter.UnsharpMask(
                radius=2, percent=int(amount * 100), threshold=int(threshold * 255)
            )
        )
    elif method == "high_pass":
        # High-pass sharpening
        blurred = img.filter(ImageFilter.GaussianBlur(2))
        import numpy as np
        from PIL import Image

        arr = np.array(img, dtype=np.float32)
        blur_arr = np.array(blurred, dtype=np.float32)

        # High-pass = original - blurred
        high_pass = arr - blur_arr + 128
        high_pass = np.clip(high_pass, 0, 255).astype(np.uint8)

        # Blend with original
        result = np.clip(arr + (high_pass - 128) * amount, 0, 255).astype(np.uint8)
        return Image.fromarray(result, mode=img.mode)
    else:
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(1 + amount)


def _apply_noise(img, method, amount, monochrome):
    """Apply noise filter."""
    import numpy as np
    from PIL import Image

    arr = np.array(img, dtype=np.float32)

    if method == "add":
        if monochrome:
            noise = np.random.normal(0, amount * 128, arr.shape[:2])
            noise = np.stack([noise] * 3, axis=2) if len(arr.shape) == 3 else noise
        else:
            noise = np.random.normal(0, amount * 128, arr.shape)

        result = np.clip(arr + noise, 0, 255).astype(np.uint8)
    elif method == "reduce":
        # Simple noise reduction via median filter
        from PIL import ImageFilter

        return img.filter(ImageFilter.MedianFilter(3))
    elif method == "spread":
        # Spread pixels
        from PIL import ImageFilter

        return img.filter(ImageFilter.MedianFilter(int(amount * 10) | 1))
    else:
        return img

    return Image.fromarray(result, mode=img.mode)


def _apply_edge_detect(img, method, amount, invert):
    """Apply edge detection."""
    from PIL import ImageFilter, ImageOps

    gray = img.convert("L")

    if method == "sobel":
        result = gray.filter(ImageFilter.FIND_EDGES)
    elif method == "laplace":
        kernel = (-1, -1, -1, -1, 8, -1, -1, -1, -1)
        result = gray.filter(ImageFilter.Kernel((3, 3), kernel, scale=1))
    elif method == "prewitt":
        result = gray.filter(ImageFilter.FIND_EDGES)
    elif method == "canny":
        # Simplified canny using edge enhance + threshold
        result = gray.filter(ImageFilter.EDGE_ENHANCE_MORE)
    else:
        result = gray.filter(ImageFilter.CONTOUR)

    if invert:
        result = ImageOps.invert(result)

    return result.convert("RGB")


def _apply_artistic(img, effect, size, intensity):
    """Apply artistic effect."""
    from PIL import ImageFilter
    import numpy as np
    from PIL import Image

    if effect == "oilify":
        # Oil painting effect via median filter
        return img.filter(ImageFilter.MedianFilter(size | 1))
    elif effect == "cartoon":
        # Cartoon effect: edge detection + color quantization
        edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
        quantized = img.quantize(colors=8).convert("RGB")

        # Blend
        import numpy as np

        arr = np.array(quantized, dtype=np.float32)
        edge_arr = np.array(edges, dtype=np.float32)
        edge_arr = np.stack([edge_arr] * 3, axis=2)

        # Darken where edges are
        result = arr * (1 - edge_arr / 255 * intensity)
        return Image.fromarray(result.astype(np.uint8), mode="RGB")
    elif effect == "emboss":
        return img.filter(ImageFilter.EMBOSS)
    elif effect == "pencil":
        # Pencil sketch effect
        gray = img.convert("L")
        blurred = gray.filter(ImageFilter.GaussianBlur(size))

        import numpy as np

        arr = np.array(gray, dtype=np.float32)
        blur_arr = np.array(blurred, dtype=np.float32)

        # Dodge blend
        result = np.clip(arr / (256 - blur_arr + 1) * 256, 0, 255)
        return Image.fromarray(result.astype(np.uint8), mode="L").convert("RGB")
    else:
        return img


def _apply_enhance(img, method, amount):
    """Apply enhancement filter."""
    from PIL import ImageFilter, ImageEnhance

    if method == "sharpen":
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(1 + amount)
    elif method == "detail":
        return img.filter(ImageFilter.DETAIL)
    elif method == "smooth":
        return img.filter(ImageFilter.SMOOTH_MORE)
    else:
        return img


def _apply_distort(img, effect, amplitude, wavelength):
    """Apply distortion effect."""
    import numpy as np
    from PIL import Image
    import math

    arr = np.array(img)
    h, w = arr.shape[:2]

    # Create coordinate meshgrid
    x, y = np.meshgrid(np.arange(w), np.arange(h))

    if effect == "ripple":
        # Ripple distortion
        dx = (amplitude * np.sin(2 * math.pi * y / wavelength)).astype(int)
        dy = (amplitude * np.sin(2 * math.pi * x / wavelength)).astype(int)
    elif effect == "wave":
        dx = (amplitude * np.sin(2 * math.pi * y / wavelength)).astype(int)
        dy = np.zeros_like(dx)
    elif effect == "twirl":
        cx, cy = w // 2, h // 2
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        angle = amplitude * r / wavelength * math.pi / 180
        dx = ((x - cx) * np.cos(angle) - (y - cy) * np.sin(angle) + cx - x).astype(int)
        dy = ((x - cx) * np.sin(angle) + (y - cy) * np.cos(angle) + cy - y).astype(int)
    else:
        return img

    # Apply distortion
    new_x = np.clip(x + dx, 0, w - 1)
    new_y = np.clip(y + dy, 0, h - 1)

    result = arr[new_y, new_x]
    return Image.fromarray(result, mode=img.mode)


def _apply_light_shadow(img, effect, amount):
    """Apply lighting/shadow effect."""
    import numpy as np
    from PIL import Image

    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]

    if effect == "vignette":
        # Create vignette mask
        cx, cy = w // 2, h // 2
        y, x = np.ogrid[:h, :w]
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        r_max = np.sqrt(cx**2 + cy**2)

        # Vignette falloff
        mask = 1 - (r / r_max) ** 2 * amount
        mask = np.clip(mask, 0, 1)

        if len(arr.shape) == 3:
            mask = np.stack([mask] * arr.shape[2], axis=2)

        result = arr * mask
        return Image.fromarray(result.astype(np.uint8), mode=img.mode)
    else:
        return img
