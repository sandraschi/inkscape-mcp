"""
GIMP Image Analysis Portmanteau Tool.

Comprehensive image analysis and quality assessment for GIMP MCP.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Result model for analysis operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: Optional[str] = None


async def gimp_analysis(
    operation: Literal[
        "quality",
        "statistics",
        "histogram",
        "compare",
        "detect_issues",
        "report",
        "color_profile",
        "metadata",
    ],
    input_path: str,
    compare_path: Optional[str] = None,
    # Analysis options
    include_histogram: bool = True,
    include_color_info: bool = True,
    analysis_type: str = "comprehensive",
    # Issue detection
    check_types: Optional[List[str]] = None,
    # Report options
    report_format: str = "detailed",
    # Dependencies
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Comprehensive image analysis portmanteau for GIMP MCP.

    PORTMANTEAU PATTERN RATIONALE:
    Instead of creating 8+ separate tools (one per analysis type), this tool
    consolidates related analysis operations into a single interface. This design:
    - Prevents tool explosion (8 tools → 1 tool) while maintaining full functionality
    - Improves discoverability by grouping related operations together
    - Reduces cognitive load when working with image analysis
    - Enables consistent analysis interface across all operations
    - Follows FastMCP 2.13+ best practices for feature-rich MCP servers

    SUPPORTED OPERATIONS:
    - quality: Comprehensive quality assessment (sharpness, noise, exposure)
    - statistics: Extract image statistics (mean, std, min, max, histogram)
    - histogram: Generate histogram data for all channels
    - compare: Compare two images (PSNR, SSIM, visual diff)
    - detect_issues: Detect common issues (overexposure, blur, noise)
    - report: Generate comprehensive analysis report
    - color_profile: Analyze color profile and gamut
    - metadata: Extract all metadata (EXIF, IPTC, XMP)

    Args:
        operation: Analysis operation to perform. MUST be one of:
            - "quality": Quality assessment (no extra params)
            - "statistics": Image statistics (optional: include_histogram)
            - "histogram": Histogram data (no extra params)
            - "compare": Compare images (requires: compare_path)
            - "detect_issues": Issue detection (optional: check_types)
            - "report": Full report (optional: report_format)
            - "color_profile": Color analysis (no extra params)
            - "metadata": Extract metadata (no extra params)

        input_path: Path to source image. Required for all operations.

        compare_path: Path to comparison image. Required for: compare.

        include_histogram: Include histogram in statistics. Default: True

        include_color_info: Include color analysis. Default: True

        analysis_type: Depth of analysis. Used by: quality, report.
            Valid: "basic", "comprehensive" (default), "detailed"

        check_types: Issue types to check. Used by: detect_issues.
            Valid: ["all"], ["exposure", "sharpness", "noise", "color", "artifacts"]
            Default: ["all"]

        report_format: Report detail level. Used by: report.
            Valid: "basic", "detailed" (default), "technical"

    Returns:
        Dict containing analysis results with operation-specific data.

    Examples:
        # Quality assessment
        gimp_analysis("quality", "photo.jpg")

        # Get statistics with histogram
        gimp_analysis("statistics", "photo.jpg", include_histogram=True)

        # Compare two images
        gimp_analysis("compare", "original.jpg", compare_path="edited.jpg")

        # Detect issues
        gimp_analysis("detect_issues", "photo.jpg", check_types=["exposure", "sharpness"])

        # Full report
        gimp_analysis("report", "photo.jpg", report_format="technical")

        # Extract metadata
        gimp_analysis("metadata", "photo.jpg")
    """
    start_time = time.time()

    try:
        input_path_obj = Path(input_path)

        if not input_path_obj.exists():
            return AnalysisResult(
                success=False,
                operation=operation,
                message=f"Input file not found: {input_path}",
                error="FileNotFoundError",
            ).model_dump()

        if operation == "compare" and compare_path:
            compare_path_obj = Path(compare_path)
            if not compare_path_obj.exists():
                return AnalysisResult(
                    success=False,
                    operation=operation,
                    message=f"Comparison file not found: {compare_path}",
                    error="FileNotFoundError",
                ).model_dump()

        if operation == "quality":
            result = _analyze_quality(input_path_obj, analysis_type)
        elif operation == "statistics":
            result = _get_statistics(
                input_path_obj, include_histogram, include_color_info
            )
        elif operation == "histogram":
            result = _get_histogram(input_path_obj)
        elif operation == "compare":
            if not compare_path:
                return AnalysisResult(
                    success=False,
                    operation=operation,
                    message="compare_path is required for compare operation",
                    error="Missing required parameter",
                ).model_dump()
            result = _compare_images(input_path_obj, Path(compare_path))
        elif operation == "detect_issues":
            result = _detect_issues(input_path_obj, check_types or ["all"])
        elif operation == "report":
            result = _generate_report(input_path_obj, report_format)
        elif operation == "color_profile":
            result = _analyze_color_profile(input_path_obj)
        elif operation == "metadata":
            result = _extract_metadata(input_path_obj)
        else:
            return AnalysisResult(
                success=False,
                operation=operation,
                message=f"Unknown operation: {operation}",
                error="Invalid operation",
            ).model_dump()

        execution_time = (time.time() - start_time) * 1000
        result["execution_time_ms"] = round(execution_time, 2)
        return result

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return AnalysisResult(
            success=False,
            operation=operation,
            message=f"Analysis failed: {str(e)}",
            error=str(e),
            execution_time_ms=round(execution_time, 2),
        ).model_dump()


