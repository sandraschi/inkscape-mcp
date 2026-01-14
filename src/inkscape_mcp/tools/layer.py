"""
GIMP Layer Management Portmanteau Tool.

Comprehensive layer operations for GIMP MCP.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class LayerResult(BaseModel):
    """Result model for layer operations."""

    success: bool
    operation: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: Optional[str] = None


async def gimp_layer(
    operation: Literal[
        "create",
        "duplicate",
        "delete",
        "merge",
        "flatten",
        "reorder",
        "properties",
        "info",
        "rename",
        "visibility",
    ],
    input_path: str,
    output_path: str,
    # Layer identification
    layer_index: int = 0,
    layer_name: Optional[str] = None,
    # Create parameters
    layer_type: str = "normal",
    width: Optional[int] = None,
    height: Optional[int] = None,
    fill_color: str = "transparent",
    # Properties
    opacity: float = 100.0,
    blend_mode: str = "normal",
    visible: bool = True,
    locked: bool = False,
    # Merge parameters
    merge_down: bool = False,
    merge_visible: bool = False,
    # Reorder
    new_position: int = 0,
    # Common
    overwrite: bool = False,
    # Dependencies
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """Comprehensive layer management portmanteau for GIMP MCP.

    PORTMANTEAU PATTERN RATIONALE:
    Instead of creating 10+ separate tools (one per layer operation), this tool
    consolidates related layer operations into a single interface. This design:
    - Prevents tool explosion (10 tools → 1 tool) while maintaining full functionality
    - Improves discoverability by grouping related operations together
    - Reduces cognitive load when working with layer management
    - Enables consistent layer interface across all operations
    - Follows FastMCP 2.13+ best practices for feature-rich MCP servers

    SUPPORTED OPERATIONS:
    - create: Create new layer
    - duplicate: Duplicate existing layer
    - delete: Remove layer
    - merge: Merge layers (down or visible)
    - flatten: Flatten all layers
    - reorder: Change layer stack position
    - properties: Set layer properties (opacity, blend mode)
    - info: Get layer information
    - rename: Rename layer
    - visibility: Toggle layer visibility

    NOTE: Full layer operations require GIMP's Script-Fu. This implementation
    provides basic layer info from supported multi-layer formats (PSD, XCF, TIFF).

    Args:
        operation: Layer operation to perform. MUST be one of:
            - "create": Create new layer (requires: layer_name)
            - "duplicate": Duplicate layer (requires: layer_index)
            - "delete": Delete layer (requires: layer_index)
            - "merge": Merge layers (requires: merge_down or merge_visible)
            - "flatten": Flatten all layers (no extra params)
            - "reorder": Reorder layer (requires: layer_index, new_position)
            - "properties": Set properties (requires: layer_index + opacity/blend_mode)
            - "info": Get layer info (requires: input_path)
            - "rename": Rename layer (requires: layer_index, layer_name)
            - "visibility": Toggle visibility (requires: layer_index, visible)

        input_path: Path to source image (XCF, PSD, TIFF). Required for all.

        output_path: Path for modified image. Required for modifying operations.

        layer_index: Zero-based layer index. Default: 0 (topmost layer)

        layer_name: Name for new/renamed layer. Used by: create, rename.

        layer_type: Type of new layer. Used by: create.
            Valid: "normal", "text", "mask"

        width: Layer width. Used by: create. Default: image width

        height: Layer height. Used by: create. Default: image height

        fill_color: Fill for new layer. Used by: create.
            Valid: "transparent", "white", "black", "foreground", "background"

        opacity: Layer opacity (0-100). Used by: properties. Default: 100

        blend_mode: Layer blend mode. Used by: properties.
            Valid: "normal", "multiply", "screen", "overlay", "soft_light", etc.

        visible: Layer visibility. Used by: visibility. Default: True

        locked: Lock layer. Used by: properties. Default: False

        merge_down: Merge with layer below. Used by: merge. Default: False

        merge_visible: Merge all visible layers. Used by: merge. Default: False

        new_position: New position in stack. Used by: reorder. 0 = top

    Returns:
        Dict containing layer operation results.

    Examples:
        # Get layer info
        gimp_layer("info", "design.psd", "design.psd")

        # Flatten image
        gimp_layer("flatten", "layered.xcf", "flat.png")

        # Set layer opacity
        gimp_layer("properties", "design.psd", "modified.psd", layer_index=1, opacity=50)

        # Merge visible layers
        gimp_layer("merge", "design.psd", "merged.psd", merge_visible=True)
    """
    start_time = time.time()

    try:
        input_path_obj = Path(input_path)
        output_path_obj = Path(output_path)

        if not input_path_obj.exists():
            return LayerResult(
                success=False,
                operation=operation,
                message=f"Input file not found: {input_path}",
                error="FileNotFoundError",
            ).model_dump()

        if output_path_obj.exists() and not overwrite and operation != "info":
            return LayerResult(
                success=False,
                operation=operation,
                message=f"Output file exists: {output_path}",
                error="Set overwrite=True",
            ).model_dump()

        if operation != "info":
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if operation == "info":
            result = _get_layer_info(input_path_obj)
        elif operation == "flatten":
            result = _flatten_layers(input_path_obj, output_path_obj)
        elif operation == "create":
            result = _create_layer(
                input_path_obj,
                output_path_obj,
                layer_name,
                layer_type,
                width,
                height,
                fill_color,
                opacity,
                blend_mode,
                cli_wrapper,
            )
        elif operation == "duplicate":
            result = _duplicate_layer(
                input_path_obj, output_path_obj, layer_index, layer_name, cli_wrapper
            )
        elif operation == "delete":
            result = _delete_layer(
                input_path_obj, output_path_obj, layer_index, cli_wrapper
            )
        elif operation == "merge":
            result = _merge_layers(
                input_path_obj,
                output_path_obj,
                layer_index,
                merge_down,
                merge_visible,
                cli_wrapper,
            )
        elif operation == "reorder":
            result = _reorder_layer(
                input_path_obj, output_path_obj, layer_index, new_position, cli_wrapper
            )
        elif operation == "properties":
            result = _set_layer_properties(
                input_path_obj,
                output_path_obj,
                layer_index,
                opacity,
                blend_mode,
                visible,
                locked,
                cli_wrapper,
            )
        elif operation == "rename":
            result = _rename_layer(
                input_path_obj, output_path_obj, layer_index, layer_name, cli_wrapper
            )
        elif operation == "visibility":
            result = _toggle_visibility(
                input_path_obj, output_path_obj, layer_index, visible, cli_wrapper
            )
        else:
            return LayerResult(
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
        return LayerResult(
            success=False,
            operation=operation,
            message=f"Layer operation failed: {str(e)}",
            error=str(e),
            execution_time_ms=round(execution_time, 2),
        ).model_dump()


def _get_layer_info(input_path: Path) -> Dict[str, Any]:
    """Get layer information from image file."""
    from PIL import Image

    ext = input_path.suffix.lower()
    layers = []

    with Image.open(input_path) as img:
        # For formats that support layers
        if ext in (".psd", ".xcf", ".tiff", ".tif"):
            # Try to get layer info if available
            n_frames = getattr(img, "n_frames", 1)

            for i in range(n_frames):
                try:
                    img.seek(i)
                    layer_info = {
                        "index": i,
                        "name": f"Layer {i}",
                        "size": img.size,
                        "mode": img.mode,
                    }
                    layers.append(layer_info)
                except EOFError:
                    break
        else:
            # Single layer image
            layers.append(
                {
                    "index": 0,
                    "name": "Background",
                    "size": img.size,
                    "mode": img.mode,
                }
            )

    return LayerResult(
        success=True,
        operation="info",
        message=f"Found {len(layers)} layer(s)",
        data={
            "layer_count": len(layers),
            "layers": layers,
            "format": ext.lstrip("."),
            "path": str(input_path.resolve()),
        },
    ).model_dump()


def _flatten_layers(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """Flatten all layers to single layer."""
    from PIL import Image

    with Image.open(input_path) as img:
        # Convert to RGB/RGBA and save - this effectively flattens
        if img.mode in ("P", "PA"):
            img = img.convert("RGBA")

        # For formats with multiple frames, composite them
        if hasattr(img, "n_frames") and img.n_frames > 1:
            # Create canvas
            canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))

            # Composite all frames
            for i in range(img.n_frames):
                try:
                    img.seek(i)
                    frame = img.convert("RGBA")
                    canvas = Image.alpha_composite(canvas, frame)
                except EOFError:
                    break

            result = canvas
        else:
            result = img.convert("RGBA" if img.mode == "RGBA" else "RGB")

        # Save
        save_kwargs = {}
        if output_path.suffix.lower() in (".jpg", ".jpeg"):
            save_kwargs["quality"] = 95
            result = result.convert("RGB")

        result.save(output_path, **save_kwargs)

    return LayerResult(
        success=True,
        operation="flatten",
        message="Layers flattened successfully",
        data={
            "output_path": str(output_path.resolve()),
            "output_size_bytes": output_path.stat().st_size,
        },
    ).model_dump()


def _create_layer(
    input_path,
    output_path,
    name,
    layer_type,
    width,
    height,
    fill_color,
    opacity,
    blend_mode,
    cli_wrapper,
):
    """Create new layer - requires GIMP Script-Fu for full implementation."""
    return LayerResult(
        success=False,
        operation="create",
        message="Layer creation requires GIMP Script-Fu integration",
        error="Full GIMP integration required for layer creation",
    ).model_dump()


def _duplicate_layer(input_path, output_path, layer_index, name, cli_wrapper):
    """Duplicate layer - requires GIMP Script-Fu for full implementation."""
    return LayerResult(
        success=False,
        operation="duplicate",
        message="Layer duplication requires GIMP Script-Fu integration",
        error="Full GIMP integration required for layer duplication",
    ).model_dump()


def _delete_layer(input_path, output_path, layer_index, cli_wrapper):
    """Delete layer - requires GIMP Script-Fu for full implementation."""
    return LayerResult(
        success=False,
        operation="delete",
        message="Layer deletion requires GIMP Script-Fu integration",
        error="Full GIMP integration required for layer deletion",
    ).model_dump()


def _merge_layers(
    input_path, output_path, layer_index, merge_down, merge_visible, cli_wrapper
):
    """Merge layers."""
    if merge_visible:
        # Merge visible is essentially flatten for our purposes
        return _flatten_layers(input_path, output_path)

    return LayerResult(
        success=False,
        operation="merge",
        message="Layer merge down requires GIMP Script-Fu integration",
        error="Full GIMP integration required for merge down",
    ).model_dump()


def _reorder_layer(input_path, output_path, layer_index, new_position, cli_wrapper):
    """Reorder layer - requires GIMP Script-Fu for full implementation."""
    return LayerResult(
        success=False,
        operation="reorder",
        message="Layer reorder requires GIMP Script-Fu integration",
        error="Full GIMP integration required for layer reorder",
    ).model_dump()


def _set_layer_properties(
    input_path,
    output_path,
    layer_index,
    opacity,
    blend_mode,
    visible,
    locked,
    cli_wrapper,
):
    """Set layer properties - requires GIMP Script-Fu for full implementation."""
    return LayerResult(
        success=False,
        operation="properties",
        message="Layer properties require GIMP Script-Fu integration",
        error="Full GIMP integration required for layer properties",
    ).model_dump()


def _rename_layer(input_path, output_path, layer_index, name, cli_wrapper):
    """Rename layer - requires GIMP Script-Fu for full implementation."""
    return LayerResult(
        success=False,
        operation="rename",
        message="Layer rename requires GIMP Script-Fu integration",
        error="Full GIMP integration required for layer rename",
    ).model_dump()


def _toggle_visibility(input_path, output_path, layer_index, visible, cli_wrapper):
    """Toggle layer visibility - requires GIMP Script-Fu for full implementation."""
    return LayerResult(
        success=False,
        operation="visibility",
        message="Layer visibility requires GIMP Script-Fu integration",
        error="Full GIMP integration required for layer visibility",
    ).model_dump()
