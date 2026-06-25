# Tool Reference

17 MCP tools across 9 portmanteau groups, 60+ operations total.

## inkscape_file — File Operations

| Operation | Description |
|-----------|-------------|
| `load` | Load SVG into Inkscape |
| `save` | Save current document |
| `convert` | Convert between formats (SVG, PDF, EPS, PNG) |
| `info` | Get document metadata |
| `validate` | Validate SVG structure |
| `list_formats` | List supported I/O formats |

## inkscape_vector — Vector Operations

| Operation | Description |
|-----------|-------------|
| `create_object` | Create primitives: rect, circle, star, text, path |
| `inspect` | Read object properties (fill, stroke, opacity, transform) |
| `text_to_path` | Convert text → editable paths |
| `text_set_content` | Change text element content |
| `text_set_style` | Set font, size, weight, fill, anchor |
| `text_list_fonts` | List available system fonts |
| `apply_boolean` | Union, difference, intersection, exclusion |
| `list_lpes` | List available Live Path Effects |
| `apply_lpe` | Apply an LPE with parameters |
| `path_simplify` | Reduce path nodes |
| `path_clean` | Remove unused defs and metadata |
| `path_combine` | Combine paths into one |
| `path_break_apart` | Break compound path into individuals |
| `path_inset_outset` | Inset or outset path boundary |
| `object_to_path` | Convert shapes to paths |
| `object_raise` | Raise Z-order |
| `object_lower` | Lower Z-order |
| `measure_object` | Get object bounding box |
| `query_document` | Get document stats + object list |
| `count_nodes` | Count path nodes |
| `render_preview` | Export PNG at specified DPI |
| `trace_image` | Bitmap → vector (potrace) |
| `export_dxf` | Export to CAD format |
| `fit_canvas_to_drawing` | Resize canvas to content |
| `optimize_svg` | Vacuum defs + cleanup |
| `scour_svg` | Aggressive SVG cleanup |
| `set_document_units` | Normalize coordinate system |

## inkscape_layers — Layer Management

| Operation | Description |
|-----------|-------------|
| `list` | List all layers |
| `get` | Get layer by ID |
| `create` | Add new layer |
| `rename` | Rename layer |
| `hide` / `show` | Toggle visibility |
| `lock` / `unlock` | Toggle edit protection |
| `reorder` | Move layer in stack |

## inkscape_animation — SVG Animation

| Operation | Description |
|-----------|-------------|
| `list_presets` | Discover presets |
| `apply_preset` | Generate bounce, fade, slide, rotate, pulse, shake |
| `animate_element` | SMIL attribute animation |
| `animate_transform` | Rotate/translate/scale via animateTransform |
| `animate_motion` | Path-following animation |
| `animate_color` | Color cycling |
| `css_animation` | CSS @keyframes generation |

## inkscape_analysis — Document Analysis

| Operation | Description |
|-----------|-------------|
| `statistics` | Dimensions, file size, object count |
| `validate` | SVG structure check |
| `dimensions` | Width, height, aspect ratio |
| `objects` | List all objects with IDs |
| `structure` | Object hierarchy |
| `quality` | Heuristics and suggestions |

## inkscape_system — System

| Operation | Description |
|-----------|-------------|
| `status` | Server + Inkscape status |
| `diagnostics` | Configuration checks |
| `execution_mode` | Hands-in vs hands-off guidance |
| `hands_in_command` | Send --actions to running Inkscape GUI |
| `version` | Server version info |
| `config` | View current config |
| `list_extensions` | Scan for .inx extension files |

## inkscape_render — Agent Vision

| Operation | Description |
|-----------|-------------|
| `export_preview` | PNG preview for vision loops |
| `export_multi_dpi` | Batch DPI export |
| `get_document_summary` | Text summary of document |

## inkscape_validation — SVG Quality

| Operation | Description |
|-----------|-------------|
| `validate_svg` | Full SVG validation |
| `check_viewbox` | ViewBox sanity check |
| `check_stroke_fill` | Stroke/fill consistency |
| `check_size_limits` | Size constraint validation |
| `audit_web_svg` | Web SVG best practices |

## inkscape_fleet / fab_art / sim_art — Cross-MCP

Fleet handoffs to GIMP, Blender, Unity, Resonite. DXF/laser fab, icon sheets, SVG refine loop.