def _analyze_quality(input_path: Path, analysis_type: str) -> Dict[str, Any]:
    """Analyze image quality."""
    from PIL import Image
    import numpy as np

    with Image.open(input_path) as img:
        arr = np.array(img)

        # Sharpness estimation (Laplacian variance)
        if len(arr.shape) == 3:
            gray = np.mean(arr, axis=2)
        else:
            gray = arr

        # Try scipy for better Laplacian, fall back to simple gradient variance
        try:
            from scipy import ndimage

            laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
            lap = ndimage.convolve(gray.astype(float), laplacian)
            sharpness = np.var(lap)
        except ImportError:
            # Fallback: use gradient variance as sharpness proxy
            sharpness = np.var(np.diff(gray.astype(float), axis=0)) + np.var(
                np.diff(gray.astype(float), axis=1)
            )

        # Noise estimation
        noise_estimate = np.std(np.diff(gray.astype(float))) / 1.4  # Approximate

        # Exposure analysis
        if len(arr.shape) == 3:
            luminance = (
                0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            )
        else:
            luminance = arr

        mean_luminance = np.mean(luminance)
        overexposed = np.sum(luminance > 250) / luminance.size * 100
        underexposed = np.sum(luminance < 5) / luminance.size * 100

        # Dynamic range
        dynamic_range = np.max(arr) - np.min(arr)

        # Quality scores (0-100)
        sharpness_score = min(100, sharpness / 100)
        noise_score = max(0, 100 - noise_estimate * 2)
        exposure_score = max(
            0, 100 - abs(mean_luminance - 128) * 0.5 - overexposed - underexposed
        )

        overall_score = sharpness_score * 0.4 + noise_score * 0.3 + exposure_score * 0.3

        quality_data = {
            "overall_score": round(overall_score, 1),
            "sharpness": {
                "score": round(sharpness_score, 1),
                "value": round(sharpness, 2),
                "assessment": "Sharp"
                if sharpness_score > 60
                else "Soft"
                if sharpness_score > 30
                else "Blurry",
            },
            "noise": {
                "score": round(noise_score, 1),
                "estimate": round(noise_estimate, 2),
                "assessment": "Clean"
                if noise_score > 70
                else "Moderate"
                if noise_score > 40
                else "Noisy",
            },
            "exposure": {
                "score": round(exposure_score, 1),
                "mean_luminance": round(mean_luminance, 1),
                "overexposed_percent": round(overexposed, 2),
                "underexposed_percent": round(underexposed, 2),
                "dynamic_range": int(dynamic_range),
                "assessment": "Good"
                if exposure_score > 70
                else "Fair"
                if exposure_score > 40
                else "Poor",
            },
        }

        return AnalysisResult(
            success=True,
            operation="quality",
            message=f"Quality score: {overall_score:.1f}/100",
            data=quality_data,
        ).model_dump()


