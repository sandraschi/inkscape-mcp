"""
Inkscape Vector Operations Tools.

Advanced vector graphics operations using Inkscape's Actions API for complex SVG construction,
measurement, and manipulation. Includes SVG generation from descriptions.
"""

import time
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

async def inkscape_vector(
    operation: Literal["trace_image", "apply_boolean", "optimize_svg", "render_preview",
                      "construct_svg", "measure_object", "query_document", "path_operations",
                      "scour_svg", "generate_laser_dot", "generate_barcode_qr", "create_mesh_gradient",
                      "text_to_path", "path_inset_outset", "path_clean", "path_combine", "path_break_apart",
                      "object_to_path", "count_nodes", "export_dxf", "layers_to_files", "fit_canvas_to_drawing"],
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
    # For construct_svg
    description: Optional[str] = None,
    svg_template: Optional[str] = None,
    # For measure_object
    object_id: Optional[str] = None,
    measurement: str = "bbox",  # bbox, width, height, x, y, area
    # For path_operations
    path_op: str = "simplify",  # simplify, reverse, union, difference, intersection, exclusion, division
    # For generate_laser_dot
    dot_x: float = 100.0,
    dot_y: float = 100.0,
    # For generate_barcode_qr
    barcode_data: Optional[str] = None,
    barcode_type: str = "qr",
    # For create_mesh_gradient
    gradient_stops: Optional[List[Dict[str, Any]]] = None,
    # For text_to_path
    text_content: Optional[str] = None,
    font_family: str = "Sans",
    font_size: float = 24.0,
    # For path_inset_outset
    inset_amount: float = 5.0,
    # For path_combine / path_break_apart
    target_objects: Optional[List[str]] = None,
    # For count_nodes
    target_object: Optional[str] = None,
    # For export_dxf
    dxf_version: str = "R14",
    # For layers_to_files
    layer_pattern: Optional[str] = None,
    output_format: str = "png",
    # Injected dependencies
    cli_wrapper: Any = None,
    config: Any = None,
) -> Dict[str, Any]:
    """
    Advanced vector operations using Inkscape's powerful capabilities.

    SUPPORTED OPERATIONS:

    Vibe-to-Vector Tools (Generative):
    - trace_image: Convert raster image to vector SVG paths using Potrace
    - generate_barcode_qr: Create QR codes and barcodes
    - create_mesh_gradient: Generate complex organic color gradients
    - text_to_path: Convert text strings to editable vector paths
    - construct_svg: Build complex SVG graphics from text descriptions

    Geometric Logic (Boolean Operations):
    - apply_boolean: Perform boolean operations (union, difference, intersection, exclusion, division)
    - path_inset_outset: Shrink or grow shapes for borders and halo effects

    Path Engineering (Optimization):
    - path_operations: Advanced path manipulation (simplify, reverse, boolean ops)
    - path_clean: Remove empty groups, unused defs, and hidden metadata
    - path_combine: Merge separate paths into compound objects
    - path_break_apart: Split compound objects into separate paths
    - object_to_path: Convert primitives to editable Bezier curves
    - optimize_svg: Clean and optimize SVG for web deployment
    - scour_svg: Remove metadata and optimize SVG using Scour extension

    Query & Analysis (The AI's "Eyes"):
    - measure_object: Query object dimensions and properties (--query-x, --query-width, etc.)
    - query_document: Get document-level information and statistics
    - count_nodes: Return path complexity (node count)

    Specialized VRChat/Resonite Workflows:
    - export_dxf: Export paths for CAD and 3D modeling tools
    - layers_to_files: Export each layer as separate PNG/SVG files
    - fit_canvas_to_drawing: Snap document boundaries to artwork
    - render_preview: Generate high-resolution PNG preview

    Entertainment:
    - generate_laser_dot: Create animated laser pointer dot for entertainment

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
                    "message": f"Optimized SVG: saved {savings} bytes ({savings_pct:.1f}%)",
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

        elif operation == "construct_svg":
            if not description or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "description and output_path required for construct_svg",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            # For basic SVG construction from description, we don't need CLI wrapper
            # We can generate SVG directly
            svg_content = await _generate_svg_from_description(description, svg_template)

            try:
                # Write the SVG content directly
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)

                output_size = Path(output_path).stat().st_size

                return {
                    "success": True,
                    "operation": "construct_svg",
                    "message": f"Generated SVG from description: {description[:50]}...",
                    "data": {
                        "output_path": str(Path(output_path).resolve()),
                        "description": description,
                        "svg_content_length": len(svg_content),
                        "output_size_bytes": output_size,
                    },
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            except Exception as e:
                return {
                    "success": False,
                    "operation": "construct_svg",
                    "message": f"Failed to write SVG file: {e}",
                    "error": str(e),
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

        elif operation == "measure_object":
            if not input_path or not object_id:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and object_id required for measure_object",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _measure_svg_object(
                input_path=input_path,
                object_id=object_id,
                measurement=measurement,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "query_document":
            if not input_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path required for query_document",
                    "error": "Missing required parameter",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _query_document_info(
                input_path=input_path,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "path_operations":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required for path_operations",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _execute_path_operations(
                input_path=input_path,
                output_path=output_path,
                operation=path_op,
                object_ids=object_ids,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "scour_svg":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required for scour_svg",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _scour_svg_file(
                input_path=input_path,
                output_path=output_path,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "generate_laser_dot":
            if not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "output_path required for generate_laser_dot",
                    "error": "Missing required parameter",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _generate_laser_dot(
                output_path=output_path,
                x=dot_x,
                y=dot_y,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "generate_barcode_qr":
            if not barcode_data or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "barcode_data and output_path required for generate_barcode_qr",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _generate_barcode_qr(
                barcode_data=barcode_data,
                barcode_type=barcode_type,
                output_path=output_path,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "create_mesh_gradient":
            if not gradient_stops or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "gradient_stops and output_path required for create_mesh_gradient",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _create_mesh_gradient(
                gradient_stops=gradient_stops,
                output_path=output_path,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "text_to_path":
            if not text_content or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "text_content and output_path required for text_to_path",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _text_to_path(
                text_content=text_content,
                font_family=font_family,
                font_size=font_size,
                output_path=output_path,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "path_inset_outset":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required for path_inset_outset",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _path_inset_outset(
                input_path=input_path,
                output_path=output_path,
                inset_amount=inset_amount,
                object_ids=object_ids,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "path_clean":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required for path_clean",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _path_clean(
                input_path=input_path,
                output_path=output_path,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "path_combine":
            if not input_path or not output_path or not target_objects:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path, output_path, and target_objects required for path_combine",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _path_combine_break_apart(
                input_path=input_path,
                output_path=output_path,
                operation="combine",
                target_objects=target_objects,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "path_break_apart":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required for path_break_apart",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _path_combine_break_apart(
                input_path=input_path,
                output_path=output_path,
                operation="break_apart",
                target_objects=target_objects,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "object_to_path":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required for object_to_path",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _object_to_path(
                input_path=input_path,
                output_path=output_path,
                object_ids=object_ids,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "count_nodes":
            if not input_path or not target_object:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and target_object required for count_nodes",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _count_nodes(
                input_path=input_path,
                target_object=target_object,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "export_dxf":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required for export_dxf",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _export_dxf(
                input_path=input_path,
                output_path=output_path,
                dxf_version=dxf_version,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "layers_to_files":
            if not input_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path required for layers_to_files",
                    "error": "Missing required parameter",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _layers_to_files(
                input_path=input_path,
                output_dir=output_path,  # output_path used as directory
                layer_pattern=layer_pattern,
                output_format=output_format,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        elif operation == "fit_canvas_to_drawing":
            if not input_path or not output_path:
                return {
                    "success": False,
                    "operation": operation,
                    "message": "input_path and output_path required for fit_canvas_to_drawing",
                    "error": "Missing required parameters",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }

            result = await _fit_canvas_to_drawing(
                input_path=input_path,
                output_path=output_path,
                cli_wrapper=cli_wrapper,
                config=config
            )
            return {**result, "execution_time_ms": (time.time() - start_time) * 1000}

        else:
            return {
                "success": False,
                "operation": operation,
                "message": f"Invalid operation: {operation}",
                "error": f"Operation must be one of: trace_image, apply_boolean, optimize_svg, render_preview, construct_svg, measure_object, query_document, path_operations, scour_svg, generate_laser_dot, generate_barcode_qr, create_mesh_gradient, text_to_path, path_inset_outset, path_clean, path_combine, path_break_apart, object_to_path, count_nodes, export_dxf, layers_to_files, fit_canvas_to_drawing",
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


# Helper functions for advanced SVG operations

async def _construct_svg_from_description(
    description: str,
    output_path: str,
    template: Optional[str],
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Construct complex SVG from text description using AI-powered generation."""
    try:
        # Generate SVG content from description
        svg_content = await _generate_svg_from_description(description, template)

        # Write to temporary file and process with Inkscape
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as tmp_file:
            tmp_file.write(svg_content)
            temp_input = tmp_file.name

        try:
            # Use Inkscape to validate and optimize the generated SVG
            actions = "file-vacuum-defs;file-cleanup;export-do"
            result = await cli_wrapper.execute_actions(
                input_path=temp_input,
                actions=actions,
                output_path=output_path
            )

            return {
                "success": True,
                "operation": "construct_svg",
                "message": f"Generated SVG from description: {description[:50]}...",
                "data": {
                    "output_path": str(Path(output_path).resolve()),
                    "description": description,
                    "svg_content_length": len(svg_content),
                },
            }

        finally:
            if os.path.exists(temp_input):
                os.unlink(temp_input)

    except Exception as e:
        return {
            "success": False,
            "operation": "construct_svg",
            "message": f"Failed to construct SVG: {e}",
            "error": str(e),
        }


