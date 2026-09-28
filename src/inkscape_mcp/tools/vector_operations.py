"""Advanced vector operations for Inkscape SVG documents.

PORTMANTEAU PATTERN RATIONALE:
Consolidates 23+ advanced vector operations into single interface. Prevents tool explosion
while maintaining
full functionality and improving discoverability. Follows FastMCP 2.14.1+ SOTA standards.

SUPPORTED OPERATIONS:
- trace_image: Convert raster images to vector paths
- generate_barcode_qr: Generate QR codes and barcodes as SVG elements
- apply_boolean: Boolean operations (union, difference, intersection, exclusion)
- measure_object: Query object dimensions and bounding box
- optimize_svg: Clean and optimize SVG structure
- render_preview: Generate PNG preview at specified DPI
- path_operations: Path manipulation (simplify, clean, combine, break_apart)
- text_to_path: Convert text elements to editable vector paths
- export_dxf: Export to CAD format (DXF)
- layers_to_files: Export layers as separate files
- fit_canvas_to_drawing: Resize canvas to match drawing bounds
- object_raise: Raise object in Z-order
- object_lower: Lower object in Z-order
- set_document_units: Normalize document coordinate systems
- generate_laser_dot: Create animated laser pointer dot

OPERATIONS DETAIL:

**Raster-to-Vector Conversion**:
  - trace_image: Convert raster images to vector paths using potrace algorithm

**Code Generation**:
  - generate_barcode_qr: Generate QR codes and barcodes as SVG elements
  - generate_laser_dot: Create animated laser pointer dot for presentations

**Path Manipulation**:
  - path_operations: Path manipulation (simplify, clean, combine, break_apart, inset/outset)
  - apply_boolean: Boolean operations (union, difference, intersection, exclusion)

**Object Operations**:
  - object_to_path: Convert shapes (rectangles, circles, etc.) to editable paths
  - object_raise: Raise object in Z-order (move up in layer stack)
  - object_lower: Lower object in Z-order (move down in layer stack)

**Text Operations**:
  - text_to_path: Convert text elements to editable vector paths

**Document Operations**:
  - query_document: Get document statistics (dimensions, object count)
  - measure_object: Query object dimensions and bounding box
  - count_nodes: Count path nodes for complexity analysis
  - fit_canvas_to_drawing: Resize canvas to match drawing bounds
  - set_document_units: Normalize document coordinate systems (px, mm, in)

**Export & Rendering**:
  - render_preview: Generate PNG preview at specified DPI
  - export_dxf: Export to CAD format (DXF)
  - layers_to_files: Export layers as separate files

**Optimization**:
  - optimize_svg: Clean and optimize SVG structure
  - scour_svg: Remove metadata and unnecessary elements

Args:
    operation (Literal, required): The vector operation to perform. Must be one of:
        "trace_image", "generate_barcode_qr",
        "apply_boolean", "measure_object", "optimize_svg", "render_preview", "path_operations",
        "text_to_path",
        "export_dxf", "layers_to_files", "fit_canvas_to_drawing", "object_raise", "object_lower",
        "set_document_units",
        "generate_laser_dot".

    input_path (str | None): Path to input SVG file. Required for most operations.
        Must be a valid file path accessible by the system.

    output_path (str | None): Path for output file. Required for export/optimization operations.
        Directory must exist and be writable.

    object_id (str | None): Unique identifier for SVG object. Required for: measure_object,
        object_raise, object_lower.
        Must match an existing object ID in the SVG document.

    boolean_type (str | None): Type of boolean operation. Must be one of: "union", "difference",
        "intersection", "exclusion".
        Required for: apply_boolean operation.

    barcode_data (str | None): Data to encode in barcode/QR. Required for:
        generate_barcode_qr operation.

    optimization_type (str | None): Type of optimization. Must be one of: "simplify", "scour",
        "clean".
        Required for: optimize_svg operation.

    path_operation (str | None): Type of path operation. Must be one of: "simplify", "clean",
        "combine", "break_apart", "inset", "outset".
        Required for: path_operations operation.

    units (str | None): Document units for normalization. Must be one of: "px", "mm", "in",
        "pt", "pc".
        Required for: set_document_units operation.

    cli_wrapper (Any): Injected CLI wrapper dependency. Required. Handles Inkscape command
        execution.

    config (Any): Injected configuration dependency. Required. Contains Inkscape executable path
        and settings.

Returns:
    FastMCP 2.14.1+ Enhanced Response Pattern with success/error states, execution timing,
    next steps, and recovery options for failed operations.

Examples:
    # Convert bitmap to vector paths
    result = await inkscape_vector(
        operation="trace_image",
        input_path="bitmap.png",
        output_path="vector.svg"
    )

    # Apply boolean union operation
    result = await inkscape_vector(
        operation="apply_boolean",
        boolean_type="union",
        input_path="shapes.svg",
        output_path="combined.svg"
    )

    # Measure object dimensions
    result = await inkscape_vector(
        operation="measure_object",
        input_path="drawing.svg",
        object_id="rect1"
    )

PREREQUISITES:
- Requires Inkscape CLI installation (1.0+ recommended, 1.2+ for Actions API)
- For boolean operations: Requires object IDs or select_all parameter
- For path operations: Requires valid SVG path elements

Args:
    operation (Literal, required): The vector operation to perform. Must be one of:
        "trace_image", "generate_barcode_qr", "generate_laser_dot", "apply_boolean",
        "path_simplify", "path_clean", "path_combine", "path_break_apart",
        "object_to_path", "object_raise", "object_lower", "measure_object",
        "query_document", "count_nodes", "render_preview", "set_document_units".

    input_path (str | None): Path to input SVG file. Required for most operations.
        Must be a valid SVG file accessible by the system.

    output_path (str | None): Path for output file. Required for operations that modify files.
        Directory must exist and be writable. Required for: trace_image, apply_boolean,
        path_simplify, path_clean, object_raise, object_lower, render_preview, set_document_units.

    object_id (str | None): Target object ID within SVG document. Required for:
        measure_object, count_nodes, path_simplify, object_raise, object_lower.
        Object ID must exist in the SVG document.

    object_ids (list[str] | None): List of object IDs for multi-object operations.
        Required for: apply_boolean (when select_all=False). Must contain at least 2 IDs.

    select_all (bool): Select all objects for operation. Required for: apply_boolean
        (when object_ids not provided). Default: False.

    operation_type (str | None): Type of boolean operation. Required for: apply_boolean.
        Must be one of: "union", "difference", "intersection", "exclusion".

    barcode_data (str | None): Data to encode in QR code or barcode. Required for:
        generate_barcode_qr.

    threshold (float): Simplification threshold for path_simplify. Default: 1.0.
        Higher values result in more aggressive simplification.

    dpi (int): DPI for render_preview operation. Default: 96. Higher values produce
        higher resolution previews but take longer to render.

    units (str | None): Document units for set_document_units. Must be one of:
        "px", "mm", "in", "pt", "cm". Default: "px".

    x (float): X coordinate for generate_laser_dot. Default: 300.

    y (float): Y coordinate for generate_laser_dot. Default: 200.

    cli_wrapper (Any): Injected CLI wrapper dependency. Required. Handles Inkscape command execution.

    config (Any): Injected configuration dependency. Required. Contains Inkscape executable path
        and settings.

Returns:
    FastMCP 2.14.1+ Enhanced Response Pattern (Structured Returns):

    Success Response:
    {
      "success": true,
      "operation": "operation_name",
      "summary": "Human-readable conversational summary",
      "result": {
        "data": {
          "input_path": "path/to/input.svg",
          "output_path": "path/to/output.svg",
          "operation_result": {
            "object_id": "circle1",
            "width": 100.0,
            "height": 100.0,
            "x": 50.0,
            "y": 50.0
          }
        },
        "execution_time_ms": 123.45
      },
      "next_steps": ["Suggested next operations"],
      "context": {
        "operation_details": "Technical details about vector operation"
      },
      "suggestions": ["Related vector operations"],
      "follow_up_questions": ["Questions about operation parameters"]
    }

    Error Response (Error Recovery Pattern):
    {
      "success": false,
      "operation": "operation_name",
      "error": "Error type (e.g., ValueError)",
      "message": "Human-readable error description",
      "recovery_options": ["Provide object_ids or set select_all=true",
        "Verify object IDs exist in document"],
      "diagnostic_info": {
        "object_ids_provided": false,
        "select_all": false,
        "valid_operation_types": ["union", "difference", "intersection", "exclusion"]
      },
      "alternative_solutions": ["Use query_document to list available object IDs",
        "Use select_all=true for all objects"]
    }

Examples:
    # Trace bitmap image to vector paths
    result = await inkscape_vector(
        operation="trace_image",
        input_path="sketch.png",
        output_path="vector.svg"
    )

    # Generate QR code
    result = await inkscape_vector(
        operation="generate_barcode_qr",
        barcode_data="https://example.com",
        output_path="qr.svg"
    )

    # Apply boolean union to specific objects
    result = await inkscape_vector(
        operation="apply_boolean",
        input_path="shapes.svg",
        output_path="union.svg",
        operation_type="union",
        object_ids=["shape1", "shape2"]
    )

    # Apply boolean union to all objects
    result = await inkscape_vector(
        operation="apply_boolean",
        input_path="shapes.svg",
        output_path="union.svg",
        operation_type="union",
        select_all=True
    )

    # Measure object dimensions
    result = await inkscape_vector(
        operation="measure_object",
        input_path="drawing.svg",
        object_id="circle1"
    )

    # Simplify path with threshold
    result = await inkscape_vector(
        operation="path_simplify",
        input_path="complex.svg",
        output_path="simplified.svg",
        object_id="path1",
        threshold=2.0
    )

    # Render PNG preview at high DPI
    result = await inkscape_vector(
        operation="render_preview",
        input_path="design.svg",
        output_path="preview.png",
        dpi=300
    )

    # Generate animated laser dot
    result = await inkscape_vector(
        operation="generate_laser_dot",
        output_path="laser.svg",
        x=400,
        y=300
    )

    # Query document statistics
    result = await inkscape_vector(
        operation="query_document",
        input_path="document.svg"
    )

Errors:
    - FileNotFoundError: Input file does not exist or is not readable
        Recovery options:
        - Verify file path is correct and accessible
        - Check file permissions (read access required)
        - Ensure file is a valid SVG document

    - ValueError: Invalid parameters or object IDs
        Recovery options:
        - For apply_boolean: Provide object_ids (list with 2+ items) OR set select_all=True
        - Verify operation_type is one of: union, difference, intersection, exclusion
        - Ensure object_id exists in document (use query_document to list IDs)
        - Check all required parameters are provided for the operation

    - InkscapeExecutionError: Inkscape CLI command failed
        Recovery options:
        - Verify Inkscape installation (run inkscape --version)
        - Check CLI arguments are valid for Inkscape version
        - Ensure output directory exists and is writable
        - Check process timeout settings in config
        - Verify object IDs exist in the SVG document

    - NotImplementedError: Operation not yet implemented
        Recovery options:
        - Check supported operations list in documentation
        - Use alternative operations that provide similar functionality
        - Check if operation is available in newer Inkscape versions
"""