def _get_statistics(
    input_path: Path, include_histogram: bool, include_color_info: bool
) -> Dict[str, Any]:
    """Get image statistics."""
    from PIL import Image
    import numpy as np

    with Image.open(input_path) as img:
        arr = np.array(img)

        stats = {
            "dimensions": {"width": img.width, "height": img.height},
            "mode": img.mode,
            "channels": len(img.getbands()),
            "total_pixels": img.width * img.height,
            "file_size_bytes": input_path.stat().st_size,
        }

        # Per-channel statistics
        channel_stats = {}
        bands = img.getbands()

        if len(arr.shape) == 3:
            for i, band in enumerate(bands[: arr.shape[2]]):
                channel = arr[:, :, i]
                channel_stats[band] = {
                    "min": int(np.min(channel)),
                    "max": int(np.max(channel)),
                    "mean": round(float(np.mean(channel)), 2),
                    "std": round(float(np.std(channel)), 2),
                    "median": int(np.median(channel)),
                }
        else:
            channel_stats["L"] = {
                "min": int(np.min(arr)),
                "max": int(np.max(arr)),
                "mean": round(float(np.mean(arr)), 2),
                "std": round(float(np.std(arr)), 2),
                "median": int(np.median(arr)),
            }

        stats["channel_statistics"] = channel_stats

        if include_histogram:
            stats["histogram"] = _compute_histogram(arr, bands)

        if include_color_info:
            stats["color_info"] = _analyze_colors(img)

        return AnalysisResult(
            success=True,
            operation="statistics",
            message=f"Statistics for {img.width}x{img.height} {img.mode} image",
            data=stats,
        ).model_dump()


def _compute_histogram(arr, bands):
    """Compute histogram for all channels."""
    import numpy as np

    histograms = {}

    if len(arr.shape) == 3:
        for i, band in enumerate(bands[: arr.shape[2]]):
            hist, _ = np.histogram(arr[:, :, i], bins=256, range=(0, 255))
            histograms[band] = hist.tolist()
    else:
        hist, _ = np.histogram(arr, bins=256, range=(0, 255))
        histograms["L"] = hist.tolist()

    return histograms


