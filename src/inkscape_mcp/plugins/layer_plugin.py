"""
Layer Management Plugin for GIMP MCP

Provides tools for creating, managing, and manipulating layers in GIMP.
"""
from typing import Dict, Any, List, Optional, Union
import logging

from fastmcp import tool

from .base_plugin import GimpToolPlugin
from ..cli_wrapper import GimpCliWrapper
from ..config import InkscapeConfig

class LayerPlugin(GimpToolPlugin):
    """Layer management tools for GIMP."""
    
    PLUGIN_NAME = "layer_tools"
    PLUGIN_DESCRIPTION = "Comprehensive layer management tools for GIMP"
    
    def __init__(self, cli_wrapper: InkscapeCliWrapper, config: InkscapeConfig):
        super().__init__(cli_wrapper, config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def register_tools(self, app) -> None:
        """Register all layer tools with the FastMCP app."""
        
        @app.tool()
        async def create_layer(
            image_path: str,
            layer_name: str,
            layer_type: str = "raster",
            width: Optional[int] = None,
            height: Optional[int] = None,
            opacity: float = 1.0,
            mode: str = "normal",
            fill_type: str = "transparent",
            fill_color: str = "#000000"
        ) -> Dict[str, Any]:
            """
            Create a new layer in the specified image.
            
            Args:
                image_path: Path to the GIMP image file
                layer_name: Name for the new layer
                layer_type: Type of layer to create (raster, text, group, etc.)
                width: Width of the new layer (defaults to image width)
                height: Height of the new layer (defaults to image height)
                opacity: Layer opacity (0.0 to 1.0)
                mode: Layer blend mode (normal, multiply, screen, etc.)
                fill_type: Initial fill type (transparent, foreground, background, color)
                fill_color: Fill color as hex string (used if fill_type is 'color')
                
            Returns:
                Dictionary with layer creation status and details
            """
            try:
                # Input validation
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                valid_types = ["raster", "text", "group", "adjustment"]
                if layer_type not in valid_types:
                    return self.create_error_response(
                        f"Invalid layer type. Must be one of: {', '.join(valid_types)}"
                    )
                
                if not (0.0 <= opacity <= 1.0):
                    return self.create_error_response("Opacity must be between 0.0 and 1.0")
                
                valid_fill_types = ["transparent", "foreground", "background", "color"]
                if fill_type not in valid_fill_types:
                    return self.create_error_response(
                        f"Invalid fill type. Must be one of: {', '.join(valid_fill_types)}"
                    )
                
                if fill_type == "color" and not self.validate_color(fill_color):
                    return self.create_error_response("Invalid fill color format")
                
                # Build Script-Fu command
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (drawable (car (gimp-image-get-active-drawable image)))
                    (width (if (or (null? width) (<= width 0)) (car (gimp-image-width image)) width))
                    (height (if (or (null? height) (<= height 0)) (car (gimp-image-height image)) height))
                    (new-layer (car (gimp-layer-new image width height RGBA-IMAGE "{layer_name}" {opacity} {mode})))
                )
                    (gimp-image-insert-layer image new-layer 0 -1)
                    {fill_command}
                    (gimp-displays-flush)
                    (gimp-file-save RUN-NONINTERACTIVE image new-layer "{image_path}" "{image_path}")
                    (gimp-image-delete image)
                    (list
                        (string-append "{layer_name}")
                        (number->string (car (gimp-image-get-layer-position image new-layer)))
                    )
                ))
                """
                
                # Handle different fill types
                if fill_type == "transparent":
                    fill_command = "(gimp-drawable-fill new-layer TRANSPARENT-FILL)"
                elif fill_type == "foreground":
                    fill_command = "(gimp-drawable-fill new-layer FOREGROUND-FILL)"
                elif fill_type == "background":
                    fill_command = "(gimp-drawable-fill new-layer BACKGROUND-FILL)"
                else:  # color
                    # Convert hex to RGB
                    r, g, b = tuple(int(fill_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                    fill_command = f"""
                    (gimp-context-set-foreground (list {r} {g} {b}))
                    (gimp-drawable-fill new-layer FOREGROUND-FILL)
                    """
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    layer_name=layer_name,
                    width=width or -1,
                    height=height or -1,
                    opacity=opacity,
                    mode=mode.upper().replace('-', '_'),
                    fill_command=fill_command
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to create layer: {result}")
                
                # Extract layer info from result
                result_parts = result.strip().split('\n')
                if len(result_parts) >= 2:
                    layer_name = result_parts[0].strip('() \"')
                    layer_index = int(result_parts[1].strip('() '))
                    
                    return self.create_success_response(
                        data={
                            "layer_name": layer_name,
                            "layer_index": layer_index,
                            "image_path": image_path
                        },
                        message=f"Successfully created layer '{layer_name}'"
                    )
                
                return self.create_error_response("Unexpected response from GIMP")
                
            except Exception as e:
                self.logger.error(f"Error creating layer: {e}", exc_info=True)
                return self.create_error_response(f"Failed to create layer: {str(e)}")
        
        @app.tool()
        async def merge_layers(
            image_path: str,
            layer_indices: List[int],
            merge_type: str = "flatten",
            new_name: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Merge multiple layers into a single layer.
            
            Args:
                image_path: Path to the GIMP image file
                layer_indices: List of layer indices to merge
                merge_type: Type of merge ('flatten', 'visible', 'linked', 'layer_group')
                new_name: Optional name for the merged layer
                
            Returns:
                Dictionary with merge status and details
            """
            try:
                # Input validation
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                if not layer_indices:
                    return self.create_error_response("No layer indices provided")
                
                valid_merge_types = ["flatten", "visible", "linked", "layer_group"]
                if merge_type not in valid_merge_types:
                    return self.create_error_response(
                        f"Invalid merge type. Must be one of: {', '.join(valid_merge_types)}"
                    )
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (layers-to-merge '({layer_indices_list}))
                    (merged-layer)
                )
                    ; Set active layers
                    {set_active_layers}
                    
                    ; Perform the merge
                    (set! merged-layer 
                        (cond
                            ((string=? "{merge_type}" "flatten") 
                             (car (gimp-image-flatten image)))
                            ((string=? "{merge_type}" "visible")
                             (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE)))
                            ((string=? "{merge_type}" "linked")
                             (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE)))
                            ((string=? "{merge_type}" "layer_group")
                             (car (gimp-image-merge-layer-group (aref layer-array (car layers-to-merge)))))
                            (else (aref layer-array (car layers-to-merge)))
                        )
                    )
                    
                    ; Rename if specified
                    {rename_command}
                    
                    ; Save and clean up
                    (gimp-displays-flush)
                    (gimp-file-save RUN-NONINTERACTIVE image merged-layer "{image_path}" "{image_path}")
                    (gimp-image-delete image)
                    
                    (list 
                        (car (gimp-item-get-name merged-layer))
                        (number->string (car (gimp-image-get-layer-position image merged-layer)))
                    )
                ))
                """
                
                # Prepare layer indices for Scheme list
                indices_str = " ".join(str(i) for i in layer_indices)
                
                # Set active layers
                set_active_layers = ""
                for idx in layer_indices:
                    set_active_layers += f"(gimp-image-set-active-layer image (aref layer-array {idx}))\n"
                
                # Handle renaming if specified
                if new_name:
                    rename_command = f'(gimp-item-set-name merged-layer "{new_name}")'
                else:
                    rename_command = '; No rename needed'
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    layer_indices_list=indices_str,
                    merge_type=merge_type,
                    set_active_layers=set_active_layers,
                    rename_command=rename_command
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to merge layers: {result}")
                
                # Extract layer info from result
                result_parts = result.strip().split('\n')
                if len(result_parts) >= 2:
                    layer_name = result_parts[0].strip('() \"')
                    layer_index = int(result_parts[1].strip('() '))
                    
                    return self.create_success_response(
                        data={
                            "merged_layer_name": layer_name,
                            "merged_layer_index": layer_index,
                            "image_path": image_path
                        },
                        message=f"Successfully merged layers into '{layer_name}'"
                    )
                
                return self.create_error_response("Unexpected response from GIMP")
                
            except Exception as e:
                self.logger.error(f"Error merging layers: {e}", exc_info=True)
                return self.create_error_response(f"Failed to merge layers: {str(e)}")
        
        @app.tool(
            name="reorder_layers",
            description="Change the stacking order of layers in the image.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Path to the GIMP image file",
                    "required": True,
                    "format": "file"
                },
                "layer_order": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                    "description": "New order of layer indices (0-based, from bottom to top)",
                    "required": True
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "reordered": {"type": "boolean"},
                    "image_path": {"type": "string"},
                    "new_order": {"type": "array", "items": {"type": "integer"}}
                },
                "description": "Result of the reorder operation"
            },
            examples=[
                {
                    "description": "Reverse layer order",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_order": [3, 2, 1, 0]
                    }
                }
            ]
        )
        async def reorder_layers(
            image_path: str,
            layer_order: List[int]
        ) -> Dict[str, Any]:
            """
            Change the stacking order of layers in the image.
            
            This tool allows reordering layers by specifying their new indices.
            The layer_order list should contain all layer indices in their desired
            new order (from bottom to top).
            
            Args:
                image_path: Path to the GIMP image file
                layer_order: New order of layer indices (0-based, from bottom to top)
                
            Returns:
                Dictionary containing:
                - success: Boolean indicating if the operation was successful
                - reordered: True if layers were actually reordered
                - image_path: Path to the modified image
                - new_order: The actual new order of layer indices
                
            Raises:
                ValueError: If input validation fails
                RuntimeError: If the reorder operation fails
            """
            try:
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                if not layer_order:
                    return self.create_error_response("No layer order specified")
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (reordered FALSE)
                )
                    ; Validate layer order
                    (when (and (= (length '{layer_order}) num-layers)
                               (apply distinct? (cons = (sort {layer_order} <))))
                        
                        ; Reorder layers
                        (let loop ((i 0))
                            (when (< i num-layers)
                                (let* ((new-pos (list-ref '{layer_order} i))
                                       (current-pos (gimp-image-get-layer-position image (vector-ref layer-array i))))
                                    (when (not (= new-pos current-pos))
                                        (gimp-image-reorder-item image (vector-ref layer-array i) -1 new-pos)
                                        (set! reordered TRUE)
                                    )
                                )
                                (loop (+ i 1))
                            )
                        )
                    )
                    
                    (gimp-file-save RUN-NONINTERACTIVE image (car (gimp-image-get-active-drawable image)) "{image_path}" "{image_path}")
                    (gimp-image-delete image)
                    (list
                        (if reordered "TRUE" "FALSE")
                        (string-join (map number->string (list {layer_order_str})) " ")
                    )
                ))
                """
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    layer_order=layer_order,
                    layer_order_str=' '.join(map(str, layer_order))
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to reorder layers: {result}")
                
                result_parts = result.strip().split('\n')
                reordered = result_parts[0].strip('()\\\"') == "TRUE"
                new_order = list(map(int, result_parts[1].strip('() ').split()))
                
                return self.create_success_response(
                    data={
                        "reordered": reordered,
                        "image_path": image_path,
                        "new_order": new_order
                    },
                    message="Layers reordered successfully" if reordered else "No reordering needed"
                )
                
            except Exception as e:
                self.logger.error(f"Error reordering layers: {e}", exc_info=True)
                return self.create_error_response(f"Failed to reorder layers: {str(e)}")
                
        @app.tool(
            name="set_layer_visibility",
            description="Show or hide specific layers in the image.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Path to the GIMP image file",
                    "required": True,
                    "format": "file"
                },
                "layer_indices": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                    "description": "Indices of layers to modify",
                    "required": True
                },
                "visible": {
                    "type": "boolean",
                    "description": "Whether to show (True) or hide (False) the layers",
                    "default": True
                },
                "affect_others": {
                    "type": "string",
                    "enum": ["none", "show", "hide", "invert"],
                    "description": "What to do with layers not in layer_indices",
                    "default": "none"
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "layers_modified": {"type": "integer"},
                    "image_path": {"type": "string"},
                    "visibility": {"type": "object", "additionalProperties": {"type": "boolean"}}
                },
                "description": "Result of the visibility change operation"
            },
            examples=[
                {
                    "description": "Show only specific layers",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [0, 2],
                        "visible": True,
                        "affect_others": "hide"
                    }
                }
            ]
        )
        async def set_layer_visibility(
            image_path: str,
            layer_indices: List[int],
            visible: bool = True,
            affect_others: str = "none"
        ) -> Dict[str, Any]:
            """
            Show or hide specific layers in the image.
            
            This tool allows controlling the visibility of multiple layers at once.
            You can also specify what to do with layers not in the provided indices.
            
            Args:
                image_path: Path to the GIMP image file
                layer_indices: Indices of layers to modify (0-based)
                visible: Whether to show (True) or hide (False) the specified layers
                affect_others: What to do with layers not in layer_indices:
                    - "none": Leave other layers unchanged (default)
                    - "show": Show all other layers
                    - "hide": Hide all other layers
                    - "invert": Toggle visibility of other layers
                
            Returns:
                Dictionary containing:
                - success: Boolean indicating if the operation was successful
                - layers_modified: Number of layers that were modified
                - image_path: Path to the modified image
                - visibility: Dict mapping layer indices to their new visibility state
                
            Raises:
                ValueError: If input validation fails
                RuntimeError: If the visibility change operation fails
            """
            try:
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                if not layer_indices:
                    return self.create_error_response("No layer indices provided")
                
                valid_affect = ["none", "show", "hide", "invert"]
                if affect_others not in valid_affect:
                    return self.create_error_response(
                        f"Invalid affect_others value. Must be one of: {', '.join(valid_affect)}"
                    )
                
                # Convert layer indices to a set for faster lookups
                target_indices = set(layer_indices)
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (modified 0)
                    (visibility '())
                )
                    ; Process each layer
                    (let loop ((i 0))
                        (when (< i num-layers)
                            (let* ((layer (vector-ref layer-array i))
                                   (is-target (member i '{target_indices_list}))
                                   (new-visible (cond
                                       (is-target {visible})
                                       ((string=? "{affect_others}" "show") TRUE)
                                       ((string=? "{affect_others}" "hide") FALSE)
                                       ((string=? "{affect_others}" "invert") (not (car (gimp-drawable-get-visible layer))))
                                       (else (car (gimp-drawable-get-visible layer)))
                                   )))
                                
                                ; Only update if visibility changes
                                (when (not (eq? new-visible (car (gimp-drawable-get-visible layer))))
                                    (gimp-drawable-set-visible layer new-visible)
                                    (set! modified (+ modified 1))
                                )
                                
                                ; Record the new visibility state
                                (set! visibility (cons (cons i new-visible) visibility))
                                
                                (loop (+ i 1))
                            )
                        )
                    )
                    
                    ; Save and clean up
                    (gimp-displays-flush)
                    (gimp-file-save RUN-NONINTERACTIVE image (car (gimp-image-get-active-drawable image)) "{image_path}" "{image_path}")
                    (gimp-image-delete image)
                    
                    ; Return the list of modified layers and their visibility
                    (cons
                        (number->string modified)
                        (map (lambda (pair) 
                            (string-append 
                                (number->string (car pair)) 
                                ":" 
                                (if (cdr pair) "true" "false")
                            )
                        ) visibility)
                    )
                ))
                """
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    target_indices_list=' '.join(map(str, layer_indices)),
                    visible="TRUE" if visible else "FALSE",
                    affect_others=affect_others
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to set layer visibility: {result}")
                
                result_parts = result.strip().split('\n')
                if not result_parts:
                    return self.create_error_response("Unexpected response from GIMP")
                
                modified_count = int(result_parts[0].strip('() '))
                
                # Parse visibility dictionary
                visibility = {}
                for part in result_parts[1:]:
                    if ':' in part:
                        idx_str, vis_str = part.strip('() ').split(':', 1)
                        visibility[int(idx_str)] = vis_str.lower() == 'true'
                
                return self.create_success_response(
                    data={
                        "layers_modified": modified_count,
                        "image_path": image_path,
                        "visibility": visibility
                    },
                    message=f"Updated visibility for {modified_count} layers"
                )
                
            except Exception as e:
                self.logger.error(f"Error setting layer visibility: {e}", exc_info=True)
                return self.create_error_response(f"Failed to set layer visibility: {str(e)}")
                
        @app.tool(
            name="create_layer_mask",
            description="Create a mask for a layer with various initialization options.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Path to the GIMP image file",
                    "required": True,
                    "format": "file"
                },
                "layer_index": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Index of the layer to add a mask to",
                    "required": True
                },
                "mask_type": {
                    "type": "string",
                    "enum": ["white", "black", "alpha", "selection", "grayscale", "transfer_alpha", "color"],
                    "default": "white",
                    "description": "Type of mask to create"
                },
                "color": {
                    "type": "string",
                    "description": "Color for 'color' mask type (hex format, e.g., '#RRGGBB' or '#RRGGBBAA')",
                    "default": "#000000"
                },
                "invert": {
                    "type": "boolean",
                    "description": "Whether to invert the mask",
                    "default": False
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "mask_created": {"type": "boolean"},
                    "image_path": {"type": "string"},
                    "layer_index": {"type": "integer"},
                    "mask_type": {"type": "string"}
                },
                "description": "Result of the mask creation operation"
            },
            examples=[
                {
                    "description": "Add a white mask to a layer",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_index": 0,
                        "mask_type": "white"
                    }
                },
                {
                    "description": "Add a grayscale mask from selection",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_index": 1,
                        "mask_type": "selection",
                        "invert": True
                    }
                }
            ]
        )
        async def create_layer_mask(
            image_path: str,
            layer_index: int,
            mask_type: str = "white",
            color: str = "#000000",
            invert: bool = False
        ) -> Dict[str, Any]:
            """
            Create a mask for a layer with various initialization options.
            
            This tool allows creating different types of masks for a layer:
            - white: Fully white (opaque) mask
            - black: Fully black (transparent) mask
            - alpha: Mask based on the layer's alpha channel
            - selection: Mask from the current selection
            - grayscale: Grayscale copy of the layer as mask
            - transfer_alpha: Transfer layer's alpha channel to mask
            - color: Mask from a specific color
            
            Args:
                image_path: Path to the GIMP image file
                layer_index: Index of the layer to add a mask to (0-based)
                mask_type: Type of mask to create
                color: Color for 'color' mask type (ignored for other types)
                invert: Whether to invert the mask
                
            Returns:
                Dictionary containing:
                - success: Boolean indicating if the operation was successful
                - mask_created: True if a new mask was created
                - image_path: Path to the modified image
                - layer_index: Index of the layer that got the mask
                - mask_type: The type of mask that was created
                
            Raises:
                ValueError: If input validation fails
                RuntimeError: If the mask creation fails
            """
            try:
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                valid_mask_types = ["white", "black", "alpha", "selection", "grayscale", "transfer_alpha", "color"]
                if mask_type not in valid_mask_types:
                    return self.create_error_response(
                        f"Invalid mask type. Must be one of: {', '.join(valid_mask_types)}"
                    )
                
                if mask_type == "color" and not self.validate_color(color, allow_alpha=True):
                    return self.create_error_response("Invalid color format. Use hex format like '#RRGGBB' or '#RRGGBBAA'")
                
                # Convert color to RGBA if needed
                color_values = [0, 0, 0, 255]  # Default black
                if mask_type == "color" and color.startswith('#'):
                    hex_color = color.lstrip('#')
                    if len(hex_color) == 3:  # Short format (#RGB)
                        color_values = [int(hex_color[i] * 2, 16) for i in range(3)] + [255]
                    elif len(hex_color) == 4:  # Short format with alpha (#RGBA)
                        color_values = [int(hex_color[i] * 2, 16) for i in range(3)] + [int(hex_color[3] * 2, 16)]
                    elif len(hex_color) == 6:  # Full format (#RRGGBB)
                        color_values = [int(hex_color[i:i+2], 16) for i in range(0, 6, 2)] + [255]
                    else:  # Full format with alpha (#RRGGBBAA)
                        color_values = [int(hex_color[i:i+2], 16) for i in range(0, 8, 2)]
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (layer (if (and (>= {layer_index} 0) (< {layer_index} num-layers))
                             (vector-ref layer-array {layer_index})
                             #f))
                    (mask-created FALSE)
                )
                    (when layer
                        ; If layer already has a mask, remove it first
                        (let ((current-mask (car (gimp-layer-get-mask layer))))
                            (when (not (null? current-mask))
                                (gimp-layer-remove-mask layer MASK-APPLY)
                            )
                        )
                        
                        ; Create the appropriate type of mask
                        (let ((mask (cond
                            ((string-ci=? "{mask_type}" "white")
                                (car (gimp-layer-create-mask layer ADD-WHITE-MASK)))
                            ((string-ci=? "{mask_type}" "black")
                                (car (gimp-layer-create-mask layer ADD-BLACK-MASK)))
                            ((string-ci=? "{mask_type}" "alpha")
                                (car (gimp-layer-create-mask layer ADD-ALPHA-MASK)))
                            ((string-ci=? "{mask_type}" "selection")
                                (car (gimp-layer-create-mask layer ADD-SELECTION-MASK)))
                            ((string-ci=? "{mask_type}" "grayscale")
                                (car (gimp-layer-create-mask layer ADD-COPY-MASK)))
                            ((string-ci=? "{mask_type}" "transfer_alpha")
                                (car (gimp-layer-create-mask layer ADD-ALPHA-TRANSFER-MASK)))
                            ((string-ci=? "{mask_type}" "color")
                                (let ((mask (car (gimp-layer-create-mask layer ADD-BLACK-MASK))))
                                    (gimp-context-set-foreground (list {r} {g} {b} {a}))
                                    (gimp-edit-fill mask FOREGROUND-FILL)
                                    mask
                                ))
                            (else (car (gimp-layer-create-mask layer ADD-WHITE-MASK)))
                        )))
                            
                            ; Add the mask to the layer
                            (when mask
                                (gimp-layer-add-mask layer mask)
                                (set! mask-created TRUE)
                                
                                ; Invert if requested
                                (when {invert}
                                    (gimp-invert mask)
                                )
                            )
                        )
                        
                        ; Save and clean up
                        (gimp-displays-flush)
                        (gimp-file-save RUN-NONINTERACTIVE image (car (gimp-image-get-active-drawable image)) "{image_path}" "{image_path}")
                    )
                    
                    (gimp-image-delete image)
                    (if layer (list "TRUE" "{mask_type}") (list "FALSE" "Invalid layer index"))
                ))
                """
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\\\', '\\\\\\\\'),
                    layer_index=layer_index,
                    mask_type=mask_type.lower(),
                    r=color_values[0],
                    g=color_values[1],
                    b=color_values[2],
                    a=color_values[3],
                    invert="TRUE" if invert else "FALSE"
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to create layer mask: {result}")
                
                result_parts = result.strip().split('\n')
                if len(result_parts) < 2:
                    return self.create_error_response("Unexpected response from GIMP")
                
                success = result_parts[0].strip('()\\\"') == "TRUE"
                mask_type_used = result_parts[1].strip('()\\\"')
                
                if not success:
                    return self.create_error_response(f"Failed to create mask: {mask_type_used}")
                
                return self.create_success_response(
                    data={
                        "mask_created": True,
                        "image_path": image_path,
                        "layer_index": layer_index,
                        "mask_type": mask_type_used
                    },
                    message=f"Successfully created {mask_type_used} mask for layer {layer_index}"
                )
                
            except Exception as e:
                self.logger.error(f"Error creating layer mask: {e}", exc_info=True)
                return self.create_error_response(f"Failed to create layer mask: {str(e)}")
                
        @app.tool(
            name="toggle_layer_visibility",
            description="Toggle visibility of specified layers in the image.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Path to the GIMP image file",
                    "required": True,
                    "format": "file"
                },
                "layer_indices": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                    "description": "Indices of layers to toggle visibility",
                    "required": True
                },
                "affect_others": {
                    "type": "string",
                    "enum": ["none", "show", "hide", "toggle"],
                    "description": "What to do with layers not in layer_indices",
                    "default": "none"
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "layers_modified": {"type": "integer"},
                    "image_path": {"type": "string"},
                    "visibility": {"type": "object", "additionalProperties": {"type": "boolean"}}
                },
                "description": "Result of the visibility toggle operation"
            },
            examples=[
                {
                    "description": "Toggle visibility of specific layers",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [0, 2]
                    }
                },
                {
                    "description": "Show only specified layers and hide others",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [1],
                        "affect_others": "hide"
                    }
                }
            ]
        )
        async def toggle_layer_visibility(
            image_path: str,
            layer_indices: List[int],
            affect_others: str = "none"
        ) -> Dict[str, Any]:
            """
            Toggle visibility of specified layers in the image.
            
            This tool allows toggling the visibility of multiple layers at once.
            You can also specify what to do with layers not in the provided indices.
            
            Args:
                image_path: Path to the GIMP image file
                layer_indices: Indices of layers to toggle visibility (0-based)
                affect_others: What to do with layers not in layer_indices:
                    - "none": Leave other layers unchanged (default)
                    - "show": Show all other layers
                    - "hide": Hide all other layers
                    - "toggle": Toggle visibility of other layers
                
            Returns:
                Dictionary containing:
                - success: Boolean indicating if the operation was successful
                - layers_modified: Number of layers that were modified
                - image_path: Path to the modified image
                - visibility: Dict mapping layer indices to their new visibility state
                
            Raises:
                ValueError: If input validation fails
                RuntimeError: If the visibility toggle operation fails
            """
            try:
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                if not layer_indices:
                    return self.create_error_response("No layer indices provided")
                
                valid_affect = ["none", "show", "hide", "toggle"]
                if affect_others not in valid_affect:
                    return self.create_error_response(
                        f"Invalid affect_others value. Must be one of: {', '.join(valid_affect)}"
                    )
                
                # Convert layer indices to a set for faster lookups
                target_indices = set(layer_indices)
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (modified 0)
                    (visibility '())
                )
                    ; Process each layer
                    (let loop ((i 0))
                        (when (< i num-layers)
                            (let* ((layer (vector-ref layer-array i))
                                   (is-target (member i '{target_indices_list}))
                                   (current-visible (car (gimp-drawable-get-visible layer)))
                                   (new-visible (cond
                                       (is-target (not current-visible))
                                       ((string=? "{affect_others}" "show") TRUE)
                                       ((string=? "{affect_others}" "hide") FALSE)
                                       ((string=? "{affect_others}" "toggle") (not current-visible))
                                       (else current-visible)
                                   )))
                                
                                ; Only update if visibility changes
                                (when (not (eq? new-visible current-visible))
                                    (gimp-drawable-set-visible layer new-visible)
                                    (set! modified (+ modified 1))
                                )
                                
                                ; Record the new visibility state
                                (set! visibility (cons (cons i new-visible) visibility))
                                
                                (loop (+ i 1))
                            )
                        )
                    )
                    
                    ; Save and clean up
                    (gimp-displays-flush)
                    (gimp-file-save RUN-NONINTERACTIVE image (car (gimp-image-get-active-drawable image)) "{image_path}" "{image_path}")
                    (gimp-image-delete image)
                    
                    ; Return the list of modified layers and their visibility
                    (cons
                        (number->string modified)
                        (map (lambda (pair) 
                            (string-append 
                                (number->string (car pair)) 
                                ":" 
                                (if (cdr pair) "true" "false")
                            )
                        ) visibility)
                    )
                ))
                """
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    target_indices_list=' '.join(map(str, layer_indices)),
                    affect_others=affect_others
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to toggle layer visibility: {result}")
                
                result_parts = result.strip().split('\n')
                if not result_parts:
                    return self.create_error_response("Unexpected response from GIMP")
                
                modified_count = int(result_parts[0].strip('() '))
                
                # Parse visibility dictionary
                visibility = {}
                for part in result_parts[1:]:
                    if ':' in part:
                        idx_str, vis_str = part.strip('() ').split(':', 1)
                        visibility[int(idx_str)] = vis_str.lower() == 'true'
                
                return self.create_success_response(
                    data={
                        "layers_modified": modified_count,
                        "image_path": image_path,
                        "visibility": visibility
                    },
                    message=f"Toggled visibility for {modified_count} layers"
                )
                
            except Exception as e:
                self.logger.error(f"Error toggling layer visibility: {e}", exc_info=True)
                return self.create_error_response(f"Failed to toggle layer visibility: {str(e)}")
                
        @app.tool(
            name="set_layer_opacity",
            description="Set the opacity of one or more layers in the image.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Path to the GIMP image file",
                    "required": True,
                    "format": "file"
                },
                "layer_indices": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                    "description": "Indices of layers to modify",
                    "required": True
                },
                "opacity": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Opacity value (0-100)",
                    "required": True
                },
                "affect_others": {
                    "type": "boolean",
                    "description": "Whether to apply the opacity to all other layers",
                    "default": False
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "layers_modified": {"type": "integer"},
                    "image_path": {"type": "string"},
                    "opacity": {"type": "number"}
                },
                "description": "Result of the opacity change operation"
            },
            examples=[
                {
                    "description": "Set opacity of specific layers",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [0, 2],
                        "opacity": 50
                    }
                },
                {
                    "description": "Set opacity of all layers",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [0],
                        "opacity": 75,
                        "affect_others": True
                    }
                }
            ]
        )
        async def set_layer_opacity(
            image_path: str,
            layer_indices: List[int],
            opacity: float,
            affect_others: bool = False
        ) -> Dict[str, Any]:
            """
            Set the opacity of one or more layers in the image.
            
            This tool allows setting the opacity of multiple layers at once.
            The opacity value should be between 0 (transparent) and 100 (opaque).
            
            Args:
                image_path: Path to the GIMP image file
                layer_indices: Indices of layers to modify (0-based)
                opacity: Opacity value (0-100)
                affect_others: If True, applies the opacity to all layers in the image
                              regardless of layer_indices
                
            Returns:
                Dictionary containing:
                - success: Boolean indicating if the operation was successful
                - layers_modified: Number of layers that were modified
                - image_path: Path to the modified image
                - opacity: The opacity value that was set
                
            Raises:
                ValueError: If input validation fails
                RuntimeError: If the opacity change operation fails
            """
            try:
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                if not layer_indices and not affect_others:
                    return self.create_error_response("No layer indices provided and affect_others is False")
                
                if not (0 <= opacity <= 100):
                    return self.create_error_response("Opacity must be between 0 and 100")
                
                # Convert opacity to 0-255 range for GIMP
                gimp_opacity = int((opacity / 100.0) * 255)
                if gimp_opacity < 0:
                    gimp_opacity = 0
                elif gimp_opacity > 255:
                    gimp_opacity = 255
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (modified 0)
                    (target-indices '{target_indices_list})
                )
                    ; Process each layer
                    (let loop ((i 0))
                        (when (< i num-layers)
                            (let ((layer (vector-ref layer-array i)))
                                (when (or {apply_all} (member i target-indices))
                                    (gimp-layer-set-opacity layer {opacity})
                                    (set! modified (+ modified 1))
                                )
                                (loop (+ i 1))
                            )
                        )
                    )
                    
                    ; Save and clean up
                    (gimp-displays-flush)
                    (gimp-file-save RUN-NONINTERACTIVE image (car (gimp-image-get-active-drawable image)) "{image_path}" "{image_path}")
                    (gimp-image-delete image)
                    
                    (number->string modified)
                )
                """
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    target_indices_list=' '.join(map(str, layer_indices)) if layer_indices else "0",
                    apply_all="#t" if affect_others else "#f",
                    opacity=gimp_opacity
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to set layer opacity: {result}")
                
                try:
                    modified_count = int(result.strip('() '))
                except (ValueError, AttributeError):
                    return self.create_error_response("Unexpected response from GIMP")
                
                return self.create_success_response(
                    data={
                        "layers_modified": modified_count,
                        "image_path": image_path,
                        "opacity": opacity
                    },
                    message=f"Set opacity to {opacity}% for {modified_count} layers"
                )
                
            except Exception as e:
                self.logger.error(f"Error setting layer opacity: {e}", exc_info=True)
                return self.create_error_response(f"Failed to set layer opacity: {str(e)}")
                
        @app.tool(
            name="set_layer_blend_mode",
            description="Set the blend mode of one or more layers in the image.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Path to the GIMP image file",
                    "required": True,
                    "format": "file"
                },
                "layer_indices": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                    "description": "Indices of layers to modify",
                    "required": True
                },
                "blend_mode": {
                    "type": "string",
                    "enum": [
                        "normal", "dissolve", "behind", "multiply", "screen", "overlay",
                        "difference", "addition", "subtract", "darken-only", "lighten-only",
                        "hue", "saturation", "color", "value", "divide", "dodge", "burn",
                        "hard-light", "soft-light", "grain-extract", "grain-merge",
                        "color-erase", "erase", "replace", "anti-erase"
                    ],
                    "description": "Blend mode to set",
                    "required": True
                },
                "affect_others": {
                    "type": "boolean",
                    "description": "Whether to apply the blend mode to all other layers",
                    "default": False
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "layers_modified": {"type": "integer"},
                    "image_path": {"type": "string"},
                    "blend_mode": {"type": "string"}
                },
                "description": "Result of the blend mode change operation"
            },
            examples=[
                {
                    "description": "Set blend mode of specific layers",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [0, 2],
                        "blend_mode": "multiply"
                    }
                },
                {
                    "description": "Set blend mode of all layers",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [0],
                        "blend_mode": "overlay",
                        "affect_others": True
                    }
                }
            ]
        )
        async def set_layer_blend_mode(
            image_path: str,
            layer_indices: List[int],
            blend_mode: str,
            affect_others: bool = False
        ) -> Dict[str, Any]:
            """
            Set the blend mode of one or more layers in the image.
            
            This tool allows setting the blend mode of multiple layers at once.
            The blend mode determines how the layer interacts with layers below it.
            
            Args:
                image_path: Path to the GIMP image file
                layer_indices: Indices of layers to modify (0-based)
                blend_mode: Blend mode to set. One of:
                    - normal, dissolve, behind, multiply, screen, overlay
                    - difference, addition, subtract, darken-only, lighten-only
                    - hue, saturation, color, value, divide, dodge, burn
                    - hard-light, soft-light, grain-extract, grain-merge
                    - color-erase, erase, replace, anti-erase
                affect_others: If True, applies the blend mode to all layers in the image
                              regardless of layer_indices
                
            Returns:
                Dictionary containing:
                - success: Boolean indicating if the operation was successful
                - layers_modified: Number of layers that were modified
                - image_path: Path to the modified image
                - blend_mode: The blend mode that was set
                
            Raises:
                ValueError: If input validation fails
                RuntimeError: If the blend mode change operation fails
            """
            try:
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                if not layer_indices and not affect_others:
                    return self.create_error_response("No layer indices provided and affect_others is False")
                
                # Map blend mode names to GIMP's internal constants
                blend_mode_map = {
                    "normal": 0, "dissolve": 1, "behind": 2, "multiply": 3,
                    "screen": 4, "overlay": 5, "difference": 6, "addition": 7,
                    "subtract": 8, "darken-only": 9, "lighten-only": 10,
                    "hue": 11, "saturation": 12, "color": 13, "value": 14,
                    "divide": 15, "dodge": 16, "burn": 17, "hard-light": 18,
                    "soft-light": 19, "grain-extract": 20, "grain-merge": 21,
                    "color-erase": 22, "erase": 23, "replace": 24, "anti-erase": 25
                }
                
                blend_mode_lower = blend_mode.lower()
                if blend_mode_lower not in blend_mode_map:
                    valid_modes = ', '.join(f'"{m}"' for m in blend_mode_map.keys())
                    return self.create_error_response(
                        f"Invalid blend mode. Must be one of: {valid_modes}"
                    )
                
                gimp_blend_mode = blend_mode_map[blend_mode_lower]
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (modified 0)
                    (target-indices '{target_indices_list})
                )
                    ; Process each layer
                    (let loop ((i 0))
                        (when (< i num-layers)
                            (let ((layer (vector-ref layer-array i)))
                                (when (or {apply_all} (member i target-indices))
                                    (gimp-layer-set-mode layer {blend_mode})
                                    (set! modified (+ modified 1))
                                )
                                (loop (+ i 1))
                            )
                        )
                    )
                    
                    ; Save and clean up
                    (gimp-displays-flush)
                    (gimp-file-save RUN-NONINTERACTIVE image (car (gimp-image-get-active-drawable image)) "{image_path}" "{image_path}")
                    (gimp-image-delete image)
                    
                    (number->string modified)
                )
                """
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    target_indices_list=' '.join(map(str, layer_indices)) if layer_indices else "0",
                    apply_all="#t" if affect_others else "#f",
                    blend_mode=gimp_blend_mode
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to set layer blend mode: {result}")
                
                try:
                    modified_count = int(result.strip('() '))
                except (ValueError, AttributeError):
                    return self.create_error_response("Unexpected response from GIMP")
                
                return self.create_success_response(
                    data={
                        "layers_modified": modified_count,
                        "image_path": image_path,
                        "blend_mode": blend_mode
                    },
                    message=f"Set blend mode to {blend_mode} for {modified_count} layers"
                )
                
            except Exception as e:
                self.logger.error(f"Error setting layer blend mode: {e}", exc_info=True)
                return self.create_error_response(f"Failed to set layer blend mode: {str(e)}")
                
        @app.tool(
            name="group_layers",
            description="Group multiple layers together in a layer group.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Path to the GIMP image file",
                    "required": True,
                    "format": "file"
                },
                "layer_indices": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                    "description": "Indices of layers to include in the group (0-based, top to bottom)",
                    "required": True
                },
                "group_name": {
                    "type": "string",
                    "description": "Name for the new layer group",
                    "default": "Group"
                },
                "position": {
                    "type": "integer",
                    "description": "Position to insert the group (0 = top, -1 = bottom, or specific index)",
                    "default": 0
                },
                "visible": {
                    "type": "boolean",
                    "description": "Whether the group should be visible after creation",
                    "default": True
                },
                "expanded": {
                    "type": "boolean",
                    "description": "Whether the group should be expanded in the layer stack",
                    "default": True
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "group_index": {"type": "integer"},
                    "image_path": {"type": "string"},
                    "layers_grouped": {"type": "integer"},
                    "group_name": {"type": "string"}
                },
                "description": "Result of the layer grouping operation"
            },
            examples=[
                {
                    "description": "Group specific layers with default settings",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [1, 2, 3],
                        "group_name": "My Group"
                    }
                },
                {
                    "description": "Group layers and place at specific position",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [0, 1],
                        "position": 2,
                        "visible": False
                    }
                }
            ]
        )
        async def group_layers(
            image_path: str,
            layer_indices: List[int],
            group_name: str = "Group",
            position: int = 0,
            visible: bool = True,
            expanded: bool = True
        ) -> Dict[str, Any]:
            """
            Group multiple layers together in a layer group.
            
            This tool creates a new layer group and moves the specified layers into it.
            The layers will be added to the group in the order specified by layer_indices.
            
            Args:
                image_path: Path to the GIMP image file
                layer_indices: Indices of layers to include in the group (0-based, top to bottom)
                group_name: Name for the new layer group
                position: Position to insert the group (0 = top, -1 = bottom, or specific index)
                visible: Whether the group should be visible after creation
                expanded: Whether the group should be expanded in the layer stack
                
            Returns:
                Dictionary containing:
                - success: Boolean indicating if the operation was successful
                - group_index: Index of the newly created group
                - image_path: Path to the modified image
                - layers_grouped: Number of layers moved into the group
                - group_name: Name of the created group
                
            Raises:
                ValueError: If input validation fails
                RuntimeError: If the group creation or layer movement fails
            """
            try:
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                if not layer_indices:
                    return self.create_error_response("No layer indices provided")
                
                if not group_name.strip():
                    group_name = "Group"
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (target-indices (list {target_indices_list}))
                    (sorted-indices (sort target-indices >))  ; Sort descending for proper removal
                    (group (car (gimp-layer-group-new image)))
                    (layers-grouped 0)
                )
                    ; Set group properties
                    (gimp-item-set-visible group {group_visible})
                    (gimp-item-set-name group "{group_name}")
                    
                    ; Add group to the image at the specified position
                    (gimp-image-insert-layer image group 0 {position})
                    
                    ; Move layers into the group
                    (for-each 
                        (lambda (i)
                            (when (and (>= i 0) (< i num-layers))
                                (let ((layer (vector-ref layer-array i)))
                                    (gimp-image-reorder-item image layer group 0)
                                    (set! layers-grouped (+ layers-grouped 1))
                                )
                            )
                        )
                        sorted-indices
                    )
                    
                    ; Set group expansion state
                    (gimp-item-set-expanded group {group_expanded})
                    
                    ; Save and clean up
                    (gimp-displays-flush)
                    (gimp-file-save RUN-NONINTERACTIVE image (car (gimp-image-get-active-drawable image)) "{image_path}" "{image_path}")
                    (gimp-image-delete image)
                    
                    ; Return group index and layers grouped
                    (list (number->string (car (gimp-item-get-index group))) (number->string layers-grouped))
                )
                """
                
                # Prepare the position parameter for Script-Fu
                # In GIMP, 0 = top, -1 = bottom, or specific index
                gimp_position = position
                if gimp_position < -1:
                    gimp_position = -1  # Bottom
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    target_indices_list=' '.join(map(str, sorted(layer_indices, reverse=True))),  # Sort descending for proper removal
                    group_name=group_name.replace('"', '\\"'),
                    position=gimp_position,
                    group_visible="TRUE" if visible else "FALSE",
                    group_expanded="TRUE" if expanded else "FALSE"
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to group layers: {result}")
                
                result_parts = result.strip().split('\n')
                if len(result_parts) < 2:
                    return self.create_error_response("Unexpected response from GIMP")
                
                try:
                    group_index = int(result_parts[0].strip('() \"'))
                    layers_grouped = int(result_parts[1].strip('() \"'))
                except (ValueError, IndexError):
                    return self.create_error_response("Failed to parse GIMP response")
                
                return self.create_success_response(
                    data={
                        "group_index": group_index,
                        "image_path": image_path,
                        "layers_grouped": layers_grouped,
                        "group_name": group_name
                    },
                    message=f"Created group '{group_name}' with {layers_grouped} layers at position {group_index}"
                )
                
            except Exception as e:
                self.logger.error(f"Error grouping layers: {e}", exc_info=True)
                return self.create_error_response(f"Failed to group layers: {str(e)}")
                
        @app.tool(
            name="ungroup_layers",
            description="Ungroup layers from a layer group.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Path to the GIMP image file",
                    "required": True,
                    "format": "file"
                },
                "group_index": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Index of the layer group to ungroup (0-based, top to bottom)",
                    "required": True
                },
                "position": {
                    "type": "integer",
                    "description": "Position to insert the ungrouped layers (0 = top, -1 = bottom, or specific index)",
                    "default": -1
                },
                "delete_empty_group": {
                    "type": "boolean",
                    "description": "Whether to delete the group if it becomes empty after ungrouping",
                    "default": True
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to recursively ungroup nested groups",
                    "default": False
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "layers_ungrouped": {"type": "integer"},
                    "image_path": {"type": "string"},
                    "group_deleted": {"type": "boolean"}
                },
                "description": "Result of the layer ungrouping operation"
            },
            examples=[
                {
                    "description": "Ungroup a layer group with default settings",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "group_index": 2
                    }
                },
                {
                    "description": "Ungroup and keep the empty group",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "group_index": 1,
                        "delete_empty_group": False,
                        "position": 0
                    }
                }
            ]
        )
        async def ungroup_layers(
            image_path: str,
            group_index: int,
            position: int = -1,
            delete_empty_group: bool = True,
            recursive: bool = False
        ) -> Dict[str, Any]:
            """
            Ungroup layers from a layer group.
            
            This tool removes layers from a group and optionally deletes the empty group.
            The layers will be moved to the specified position in the layer stack.
            
            Args:
                image_path: Path to the GIMP image file
                group_index: Index of the layer group to ungroup (0-based, top to bottom)
                position: Position to insert the ungrouped layers (0 = top, -1 = bottom, or specific index)
                delete_empty_group: Whether to delete the group if it becomes empty after ungrouping
                recursive: Whether to recursively ungroup nested groups
                
            Returns:
                Dictionary containing:
                - success: Boolean indicating if the operation was successful
                - layers_ungrouped: Number of layers that were ungrouped
                - image_path: Path to the modified image
                - group_deleted: Whether the group was deleted (if delete_empty_group was True)
                
            Raises:
                ValueError: If input validation fails
                RuntimeError: If the ungrouping operation fails
            """
            try:
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                if group_index < 0:
                    return self.create_error_response("Group index must be non-negative")
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (group (if (and (>= {group_index} 0) (< {group_index} num-layers))
                            (vector-ref layer-array {group_index})
                            #f))
                    (layers-ungrouped 0)
                    (group-deleted #f)
                )
                    (when (and group (gimp-item-is-group group))
                        (let* (
                            (group-layers (gimp-item-get-children group))
                            (num-group-layers (car group-layers))
                            (group-layer-array (cadr group-layers))
                            (i (- num-group-layers 1))  ; Process from bottom to top to maintain order
                        )
                            ; Process each layer in the group
                            (while (>= i 0)
                                (let ((layer (vector-ref group-layer-array i)))
                                    (when (or {recursive} (not (gimp-item-is-group layer)))
                                        ; Move layer out of the group to the specified position
                                        (gimp-image-reorder-item image layer 0 {position})
                                        (set! layers-ungrouped (+ layers-ungrouped 1))
                                    )
                                )
                                (set! i (- i 1))
                            )
                            
                            ; Delete the group if it's empty and requested
                            (when (and {delete_empty} (<= (car (gimp-item-get-children group)) 0))
                                (gimp-image-remove-layer image group)
                                (set! group-deleted #t)
                            )
                        )
                    )
                    
                    ; Save and clean up
                    (gimp-displays-flush)
                    (gimp-file-save RUN-NONINTERACTIVE image (car (gimp-image-get-active-drawable image)) "{image_path}" "{image_path}")
                    (gimp-image-delete image)
                    
                    ; Return the number of layers ungrouped and whether the group was deleted
                    (list (number->string layers-ungrouped) (if group-deleted "#t" "#f"))
                )
                """
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    group_index=group_index,
                    position=position,
                    delete_empty="#t" if delete_empty_group else "#f",
                    recursive="#t" if recursive else "#f"
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to ungroup layers: {result}")
                
                result_parts = result.strip().split('\n')
                if len(result_parts) < 2:
                    return self.create_error_response("Unexpected response from GIMP")
                
                try:
                    layers_ungrouped = int(result_parts[0].strip('() \"'))
                    group_deleted = result_parts[1].strip('() \"').lower() == '#t'
                except (ValueError, IndexError):
                    return self.create_error_response("Failed to parse GIMP response")
                
                return self.create_success_response(
                    data={
                        "layers_ungrouped": layers_ungrouped,
                        "image_path": image_path,
                        "group_deleted": group_deleted
                    },
                    message=f"Ungrouped {layers_ungrouped} layers" + (" and deleted empty group" if group_deleted else "")
                )
                
            except Exception as e:
                self.logger.error(f"Error ungrouping layers: {e}", exc_info=True)
                return self.create_error_response(f"Failed to ungroup layers: {str(e)}")
                
        @app.tool(
            name="duplicate_layers",
            description="Duplicate one or more layers with optional offset and naming.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Path to the GIMP image file",
                    "required": True,
                    "format": "file"
                },
                "layer_indices": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                    "description": "Indices of layers to duplicate (0-based, top to bottom)",
                    "required": True
                },
                "count": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of times to duplicate each layer",
                    "default": 1
                },
                "offset_x": {
                    "type": "integer",
                    "description": "Horizontal offset for each duplicate (pixels)",
                    "default": 10
                },
                "offset_y": {
                    "type": "integer",
                    "description": "Vertical offset for each duplicate (pixels)",
                    "default": 10
                },
                "name_suffix": {
                    "type": "string",
                    "description": "Suffix to append to duplicated layer names (e.g., 'copy')",
                    "default": "copy"
                },
                "link_duplicates": {
                    "type": "boolean",
                    "description": "Whether to link the duplicated layers together",
                    "default": False
                },
                "position": {
                    "type": "integer",
                    "description": "Position to insert duplicates (0 = above original, -1 = below, or specific index)",
                    "default": 0
                }
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "duplicated_layers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "original_index": {"type": "integer"},
                                "original_name": {"type": "string"},
                                "new_indices": {"type": "array", "items": {"type": "integer"}},
                                "new_names": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "image_path": {"type": "string"}
                },
                "description": "Result of the layer duplication operation"
            },
            examples=[
                {
                    "description": "Duplicate a single layer once with default settings",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [2],
                        "count": 1
                    }
                },
                {
                    "description": "Create multiple duplicates with offset and custom naming",
                    "parameters": {
                        "image_path": "/path/to/image.xcf",
                        "layer_indices": [0, 1],
                        "count": 3,
                        "offset_x": 20,
                        "offset_y": 20,
                        "name_suffix": "duplicate"
                    }
                }
            ]
        )
        async def duplicate_layers(
            image_path: str,
            layer_indices: List[int],
            count: int = 1,
            offset_x: int = 10,
            offset_y: int = 10,
            name_suffix: str = "copy",
            link_duplicates: bool = False,
            position: int = 0
        ) -> Dict[str, Any]:
            """
            Duplicate one or more layers with optional offset and naming.
            
            This tool creates copies of the specified layers with the given options.
            Each duplicate can be offset from the original and given a new name.
            
            Args:
                image_path: Path to the GIMP image file
                layer_indices: Indices of layers to duplicate (0-based, top to bottom)
                count: Number of times to duplicate each layer
                offset_x: Horizontal offset for each duplicate (pixels)
                offset_y: Vertical offset for each duplicate (pixels)
                name_suffix: Suffix to append to duplicated layer names
                link_duplicates: Whether to link the duplicated layers together
                position: Position to insert duplicates (0 = above original, -1 = below, or specific index)
                
            Returns:
                Dictionary containing:
                - success: Boolean indicating if the operation was successful
                - duplicated_layers: List of objects with original and new layer information
                - image_path: Path to the modified image
                
            Raises:
                ValueError: If input validation fails
                RuntimeError: If the duplication operation fails
            """
            try:
                if not self.validate_file_path(image_path, must_exist=True):
                    return self.create_error_response("Invalid image file")
                
                if not layer_indices:
                    return self.create_error_response("No layer indices provided")
                
                if count < 1:
                    return self.create_error_response("Count must be at least 1")
                
                # Build Script-Fu command
                script = """
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{image_path}" "{image_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers))
                    (result '())
                )
                    ; Process each source layer
                    (for-each
                        (lambda (layer-index)
                            (when (and (>= layer-index 0) (< layer-index num-layers))
                                (let* (
                                    (original-layer (vector-ref layer-array layer-index))
                                    (original-name (car (gimp-item-get-name original-layer)))
                                    (original-visible (car (gimp-item-get-visible original-layer)))
                                    (original-opacity (car (gimp-layer-get-opacity original-layer)))
                                    (original-mode (car (gimp-layer-get-mode original-layer)))
                                    (original-offsets (gimp-drawable-offsets original-layer))
                                    (original-x (car original-offsets))
                                    (original-y (cadr original-offsets))
                                    (new-indices '())
                                    (new-names '())
                                    (duplicates '())
                                )
                                    ; Create the specified number of duplicates
                                    (do ((i 1 (+ i 1)))
                                        ((> i {count}) #t)
                                        (let* (
                                            (duplicate (car (gimp-layer-copy original-layer TRUE)))
                                            (new-name (string-append original-name " {name_suffix}" (if (> {count} 1) (number->string i) "")))
                                            (offset-x (* i {offset_x}))
                                            (offset-y (* i {offset_y}))
                                        )
                                            ; Add the duplicate to the image
                                            (gimp-image-insert-layer image duplicate 0 {position})
                                            
                                            ; Set the duplicate's properties
                                            (gimp-item-set-name duplicate new-name)
                                            (gimp-item-set-visible duplicate original-visible)
                                            (gimp-layer-set-opacity duplicate original-opacity)
                                            (gimp-layer-set-mode duplicate original-mode)
                                            (gimp-layer-set-offsets duplicate (+ original-x offset-x) (+ original-y offset-y))
                                            
                                            ; Add to our tracking lists
                                            (set! new-indices (cons (car (gimp-item-get-index duplicate)) new-indices))
                                            (set! new-names (cons new-name new-names))
                                            (set! duplicates (cons duplicate duplicates))
                                        )
                                    )
                                    
                                    ; Link duplicates if requested
                                    (when (and {link_duplicates} (not (null? duplicates)))
                                        (gimp-item-set-linked (car duplicates) TRUE)
                                        (for-each 
                                            (lambda (dup) 
                                                (gimp-item-set-linked dup TRUE)
                                                (gimp-item-add-to-selection image dup)
                                            )
                                            (cdr duplicates)
                                        )
                                        (gimp-item-remove-selection image)
                                    )
                                    
                                    ; Add to result
                                    (set! result (cons 
                                        (list 
                                            layer-index
                                            original-name
                                            (list->vector (reverse new-indices))
                                            (list->vector (reverse new-names))
                                        )
                                        result
                                    ))
                                )
                            )
                        )
                        (list {layer_indices_list})
                    )
                    
                    ; Save and clean up
                    (gimp-displays-flush)
                    (gimp-file-save RUN-NONINTERACTIVE image (car (gimp-image-get-active-drawable image)) "{image_path}" "{image_path}")
                    
                    ; Build the result string
                    (let ((result-str "("))
                        (for-each
                            (lambda (item)
                                (set! result-str (string-append result-str "(" 
                                    (number->string (car item)) " "
                                    "\"" (cadr item) "\" "
                                    "#(" (string-join (map number->string (vector->list (caddr item))) " ") ") "
                                    "#(\"" (string-join (vector->list (cadddr item)) "\" \"") "\")"
                                    ") "
                                ))
                            )
                            result
                        )
                        (set! result-str (string-append result-str ")"))
                        (gimp-message result-str)
                        result-str
                    )
                )
                """
                
                # Execute the script
                result = await self.cli_wrapper.execute_script_fu(script.format(
                    image_path=image_path.replace('\\', '\\\\'),
                    layer_indices_list=' '.join(map(str, layer_indices)),
                    count=count,
                    offset_x=offset_x,
                    offset_y=offset_y,
                    name_suffix=name_suffix.replace('"', '\\"'),
                    link_duplicates="#t" if link_duplicates else "#f",
                    position=position
                ))
                
                # Parse the result
                if not result or "Error" in result:
                    return self.create_error_response(f"Failed to duplicate layers: {result}")
                
                # Parse the result string into a structured format
                try:
                    # The result is in the format: ((original_index "original_name" #(new_indices...) #("new_names"...)) ...)
                    # We need to parse this into a proper Python structure
                    result_str = result.strip()
                    if not result_str.startswith('((') or not result_str.endswith('))'):
                        raise ValueError("Unexpected result format")
                        
                    # Parse the result into a list of (original_index, original_name, [new_indices], [new_names])
                    parsed_results = []
                    for item in result_str[2:-2].split(')('):
                        parts = item.split()
                        if len(parts) < 4:
                            continue
                            
                        original_index = int(parts[0])
                        original_name = ' '.join(parts[1:-2]).strip('"')
                        
                        # Parse new indices (format: #(1 2 3))
                        new_indices = [int(idx) for idx in parts[-2][2:-1].split()]
                        
                        # Parse new names (format: #("name1" "name2"))
                        new_names = [name.strip('"') for name in ' '.join(parts[-1:])[3:-1].split('" "')]
                        
                        parsed_results.append({
                            "original_index": original_index,
                            "original_name": original_name,
                            "new_indices": new_indices,
                            "new_names": new_names
                        })
                    
                    return self.create_success_response(
                        data={
                            "duplicated_layers": parsed_results,
                            "image_path": image_path
                        },
                        message=f"Successfully duplicated {sum(len(r['new_indices']) for r in parsed_results)} layers"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Error parsing duplication result: {e}\nRaw result: {result}", exc_info=True)
                    return self.create_error_response("Failed to parse layer duplication result")
                
            except Exception as e:
                self.logger.error(f"Error duplicating layers: {e}", exc_info=True)
                return self.create_error_response(f"Failed to duplicate layers: {str(e)}")