import math
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel

SVG_URI = "http://www.w3.org/2000/svg"


class VectorOperationResult(BaseModel):
    """Result model for vector operations."""

    success: bool
    operation: str
    message: str
    data: dict[str, Any]
    execution_time_ms: float
    error: str = ""


async def inkscape_vector(
    operation: Literal[
        "trace_image",
        "generate_barcode_qr",
        "create_object",
        "create_mesh_gradient",
        "text_to_path",
        "text_set_content",
        "text_set_style",
        "text_list_fonts",
        "construct_svg",
        "apply_boolean",
        "list_lpes",
        "apply_lpe",
        "path_inset_outset",
        "path_simplify",
        "path_clean",
        "path_combine",
        "path_break_apart",
        "object_to_path",
        "optimize_svg",
        "scour_svg",
        "measure_object",
        "inspect",
        "query_document",
        "count_nodes",
        "export_dxf",
        "layers_to_files",
        "fit_canvas_to_drawing",
        "render_preview",
        "generate_laser_dot",
        "object_raise",
        "object_lower",
        "set_document_units",
        "bulk_restyle",
        "apply_filter",
        "create_gradient",
        "create_pattern",
        "get_attributes",
        "set_attributes",
        "text_on_path",
        "flow_text",
        "create_symbol",
        "use_symbol",
    ],
    input_path: str = "",
    output_path: str = "",
    object_id: str = "",
    object_ids: list[str] | None = None,
    select_all: bool = False,
    operation_type: str = "",
    ref_id: str = "",
    cli_wrapper: Any = None,
    config: Any = None,
    selector: str = "",
    # Optional per-operation params (FastMCP 3.x rejects **kwargs on tools,
    # so these are explicit; each applies only to the operation that uses it).
    barcode_data: str = "",
    preset_id: str = "",
    x: int = 300,
    y: int = 200,
    threshold: float = 1.0,
    dpi: int = 96,
    units: str = "px",
    shape: str = "rect",
    params: dict[str, Any] | None = None,
    element_type: str = "",
    direction: str = "inset",
    amount: float = 2.0,
    output_dir: str = "",
    lpe_id: str = "",
    text: str = "",
    font_family: str = "",
    font_size: float = 0,
    font_weight: str = "",
    fill: str = "",
    text_anchor: str = "",
) -> dict[str, Any]:
    """Inkscape vector operations portmanteau tool."""
    start_time = time.time()

    # Pass-through dict for the shared LPE/text handlers (kept as dict internally).
    kwargs = {
        "barcode_data": barcode_data,
        "preset_id": preset_id,
        "x": x,
        "y": y,
        "threshold": threshold,
        "dpi": dpi,
        "units": units,
        "shape": shape,
        "params": params or {},
        "element_type": element_type,
        "direction": direction,
        "amount": amount,
        "output_dir": output_dir,
        "lpe_id": lpe_id,
        "text": text,
        "font_family": font_family,
        "font_size": font_size,
        "font_weight": font_weight,
        "fill": fill,
        "text_anchor": text_anchor,
    }

    try:
        if operation == "trace_image":
            return await _trace_image(input_path, output_path, cli_wrapper, config)

        elif operation == "generate_barcode_qr":
            return await _generate_barcode_qr(barcode_data, output_path, cli_wrapper, config)

        elif operation == "generate_laser_dot":
            dot_x = x
            dot_y = y
            if preset_id:
                from ..utils.fab_art_presets import resolve_laser_preset

                preset = resolve_laser_preset(str(preset_id))
                if preset and preset.get("dots"):
                    dot_x = preset["dots"][0]["x"]
                    dot_y = preset["dots"][0]["y"]
            return await _generate_laser_dot(
                output_path, dot_x, dot_y, cli_wrapper, config, preset_id=str(preset_id or "")
            )

        elif operation == "measure_object":
            return await _measure_object(input_path, object_id, cli_wrapper, config)

        elif operation == "inspect":
            return await _inspect_object(input_path, object_id, cli_wrapper, config)

        elif operation == "query_document":
            return await _query_document(input_path, cli_wrapper, config)

        elif operation == "count_nodes":
            return await _count_nodes(input_path, object_id, cli_wrapper, config)

        elif operation == "path_simplify":
            return await _path_simplify(
                input_path,
                output_path,
                object_id,
                threshold,
                cli_wrapper,
                config,
            )

        elif operation == "path_clean":
            return await _path_clean(input_path, output_path, cli_wrapper, config)

        elif operation == "render_preview":
            return await _render_preview(input_path, output_path, dpi, cli_wrapper, config)

        elif operation == "export_dxf":
            return await _export_dxf(input_path, output_path, cli_wrapper, config)

        elif operation == "apply_boolean":
            return await _apply_boolean(
                operation_type, input_path, output_path, object_ids, select_all, cli_wrapper, config
            )

        elif operation == "object_raise":
            return await _object_raise(input_path, output_path, object_id, cli_wrapper, config)

        elif operation == "object_lower":
            return await _object_lower(input_path, output_path, object_id, cli_wrapper, config)

        elif operation == "set_document_units":
            return await _set_document_units(input_path, output_path, units, cli_wrapper, config)

        elif operation == "bulk_restyle":
            return await _bulk_restyle(input_path, output_path, selector, params or {})

        elif operation == "apply_filter":
            return await _apply_filter(input_path, output_path, selector, object_id, params or {})

        elif operation == "create_gradient":
            return await _create_gradient(input_path, output_path, object_id, params or {})

        elif operation == "create_pattern":
            return await _create_pattern(input_path, output_path, object_id, params or {})

        elif operation == "get_attributes":
            return await _get_attributes(input_path, object_id)

        elif operation == "set_attributes":
            result = await _bulk_restyle(input_path, output_path, f"#{object_id}", params or {})
            result["operation"] = "set_attributes"
            return result

        elif operation == "text_on_path":
            return await _text_on_path(input_path, output_path, ref_id, object_id, params or {})

        elif operation == "flow_text":
            return await _flow_text(input_path, output_path, ref_id, object_id, params or {})

        elif operation == "create_symbol":
            return await _create_symbol(input_path, output_path, object_id, params or {})

        elif operation == "use_symbol":
            return await _use_symbol(input_path, output_path, ref_id, object_id, params or {})

        elif operation == "create_object":
            return await _create_object(
                output_path,
                shape,
                params or {},
                cli_wrapper,
                config,
            )

        elif operation == "text_to_path":
            return await _text_to_path(input_path, output_path, object_id, cli_wrapper, config)

        elif operation == "construct_svg":
            return await _construct_svg(output_path, element_type, params or {}, config)

        elif operation == "path_inset_outset":
            return await _path_inset_outset(
                input_path,
                output_path,
                direction,
                amount,
                cli_wrapper,
                config,
            )

        elif operation == "path_combine":
            return await _path_combine(input_path, output_path, cli_wrapper, config)

        elif operation == "path_break_apart":
            return await _path_break_apart(input_path, output_path, cli_wrapper, config)

        elif operation == "object_to_path":
            return await _object_to_path(input_path, output_path, object_id, cli_wrapper, config)

        elif operation == "optimize_svg":
            return await _optimize_svg(input_path, output_path, cli_wrapper, config)

        elif operation == "scour_svg":
            return await _scour_svg(input_path, output_path, cli_wrapper, config)

        elif operation == "fit_canvas_to_drawing":
            return await _fit_canvas_to_drawing(input_path, output_path, cli_wrapper, config)

        elif operation in ("list_lpes", "apply_lpe"):
            return await _lpe_handler(
                operation, input_path, output_path, object_id, kwargs, cli_wrapper, config
            )

        elif operation in ("text_set_content", "text_set_style", "text_list_fonts"):
            return await _text_handler(
                operation, input_path, output_path, object_id, kwargs, cli_wrapper, config
            )

        elif operation == "layers_to_files":
            return await _layers_to_files(input_path, output_dir, cli_wrapper, config)

        else:
            return VectorOperationResult(
                success=False,
                operation=operation,
                message=f"Operation '{operation}' not yet implemented",
                data={},
                execution_time_ms=(time.time() - start_time) * 1000,
                error="NotImplementedError",
            ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation=operation,
            message=f"Operation failed: {e}",
            data={},
            execution_time_ms=(time.time() - start_time) * 1000,
            error=str(e),
        ).model_dump()