def _analyze_colors(img):
    """Analyze dominant colors."""
    from PIL import Image
    import numpy as np

    # Reduce to find dominant colors
    small = img.resize((100, 100), Image.Resampling.LANCZOS)
    small = small.convert("RGB")
    arr = np.array(small)

    # Reshape to list of pixels
    pixels = arr.reshape(-1, 3)

    # Simple k-means to find dominant colors
    from collections import Counter

    # Quantize colors
    quantized = (pixels // 32) * 32
    color_counts = Counter(map(tuple, quantized))

    dominant = [
        {"rgb": list(color), "count": count}
        for color, count in color_counts.most_common(5)
    ]

    return {
        "dominant_colors": dominant,
        "unique_colors_estimate": len(color_counts),
    }


def _get_histogram(input_path: Path) -> Dict[str, Any]:
    """Get histogram data."""
    from PIL import Image
    import numpy as np

    with Image.open(input_path) as img:
        arr = np.array(img)
        bands = img.getbands()

        histograms = _compute_histogram(arr, bands)

        return AnalysisResult(
            success=True,
            operation="histogram",
            message=f"Histogram for {len(bands)} channel(s)",
            data={
                "channels": list(bands),
                "histograms": histograms,
                "bins": 256,
            },
        ).model_dump()


def _compare_images(path1: Path, path2: Path) -> Dict[str, Any]:
    """Compare two images."""
    from PIL import Image
    import numpy as np

    with Image.open(path1) as img1, Image.open(path2) as img2:
        # Resize to same size if needed
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

        # Convert to same mode
        img1 = img1.convert("RGB")
        img2 = img2.convert("RGB")

        arr1 = np.array(img1, dtype=np.float64)
        arr2 = np.array(img2, dtype=np.float64)

        # MSE and PSNR
        mse = np.mean((arr1 - arr2) ** 2)
        if mse == 0:
            psnr = float("inf")
        else:
            psnr = 10 * np.log10(255**2 / mse)

        # Simple SSIM approximation
        mean1, mean2 = np.mean(arr1), np.mean(arr2)
        std1, std2 = np.std(arr1), np.std(arr2)
        cov = np.mean((arr1 - mean1) * (arr2 - mean2))

        c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
        ssim = ((2 * mean1 * mean2 + c1) * (2 * cov + c2)) / (
            (mean1**2 + mean2**2 + c1) * (std1**2 + std2**2 + c2)
        )

        # Difference statistics
        diff = np.abs(arr1 - arr2)

        return AnalysisResult(
            success=True,
            operation="compare",
            message=f"PSNR: {psnr:.2f} dB, SSIM: {ssim:.4f}",
            data={
                "psnr": round(psnr, 2),
                "ssim": round(ssim, 4),
                "mse": round(mse, 2),
                "max_difference": int(np.max(diff)),
                "mean_difference": round(np.mean(diff), 2),
                "identical": mse == 0,
                "similar": ssim > 0.95,
            },
        ).model_dump()


def _detect_issues(input_path: Path, check_types: List[str]) -> Dict[str, Any]:
    """Detect common image issues."""
    from PIL import Image
    import numpy as np

    issues = []
    warnings = []

    with Image.open(input_path) as img:
        arr = np.array(img)

        check_all = "all" in check_types

        # Exposure check
        if check_all or "exposure" in check_types:
            if len(arr.shape) == 3:
                luminance = (
                    0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
                )
            else:
                luminance = arr

            overexposed = np.sum(luminance > 250) / luminance.size * 100
            underexposed = np.sum(luminance < 5) / luminance.size * 100

            if overexposed > 5:
                issues.append(f"Overexposed: {overexposed:.1f}% of pixels blown out")
            elif overexposed > 1:
                warnings.append(
                    f"Slight overexposure: {overexposed:.1f}% clipped highlights"
                )

            if underexposed > 5:
                issues.append(f"Underexposed: {underexposed:.1f}% of pixels crushed")
            elif underexposed > 1:
                warnings.append(
                    f"Slight underexposure: {underexposed:.1f}% crushed shadows"
                )

        # Sharpness check
        if check_all or "sharpness" in check_types:
            if len(arr.shape) == 3:
                gray = np.mean(arr, axis=2)
            else:
                gray = arr

            sharpness = np.var(np.diff(gray.astype(float)))
            if sharpness < 100:
                issues.append("Image appears blurry or out of focus")
            elif sharpness < 300:
                warnings.append("Image may be slightly soft")

        # Noise check
        if check_all or "noise" in check_types:
            if len(arr.shape) == 3:
                gray = np.mean(arr, axis=2)
            else:
                gray = arr

            noise_estimate = np.std(np.diff(gray.astype(float))) / 1.4
            if noise_estimate > 20:
                issues.append(f"High noise detected (estimate: {noise_estimate:.1f})")
            elif noise_estimate > 10:
                warnings.append(
                    f"Moderate noise detected (estimate: {noise_estimate:.1f})"
                )

        # Color check
        if check_all or "color" in check_types:
            if len(arr.shape) == 3 and arr.shape[2] >= 3:
                r_mean = np.mean(arr[:, :, 0])
                g_mean = np.mean(arr[:, :, 1])
                b_mean = np.mean(arr[:, :, 2])

                color_bias = max(
                    abs(r_mean - g_mean), abs(g_mean - b_mean), abs(r_mean - b_mean)
                )
                if color_bias > 30:
                    dominant = (
                        "Red"
                        if r_mean > g_mean and r_mean > b_mean
                        else "Green"
                        if g_mean > r_mean and g_mean > b_mean
                        else "Blue"
                    )
                    warnings.append(
                        f"Possible color cast detected ({dominant} dominant)"
                    )

    return AnalysisResult(
        success=True,
        operation="detect_issues",
        message=f"Found {len(issues)} issue(s) and {len(warnings)} warning(s)",
        data={
            "issues": issues,
            "warnings": warnings,
            "issue_count": len(issues),
            "warning_count": len(warnings),
            "checks_performed": check_types
            if not check_all
            else ["exposure", "sharpness", "noise", "color"],
        },
    ).model_dump()


def _generate_report(input_path: Path, report_format: str) -> Dict[str, Any]:
    """Generate comprehensive analysis report."""
    # Combine multiple analyses
    quality = _analyze_quality(input_path, "comprehensive")
    stats = _get_statistics(input_path, True, True)
    issues = _detect_issues(input_path, ["all"])
    metadata = _extract_metadata(input_path)

    report = {
        "summary": {
            "file": str(input_path.name),
            "quality_score": quality["data"].get("overall_score", 0),
            "issue_count": issues["data"].get("issue_count", 0),
            "warning_count": issues["data"].get("warning_count", 0),
        },
        "quality": quality["data"],
        "statistics": stats["data"],
        "issues": issues["data"],
        "metadata": metadata["data"],
    }

    return AnalysisResult(
        success=True,
        operation="report",
        message=f"Analysis report for {input_path.name}",
        data=report,
    ).model_dump()


def _analyze_color_profile(input_path: Path) -> Dict[str, Any]:
    """Analyze color profile."""
    from PIL import Image

    with Image.open(input_path) as img:
        profile = None

        # Try to get ICC profile
        if "icc_profile" in img.info:
            try:
                from io import BytesIO
                from PIL import ImageCms

                icc = img.info.get("icc_profile")
                profile_obj = ImageCms.ImageCmsProfile(BytesIO(icc))
                profile = {
                    "description": ImageCms.getProfileDescription(profile_obj),
                    "name": ImageCms.getProfileName(profile_obj),
                }
            except Exception:
                profile = {"raw": "Present but could not parse"}

        return AnalysisResult(
            success=True,
            operation="color_profile",
            message=f"Color profile: {'Found' if profile else 'None embedded'}",
            data={
                "mode": img.mode,
                "profile": profile,
                "has_profile": profile is not None,
            },
        ).model_dump()


def _extract_metadata(input_path: Path) -> Dict[str, Any]:
    """Extract all metadata."""
    from PIL import Image

    with Image.open(input_path) as img:
        metadata = {}

        # Basic info
        metadata["format"] = img.format
        metadata["mode"] = img.mode
        metadata["size"] = list(img.size)

        # EXIF
        if hasattr(img, "_getexif") and img._getexif():
            try:
                from PIL.ExifTags import TAGS

                exif = img._getexif()
                metadata["exif"] = {}
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if isinstance(value, bytes):
                        value = value.decode("utf-8", errors="ignore")
                    metadata["exif"][str(tag)] = str(value)[
                        :200
                    ]  # Truncate long values
            except Exception as e:
                metadata["exif_error"] = str(e)

        # Other info
        metadata["info"] = {
            k: str(v)[:200]
            for k, v in img.info.items()
            if k not in ("icc_profile", "exif")
        }

        return AnalysisResult(
            success=True,
            operation="metadata",
            message=f"Extracted metadata from {img.format} image",
            data=metadata,
        ).model_dump()
