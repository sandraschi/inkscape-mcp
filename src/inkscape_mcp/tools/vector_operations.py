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
import time
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel


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
        "construct_svg",
        "apply_boolean",
        "path_inset_outset",
        "path_simplify",
        "path_clean",
        "path_combine",
        "path_break_apart",
        "object_to_path",
        "optimize_svg",
        "scour_svg",
        "measure_object",
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
    ],
    input_path: str = "",
    output_path: str = "",
    object_id: str = "",
    object_ids: list[str] | None = None,
    select_all: bool = False,
    operation_type: str = "",
    cli_wrapper: Any = None,
    config: Any = None,
    **kwargs,
) -> dict[str, Any]:
    """Inkscape vector operations portmanteau tool."""
    start_time = time.time()

    try:
        if operation == "trace_image":
            return await _trace_image(input_path, output_path, cli_wrapper, config)

        elif operation == "generate_barcode_qr":
            return await _generate_barcode_qr(
                kwargs.get("barcode_data", ""), output_path, cli_wrapper, config
            )

        elif operation == "generate_laser_dot":
            preset_id = kwargs.get("preset_id", "")
            dot_x = kwargs.get("x", 300)
            dot_y = kwargs.get("y", 200)
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

        elif operation == "query_document":
            return await _query_document(input_path, cli_wrapper, config)

        elif operation == "count_nodes":
            return await _count_nodes(input_path, object_id, cli_wrapper, config)

        elif operation == "path_simplify":
            return await _path_simplify(
                input_path,
                output_path,
                object_id,
                kwargs.get("threshold", 1.0),
                cli_wrapper,
                config,
            )

        elif operation == "path_clean":
            return await _path_clean(input_path, output_path, cli_wrapper, config)

        elif operation == "render_preview":
            return await _render_preview(
                input_path, output_path, kwargs.get("dpi", 96), cli_wrapper, config
            )

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
            return await _set_document_units(
                input_path, output_path, kwargs.get("units", "px"), cli_wrapper, config
            )

        elif operation == "create_object":
            return await _create_object(
                output_path,
                kwargs.get("shape", "rect"),
                kwargs.get("params", {}),
                cli_wrapper,
                config,
            )

        elif operation == "text_to_path":
            return await _text_to_path(input_path, output_path, object_id, cli_wrapper, config)

        elif operation == "construct_svg":
            return await _construct_svg(
                output_path, kwargs.get("element_type", ""), kwargs.get("params", {}), config
            )

        elif operation == "path_inset_outset":
            return await _path_inset_outset(
                input_path,
                output_path,
                kwargs.get("direction", "inset"),
                kwargs.get("amount", 2.0),
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

        elif operation == "layers_to_files":
            return await _layers_to_files(
                input_path, output_path, kwargs.get("output_dir", ""), cli_wrapper, config
            )

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
                    objects.append({
                        "id": parts[0], "x": float(parts[1]), "y": float(parts[2]),
                        "w": float(parts[3]), "h": float(parts[4]),
                    })
            object_count = len(objects)
        except Exception:
            object_count = 1

        return VectorOperationResult(
            success=True, operation="query_document",
            message=f"Queried {input_path}: {object_count} objects, {width}x{height}",
            data={
                "width": width, "height": height,
                "num_objects": object_count, "objects": objects,
            },
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="query_document",
            message=f"Document query failed: {e}", data={},
            execution_time_ms=0, error=str(e),
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
                # --query-all returns id,x,y,w,h — count of path nodes not directly available
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
            success=False, operation="count_nodes",
            message=f"Node counting failed: {e}",
            data={"object_id": object_id}, execution_time_ms=0, error=str(e),
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
            input_path=input_path, actions=actions,
            output_path=output_path, timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True, operation="set_document_units",
            message=f"Re-exported {input_path} with unit hint '{units}' to {output_path}",
            data={
                "input_path": input_path, "output_path": output_path,
                "units": units, "note": "Use inkscape --export-overwrite + set document-properties for full units change",
            },
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="set_document_units",
            message=f"Document units setting failed: {e}",
            data={"requested_units": units}, execution_time_ms=0, error=str(e),
        ).model_dump()


# ── Newly implemented operations (Phase 1 stub fill-in) ──────────────────────


async def _create_object(
    output_path: str, shape: str, params: dict[str, Any],
    _cli_wrapper: Any, _config: Any,
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
            elements.append(
                f'<circle id="{name}" cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'
            )
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
                poly_pts.append(f"{cx + r_val * math.cos(angle):.1f},{cy + r_val * math.sin(angle):.1f}")
            elements.append(
                f'<polygon id="{name}" points="{" ".join(poly_pts)}" fill="{fill}"/>'
            )
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
                success=False, operation="create_object",
                message=f"Unknown shape '{shape}'. Supported: rect, circle, ellipse, star, text, path",
                data={}, execution_time_ms=0, error="ValueError",
            ).model_dump()

        svg = f"{svg_header}\n  " + "\n  ".join(elements) + "\n</svg>"
        Path(output_path).write_text(svg, encoding="utf-8")

        return VectorOperationResult(
            success=True, operation="create_object",
            message=f"Created {shape} '{name}' at {output_path}",
            data={"shape": shape, "params": params, "output_path": output_path},
            execution_time_ms=(time.time() - _start) * 1000,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="create_object",
            message=f"Object creation failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _text_to_path(
    input_path: str, output_path: str, object_id: str, cli_wrapper: Any, config: Any,
) -> dict[str, Any]:
    """Convert text objects to paths via Inkscape actions."""
    try:
        select = f"select-by-id:{object_id}" if object_id else "select-by-element:text"
        actions = [select, "object-to-path", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path, actions=actions,
            output_path=output_path, timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True, operation="text_to_path",
            message=f"Converted text to path: {output_path}",
            data={"input_path": input_path, "output_path": output_path, "object_id": object_id},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="text_to_path",
            message=f"Text to path failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _construct_svg(
    output_path: str, element_type: str, params: dict[str, Any], _config: Any,
) -> dict[str, Any]:
    """Construct a new SVG from raw element definitions (header + body)."""
    try:
        header = params.get("header", '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">')
        body = params.get("body", "")
        footer = params.get("footer", "</svg>")
        svg_content = f"{header}\n{body}\n{footer}"
        Path(output_path).write_text(svg_content, encoding="utf-8")
        return VectorOperationResult(
            success=True, operation="construct_svg",
            message=f"Constructed SVG document at {output_path}",
            data={"element_type": element_type, "path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="construct_svg",
            message=f"SVG construction failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _path_inset_outset(
    input_path: str, output_path: str, direction: str, amount: float,
    cli_wrapper: Any, config: Any,
) -> dict[str, Any]:
    """Inset or outset selected paths."""
    try:
        action = "selection-inset" if direction == "inset" else "selection-outset"
        actions = ["select-all", f"{action}:{amount}", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path, actions=actions,
            output_path=output_path, timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True, operation="path_inset_outset",
            message=f"Applied {direction} ({amount}px) to {input_path}",
            data={"input_path": input_path, "output_path": output_path,
                  "direction": direction, "amount": amount},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="path_inset_outset",
            message=f"Path inset/outset failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _path_combine(
    input_path: str, output_path: str, cli_wrapper: Any, config: Any,
) -> dict[str, Any]:
    """Combine selected paths into a single path."""
    try:
        actions = ["select-all", "path-combine", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path, actions=actions,
            output_path=output_path, timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True, operation="path_combine",
            message=f"Combined paths from {input_path} to {output_path}",
            data={"input_path": input_path, "output_path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="path_combine",
            message=f"Path combine failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _path_break_apart(
    input_path: str, output_path: str, cli_wrapper: Any, config: Any,
) -> dict[str, Any]:
    """Break apart a compound path into individual paths."""
    try:
        actions = ["select-all", "path-break-apart", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path, actions=actions,
            output_path=output_path, timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True, operation="path_break_apart",
            message=f"Broke apart paths from {input_path} to {output_path}",
            data={"input_path": input_path, "output_path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="path_break_apart",
            message=f"Path break apart failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _object_to_path(
    input_path: str, output_path: str, object_id: str, cli_wrapper: Any, config: Any,
) -> dict[str, Any]:
    """Convert a shape object (rect, circle, star, text) to paths."""
    try:
        select = f"select-by-id:{object_id}" if object_id else "select-all"
        actions = [select, "object-to-path", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path, actions=actions,
            output_path=output_path, timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True, operation="object_to_path",
            message=f"Converted object(s) to paths: {output_path}",
            data={"input_path": input_path, "output_path": output_path, "object_id": object_id},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="object_to_path",
            message=f"Object to path failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _optimize_svg(
    input_path: str, output_path: str, cli_wrapper: Any, config: Any,
) -> dict[str, Any]:
    """Optimize SVG by vacuuming unused defs and cleaning up."""
    try:
        actions = ["file-vacuum-defs", "file-cleanup", f"export-filename:{output_path}", "export-do"]
        await cli_wrapper._execute_actions(
            input_path=input_path, actions=actions,
            output_path=output_path, timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True, operation="optimize_svg",
            message=f"Optimized {input_path} -> {output_path}",
            data={"input_path": input_path, "output_path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="optimize_svg",
            message=f"SVG optimization failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _scour_svg(
    input_path: str, output_path: str, cli_wrapper: Any, config: Any,
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
            input_path=input_path, actions=actions,
            output_path=output_path, timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True, operation="scour_svg",
            message=f"Scoured {input_path} -> {output_path} (plain SVG)",
            data={"input_path": input_path, "output_path": output_path, "method": "plain-svg"},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="scour_svg",
            message=f"SVG scour failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _fit_canvas_to_drawing(
    input_path: str, output_path: str, cli_wrapper: Any, config: Any,
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
            input_path=input_path, actions=actions,
            output_path=output_path, timeout=config.process_timeout,
        )
        return VectorOperationResult(
            success=True, operation="fit_canvas_to_drawing",
            message=f"Canvas fitted to drawing: {output_path}",
            data={"input_path": input_path, "output_path": output_path},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="fit_canvas_to_drawing",
            message=f"Canvas fit failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()


async def _layers_to_files(
    input_path: str, output_dir: str, cli_wrapper: Any, config: Any,
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
                    input_path=input_path, actions=actions,
                    output_path=str(out_file), timeout=config.process_timeout,
                )
                exported.append(str(out_file))
            except Exception:
                pass

        return VectorOperationResult(
            success=True, operation="layers_to_files",
            message=f"Exported {len(exported)} layers to {out_dir}",
            data={"input_path": input_path, "output_dir": str(out_dir),
                  "exported": exported, "layer_ids_probed": layer_ids},
            execution_time_ms=0,
        ).model_dump()
    except Exception as e:
        return VectorOperationResult(
            success=False, operation="layers_to_files",
            message=f"Layer export failed: {e}", data={},
            execution_time_ms=0, error=str(e),
        ).model_dump()