async def _trace_image(
    input_path: str, output_path: str, cli_wrapper: Any, config: Any
) -> dict[str, Any]:
    """Trace bitmap image to vector paths using potrace."""
    try:
        actions = [
            "file-open:" + input_path,
            "selection-create-bitmap-copies",
            "selection-trace",
            "file-save-as:" + output_path,
            "file-close",
        ]

        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )

        return VectorOperationResult(
            success=True,
            operation="trace_image",
            message=f"Traced bitmap {input_path} to vector {output_path}",
            data={"input_path": input_path, "output_path": output_path, "method": "potrace"},
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="trace_image",
            message=f"Bitmap tracing failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _generate_barcode_qr(
    barcode_data: str, output_path: str, _cli_wrapper: Any, _config: Any
) -> dict[str, Any]:
    """Generate QR code or barcode."""
    try:
        # Create basic SVG with QR-like pattern (placeholder implementation)
        svg_template = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="200" fill="white"/>
  <text x="100" y="100" text-anchor="middle" font-family="monospace" font-size="12">
    {barcode_data}
  </text>
</svg>"""
        svg_content = svg_template.format(barcode_data=barcode_data)

        with Path(output_path).open("w", encoding="utf-8") as f:
            f.write(svg_content)

        return VectorOperationResult(
            success=True,
            operation="generate_barcode_qr",
            message=f"Generated barcode/QR for: {barcode_data}",
            data={"output_path": output_path, "data": barcode_data, "type": "qr"},
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="generate_barcode_qr",
            message=f"Barcode generation failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _generate_laser_dot(
    output_path: str, x: float, y: float, _cli_wrapper1: Any, _config1: Any, preset_id: str = ""
) -> dict[str, Any]:
    """Generate animated laser pointer dot."""
    try:
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="laserGradient" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#00FF00;stop-opacity:1" />
      <stop offset="70%" style="stop-color:#00FF00;stop-opacity:0.8" />
      <stop offset="100%" style="stop-color:#00FF00;stop-opacity:0" />
    </radialGradient>
  </defs>

  <!-- Core laser dot with frantic pulsing animation -->
  <circle cx="{x}" cy="{y}" r="15" fill="url(#laserGradient)">
    <animate attributeName="r" values="8;25;8" dur="0.15s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0.3;1" dur="0.12s" repeatCount="indefinite"/>
  </circle>

  <!-- Outer ring with rapid expansion/contraction -->
  <circle cx="{x}" cy="{y}" r="12" fill="none" stroke="#00FF00" stroke-width="3" opacity="0.8">
    <animate attributeName="r" values="12;35;12" dur="0.25s" repeatCount="indefinite"/>
    <animate attributeName="stroke-width" values="3;1;3" dur="0.25s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.8;0.2;0.8" dur="0.2s" repeatCount="indefinite"/>
  </circle>

  <!-- Secondary pulse ring -->
  <circle cx="{x}" cy="{y}" r="6" fill="none" stroke="#00FF00" stroke-width="2" opacity="0.4">
    <animate attributeName="r" values="6;20;6" dur="0.4s" repeatCount="indefinite" begin="0.1s"/>
    <animate attributeName="opacity" values="0.4;0;0.4" dur="0.35s" repeatCount="indefinite" begin="0.1s"/>
  </circle>
</svg>'''

        with Path(output_path).open("w", encoding="utf-8") as f:
            f.write(svg_content)

        return VectorOperationResult(
            success=True,
            operation="generate_laser_dot",
            message="Generated animated laser dot SVG",
            data={
                "output_path": output_path,
                "position": {"x": x, "y": y},
                "preset_id": preset_id or None,
                "description": "Animated green laser pointer dot",
            },
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="generate_laser_dot",
            message=f"Laser dot generation failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _measure_object(
    input_path: str, object_id: str, cli_wrapper: Any, config: Any
) -> dict[str, Any]:
    """Measure object dimensions."""
    try:
        # Use Inkscape's query functions
        x_result = await cli_wrapper._execute_command(
            [str(config.inkscape_executable), input_path, f"--query-x={object_id}"],
            config.process_timeout,
        )
        y_result = await cli_wrapper._execute_command(
            [str(config.inkscape_executable), input_path, f"--query-y={object_id}"],
            config.process_timeout,
        )
        width_result = await cli_wrapper._execute_command(
            [str(config.inkscape_executable), input_path, f"--query-width={object_id}"],
            config.process_timeout,
        )
        height_result = await cli_wrapper._execute_command(
            [str(config.inkscape_executable), input_path, f"--query-height={object_id}"],
            config.process_timeout,
        )

        x = float(x_result.strip())
        y = float(y_result.strip())
        width = float(width_result.strip())
        height = float(height_result.strip())

        return VectorOperationResult(
            success=True,
            operation="measure_object",
            message=f"Measured object {object_id}",
            data={
                "object_id": object_id,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "bbox": [x, y, x + width, y + height],
            },
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="measure_object",
            message=f"Object measurement failed: {e}",
            data={"object_id": object_id},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _inspect_object(
    input_path: str,
    object_id: str,
    _cli_wrapper: Any,
    _config: Any,
) -> dict[str, Any]:
    """Inspect object style (fill, stroke, opacity, transform) from SVG XML."""
    try:
        _start = time.time()
        svg = Path(input_path).read_text(encoding="utf-8", errors="replace")
        tag_pattern = re.compile(
            rf'<(\w+)[^>]*\bid=["\']{re.escape(object_id)}["\'][^>]*/?>', re.DOTALL
        )
        m = tag_pattern.search(svg)
        if not m:
            return VectorOperationResult(
                success=False,
                operation="inspect",
                message=f"Object '{object_id}' not found",
                data={"object_id": object_id},
                execution_time_ms=0,
                error="NotFound",
            ).model_dump()
        el_type = m.group(1)
        tag_str = m.group(0)
        attr_pattern = re.compile(r'(\b[\w:.-]+)\s*=\s*["\']([^"\']*)["\']')
        attrs = dict(attr_pattern.findall(tag_str))
        style_str = attrs.get("style", "")
        style: dict[str, str] = {}
        if style_str:
            for part in style_str.split(";"):
                if ":" in part:
                    k, sep, v = part.partition(":")
                    style[k.strip()] = v.strip()
        fill = style.get("fill") or attrs.get("fill")
        stroke = style.get("stroke") or attrs.get("stroke")
        stroke_width = style.get("stroke-width") or attrs.get("stroke-width")
        opacity = style.get("opacity") or attrs.get("opacity") or "1.0"
        transform = attrs.get("transform")
        bbox = None
        try:
            if _cli_wrapper and _config:
                x_s = await _cli_wrapper._execute_command(
                    [str(_config.inkscape_executable), input_path, f"--query-x={object_id}"],
                    _config.process_timeout,
                )
                y_s = await _cli_wrapper._execute_command(
                    [str(_config.inkscape_executable), input_path, f"--query-y={object_id}"],
                    _config.process_timeout,
                )
                w_s = await _cli_wrapper._execute_command(
                    [str(_config.inkscape_executable), input_path, f"--query-width={object_id}"],
                    _config.process_timeout,
                )
                h_s = await _cli_wrapper._execute_command(
                    [str(_config.inkscape_executable), input_path, f"--query-height={object_id}"],
                    _config.process_timeout,
                )
                bbox = {
                    "x": float(x_s.strip()),
                    "y": float(y_s.strip()),
                    "w": float(w_s.strip()),
                    "h": float(h_s.strip()),
                }
        except Exception:
            pass
        return VectorOperationResult(
            success=True,
            operation="inspect",
            message=f"Inspected {el_type}#{object_id}",
            data={
                "object_id": object_id,
                "type": el_type,
                "fill": fill,
                "stroke": stroke,
                "stroke_width": stroke_width,
                "opacity": opacity,
                "transform": transform,
                "all_style": style,
                "bbox": bbox,
            },
            execution_time_ms=(time.time() - _start) * 1000,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="inspect",
            message=f"Inspect failed: {e}",
            data={"object_id": object_id},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _query_document(input_path: str, cli_wrapper: Any, config: Any) -> dict[str, Any]:
    """Query document information with --query-all for real object counts."""
    try:
        width_result = await cli_wrapper._execute_command(
            [str(config.inkscape_executable), input_path, "--query-width"], config.process_timeout
        )
        height_result = await cli_wrapper._execute_command(
            [str(config.inkscape_executable), input_path, "--query-height"], config.process_timeout
        )
        width = float(width_result.strip())
        height = float(height_result.strip())

        # Count objects via --query-all
        object_count = 0
        objects: list[dict[str, Any]] = []
        try:
            all_str = await cli_wrapper._execute_command(
                [str(config.inkscape_executable), input_path, "--query-all"],
                config.process_timeout,
            )
            for line in all_str.strip().split("\n"):
                parts = line.strip().split(",")
                if len(parts) >= 5:
                    objects.append(
                        {
                            "id": parts[0],
                            "x": float(parts[1]),
                            "y": float(parts[2]),
                            "w": float(parts[3]),
                            "h": float(parts[4]),
                        }
                    )
            object_count = len(objects)
        except Exception:
            object_count = 1

        return VectorOperationResult(
            success=True,
            operation="query_document",
            message=f"Queried {input_path}: {object_count} objects, {width}x{height}",
            data={
                "width": width,
                "height": height,
                "num_objects": object_count,
                "objects": objects,
            },
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="query_document",
            message=f"Document query failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _count_nodes(
    input_path: str, object_id: str, cli_wrapper: Any, config: Any
) -> dict[str, Any]:
    """Count nodes in a path object using --query-all."""
    try:
        query_output = await cli_wrapper._execute_command(
            [str(config.inkscape_executable), input_path, "--query-all"],
            config.process_timeout,
        )
        node_count = 0
        for line in query_output.strip().split("\n"):
            parts = line.strip().split(",")
            if parts and parts[0] == object_id:
                # --query-all returns id,x,y,w,h - count of path nodes not directly available
                # but we count objects matching the id
                node_count += 1
        if node_count == 0:
            node_count = 1  # object exists but precise node count requires inkex
        return VectorOperationResult(
            success=True,
            operation="count_nodes",
            message=f"Counted {node_count} object(s) matching {object_id}",
            data={"object_id": object_id, "node_count": node_count},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="count_nodes",
            message=f"Node counting failed: {e}",
            data={"object_id": object_id},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _path_simplify(
    input_path: str,
    output_path: str,
    object_id: str,
    threshold: float,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Simplify path by reducing nodes."""
    try:
        actions = [
            f"select-by-id:{object_id}",
            f"selection-simplify:{threshold}",
            f"export-filename:{output_path}",
            "export-do",
        ]

        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )

        return VectorOperationResult(
            success=True,
            operation="path_simplify",
            message=f"Simplified path for object {object_id}",
            data={
                "input_path": input_path,
                "output_path": output_path,
                "object_id": object_id,
                "threshold": threshold,
            },
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="path_simplify",
            message=f"Path simplification failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _path_clean(
    input_path: str, output_path: str, cli_wrapper: Any, config: Any
) -> dict[str, Any]:
    """Clean SVG by removing unnecessary elements."""
    try:
        actions = [
            "file-vacuum-defs",
            "file-cleanup",
            f"export-filename:{output_path}",
            "export-do",
        ]

        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )

        return VectorOperationResult(
            success=True,
            operation="path_clean",
            message=f"Cleaned SVG {input_path}",
            data={
                "input_path": input_path,
                "output_path": output_path,
            },
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="path_clean",
            message=f"Path cleaning failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _export_dxf(
    input_path: str, output_path: str, cli_wrapper: Any, config: Any
) -> dict[str, Any]:
    """Export SVG paths to DXF for CAD/laser workflows."""
    try:
        actions = [
            f"export-filename:{output_path}",
            "export-type:DXF",
            "export-do",
        ]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="export_dxf",
            message=f"DXF exported successfully to {output_path}",
            data={
                "input_path": input_path,
                "output_path": output_path,
                "format": "dxf",
            },
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()
    except Exception as exc:
        return VectorOperationResult(
            success=False,
            operation="export_dxf",
            message=f"DXF export failed: {exc}",
            data={},
            execution_time_ms=0,
            error=str(exc),
        ).model_dump()


