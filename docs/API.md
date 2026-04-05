# API Reference

## Portmanteau Tools

### generate_svg

Generate SVG graphics from natural language descriptions.

**Parameters:**
- `description` (str): Natural language description of the desired SVG
- `style_preset` (str, optional): Style preset (geometric, organic, technical, heraldic, abstract). Default: "geometric"
- `dimensions` (str, optional): Output dimensions (e.g., "800x600"). Default: "800x600"
- `model` (str, optional): AI model to use. Default: "flux-dev"
- `quality` (str, optional): Quality level (draft, standard, high, ultra). Default: "standard"
- `reference_svgs` (List[str], optional): Paths to reference SVG files
- `post_processing` (List[str], optional): Post-processing operations to apply
- `max_iterations` (int, optional): Maximum refinement iterations. Default: 3

**Returns:**
```python
{
    "success": bool,
    "svg_path": str,
    "metadata": {
        "dimensions": str,
        "style_preset": str,
        "quality_level": str,
        "generation_time": float,
        "iterations": int
    },
    "quality_score": float
}
```

### inkscape_file

File operations and format management.

**Operations:**
- `load`: Load and validate SVG file
- `save`: Save SVG with specified format
- `convert`: Convert between vector formats
- `info`: Get file information and metadata
- `validate`: Validate SVG structure and compliance
- `list_formats`: List supported input/output formats

### inkscape_vector

Complete vector operations suite.

**Operations:**
- `construct_svg`: Build SVGs from text descriptions
- `apply_boolean`: Boolean operations on shapes
- `path_simplify`: Reduce path complexity
- `measure_object`: Query object dimensions
- `trace_image`: Convert raster to vector
- `export_dxf`: Export for CAD applications

### inkscape_analysis

Document and object analysis.

**Operations:**
- `quality`: Assess SVG quality metrics
- `statistics`: Comprehensive document statistics
- `validate`: SVG validation and compliance
- `objects`: List all objects in document
- `dimensions`: Get document dimensions
- `layers`: Analyze layer structure

### inkscape_system

System management and extension operations.

**Operations:**
- `status`: Server status and health information
- `diagnostics`: Detailed system diagnostics
- `version`: Inkscape and system version information
- `list_extensions`: Discover available extensions
- `execute_extension`: Run Inkscape extensions

### inkscape_transform

Geometric transformations.

**Operations:**
- `scale`: Scale objects by factor or dimensions
- `rotate`: Rotate objects by angle
- `translate`: Move objects by coordinates
- `skew`: Apply skew transformations
- `matrix`: Apply transformation matrix
- `reset`: Reset transformations to identity

### inkscape_color

Color adjustments and management.

**Operations:**
- `brightness_contrast`: Adjust brightness and contrast
- `hue_saturation`: Modify hue and saturation
- `levels`: Adjust tonal range
- `curves`: Apply tone curves
- `hsl_adjust`: Fine-tune HSL values
- `colorize`: Apply colorization effects
- `desaturate`: Convert to grayscale

### inkscape_filter

Filter and effect application.

**Operations:**
- `blur`: Apply blur effects
- `sharpen`: Sharpen image details
- `noise`: Add or reduce noise
- `emboss`: Apply emboss effects
- `edge_detect`: Detect and highlight edges
- `morphology`: Apply morphological operations

### inkscape_layer

Layer management operations.

**Operations:**
- `create`: Create new layers
- `delete`: Remove existing layers
- `duplicate`: Copy layers
- `merge`: Combine layers
- `flatten`: Merge all layers
- `reorder`: Change layer stacking order
- `isolate`: Show only selected layer

### inkscape_batch

Batch processing operations.

**Operations:**
- `resize`: Resize multiple files
- `convert`: Batch format conversion
- `watermark`: Apply watermarks
- `optimize`: Batch optimization
- `rename`: Bulk file renaming
- `process`: Apply operations to multiple files
- `validate`: Batch validation

## Extension API

### list_extensions

Discover all available Inkscape extensions.

**Returns:**
```python
[
    {
        "id": str,
        "name": str,
        "category": str,
        "description": str,
        "parameters": [
            {
                "name": str,
                "type": str,
                "required": bool,
                "description": str
            }
        ]
    }
]
```

### execute_extension

Execute an Inkscape extension with parameters.

**Parameters:**
- `extension_id` (str): Extension identifier
- `extension_params` (dict): Extension-specific parameters

**Returns:**
```python
{
    "success": bool,
    "output_path": str,
    "execution_time": float,
    "extension_info": {
        "id": str,
        "name": str,
        "version": str
    }
}
```

## Error Handling

All operations return structured error responses:

```python
{
    "success": false,
    "error": {
        "type": str,  # "validation", "execution", "timeout", "resource"
        "message": str,
        "details": dict,
        "suggestion": str  # Actionable fix suggestion
    }
}
```

## Common Parameters

Most operations accept these standard parameters:

- `input_path` (str): Path to input SVG file
- `output_path` (str, optional): Path for output file
- `object_ids` (List[str], optional): Specific object IDs to operate on
- `options` (dict, optional): Operation-specific options

## Authentication

No authentication required. Access control is managed through:
- File system permissions
- Configurable allowed directories
- Process isolation and resource limits