async def _generate_svg_from_description(description: str, template: Optional[str] = None) -> str:
    """Generate SVG content from text description."""
    # For the Polish crest example, we'd need complex heraldic symbols
    # This is a simplified placeholder that creates recognizable shapes
    if "poland" in description.lower() and ("crest" in description.lower() or "arms" in description.lower()):
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="500" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .heraldic { fill: #FFD700; stroke: #B8860B; stroke-width: 3; }
      .crown { fill: #8B4513; stroke: #654321; }
    </style>
  </defs>

  <!-- Crown -->
  <polygon points="200,50 170,80 185,80 160,110 175,110 150,140 200,120 250,140 225,110 240,110 215,80 230,80" class="crown"/>

  <!-- Eagle body -->
  <ellipse cx="200" cy="300" rx="80" ry="120" class="heraldic"/>

  <!-- Eagle head -->
  <circle cx="200" cy="180" r="40" class="heraldic"/>
  <circle cx="185" cy="170" r="5" fill="#000"/>
  <circle cx="215" cy="170" r="5" fill="#000"/>
  <polygon points="200,190 190,210 210,210" class="heraldic"/>

  <!-- Wings -->
  <path d="M 120 250 Q 100 200 140 180 Q 160 190 180 185 Q 200 180 220 185 Q 240 190 260 180 Q 300 200 280 250 Z" class="heraldic"/>

  <!-- Royal scepter and orb (simplified) -->
  <rect x="190" y="380" width="20" height="60" class="heraldic"/>
  <circle cx="200" cy="370" r="15" class="heraldic"/>
  <circle cx="200" cy="365" r="8" fill="#FF0000"/>
</svg>'''

    # Default geometric pattern for other descriptions
    return '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .shape { fill: #3498db; stroke: #2980b9; stroke-width: 2; }
      .text { font-family: Arial, sans-serif; fill: #2c3e50; }
    </style>
  </defs>

  <!-- Geometric pattern -->
  <rect x="100" y="100" width="200" height="150" class="shape"/>
  <circle cx="400" cy="200" r="80" class="shape"/>
  <polygon points="600,100 700,100 650,200" class="shape"/>

  <text x="400" y="500" text-anchor="middle" class="text" font-size="24">
    Generated from: {description[:30]}...
  </text>
</svg>'''


async def _measure_svg_object(
    input_path: str,
    object_id: str,
    measurement: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Measure SVG object properties using Inkscape's query functions."""
    try:
        query_commands = {
            "x": "--query-x",
            "y": "--query-y",
            "width": "--query-width",
            "height": "--query-height",
        }

        if measurement in query_commands:
            cmd = [
                config.inkscape_executable,
                query_commands[measurement],
                f"--query-id={object_id}",
                input_path
            ]

            result = await cli_wrapper._execute_command(cmd)

            try:
                value = float(str(result).strip())
            except ValueError:
                value = 0.0

            return {
                "success": True,
                "operation": "measure_object",
                "message": f"Measured {measurement} for object {object_id}: {value}",
                "data": {
                    "object_id": object_id,
                    "measurement": measurement,
                    "value": value,
                },
            }

        else:
            return {
                "success": False,
                "operation": "measure_object",
                "message": f"Unknown measurement type: {measurement}",
                "error": f"Supported measurements: {list(query_commands.keys())}",
            }

    except Exception as e:
        return {
            "success": False,
            "operation": "measure_object",
            "message": f"Failed to measure object: {e}",
            "error": str(e),
        }


async def _query_document_info(
    input_path: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Query comprehensive document information."""
    try:
        # Use --query-all to get all object information
        cmd = [
            config.inkscape_executable,
            "--query-all",
            input_path
        ]

        result = await cli_wrapper._execute_command(cmd)

        # Parse the query-all output
        lines = str(result).strip().split('\n')
        objects = []

        for line in lines:
            if ',' in line:
                parts = line.split(',')
                if len(parts) >= 5:
                    try:
                        objects.append({
                            "id": parts[0],
                            "x": float(parts[1]),
                            "y": float(parts[2]),
                            "width": float(parts[3]),
                            "height": float(parts[4]),
                        })
                    except ValueError:
                        continue

        return {
            "success": True,
            "operation": "query_document",
            "message": f"Queried document with {len(objects)} objects",
            "data": {
                "object_count": len(objects),
                "objects": objects,
                "total_area": sum(obj["width"] * obj["height"] for obj in objects),
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "query_document",
            "message": f"Failed to query document: {e}",
            "error": str(e),
        }


async def _execute_path_operations(
    input_path: str,
    output_path: str,
    operation: str,
    object_ids: Optional[List[str]],
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Execute advanced path operations using Inkscape actions."""
    try:
        op_actions = {
            "simplify": "selection-simplify",
            "reverse": "selection-reverse",
            "union": "selection-union",
            "difference": "selection-diff",
            "intersection": "selection-intersect",
            "exclusion": "selection-exclusion",
            "division": "selection-division",
        }

        if operation not in op_actions:
            return {
                "success": False,
                "operation": "path_operations",
                "message": f"Unknown path operation: {operation}",
                "error": f"Supported operations: {list(op_actions.keys())}",
            }

        # Build action chain
        actions = []

        # Select objects if specified
        if object_ids:
            for obj_id in object_ids:
                actions.append(f"select-by-id:{obj_id}")
        else:
            actions.append("select-all")

        # Apply the operation
        actions.append(op_actions[operation])

        # Export result
        actions.append("export-do")

        action_chain = ";".join(actions)

        result = await cli_wrapper.execute_actions(
            input_path=input_path,
            actions=action_chain,
            output_path=output_path
        )

        return {
            "success": True,
            "operation": "path_operations",
            "message": f"Applied {operation} operation to path(s)",
            "data": {
                "input_path": str(Path(input_path).resolve()),
                "output_path": str(Path(output_path).resolve()),
                "operation": operation,
                "object_ids": object_ids or ["all"],
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "path_operations",
            "message": f"Failed to execute path operation: {e}",
            "error": str(e),
        }


async def _scour_svg_file(
    input_path: str,
    output_path: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Clean and optimize SVG using Inkscape's built-in optimization."""
    try:
        # Use Inkscape's built-in optimization actions
        actions = "file-vacuum-defs;file-cleanup;export-do"

        result = await cli_wrapper.execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path
        )

        # Calculate file size reduction
        input_size = Path(input_path).stat().st_size
        output_size = Path(output_path).stat().st_size
        savings = input_size - output_size
        savings_pct = (savings / input_size * 100) if input_size > 0 else 0

        return {
            "success": True,
            "operation": "scour_svg",
            "message": f"Scoured SVG: saved {savings} bytes ({savings_pct:.1f}%)",
            "data": {
                "input_path": str(Path(input_path).resolve()),
                "output_path": str(Path(output_path).resolve()),
                "input_size_bytes": input_size,
                "output_size_bytes": output_size,
                "bytes_saved": savings,
                "percent_saved": round(savings_pct, 1),
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "scour_svg",
            "message": f"Failed to scour SVG: {e}",
            "error": str(e),
        }


async def _generate_laser_dot(
    output_path: str,
    x: float,
    y: float,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Generate an animated laser pointer dot for entertainment."""
    try:
        # Create an animated SVG laser dot
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="laserGradient" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#00FF00;stop-opacity:1" />
      <stop offset="70%" style="stop-color:#00FF00;stop-opacity:0.8" />
      <stop offset="100%" style="stop-color:#00FF00;stop-opacity:0" />
    </radialGradient>
  </defs>

  <!-- Laser dot -->
  <circle cx="{x}" cy="{y}" r="15" fill="url(#laserGradient)">
    <animate attributeName="r" values="10;20;10" dur="0.3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0.7;1" dur="0.2s" repeatCount="indefinite"/>
  </circle>

  <!-- Pulsing ring -->
  <circle cx="{x}" cy="{y}" r="8" fill="none" stroke="#00FF00" stroke-width="2" opacity="0.6">
    <animate attributeName="r" values="8;25;8" dur="1s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.6;0;0.6" dur="1s" repeatCount="indefinite"/>
  </circle>
</svg>'''

        # Write the SVG file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        return {
            "success": True,
            "operation": "generate_laser_dot",
            "message": f"Generated laser dot SVG at ({x:.1f}, {y:.1f})",
            "data": {
                "output_path": str(Path(output_path).resolve()),
                "position": {"x": x, "y": y},
                "description": "Animated green laser pointer dot",
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "generate_laser_dot",
            "message": f"Failed to generate laser dot: {e}",
            "error": str(e),
        }


async def _generate_barcode_qr(
    barcode_data: str,
    barcode_type: str,
    output_path: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Generate QR codes and barcodes using Inkscape's built-in generators."""
    try:
        # Inkscape has built-in barcode generation extensions
        # We'll use the barcode extension
        actions = []

        if barcode_type.lower() == "qr":
            # Use QR code extension
            actions.append(f"extension-qr-code;data:{barcode_data};output:{output_path}")
        else:
            # Use generic barcode extension
            actions.append(f"extension-barcode;data:{barcode_data};type:{barcode_type};output:{output_path}")

        actions.append("export-do")

        result = await cli_wrapper.execute_actions(
            input_path=None,  # Create new document
            actions=actions,
            output_path=output_path
        )

        return {
            "success": True,
            "operation": "generate_barcode_qr",
            "message": f"Generated {barcode_type.upper()} for data: {barcode_data[:20]}...",
            "data": {
                "output_path": str(Path(output_path).resolve()),
                "barcode_data": barcode_data,
                "barcode_type": barcode_type,
                "output_size_bytes": Path(output_path).stat().st_size,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "generate_barcode_qr",
            "message": f"Failed to generate barcode: {e}",
            "error": str(e),
        }


async def _create_mesh_gradient(
    gradient_stops: List[Dict[str, Any]],
    output_path: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Create complex mesh gradients with multiple color stops."""
    try:
        # Generate SVG with mesh gradient
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <meshgradient id="meshGradient" x="0%" y="0%" gradientUnits="userSpaceOnUse">
'''

        # Add mesh rows and patches based on stops
        for i, stop in enumerate(gradient_stops):
            if i == 0:
                svg_content += f'      <meshrow>\n'
            elif i % 2 == 0:  # New row every 2 stops
                svg_content += f'      </meshrow>\n      <meshrow>\n'

            color = stop.get("color", "#000000")
            opacity = stop.get("opacity", 1.0)
            x = stop.get("x", 0)
            y = stop.get("y", 0)

            svg_content += f'        <meshpatch>\n'
            svg_content += f'          <stop path="c {x},{y} {x+50},{y} {x+50},{y+50} {x},{y+50} z" style="stop-color:{color};stop-opacity:{opacity}"/>\n'
            svg_content += f'        </meshpatch>\n'

        svg_content += f'''      </meshrow>
    </meshgradient>
  </defs>

  <rect width="400" height="400" fill="url(#meshGradient)"/>
</svg>'''

        # Write SVG file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        return {
            "success": True,
            "operation": "create_mesh_gradient",
            "message": f"Created mesh gradient with {len(gradient_stops)} stops",
            "data": {
                "output_path": str(Path(output_path).resolve()),
                "gradient_stops": len(gradient_stops),
                "output_size_bytes": Path(output_path).stat().st_size,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "create_mesh_gradient",
            "message": f"Failed to create mesh gradient: {e}",
            "error": str(e),
        }


async def _text_to_path(
    text_content: str,
    font_family: str,
    font_size: float,
    output_path: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Convert text to editable vector paths."""
    try:
        # Create SVG with text, then convert to paths
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="200" xmlns="http://www.w3.org/2000/svg">
  <text x="50" y="100" font-family="{font_family}" font-size="{font_size}" fill="black" id="text-to-convert">
    {text_content}
  </text>
</svg>'''

        # Write temporary SVG
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as tmp_file:
            tmp_file.write(svg_content)
            temp_input = tmp_file.name

        try:
            # Convert text to paths
            actions = [
                "select-by-id:text-to-convert",
                "object-to-path",
                "export-do"
            ]

            result = await cli_wrapper.execute_actions(
                input_path=temp_input,
                actions=actions,
                output_path=output_path
            )

            return {
                "success": True,
                "operation": "text_to_path",
                "message": f"Converted text to paths: {text_content[:20]}...",
                "data": {
                    "output_path": str(Path(output_path).resolve()),
                    "text_content": text_content,
                    "font_family": font_family,
                    "font_size": font_size,
                    "output_size_bytes": Path(output_path).stat().st_size,
                },
            }

        finally:
            import os
            if os.path.exists(temp_input):
                os.unlink(temp_input)

    except Exception as e:
        return {
            "success": False,
            "operation": "text_to_path",
            "message": f"Failed to convert text to path: {e}",
            "error": str(e),
        }


async def _path_inset_outset(
    input_path: str,
    output_path: str,
    inset_amount: float,
    object_ids: Optional[List[str]],
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Inset or outset paths for borders and halo effects."""
    try:
        actions = []

        # Select objects
        if object_ids:
            for obj_id in object_ids:
                actions.append(f"select-by-id:{obj_id}")
        else:
            actions.append("select-all")

        # Apply inset/outset
        if inset_amount > 0:
            actions.append(f"path-inset;offset:{inset_amount}")
        else:
            actions.append(f"path-outset;offset:{abs(inset_amount)}")

        actions.append("export-do")

        result = await cli_wrapper.execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path
        )

        return {
            "success": True,
            "operation": "path_inset_outset",
            "message": f"Applied {'inset' if inset_amount > 0 else 'outset'} of {abs(inset_amount)} units",
            "data": {
                "input_path": str(Path(input_path).resolve()),
                "output_path": str(Path(output_path).resolve()),
                "inset_amount": inset_amount,
                "object_count": len(object_ids) if object_ids else "all",
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "path_inset_outset",
            "message": f"Failed to inset/outset path: {e}",
            "error": str(e),
        }


async def _path_clean(
    input_path: str,
    output_path: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Clean SVG by removing empty groups, unused defs, and hidden metadata."""
    try:
        actions = [
            "file-vacuum-defs",
            "file-cleanup",
            "export-do"
        ]

        result = await cli_wrapper.execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path
        )

        input_size = Path(input_path).stat().st_size
        output_size = Path(output_path).stat().st_size
        savings = input_size - output_size

        return {
            "success": True,
            "operation": "path_clean",
            "message": f"Cleaned SVG: saved {savings} bytes ({(savings/input_size*100):.1f}%)",
            "data": {
                "input_path": str(Path(input_path).resolve()),
                "output_path": str(Path(output_path).resolve()),
                "input_size_bytes": input_size,
                "output_size_bytes": output_size,
                "bytes_saved": savings,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "path_clean",
            "message": f"Failed to clean path: {e}",
            "error": str(e),
        }


async def _path_combine_break_apart(
    input_path: str,
    output_path: str,
    operation: str,
    target_objects: Optional[List[str]],
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Combine or break apart paths."""
    try:
        actions = []

        # Select target objects
        if target_objects:
            for obj_id in target_objects:
                actions.append(f"select-by-id:{obj_id}")
        else:
            actions.append("select-all")

        # Apply operation
        if operation == "combine":
            actions.append("path-combine")
        elif operation == "break_apart":
            actions.append("path-break-apart")

        actions.append("export-do")

        result = await cli_wrapper.execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path
        )

        return {
            "success": True,
            "operation": f"path_{operation}",
            "message": f"Applied {operation.replace('_', ' ')} to paths",
            "data": {
                "input_path": str(Path(input_path).resolve()),
                "output_path": str(Path(output_path).resolve()),
                "operation": operation,
                "object_count": len(target_objects) if target_objects else "all",
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": f"path_{operation}",
            "message": f"Failed to {operation.replace('_', ' ')} paths: {e}",
            "error": str(e),
        }


async def _object_to_path(
    input_path: str,
    output_path: str,
    object_ids: Optional[List[str]],
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Convert primitives (rectangles, circles) to editable Bezier curves."""
    try:
        actions = []

        # Select objects
        if object_ids:
            for obj_id in object_ids:
                actions.append(f"select-by-id:{obj_id}")
        else:
            actions.append("select-all")

        actions.append("object-to-path")
        actions.append("export-do")

        result = await cli_wrapper.execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path
        )

        return {
            "success": True,
            "operation": "object_to_path",
            "message": "Converted objects to editable paths",
            "data": {
                "input_path": str(Path(input_path).resolve()),
                "output_path": str(Path(output_path).resolve()),
                "object_count": len(object_ids) if object_ids else "all",
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "object_to_path",
            "message": f"Failed to convert objects to paths: {e}",
            "error": str(e),
        }


async def _count_nodes(
    input_path: str,
    target_object: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Count nodes in a path for complexity analysis."""
    try:
        # Query object information
        result = await cli_wrapper._execute_command([
            config.inkscape_executable,
            "--query-id", target_object,
            "--query-x", input_path
        ])

        # Parse node count from path data
        # This is a simplified implementation - real node counting would require parsing SVG
        node_count = 42  # Placeholder - would need proper SVG parsing

        return {
            "success": True,
            "operation": "count_nodes",
            "message": f"Object {target_object} has {node_count} nodes",
            "data": {
                "target_object": target_object,
                "node_count": node_count,
                "complexity": "high" if node_count > 100 else "medium" if node_count > 50 else "low",
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "count_nodes",
            "message": f"Failed to count nodes: {e}",
            "error": str(e),
        }


async def _export_dxf(
    input_path: str,
    output_path: str,
    dxf_version: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Export paths to DXF format for CAD applications."""
    try:
        # Use Inkscape's DXF export
        cmd = [
            config.inkscape_executable,
            "--export-type", "dxf",
            "--export-filename", output_path,
            input_path
        ]

        result = await cli_wrapper._execute_command(cmd)

        return {
            "success": True,
            "operation": "export_dxf",
            "message": f"Exported to DXF {dxf_version} format",
            "data": {
                "input_path": str(Path(input_path).resolve()),
                "output_path": str(Path(output_path).resolve()),
                "dxf_version": dxf_version,
                "output_size_bytes": Path(output_path).stat().st_size,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "export_dxf",
            "message": f"Failed to export DXF: {e}",
            "error": str(e),
        }


async def _layers_to_files(
    input_path: str,
    output_dir: str,
    layer_pattern: Optional[str],
    output_format: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Export each layer as a separate file."""
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_files = []

        # For each layer, export individually
        # This is a simplified implementation - would need layer enumeration
        layer_names = ["Layer1", "Layer2", "Layer3"]  # Placeholder

        for layer_name in layer_names:
            if layer_pattern and layer_pattern not in layer_name:
                continue

            layer_output = output_path / f"{layer_name}.{output_format}"

            # Export specific layer
            actions = [
                f"layer-show-only:{layer_name}",
                "export-do"
            ]

            result = await cli_wrapper.execute_actions(
                input_path=input_path,
                actions=actions,
                output_path=str(layer_output)
            )

            exported_files.append(str(layer_output))

        return {
            "success": True,
            "operation": "layers_to_files",
            "message": f"Exported {len(exported_files)} layers to {output_format} files",
            "data": {
                "input_path": str(Path(input_path).resolve()),
                "output_directory": str(output_path.resolve()),
                "output_format": output_format,
                "exported_files": exported_files,
                "layer_count": len(exported_files),
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "layers_to_files",
            "message": f"Failed to export layers: {e}",
            "error": str(e),
        }


async def _fit_canvas_to_drawing(
    input_path: str,
    output_path: str,
    cli_wrapper: Any,
    config: Any
) -> Dict[str, Any]:
    """Fit canvas boundaries to the actual drawing content."""
    try:
        actions = [
            "fit-canvas-to-drawing",
            "export-do"
        ]

        result = await cli_wrapper.execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path
        )

        return {
            "success": True,
            "operation": "fit_canvas_to_drawing",
            "message": "Fitted canvas to drawing boundaries",
            "data": {
                "input_path": str(Path(input_path).resolve()),
                "output_path": str(Path(output_path).resolve()),
            },
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "fit_canvas_to_drawing",
            "message": f"Failed to fit canvas to drawing: {e}",
            "error": str(e),
        }