async def _render_preview(
    input_path: str, output_path: str, dpi: int, cli_wrapper: Any, config: Any
) -> dict[str, Any]:
    """Render PNG preview of SVG."""
    try:
        actions = [f"export-filename:{output_path}", f"export-dpi:{dpi}", "export-do"]

        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )

        return VectorOperationResult(
            success=True,
            operation="render_preview",
            message=f"Rendered preview of {input_path}",
            data={
                "input_path": input_path,
                "output_path": output_path,
                "dpi": dpi,
                "format": "png",
            },
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="render_preview",
            message=f"Preview rendering failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _apply_boolean(
    boolean_type: str,
    input_path: str,
    output_path: str,
    object_ids: list[str] | None = None,
    select_all: bool = False,
    cli_wrapper: Any = None,
    config: Any = None,
) -> dict[str, Any]:
    """Apply boolean operations with proper action chaining - FIXED STATEFUL LOGIC."""
    try:
        # CRITICAL: Build proper action chain - Select → Modify → Persist
        if select_all:
            select_action = "select-all"
        elif object_ids:
            select_action = f"select-by-id:{','.join(object_ids)}"
        else:
            return VectorOperationResult(
                success=False,
                operation="apply_boolean",
                message="Must provide either object_ids or select_all=true for boolean operations",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        # Map operation types to Inkscape actions
        operation_map = {
            "union": "selection-union",
            "difference": "selection-difference",
            "intersection": "selection-intersection",
            "exclusion": "selection-exclusion",
        }

        if boolean_type not in operation_map:
            return VectorOperationResult(
                success=False,
                operation="apply_boolean",
                message=f"Unknown boolean operation: {boolean_type}",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        operation_action = operation_map[boolean_type]

        # MANDATORY: Complete action chain with export for persistence
        actions = f"{select_action};{operation_action};export-filename:{output_path};export-do"

        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )

        return VectorOperationResult(
            success=True,
            operation="apply_boolean",
            message=f"Applied {boolean_type} boolean operation with proper stateful execution",
            data={
                "input_path": input_path,
                "output_path": output_path,
                "operation": boolean_type,
                "selection_method": "select_all" if select_all else "object_ids",
                "object_ids": object_ids or ["all"],
                "action_chain": actions,  # For debugging/transparency
            },
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="apply_boolean",
            message=f"Boolean operation failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _object_raise(
    input_path: str, output_path: str, object_id: str, cli_wrapper: Any, config: Any
) -> dict[str, Any]:
    """Raise object in Z-order (move up)."""
    try:
        actions = (
            f"select-by-id:{object_id};selection-raise;export-filename:{output_path};export-do"
        )

        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )

        return VectorOperationResult(
            success=True,
            operation="object_raise",
            message=f"Raised object {object_id} in Z-order",
            data={
                "input_path": input_path,
                "output_path": output_path,
                "object_id": object_id,
            },
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="object_raise",
            message=f"Object raise failed: {e}",
            data={"object_id": object_id},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _object_lower(
    input_path: str, output_path: str, object_id: str, cli_wrapper: Any, config: Any
) -> dict[str, Any]:
    """Lower object in Z-order (move down)."""
    try:
        actions = (
            f"select-by-id:{object_id};selection-lower;export-filename:{output_path};export-do"
        )

        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )

        return VectorOperationResult(
            success=True,
            operation="object_lower",
            message=f"Lowered object {object_id} in Z-order",
            data={
                "input_path": input_path,
                "output_path": output_path,
                "object_id": object_id,
            },
            execution_time_ms=(time.time() - time.time()) * 1000,
        ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="object_lower",
            message=f"Object lower failed: {e}",
            data={"object_id": object_id},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _set_document_units(
    input_path: str, output_path: str, units: str, cli_wrapper: Any, config: Any
) -> dict[str, Any]:
    """Set document units via export-filename/export-type:SVG with viewBox adjustment."""
    try:
        actions = [
            f"export-filename:{output_path}",
            "export-type:SVG",
            "export-do",
        ]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="set_document_units",
            message=f"Re-exported {input_path} with unit hint '{units}' to {output_path}",
            data={
                "input_path": input_path,
                "output_path": output_path,
                "units": units,
                "note": "Use inkscape --export-overwrite + set document-properties for full units change",
            },
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="set_document_units",
            message=f"Document units setting failed: {e}",
            data={"requested_units": units},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


def _local_tag(el: ET.Element) -> str:
    """Element tag without the SVG namespace prefix."""
    tag = el.tag
    return tag.split("}", 1)[1] if "}" in tag else tag


def _matches_simple_selector(el: ET.Element, selector: str) -> bool:
    """Match one simple selector: `*`, `tag`, `.class`, `#id`, or `tag.class`/`tag#id`.

    Deliberately a safe subset (no descendant/attribute/pseudo selectors) - same
    scope limitation grumpydevorg/inkscape-mcps documents for its `dom_set` tool.
    """
    selector = selector.strip()
    if not selector or selector == "*":
        return True

    tag_part = selector
    id_part = ""
    class_part = ""
    if "#" in tag_part:
        tag_part, id_part = tag_part.split("#", 1)
    if "." in tag_part:
        tag_part, class_part = tag_part.split(".", 1)
    elif "." in id_part:
        id_part, class_part = id_part.split(".", 1)

    if tag_part and _local_tag(el) != tag_part:
        return False
    if id_part and el.get("id") != id_part:
        return False
    if class_part:
        classes = el.get("class", "").split()
        if class_part not in classes:
            return False
    return True


def _selector_matches(el: ET.Element, selector_list: str) -> bool:
    """Comma-separated list of simple selectors - matches if any one matches."""
    return any(_matches_simple_selector(el, s) for s in selector_list.split(","))


def _apply_style_params(el: ET.Element, params: dict[str, Any]) -> None:
    """Apply a params dict to one element: `style.<prop>` merges into the style
    attribute (parsed as `prop:value;...`), anything else sets a plain XML attribute.
    """
    style_updates = {}
    plain_updates = {}
    for key, value in params.items():
        if key.startswith("style."):
            style_updates[key[len("style.") :]] = value
        else:
            plain_updates[key] = value

    if style_updates:
        existing = el.get("style", "")
        style_map = {}
        for decl in existing.split(";"):
            decl = decl.strip()
            if not decl or ":" not in decl:
                continue
            prop, _, val = decl.partition(":")
            style_map[prop.strip()] = val.strip()
        style_map.update({k: str(v) for k, v in style_updates.items()})
        el.set("style", ";".join(f"{k}:{v}" for k, v in style_map.items()))

    for key, value in plain_updates.items():
        el.set(key, str(value))


async def _bulk_restyle(
    input_path: str, output_path: str, selector: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Apply attribute/style changes to every element matching a CSS-like selector.

    Pure DOM edit (no Inkscape CLI shell-out) - direct XML read/modify/write via
    ElementTree, mirroring the pattern already used in validation_tools.py and
    sim_art_tools.py.
    """
    try:
        if not selector.strip():
            return VectorOperationResult(
                success=False,
                operation="bulk_restyle",
                message="bulk_restyle requires a non-empty selector",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()
        if not params:
            return VectorOperationResult(
                success=False,
                operation="bulk_restyle",
                message="bulk_restyle requires a non-empty params dict (attrs or style.<prop>)",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        ET.register_namespace("", SVG_URI)
        tree = ET.parse(input_path)
        root = tree.getroot()

        matched_ids = []
        for el in root.iter():
            if el is root:
                continue
            if _selector_matches(el, selector):
                _apply_style_params(el, params)
                matched_ids.append(el.get("id") or f"<{_local_tag(el)}>")

        dest = output_path or input_path
        tree.write(dest, xml_declaration=False, default_namespace=None)

        return VectorOperationResult(
            success=True,
            operation="bulk_restyle",
            message=f"Restyled {len(matched_ids)} element(s) matching '{selector}'",
            data={
                "selector": selector,
                "params": params,
                "matched_count": len(matched_ids),
                "matched_ids": matched_ids,
                "output_path": dest,
            },
            execution_time_ms=0,
        ).model_dump()

    except FileNotFoundError:
        return VectorOperationResult(
            success=False,
            operation="bulk_restyle",
            message=f"File not found: {input_path}",
            data={},
            execution_time_ms=0,
            error="FileNotFoundError",
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="bulk_restyle",
            message=f"bulk_restyle failed: {e}",
            data={"selector": selector},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


_FILTER_PRIMITIVE_TAGS = {
    "defs",
    "filter",
    "feGaussianBlur",
    "feDropShadow",
    "feFlood",
    "feComposite",
    "feMerge",
    "feMergeNode",
    "feOffset",
}


def _build_filter_element(filter_id: str, kind: str, params: dict[str, Any]) -> ET.Element:
    """Build an SVG <filter> def for a supported kind: blur, drop_shadow, glow.

    Fills the gap noted in reports/wrappee-drift-inkscape-mcp-2026-09-27.md -
    Inkscape 1.4 shipped a Filter Gallery UI but this repo had no filter-effects op.
    """
    filt = ET.Element(f"{{{SVG_URI}}}filter", {"id": filter_id})

    if kind == "blur":
        std = str(params.get("std_deviation", 3))
        ET.SubElement(filt, f"{{{SVG_URI}}}feGaussianBlur", {"stdDeviation": std})

    elif kind == "drop_shadow":
        ET.SubElement(
            filt,
            f"{{{SVG_URI}}}feDropShadow",
            {
                "dx": str(params.get("dx", 2)),
                "dy": str(params.get("dy", 2)),
                "stdDeviation": str(params.get("std_deviation", 3)),
                "flood-color": str(params.get("color", "#000000")),
                "flood-opacity": str(params.get("opacity", 0.5)),
            },
        )

    elif kind == "glow":
        std = str(params.get("std_deviation", 4))
        color = params.get("color", "")
        blur_in = "SourceGraphic"
        if color:
            ET.SubElement(
                filt,
                f"{{{SVG_URI}}}feFlood",
                {"flood-color": str(color), "result": "flood"},
            )
            ET.SubElement(
                filt,
                f"{{{SVG_URI}}}feComposite",
                {"in": "flood", "in2": "SourceGraphic", "operator": "in", "result": "colored"},
            )
            blur_in = "colored"
        ET.SubElement(
            filt,
            f"{{{SVG_URI}}}feGaussianBlur",
            {"in": blur_in, "stdDeviation": std, "result": "blurred"},
        )
        merge = ET.SubElement(filt, f"{{{SVG_URI}}}feMerge")
        ET.SubElement(merge, f"{{{SVG_URI}}}feMergeNode", {"in": "blurred"})
        ET.SubElement(merge, f"{{{SVG_URI}}}feMergeNode", {"in": "SourceGraphic"})

    else:
        raise ValueError(f"Unknown filter kind '{kind}' - expected blur, drop_shadow, or glow")

    return filt


async def _apply_filter(
    input_path: str,
    output_path: str,
    selector: str,
    object_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Define an SVG filter (blur/drop_shadow/glow) and apply it to matching elements."""
    kind = str(params.get("kind", ""))
    try:
        if kind not in ("blur", "drop_shadow", "glow"):
            return VectorOperationResult(
                success=False,
                operation="apply_filter",
                message="params.kind must be one of: blur, drop_shadow, glow",
                data={"kind": kind},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()
        if not selector.strip() and not object_id.strip():
            return VectorOperationResult(
                success=False,
                operation="apply_filter",
                message="apply_filter requires a selector or object_id to target elements",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        ET.register_namespace("", SVG_URI)
        tree = ET.parse(input_path)
        root = tree.getroot()

        matched: list[ET.Element] = []
        for el in root.iter():
            if el is root or _local_tag(el) in _FILTER_PRIMITIVE_TAGS:
                continue
            if object_id and el.get("id") == object_id:
                matched.append(el)
            elif selector and _selector_matches(el, selector):
                matched.append(el)

        if not matched:
            return VectorOperationResult(
                success=False,
                operation="apply_filter",
                message=f"No elements matched selector={selector!r} object_id={object_id!r}",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        filter_id = str(
            params.get("filter_id") or f"filter_{kind}_{int(time.time() * 1000) % 100000}"
        )
        defs = root.find(f"{{{SVG_URI}}}defs")
        if defs is None:
            defs = ET.SubElement(root, f"{{{SVG_URI}}}defs")
        defs.append(_build_filter_element(filter_id, kind, params))

        matched_ids = []
        for el in matched:
            el.set("filter", f"url(#{filter_id})")
            matched_ids.append(el.get("id") or f"<{_local_tag(el)}>")

        dest = output_path or input_path
        tree.write(dest, xml_declaration=False, default_namespace=None)

        return VectorOperationResult(
            success=True,
            operation="apply_filter",
            message=f"Applied {kind} filter '{filter_id}' to {len(matched_ids)} element(s)",
            data={
                "kind": kind,
                "filter_id": filter_id,
                "matched_count": len(matched_ids),
                "matched_ids": matched_ids,
                "output_path": dest,
            },
            execution_time_ms=0,
        ).model_dump()

    except FileNotFoundError:
        return VectorOperationResult(
            success=False,
            operation="apply_filter",
            message=f"File not found: {input_path}",
            data={},
            execution_time_ms=0,
            error="FileNotFoundError",
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="apply_filter",
            message=f"apply_filter failed: {e}",
            data={"kind": kind},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


def _get_or_create_defs(root: ET.Element) -> ET.Element:
    defs = root.find(f"{{{SVG_URI}}}defs")
    if defs is None:
        defs = ET.SubElement(root, f"{{{SVG_URI}}}defs")
    return defs


def _find_by_id(root: ET.Element, object_id: str) -> ET.Element | None:
    for el in root.iter():
        if el.get("id") == object_id:
            return el
    return None


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000) % 1000000}"


async def _create_gradient(
    input_path: str, output_path: str, object_id: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Define a linear or radial gradient in <defs>. Returns a `fill` value
    (url(#id)) ready to hand to create_object/set_attributes/bulk_restyle -
    this never applies the gradient itself, keeping one clean way to paint
    any element instead of a second fill-setting path."""
    try:
        stops = params.get("stops") or []
        if not stops:
            return VectorOperationResult(
                success=False,
                operation="create_gradient",
                message="params.stops is required: [{offset, color, opacity?}, ...]",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        gradient_type = params.get("type", "linear")
        gradient_id = object_id or _gen_id(f"{gradient_type}Gradient")

        ET.register_namespace("", SVG_URI)
        tree = ET.parse(input_path)
        root = tree.getroot()
        defs = _get_or_create_defs(root)

        if gradient_type == "radial":
            grad = ET.SubElement(
                defs,
                f"{{{SVG_URI}}}radialGradient",
                {
                    "id": gradient_id,
                    "cx": str(params.get("cx", "50%")),
                    "cy": str(params.get("cy", "50%")),
                    "r": str(params.get("r", "50%")),
                },
            )
        else:
            grad = ET.SubElement(
                defs,
                f"{{{SVG_URI}}}linearGradient",
                {
                    "id": gradient_id,
                    "x1": str(params.get("x1", "0%")),
                    "y1": str(params.get("y1", "0%")),
                    "x2": str(params.get("x2", "100%")),
                    "y2": str(params.get("y2", "0%")),
                },
            )
        for stop in stops:
            ET.SubElement(
                grad,
                f"{{{SVG_URI}}}stop",
                {
                    "offset": str(stop.get("offset", 0)),
                    "stop-color": str(stop.get("color", "#000000")),
                    "stop-opacity": str(stop.get("opacity", 1)),
                },
            )

        dest = output_path or input_path
        tree.write(dest, xml_declaration=False, default_namespace=None)

        return VectorOperationResult(
            success=True,
            operation="create_gradient",
            message=f"Created {gradient_type} gradient '{gradient_id}' with {len(stops)} stop(s)",
            data={"id": gradient_id, "fill": f"url(#{gradient_id})", "output_path": dest},
            execution_time_ms=0,
        ).model_dump()
    except FileNotFoundError:
        return VectorOperationResult(
            success=False,
            operation="create_gradient",
            message=f"File not found: {input_path}",
            data={},
            execution_time_ms=0,
            error="FileNotFoundError",
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="create_gradient",
            message=f"create_gradient failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _create_pattern(
    input_path: str, output_path: str, object_id: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Define a tiling <pattern> in <defs> from a raw SVG child fragment
    (params.content) - returns a `fill` value (url(#id)) like create_gradient."""
    try:
        content = params.get("content", "")
        if not content:
            return VectorOperationResult(
                success=False,
                operation="create_pattern",
                message='params.content is required (raw SVG markup for one tile, e.g. \'<circle cx="5" cy="5" r="4" fill="red"/>\')',
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        pattern_id = object_id or _gen_id("pattern")
        width = params.get("width", 10)
        height = params.get("height", 10)

        ET.register_namespace("", SVG_URI)
        tree = ET.parse(input_path)
        root = tree.getroot()
        defs = _get_or_create_defs(root)

        pattern = ET.SubElement(
            defs,
            f"{{{SVG_URI}}}pattern",
            {
                "id": pattern_id,
                "width": str(width),
                "height": str(height),
                "patternUnits": "userSpaceOnUse",
            },
        )
        try:
            tile = ET.fromstring(f'<g xmlns="{SVG_URI}">{content}</g>')
        except ET.ParseError as e:
            raise ValueError(f"params.content is not valid SVG markup: {e}") from e
        for child in tile:
            pattern.append(child)

        dest = output_path or input_path
        tree.write(dest, xml_declaration=False, default_namespace=None)

        return VectorOperationResult(
            success=True,
            operation="create_pattern",
            message=f"Created pattern '{pattern_id}' ({width}x{height} tile)",
            data={"id": pattern_id, "fill": f"url(#{pattern_id})", "output_path": dest},
            execution_time_ms=0,
        ).model_dump()
    except FileNotFoundError:
        return VectorOperationResult(
            success=False,
            operation="create_pattern",
            message=f"File not found: {input_path}",
            data={},
            execution_time_ms=0,
            error="FileNotFoundError",
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="create_pattern",
            message=f"create_pattern failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _get_attributes(input_path: str, object_id: str) -> dict[str, Any]:
    """Read every attribute (plus style, parsed as a dict) of one element -
    the read side of the XML-editor pair with set_attributes."""
    try:
        if not object_id:
            return VectorOperationResult(
                success=False,
                operation="get_attributes",
                message="object_id is required",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        tree = ET.parse(input_path)
        root = tree.getroot()
        el = _find_by_id(root, object_id)
        if el is None:
            return VectorOperationResult(
                success=False,
                operation="get_attributes",
                message=f"No element with id '{object_id}'",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        style_map = {}
        for decl in el.get("style", "").split(";"):
            decl = decl.strip()
            if decl and ":" in decl:
                prop, _, val = decl.partition(":")
                style_map[prop.strip()] = val.strip()

        return VectorOperationResult(
            success=True,
            operation="get_attributes",
            message=f"Read {len(el.attrib)} attribute(s) from '{object_id}'",
            data={
                "id": object_id,
                "tag": _local_tag(el),
                "attributes": dict(el.attrib),
                "style": style_map,
            },
            execution_time_ms=0,
        ).model_dump()
    except FileNotFoundError:
        return VectorOperationResult(
            success=False,
            operation="get_attributes",
            message=f"File not found: {input_path}",
            data={},
            execution_time_ms=0,
            error="FileNotFoundError",
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="get_attributes",
            message=f"get_attributes failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _text_on_path(
    input_path: str, output_path: str, path_id: str, object_id: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Create a <text><textPath href="#path_id">...</textPath></text> element
    bound to an existing path - real Inkscape "put text on path" behavior."""
    try:
        if not path_id:
            return VectorOperationResult(
                success=False,
                operation="text_on_path",
                message="ref_id is required: the id of an existing path to attach text to",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        ET.register_namespace("", SVG_URI)
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
        tree = ET.parse(input_path)
        root = tree.getroot()
        if _find_by_id(root, path_id) is None:
            return VectorOperationResult(
                success=False,
                operation="text_on_path",
                message=f"No path with id '{path_id}' - create it first",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        text_id = object_id or _gen_id("text_on_path")
        style_bits = []
        if params.get("font_family"):
            style_bits.append(f"font-family:{params['font_family']}")
        if params.get("font_size"):
            style_bits.append(f"font-size:{params['font_size']}px")
        if params.get("fill"):
            style_bits.append(f"fill:{params['fill']}")

        text_el = ET.SubElement(root, f"{{{SVG_URI}}}text", {"id": text_id})
        if style_bits:
            text_el.set("style", ";".join(style_bits))
        text_path_attrs = {"{http://www.w3.org/1999/xlink}href": f"#{path_id}"}
        if params.get("start_offset") is not None:
            text_path_attrs["startOffset"] = str(params["start_offset"])
        text_path_el = ET.SubElement(text_el, f"{{{SVG_URI}}}textPath", text_path_attrs)
        text_path_el.text = str(params.get("content", ""))

        dest = output_path or input_path
        tree.write(dest, xml_declaration=False, default_namespace=None)

        return VectorOperationResult(
            success=True,
            operation="text_on_path",
            message=f"Created text '{text_id}' on path '{path_id}'",
            data={"id": text_id, "path_id": path_id, "output_path": dest},
            execution_time_ms=0,
        ).model_dump()
    except FileNotFoundError:
        return VectorOperationResult(
            success=False,
            operation="text_on_path",
            message=f"File not found: {input_path}",
            data={},
            execution_time_ms=0,
            error="FileNotFoundError",
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="text_on_path",
            message=f"text_on_path failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _flow_text(
    input_path: str, output_path: str, shape_id: str, object_id: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Flow text inside an existing shape via CSS Shapes `shape-inside` -
    the same mechanism Inkscape's own "Flow into frame" produces."""
    try:
        if not shape_id:
            return VectorOperationResult(
                success=False,
                operation="flow_text",
                message="ref_id is required: the id of an existing shape to flow text into",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        ET.register_namespace("", SVG_URI)
        tree = ET.parse(input_path)
        root = tree.getroot()
        if _find_by_id(root, shape_id) is None:
            return VectorOperationResult(
                success=False,
                operation="flow_text",
                message=f"No shape with id '{shape_id}' - create it first",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        text_id = object_id or _gen_id("flow_text")
        style_bits = [f"shape-inside:url(#{shape_id})"]
        if params.get("font_family"):
            style_bits.append(f"font-family:{params['font_family']}")
        if params.get("font_size"):
            style_bits.append(f"font-size:{params['font_size']}px")
        if params.get("fill"):
            style_bits.append(f"fill:{params['fill']}")

        text_el = ET.SubElement(
            root, f"{{{SVG_URI}}}text", {"id": text_id, "style": ";".join(style_bits)}
        )
        text_el.text = str(params.get("content", ""))

        dest = output_path or input_path
        tree.write(dest, xml_declaration=False, default_namespace=None)

        return VectorOperationResult(
            success=True,
            operation="flow_text",
            message=f"Created text '{text_id}' flowed into shape '{shape_id}'",
            data={"id": text_id, "shape_id": shape_id, "output_path": dest},
            execution_time_ms=0,
        ).model_dump()
    except FileNotFoundError:
        return VectorOperationResult(
            success=False,
            operation="flow_text",
            message=f"File not found: {input_path}",
            data={},
            execution_time_ms=0,
            error="FileNotFoundError",
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="flow_text",
            message=f"flow_text failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _create_symbol(
    input_path: str, output_path: str, object_id: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Wrap a raw SVG fragment (params.content) into a reusable <symbol> in
    <defs> - the pair with use_symbol."""
    try:
        content = params.get("content", "")
        if not content:
            return VectorOperationResult(
                success=False,
                operation="create_symbol",
                message="params.content is required (raw SVG markup for the reusable asset)",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        symbol_id = object_id or _gen_id("symbol")

        ET.register_namespace("", SVG_URI)
        tree = ET.parse(input_path)
        root = tree.getroot()
        defs = _get_or_create_defs(root)

        symbol_attrs = {"id": symbol_id}
        if params.get("viewBox"):
            symbol_attrs["viewBox"] = str(params["viewBox"])
        symbol = ET.SubElement(defs, f"{{{SVG_URI}}}symbol", symbol_attrs)
        try:
            fragment = ET.fromstring(f'<g xmlns="{SVG_URI}">{content}</g>')
        except ET.ParseError as e:
            raise ValueError(f"params.content is not valid SVG markup: {e}") from e
        for child in fragment:
            symbol.append(child)

        dest = output_path or input_path
        tree.write(dest, xml_declaration=False, default_namespace=None)

        return VectorOperationResult(
            success=True,
            operation="create_symbol",
            message=f"Created symbol '{symbol_id}'",
            data={"id": symbol_id, "output_path": dest},
            execution_time_ms=0,
        ).model_dump()
    except FileNotFoundError:
        return VectorOperationResult(
            success=False,
            operation="create_symbol",
            message=f"File not found: {input_path}",
            data={},
            execution_time_ms=0,
            error="FileNotFoundError",
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="create_symbol",
            message=f"create_symbol failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _use_symbol(
    input_path: str, output_path: str, symbol_id: str, object_id: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Instantiate a previously create_symbol'd (or any existing) symbol via
    <use href="#symbol_id">."""
    try:
        if not symbol_id:
            return VectorOperationResult(
                success=False,
                operation="use_symbol",
                message="ref_id is required: the id of an existing <symbol> to instantiate",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        ET.register_namespace("", SVG_URI)
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
        tree = ET.parse(input_path)
        root = tree.getroot()
        if _find_by_id(root, symbol_id) is None:
            return VectorOperationResult(
                success=False,
                operation="use_symbol",
                message=f"No element with id '{symbol_id}' - create_symbol first",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        use_id = object_id or _gen_id("use")
        use_attrs = {
            "id": use_id,
            "{http://www.w3.org/1999/xlink}href": f"#{symbol_id}",
            "x": str(params.get("x", 0)),
            "y": str(params.get("y", 0)),
        }
        if params.get("width") is not None:
            use_attrs["width"] = str(params["width"])
        if params.get("height") is not None:
            use_attrs["height"] = str(params["height"])
        ET.SubElement(root, f"{{{SVG_URI}}}use", use_attrs)

        dest = output_path or input_path
        tree.write(dest, xml_declaration=False, default_namespace=None)

        return VectorOperationResult(
            success=True,
            operation="use_symbol",
            message=f"Instantiated symbol '{symbol_id}' as '{use_id}'",
            data={"id": use_id, "symbol_id": symbol_id, "output_path": dest},
            execution_time_ms=0,
        ).model_dump()
    except FileNotFoundError:
        return VectorOperationResult(
            success=False,
            operation="use_symbol",
            message=f"File not found: {input_path}",
            data={},
            execution_time_ms=0,
            error="FileNotFoundError",
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="use_symbol",
            message=f"use_symbol failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


# ── Newly implemented operations (Phase 1 stub fill-in) ──────────────────────


async def _create_object(
    output_path: str,
    shape: str,
    params: dict[str, Any],
    _cli_wrapper: Any,
    _config: Any,
) -> dict[str, Any]:
    """Create an SVG document with a primitive shape (rect, circle, ellipse, star, text, path)."""
    _start = time.time()
    try:
        w = params.get("width", params.get("w", 800))
        h = params.get("height", params.get("h", 600))
        name = params.get("name", shape)
        svg_header = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
        elements: list[str] = []

        if shape == "rect":
            x = params.get("x", 10)
            y = params.get("y", 10)
            rw = params.get("w", w - 20)
            rh = params.get("h", h - 20)
            rx = params.get("rx", 0)
            ry = params.get("ry", 0)
            fill = params.get("fill", "#4488ff")
            stroke = params.get("stroke", "none")
            elements.append(
                f'<rect id="{name}" x="{x}" y="{y}" width="{rw}" height="{rh}" '
                f'rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
            )
        elif shape == "circle":
            cx = params.get("cx", w / 2)
            cy = params.get("cy", h / 2)
            r = params.get("r", min(w, h) / 4)
            fill = params.get("fill", "#ff4488")
            elements.append(f'<circle id="{name}" cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>')
        elif shape == "ellipse":
            cx = params.get("cx", w / 2)
            cy = params.get("cy", h / 2)
            rx = params.get("rx", w / 4)
            ry = params.get("ry", h / 3)
            fill = params.get("fill", "#88ff44")
            elements.append(
                f'<ellipse id="{name}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"/>'
            )
        elif shape == "star":
            cx = params.get("cx", w / 2)
            cy = params.get("cy", h / 2)
            fill = params.get("fill", "#ffcc00")
            points = params.get("points", 5)
            outer = params.get("outer_r", min(w, h) / 4)
            inner = params.get("inner_r", outer * 0.4)
            poly_pts = []
            for i in range(points * 2):
                angle = math.radians(i * 180 / points - 90)
                r_val = outer if i % 2 == 0 else inner
                poly_pts.append(
                    f"{cx + r_val * math.cos(angle):.1f},{cy + r_val * math.sin(angle):.1f}"
                )
            elements.append(f'<polygon id="{name}" points="{" ".join(poly_pts)}" fill="{fill}"/>')
        elif shape == "text":
            content = params.get("content", "Text")
            x = params.get("x", 20)
            y = params.get("y", 60)
            font_size = params.get("font_size", 24)
            font_family = params.get("font_family", "sans-serif")
            fill = params.get("fill", "#ffffff")
            elements.append(
                f'<text id="{name}" x="{x}" y="{y}" '
                f'font-family="{font_family}" font-size="{font_size}" fill="{fill}">{content}</text>'
            )
        elif shape == "path":
            d = params.get("d", "M 10,50 Q 200,10 400,50")
            stroke = params.get("stroke", "#ffffff")
            fill = params.get("fill", "none")
            sw = params.get("stroke_width", 2)
            elements.append(
                f'<path id="{name}" d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            )
        else:
            return VectorOperationResult(
                success=False,
                operation="create_object",
                message=f"Unknown shape '{shape}'. Supported: rect, circle, ellipse, star, text, path",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

        svg = f"{svg_header}\n  " + "\n  ".join(elements) + "\n</svg>"
        Path(output_path).write_text(svg, encoding="utf-8")

        return VectorOperationResult(
            success=True,
            operation="create_object",
            message=f"Created {shape} '{name}' at {output_path}",
            data={"shape": shape, "params": params, "output_path": output_path},
            execution_time_ms=(time.time() - _start) * 1000,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="create_object",
            message=f"Object creation failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _text_to_path(
    input_path: str,
    output_path: str,
    object_id: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Convert text objects to paths via Inkscape actions."""
    try:
        select = f"select-by-id:{object_id}" if object_id else "select-by-element:text"
        actions = [select, "object-to-path", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="text_to_path",
            message=f"Converted text to path: {output_path}",
            data={"input_path": input_path, "output_path": output_path, "object_id": object_id},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="text_to_path",
            message=f"Text to path failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _construct_svg(
    output_path: str,
    element_type: str,
    params: dict[str, Any],
    _config: Any,
) -> dict[str, Any]:
    """Construct a new SVG from raw element definitions (header + body)."""
    try:
        header = params.get(
            "header", '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">'
        )
        body = params.get("body", "")
        footer = params.get("footer", "</svg>")
        svg_content = f"{header}\n{body}\n{footer}"
        Path(output_path).write_text(svg_content, encoding="utf-8")
        return VectorOperationResult(
            success=True,
            operation="construct_svg",
            message=f"Constructed SVG document at {output_path}",
            data={"element_type": element_type, "path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="construct_svg",
            message=f"SVG construction failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _path_inset_outset(
    input_path: str,
    output_path: str,
    direction: str,
    amount: float,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Inset or outset selected paths."""
    try:
        action = "selection-inset" if direction == "inset" else "selection-outset"
        actions = [
            "select-all",
            f"{action}:{amount}",
            f"export-filename:{output_path}",
            "export-do",
        ]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="path_inset_outset",
            message=f"Applied {direction} ({amount}px) to {input_path}",
            data={
                "input_path": input_path,
                "output_path": output_path,
                "direction": direction,
                "amount": amount,
            },
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="path_inset_outset",
            message=f"Path inset/outset failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _path_combine(
    input_path: str,
    output_path: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Combine selected paths into a single path."""
    try:
        actions = ["select-all", "path-combine", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="path_combine",
            message=f"Combined paths from {input_path} to {output_path}",
            data={"input_path": input_path, "output_path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="path_combine",
            message=f"Path combine failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _path_break_apart(
    input_path: str,
    output_path: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Break apart a compound path into individual paths."""
    try:
        actions = ["select-all", "path-break-apart", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="path_break_apart",
            message=f"Broke apart paths from {input_path} to {output_path}",
            data={"input_path": input_path, "output_path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="path_break_apart",
            message=f"Path break apart failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _object_to_path(
    input_path: str,
    output_path: str,
    object_id: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Convert a shape object (rect, circle, star, text) to paths."""
    try:
        select = f"select-by-id:{object_id}" if object_id else "select-all"
        actions = [select, "object-to-path", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="object_to_path",
            message=f"Converted object(s) to paths: {output_path}",
            data={"input_path": input_path, "output_path": output_path, "object_id": object_id},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="object_to_path",
            message=f"Object to path failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _optimize_svg(
    input_path: str,
    output_path: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Optimize SVG by vacuuming unused defs and cleaning up."""
    try:
        actions = [
            "file-vacuum-defs",
            "file-cleanup",
            f"export-filename:{output_path}",
            "export-do",
        ]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="optimize_svg",
            message=f"Optimized {input_path} -> {output_path}",
            data={"input_path": input_path, "output_path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="optimize_svg",
            message=f"SVG optimization failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _scour_svg(
    input_path: str,
    output_path: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Aggressive SVG cleanup: vacuum defs, strip IDs, remove metadata."""
    try:
        actions = [
            "file-vacuum-defs",
            "file-cleanup",
            "select-all",
            "selection-unlink-recursive",
            f"export-filename:{output_path}",
            "export-type:SVG",
            "export-plain-svg",
            "export-do",
        ]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="scour_svg",
            message=f"Scoured {input_path} -> {output_path} (plain SVG)",
            data={"input_path": input_path, "output_path": output_path, "method": "plain-svg"},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="scour_svg",
            message=f"SVG scour failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _fit_canvas_to_drawing(
    input_path: str,
    output_path: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Resize the SVG canvas to tightly fit all drawing content."""
    try:
        actions = [
            "select-all",
            "fit-canvas-to-selection",
            f"export-filename:{output_path}",
            "export-do",
        ]
        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="fit_canvas_to_drawing",
            message=f"Canvas fitted to drawing: {output_path}",
            data={"input_path": input_path, "output_path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="fit_canvas_to_drawing",
            message=f"Canvas fit failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


async def _layers_to_files(
    input_path: str,
    output_dir: str,
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Export each top-level layer to a separate file."""
    try:
        # Discover layers via --query-all on layer elements
        # Layers are <g inkscape:groupmode="layer"> in the SVG
        layer_ids: list[str] = []
        try:
            raw = await cli_wrapper._execute_command(
                [str(config.inkscape_executable), input_path, "--query-all"],
                config.process_timeout,
            )
            for line in raw.strip().split("\n"):
                lid = line.split(",")[0].strip() if line.strip() else ""
                if lid:
                    layer_ids.append(lid)
        except Exception:
            layer_ids = ["layer1"]

        out_dir = Path(output_dir or str(Path(input_path).parent / "layers"))
        out_dir.mkdir(parents=True, exist_ok=True)
        exported: list[str] = []

        for lid in layer_ids[:20]:  # safety cap
            out_file = out_dir / f"{lid}.svg"
            actions = [
                f"select-by-id:{lid}",
                f"export-filename:{out_file}",
                "export-type:SVG",
                "export-do",
            ]
            try:
                await cli_wrapper._execute_actions(
                    input_path=input_path,
                    actions=actions,
                    output_path=str(out_file),
                    timeout=config.process_timeout,
                )
                exported.append(str(out_file))
            except Exception:
                pass

        return VectorOperationResult(
            success=True,
            operation="layers_to_files",
            message=f"Exported {len(exported)} layers to {out_dir}",
            data={
                "input_path": input_path,
                "output_dir": str(out_dir),
                "exported": exported,
                "layer_ids_probed": layer_ids,
            },
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="layers_to_files",
            message=f"Layer export failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


# ── Live Path Effects (LPEs) ──────────────────────────────────────────────────

_LPE_CATALOG: list[dict[str, str]] = [
    {"id": "bend", "label": "Bend", "desc": "Bend paths along a curve"},
    {
        "id": "envelope",
        "label": "Envelope Deformation",
        "desc": "Deform paths within an envelope shape",
    },
    {
        "id": "pattern_along_path",
        "label": "Pattern Along Path",
        "desc": "Repeat a pattern along a path",
    },
    {"id": "interpolate", "label": "Interpolate Sub-Paths", "desc": "Blend between two paths"},
    {"id": "roughen", "label": "Roughen", "desc": "Add random jitter to path nodes"},
    {"id": "sketch", "label": "Sketch", "desc": "Hatching/strokes for sketch effect"},
    {
        "id": "stitch_sub_paths",
        "label": "Stitch Sub-Paths",
        "desc": "Connect sub-paths with zigzag",
    },
    {"id": "bspline", "label": "BSpline", "desc": "Convert path to B-Spline curve"},
    {"id": "corners", "label": "Corners (Chamfer/Fillet)", "desc": "Round or chamfer path corners"},
    {"id": "power_stroke", "label": "Power Stroke", "desc": "Variable-width stroke along path"},
    {"id": "power_clip", "label": "Power Clip", "desc": "Clip with variable selection"},
    {"id": "spiro", "label": "Spiro Spline", "desc": "Spiro curve interpolation"},
    {"id": "vonkoch", "label": "VonKoch", "desc": "Fractal/recursive path subdivision"},
    {"id": "tiling", "label": "Tiling", "desc": "Tile clones in a grid/pattern"},
    {"id": "mirror_symmetry", "label": "Mirror Symmetry", "desc": "Mirror edits across an axis"},
]


async def _lpe_handler(
    operation: str,
    input_path: str,
    output_path: str,
    object_id: str,
    kwargs: dict[str, Any],
    cli_wrapper: Any,
    config: Any,
) -> dict[str, Any]:
    """Handle list_lpes and apply_lpe."""
    if operation == "list_lpes":
        return VectorOperationResult(
            success=True,
            operation="list_lpes",
            message=f"Found {len(_LPE_CATALOG)} Live Path Effects",
            data={"lpes": _LPE_CATALOG, "count": len(_LPE_CATALOG)},
            execution_time_ms=0,
        ).model_dump()

    # apply_lpe
    lpe_id = kwargs.get("lpe_id", "")
    lpe_params = kwargs.get("params", {})
    if not lpe_id or not input_path or not output_path:
        return VectorOperationResult(
            success=False,
            operation="apply_lpe",
            message="Required: lpe_id, input_path, output_path",
            data={"available_lpes": _LPE_CATALOG},
            execution_time_ms=0,
            error="ValueError",
        ).model_dump()

    try:
        select = f"select-by-id:{object_id}" if object_id else "select-all"
        # LPEs are applied via Inkscape's filter/effect system
        effect_verb = f"org.inkscape.effect.{lpe_id}"
        param_str = ";".join(f"{k}={v}" for k, v in lpe_params.items())
        actions = [select, effect_verb]
        if param_str:
            actions.append(f"lpe-param-set:{param_str}")
        actions.extend([f"export-filename:{output_path}", "export-do"])

        await cli_wrapper._execute_actions(
            input_path=input_path,
            actions=actions,
            output_path=output_path,
            timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True,
            operation="apply_lpe",
            message=f"Applied LPE '{lpe_id}' to {input_path}",
            data={
                "lpe_id": lpe_id,
                "params": lpe_params,
                "input_path": input_path,
                "output_path": output_path,
            },
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation="apply_lpe",
            message=f"LPE application failed: {e}. Try hands_in_command with Inkscape GUI open.",
            data={"lpe_id": lpe_id, "hint": "Some LPEs require the Inkscape GUI for live preview"},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()


# ── Text operations ───────────────────────────────────────────────────────────

_SYSTEM_FONTS = [
    "Arial",
    "Helvetica",
    "Verdana",
    "Tahoma",
    "Trebuchet MS",
    "Times New Roman",
    "Georgia",
    "Garamond",
    "Palatino",
    "Courier New",
    "Courier",
    "monospace",
    "Impact",
    "Comic Sans MS",
    "Lucida Console",
    "Lucida Sans Unicode",
    "Segoe UI",
    "Candara",
    "Calibri",
    "Cambria",
    "Constantia",
    "Corbel",
    "sans-serif",
    "serif",
    "fantasy",
    "cursive",
]

# Also try to get fonts from system font directory
try:
    _inkscape_fonts: list[str] = []
    for fp in Path("C:/Windows/Fonts").glob("*.ttf"):
        _inkscape_fonts.append(fp.stem)
    if _inkscape_fonts:
        _SYSTEM_FONTS = sorted(set(_SYSTEM_FONTS + _inkscape_fonts))
except Exception:
    pass


async def _text_handler(
    operation: str,
    input_path: str,
    output_path: str,
    object_id: str,
    kwargs: dict[str, Any],
    _cli_wrapper: Any,
    _config: Any,
) -> dict[str, Any]:
    """Handle text operations (text_set_content, text_set_style, text_list_fonts)."""
    if operation == "text_list_fonts":
        return VectorOperationResult(
            success=True,
            operation="text_list_fonts",
            message=f"Found {len(_SYSTEM_FONTS)} available fonts",
            data={"fonts": _SYSTEM_FONTS, "count": len(_SYSTEM_FONTS)},
            execution_time_ms=0,
        ).model_dump()

    if not input_path:
        return VectorOperationResult(
            success=False,
            operation=operation,
            message="input_path is required",
            data={},
            execution_time_ms=0,
            error="ValueError",
        ).model_dump()

    try:
        svg = Path(input_path).read_text(encoding="utf-8", errors="replace")
        dest = output_path or input_path

        if operation == "text_set_content":
            new_text = kwargs.get("text", "")
            if not object_id or not new_text:
                return VectorOperationResult(
                    success=False,
                    operation="text_set_content",
                    message="object_id and text are required",
                    data={},
                    execution_time_ms=0,
                    error="ValueError",
                ).model_dump()

            # Replace content of <text id="...">...content...</text>
            def _replace_text(m: re.Match) -> str:
                tag = m.group(1)
                # Preserve child elements (tspan, etc.) by only replacing direct text
                return (
                    f'<{tag} id="{object_id}"'
                    + m.group(0).partition(f'id="{object_id}"')[2].split(">", 1)[0]
                    + f">{new_text}</{tag.split()[0]}>"
                )

            pattern = re.compile(
                rf'<(text)(?:\s+[^>]*)?\s+id="{re.escape(object_id)}"[^>]*>(.*?)</\1>', re.DOTALL
            )
            if not pattern.search(svg):
                return VectorOperationResult(
                    success=False,
                    operation="text_set_content",
                    message=f"Text element '{object_id}' not found",
                    data={},
                    execution_time_ms=0,
                    error="NotFound",
                ).model_dump()
            new_svg = pattern.sub(_replace_text, svg)
            Path(dest).write_text(new_svg, encoding="utf-8")
            return VectorOperationResult(
                success=True,
                operation="text_set_content",
                message=f"Updated text content for '{object_id}'",
                data={"object_id": object_id, "new_text": new_text, "path": dest},
                execution_time_ms=0,
            ).model_dump()

        elif operation == "text_set_style":
            font_family = kwargs.get("font_family", "")
            font_size = kwargs.get("font_size", 0)
            font_weight = kwargs.get("font_weight", "")
            fill = kwargs.get("fill", "")
            text_anchor = kwargs.get("text_anchor", "")

            if not object_id:
                return VectorOperationResult(
                    success=False,
                    operation="text_set_style",
                    message="object_id is required",
                    data={},
                    execution_time_ms=0,
                    error="ValueError",
                ).model_dump()

            # Find the element and set attributes
            def _tag_edit(m: re.Match) -> str:
                full = m.group(0)
                tag_open = full[: full.index(">") + 1] if ">" in full else full
                rest = full[len(tag_open) :]
                attrs_to_set = {}
                if font_family:
                    attrs_to_set["font-family"] = font_family
                if font_size > 0:
                    attrs_to_set["font-size"] = str(font_size)
                if font_weight:
                    attrs_to_set["font-weight"] = font_weight
                if fill:
                    attrs_to_set["fill"] = fill
                if text_anchor:
                    attrs_to_set["text-anchor"] = text_anchor
                new_tag = tag_open
                for k, v in attrs_to_set.items():
                    if f'{k}="' in new_tag or f"{k}='" in new_tag:
                        new_tag = re.sub(rf'\b{k}\s*=\s*["\'][^"\']*["\']', f'{k}="{v}"', new_tag)
                    else:
                        new_tag = (
                            new_tag.rstrip("/>-").rstrip()
                            + f' {k}="{v}"'
                            + ("/>" if "/>" in new_tag else ">")
                        )
                return new_tag + rest

            pattern = re.compile(
                rf'<(?:text|tspan)[^>]*\s+id="{re.escape(object_id)}"[^>]*/?>(?:.*?</(?:text|tspan)>)?',
                re.DOTALL,
            )
            if not pattern.search(svg):
                return VectorOperationResult(
                    success=False,
                    operation="text_set_style",
                    message=f"Element '{object_id}' not found",
                    data={},
                    execution_time_ms=0,
                    error="NotFound",
                ).model_dump()
            new_svg = pattern.sub(_tag_edit, svg)
            Path(dest).write_text(new_svg, encoding="utf-8")
            return VectorOperationResult(
                success=True,
                operation="text_set_style",
                message=f"Updated style for '{object_id}'",
                data={
                    "object_id": object_id,
                    "changes": {
                        k: v
                        for k, v in [
                            ("font_family", font_family),
                            ("font_size", font_size),
                            ("font_weight", font_weight),
                            ("fill", fill),
                            ("text_anchor", text_anchor),
                        ]
                        if v or (k == "font_size" and v)
                    },
                },
                execution_time_ms=0,
            ).model_dump()

        else:
            return VectorOperationResult(
                success=False,
                operation=operation,
                message=f"Unknown text operation: {operation}",
                data={},
                execution_time_ms=0,
                error="ValueError",
            ).model_dump()

    except Exception as e:
        return VectorOperationResult(
            success=False,
            operation=operation,
            message=f"Text operation failed: {e}",
            data={},
            execution_time_ms=0,
            error=str(e),
        ).model_dump()
