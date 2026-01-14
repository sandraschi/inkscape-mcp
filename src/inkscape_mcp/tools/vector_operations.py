"""
Inkscape Vector Operations Tools.

Advanced vector graphics operations using Inkscape's actions system.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

async def inkscape_vector(
    operation: Literal["trace_image", "apply_boolean", "optimize_svg", "render_preview"],
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    # For trace_image
    trace_type: str = "brightness",
    threshold: int = 128,
    # For apply_boolean
    boolean_op: str = "union",
    object_ids: Optional[List[str]] = None,
    # For render_preview
    dpi: int = 300,
    # Injected dependencies
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """
    Advanced vector operations using Inkscape's powerful capabilities.

    SUPPORTED OPERATIONS:
    - trace_image: Convert raster image to vector SVG paths
    - apply_boolean: Perform boolean operations on vector shapes
    - optimize_svg: Clean and optimize SVG for web use
    - render_preview: Generate high-res PNG preview

    Returns:
        Dict with operation results
    """

    start_time = time.time()

    try:
        if operation == "trace_image":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            if cli_wrapper:
                result = await cli_wrapper.trace_bitmap(
                    input_path=input_path,
                    output_path=output_path,
                    trace_type=trace_type,
                    threshold=threshold
                )

                output_size = Path(output_path).stat().st_size

                return {
                    "success": True,
                    "operation": "trace_image",
                    "message": f"Traced bitmap to vector: {Path(input_path).name}",
                    "data": {
                        "input_path": str(Path(input_path).resolve()),
                        "output_path": str(Path(output_path).resolve()),
                        "trace_type": trace_type,
                        "threshold": threshold,
                        "output_size_bytes": output_size,
                    },
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }
            else:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "CLI wrapper not available",
                    "error": "Inkscape CLI wrapper required",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

        elif operation == "apply_boolean":
            if not input_path or not output_path or not object_ids:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path, output_path, and object_ids required",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            if cli_wrapper:
                result = await cli_wrapper.apply_boolean(
                    input_path=input_path,
                    output_path=output_path,
                    operation=boolean_op,
                    object_ids=object_ids
                )

                return {
                    "success": True,
                    "operation": "apply_boolean",
                    "message": f"Applied {boolean_op} operation to {len(object_ids)} objects",
                    "data": {
                        "input_path": str(Path(input_path).resolve()),
                        "output_path": str(Path(output_path).resolve()),
                        "operation": boolean_op,
                        "object_count": len(object_ids),
                        "object_ids": object_ids,
                    },
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }
            else:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "CLI wrapper not available",
                    "error": "Inkscape CLI wrapper required",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

        elif operation == "optimize_svg":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            # Use Inkscape actions to clean up SVG
            actions = "file-vacuum-defs;file-cleanup;export-do"

            if cli_wrapper:
                result = await cli_wrapper.execute_actions(
                    input_path=input_path,
                    actions=actions,
                    output_path=output_path
                )

                input_size = Path(input_path).stat().st_size
                output_size = Path(output_path).stat().st_size
                savings = input_size - output_size
                savings_pct = (savings / input_size * 100) if input_size > 0 else 0

                return {
                    "success": True,
                    "operation": "optimize_svg",
                    "message": ".1f",
                    "data": {
                        "input_path": str(Path(input_path).resolve()),
                        "output_path": str(Path(output_path).resolve()),
                        "input_size_bytes": input_size,
                        "output_size_bytes": output_size,
                        "bytes_saved": savings,
                        "percent_saved": round(savings_pct, 1),
                    },
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }
            else:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "CLI wrapper not available",
                    "error": "Inkscape CLI wrapper required",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

        elif operation == "render_preview":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            if cli_wrapper:
                result = await cli_wrapper.export_file(
                    input_path=input_path,
                    output_path=output_path,
                    export_type="png",
                    dpi=dpi
                )

                output_size = Path(output_path).stat().st_size

                return {
                    "success": True,
                    "operation": "render_preview",
                    "message": f"Rendered SVG preview at {dpi} DPI",
                    "data": {
                        "input_path": str(Path(input_path).resolve()),
                        "output_path": str(Path(output_path).resolve()),
                        "dpi": dpi,
                        "output_size_bytes": output_size,
                    },
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }
            else:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "CLI wrapper not available",
                    "error": "Inkscape CLI wrapper required",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

        else:
            return {
                "success": False,
                "operation": operation,
                "message": f"Invalid operation: {operation}",
                "error": f"Operation must be one of: trace_image, apply_boolean, optimize_svg, render_preview",
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

    except Exception as e:
        return {
            "success": False,
            "operation": operation,
            "message": f"Operation failed: {e}",
            "error": str(e),
            "execution_time_ms": (time.time() - start_time) * 1000,
        }
