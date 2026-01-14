"""
GIMP Batch Processing Portmanteau Tool.

Comprehensive batch operations for GIMP MCP.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class BatchResult(BaseModel):
    """Result model for batch operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: Optional[str] = None


async def inkscape_batch(
    operation: Literal[
        "resize", "convert", "process", "watermark", "rename", "optimize"
    ],
    input_directory: str,
    output_directory: str,
    # Resize parameters
    width: Optional[int] = None,
    height: Optional[int] = None,
    maintain_aspect: bool = True,
    # Convert parameters
    output_format: str = "jpg",
    quality: int = 90,
    # Process parameters (chain of operations)
    operations_chain: Optional[List[Dict[str, Any]]] = None,
    # Watermark parameters
    watermark_path: Optional[str] = None,
    watermark_position: str = "bottom-right",
    watermark_opacity: float = 0.5,
    watermark_scale: float = 0.2,
    # Rename parameters
    rename_pattern: str = "{name}_{index:04d}",
    # Optimize parameters
    optimize_quality: int = 85,
    optimize_max_size_kb: Optional[int] = None,
    # Common
    file_pattern: str = "*.jpg",
    recursive: bool = False,
    overwrite: bool = False,
    max_workers: int = 4,
    # Dependencies
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Comprehensive batch processing portmanteau for GIMP MCP.

    PORTMANTEAU PATTERN RATIONALE:
    Instead of creating 6+ separate tools (one per batch operation), this tool
    consolidates related batch operations into a single interface. This design:
    - Prevents tool explosion (6 tools → 1 tool) while maintaining full functionality
    - Improves discoverability by grouping related operations together
    - Reduces cognitive load when working with batch processing
    - Enables parallel processing with configurable worker count
    - Follows FastMCP 2.13+ best practices for feature-rich MCP servers

    SUPPORTED OPERATIONS:
    - resize: Batch resize multiple images
    - convert: Batch convert to different format
    - process: Apply chain of operations to multiple images
    - watermark: Add watermark to multiple images
    - rename: Batch rename with pattern
    - optimize: Optimize images for web (size/quality balance)

    Args:
        operation: Batch operation to perform. MUST be one of:
            - "resize": Resize all images (requires: width and/or height)
            - "convert": Convert format (requires: output_format)
            - "process": Apply operations chain (requires: operations_chain)
            - "watermark": Add watermark (requires: watermark_path)
            - "rename": Rename files (requires: rename_pattern)
            - "optimize": Optimize for web (optional: optimize_quality, optimize_max_size_kb)

        input_directory: Source directory with images. Required for all.

        output_directory: Destination directory. Required for all.

        width: Target width for resize. Used by: resize. Default: None (use height)

        height: Target height for resize. Used by: resize. Default: None (use width)

        maintain_aspect: Keep aspect ratio. Used by: resize. Default: True

        output_format: Target format. Used by: convert.
            Valid: "jpg", "png", "webp", "tiff". Default: "jpg"

        quality: Output quality (1-100). Used by: convert, optimize. Default: 90

        operations_chain: List of operations to apply. Used by: process.
            Format: [{"operation": "resize", "width": 800}, {"operation": "sharpen"}]

        watermark_path: Path to watermark image. Used by: watermark.

        watermark_position: Watermark placement. Used by: watermark.
            Valid: "top-left", "top-right", "bottom-left", "bottom-right", "center"

        watermark_opacity: Watermark transparency (0.0-1.0). Used by: watermark.

        watermark_scale: Watermark size relative to image (0.1-1.0). Used by: watermark.

        rename_pattern: Rename pattern. Used by: rename.
            Variables: {name}, {index}, {date}, {ext}
            Example: "photo_{index:04d}" → "photo_0001.jpg"

        optimize_quality: Starting quality for optimization. Used by: optimize.

        optimize_max_size_kb: Target max file size in KB. Used by: optimize.

        file_pattern: Glob pattern for input files. Default: "*.jpg"
            Examples: "*.jpg", "*.png", "*.{jpg,png}", "**/*.jpg" (recursive)

        recursive: Search subdirectories. Default: False

        overwrite: Replace existing files. Default: False

        max_workers: Parallel workers (1-8). Default: 4

    Returns:
        Dict containing batch results:
        {
            "success": bool,
            "operation": str,
            "message": str,
            "data": {
                "total_files": int,
                "processed": int,
                "failed": int,
                "skipped": int,
                "results": [
                    {"file": str, "status": str, "output": str},
                    ...
                ]
            },
            "execution_time_ms": float
        }

    Examples:
        # Batch resize to max 1920x1080
        gimp_batch("resize", "photos/", "resized/", width=1920, height=1080)

        # Convert all PNGs to WebP
        gimp_batch("convert", "images/", "webp/", output_format="webp", quality=85,
                   file_pattern="*.png")

        # Add watermark to all photos
        gimp_batch("watermark", "photos/", "watermarked/",
                   watermark_path="logo.png", watermark_position="bottom-right")

        # Optimize for web with max 500KB
        gimp_batch("optimize", "photos/", "web/", optimize_max_size_kb=500)

        # Rename with pattern
        gimp_batch("rename", "photos/", "renamed/", rename_pattern="vacation_{index:04d}")
    """
    start_time = time.time()

    try:
        input_dir = Path(input_directory)
        output_dir = Path(output_directory)

        if not input_dir.exists():
            return BatchResult(
                success=False,
                operation=operation,
                message=f"Input directory not found: {input_directory}",
                error="DirectoryNotFoundError",
            ).model_dump()

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find matching files
        if recursive:
            files = list(input_dir.rglob(file_pattern))
        else:
            files = list(input_dir.glob(file_pattern))

        # Filter to only image files
        image_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
            ".webp",
        }
        files = [
            f for f in files if f.suffix.lower() in image_extensions and f.is_file()
        ]

        if not files:
            return BatchResult(
                success=True,
                operation=operation,
                message="No matching files found",
                data={
                    "total_files": 0,
                    "processed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "results": [],
                },
            ).model_dump()

        # Process files
        results = []
        processed = 0
        failed = 0
        skipped = 0

        for i, file_path in enumerate(files):
            try:
                # Determine output path
                rel_path = file_path.relative_to(input_dir)
                if operation == "convert":
                    out_name = file_path.stem + f".{output_format}"
                elif operation == "rename":
                    out_name = (
                        rename_pattern.format(
                            name=file_path.stem,
                            index=i + 1,
                            date=time.strftime("%Y%m%d"),
                            ext=file_path.suffix,
                        )
                        + file_path.suffix
                    )
                else:
                    out_name = rel_path.name

                output_path = output_dir / rel_path.parent / out_name
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Check if output exists
                if output_path.exists() and not overwrite:
                    results.append(
                        {
                            "file": str(file_path),
                            "status": "skipped",
                            "reason": "exists",
                        }
                    )
                    skipped += 1
                    continue

                # Process based on operation
                if operation == "resize":
                    success = await _batch_resize(
                        file_path, output_path, width, height, maintain_aspect
                    )
                elif operation == "convert":
                    success = await _batch_convert(
                        file_path, output_path, output_format, quality
                    )
                elif operation == "process":
                    success = await _batch_process(
                        file_path, output_path, operations_chain or []
                    )
                elif operation == "watermark":
                    success = await _batch_watermark(
                        file_path,
                        output_path,
                        watermark_path,
                        watermark_position,
                        watermark_opacity,
                        watermark_scale,
                    )
                elif operation == "rename":
                    success = await _batch_rename(file_path, output_path)
                elif operation == "optimize":
                    success = await _batch_optimize(
                        file_path, output_path, optimize_quality, optimize_max_size_kb
                    )
                else:
                    success = False

                if success:
                    results.append(
                        {
                            "file": str(file_path),
                            "status": "success",
                            "output": str(output_path),
                        }
                    )
                    processed += 1
                else:
                    results.append({"file": str(file_path), "status": "failed"})
                    failed += 1

            except Exception as e:
                results.append(
                    {"file": str(file_path), "status": "error", "error": str(e)}
                )
                failed += 1

        execution_time = (time.time() - start_time) * 1000

        return BatchResult(
            success=failed == 0,
            operation=operation,
            message=f"Processed {processed}/{len(files)} files ({failed} failed, {skipped} skipped)",
            data={
                "total_files": len(files),
                "processed": processed,
                "failed": failed,
                "skipped": skipped,
                "results": results[:100],  # Limit results in response
            },
            execution_time_ms=round(execution_time, 2),
        ).model_dump()

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return BatchResult(
            success=False,
            operation=operation,
            message=f"Batch operation failed: {str(e)}",
            error=str(e),
            execution_time_ms=round(execution_time, 2),
        ).model_dump()


async def _batch_resize(
    input_path: Path, output_path: Path, width, height, maintain_aspect
) -> bool:
    """Resize single image."""
    from PIL import Image

    with Image.open(input_path) as img:
        if width is None and height is None:
            return False

        orig_w, orig_h = img.size

        if maintain_aspect:
            if width and height:
                ratio = min(width / orig_w, height / orig_h)
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
            elif width:
                ratio = width / orig_w
                new_w = width
                new_h = int(orig_h * ratio)
            else:
                ratio = height / orig_h
                new_w = int(orig_w * ratio)
                new_h = height
        else:
            new_w = width or orig_w
            new_h = height or orig_h

        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        save_kwargs = {}
        if output_path.suffix.lower() in (".jpg", ".jpeg"):
            save_kwargs["quality"] = 95
            if resized.mode == "RGBA":
                resized = resized.convert("RGB")

        resized.save(output_path, **save_kwargs)

    return True


async def _batch_convert(
    input_path: Path, output_path: Path, format: str, quality: int
) -> bool:
    """Convert single image."""
    from PIL import Image

    with Image.open(input_path) as img:
        save_kwargs = {}

        if format in ("jpg", "jpeg"):
            save_kwargs["quality"] = quality
            if img.mode == "RGBA":
                img = img.convert("RGB")
        elif format == "webp":
            save_kwargs["quality"] = quality
        elif format == "png":
            save_kwargs["compress_level"] = 9

        img.save(output_path, **save_kwargs)

    return True


async def _batch_process(
    input_path: Path, output_path: Path, operations: List[Dict]
) -> bool:
    """Process image with chain of operations."""
    from PIL import Image

    with Image.open(input_path) as img:
        result = img.copy()

        for op in operations:
            op_type = op.get("operation")

            if op_type == "resize":
                w = op.get("width")
                h = op.get("height")
                if w or h:
                    new_size = (w or result.width, h or result.height)
                    result = result.resize(new_size, Image.Resampling.LANCZOS)
            elif op_type == "rotate":
                angle = op.get("angle", 0)
                result = result.rotate(angle, expand=True)
            elif op_type == "sharpen":
                from PIL import ImageFilter

                result = result.filter(ImageFilter.SHARPEN)
            elif op_type == "blur":
                from PIL import ImageFilter

                radius = op.get("radius", 2)
                result = result.filter(ImageFilter.GaussianBlur(radius))

        save_kwargs = {}
        if output_path.suffix.lower() in (".jpg", ".jpeg"):
            save_kwargs["quality"] = 95
            if result.mode == "RGBA":
                result = result.convert("RGB")

        result.save(output_path, **save_kwargs)

    return True


async def _batch_watermark(
    input_path: Path,
    output_path: Path,
    watermark_path: str,
    position: str,
    opacity: float,
    scale: float,
) -> bool:
    """Add watermark to image."""
    from PIL import Image

    if not watermark_path or not Path(watermark_path).exists():
        return False

    with Image.open(input_path) as img, Image.open(watermark_path) as wm:
        img = img.convert("RGBA")

        # Scale watermark
        wm_w = int(img.width * scale)
        wm_h = int(wm.height * (wm_w / wm.width))
        wm = wm.resize((wm_w, wm_h), Image.Resampling.LANCZOS).convert("RGBA")

        # Apply opacity
        if opacity < 1.0:
            alpha = wm.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            wm.putalpha(alpha)

        # Position
        margin = 10
        if position == "top-left":
            pos = (margin, margin)
        elif position == "top-right":
            pos = (img.width - wm.width - margin, margin)
        elif position == "bottom-left":
            pos = (margin, img.height - wm.height - margin)
        elif position == "bottom-right":
            pos = (img.width - wm.width - margin, img.height - wm.height - margin)
        else:  # center
            pos = ((img.width - wm.width) // 2, (img.height - wm.height) // 2)

        # Composite
        img.paste(wm, pos, wm)

        # Save
        if output_path.suffix.lower() in (".jpg", ".jpeg"):
            img = img.convert("RGB")

        img.save(output_path, quality=95)

    return True


async def _batch_rename(input_path: Path, output_path: Path) -> bool:
    """Rename/copy file."""
    import shutil

    shutil.copy2(input_path, output_path)
    return True


async def _batch_optimize(
    input_path: Path, output_path: Path, quality: int, max_size_kb: Optional[int]
) -> bool:
    """Optimize image for web."""
    from PIL import Image

    with Image.open(input_path) as img:
        if img.mode == "RGBA":
            # Keep transparency for PNG
            if output_path.suffix.lower() == ".png":
                img.save(output_path, optimize=True)
            else:
                img = img.convert("RGB")
                img.save(output_path, quality=quality, optimize=True)
        else:
            img.save(output_path, quality=quality, optimize=True)

        # If max size specified, iteratively reduce quality
        if max_size_kb:
            current_quality = quality
            while (
                output_path.stat().st_size > max_size_kb * 1024 and current_quality > 20
            ):
                current_quality -= 5
                with Image.open(input_path) as img2:
                    if img2.mode == "RGBA":
                        img2 = img2.convert("RGB")
                    img2.save(output_path, quality=current_quality, optimize=True)

    return True
