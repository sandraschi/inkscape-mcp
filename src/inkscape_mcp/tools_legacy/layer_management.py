from __future__ import annotations

"""
Layer Management Tools for GIMP MCP Server.

Provides comprehensive layer operations including creation, manipulation,
blending modes, effects, and organization following FastMCP 2.10 standards.
"""

import asyncio
import enum
import logging
import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any, Dict, List, Literal, Optional, Sequence, Set, Tuple, TypeVar, Union, cast
)

from fastmcp import FastMCP

from .base import BaseToolCategory, tool

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

logger = logging.getLogger(__name__)

# Type aliases
FilePath: TypeAlias = str
LayerName: TypeAlias = str
LayerID: TypeAlias = str
LayerResult: TypeAlias = Dict[str, Any]

class LayerType(str, Enum):
    """Supported layer types in GIMP."""
    NORMAL = "normal"
    TEXT = "text"
    VECTOR = "vector"
    LAYER_GROUP = "group"
    LAYER_MASK = "mask"
    CHANNEL_MASK = "channel-mask"
    SELECTION_MASK = "selection-mask"
    LAYER_EFFECT = "effect"

class BlendMode(str, Enum):
    """Supported layer blending modes in GIMP."""
    NORMAL = "normal"
    DISSOLVE = "dissolve"
    BEHIND = "behind"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    DIFFERENCE = "difference"
    ADDITION = "addition"
    SUBTRACT = "subtract"
    DARKEN_ONLY = "darken-only"
    LIGHTEN_ONLY = "lighten-only"
    HUE = "hue"
    SATURATION = "saturation"
    COLOR = "color"
    VALUE = "value"
    DIVIDE = "divide"
    DODGE = "dodge"
    BURN = "burn"
    HARDLIGHT = "hardlight"
    SOFTLIGHT = "softlight"
    GRAIN_EXTRACT = "grain-extract"
    GRAIN_MERGE = "grain-merge"
    COLOR_ERASE = "color-erase"
    ERASE = "erase"
    REPLACE = "replace"
    ANTI_ERASE = "anti-erase"

@dataclass
class LayerConfig:
    """Configuration for creating or modifying a layer."""
    name: str = "New Layer"
    layer_type: LayerType = LayerType.NORMAL
    opacity: float = 100.0
    blend_mode: BlendMode = BlendMode.NORMAL
    visible: bool = True
    linked: bool = False
    lock_alpha: bool = False
    lock_position: bool = False
    lock_visibility: bool = False
    lock_edit: bool = False
    preserve_transparency: bool = False
    apply_mask: bool = False
    show_mask: bool = False
    edit_mask: bool = False
    apply_matrix: bool = False

class LayerManagementTools(BaseToolCategory):
    """
    Comprehensive layer management tools for GIMP operations.
    
    Provides tools for creating, manipulating, and organizing layers
    with support for blending modes, effects, and advanced operations.
    """
    
    def register_tools(self, app: FastMCP) -> None:
        """Register all layer management tools with FastMCP."""
        
        @app.tool()
        async def create_layer(
            input_path: str,
            output_path: str,
            layer_name: str = "New Layer",
            layer_type: str = "normal",
            opacity: float = 100.0,
            blend_mode: str = "normal"
        ) -> Dict[str, Any]:
            """
            Create a new layer in an image.
            
            Args:
                input_path: Source image file path
                output_path: Destination file path
                layer_name: Name for the new layer
                layer_type: Type of layer (normal, text, vector, etc.)
                opacity: Layer opacity (0-100)
                blend_mode: Blending mode for the layer
                
            Returns:
                Dict containing layer creation results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response(f"Invalid output path: {output_path}")
                
                # Validate parameters
                if not (0 <= opacity <= 100):
                    return self.create_error_response("Opacity must be between 0 and 100")
                
                valid_blend_modes = [
                    "normal", "multiply", "screen", "overlay", "darken", "lighten",
                    "color-dodge", "color-burn", "hard-light", "soft-light",
                    "difference", "exclusion", "hue", "saturation", "color", "value"
                ]
                if blend_mode.lower() not in valid_blend_modes:
                    return self.create_error_response(
                        f"Invalid blend mode. Must be one of: {valid_blend_modes}")
                
                # Create GIMP script for layer creation
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (new-layer (car (gimp-layer-new image 
                        (car (gimp-image-width image))
                        (car (gimp-image-height image))
                        RGBA-IMAGE "{layer_name}" {opacity} {blend_mode}))))
                    
                    ; Add the new layer to the image
                    (gimp-image-insert-layer image new-layer 0 0)
                    
                    ; Set layer position (above current layer)
                    (gimp-image-raise-layer image new-layer)
                    
                    ; Save the result
                    (gimp-file-save RUN-NONINTERACTIVE image new-layer "{output_path}" "{output_path}")
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message=f"Layer '{layer_name}' created successfully",
                    details={
                        "layer_name": layer_name,
                        "layer_type": layer_type,
                        "opacity": opacity,
                        "blend_mode": blend_mode,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Layer creation failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Layer creation failed: {str(e)}")
        
        @app.tool()
        async def duplicate_layer(
            input_path: str,
            output_path: str,
            layer_index: int = 0,
            new_name: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Duplicate an existing layer in an image.
            
            Args:
                input_path: Source image file path
                output_path: Destination file path
                layer_index: Index of layer to duplicate (0-based)
                new_name: Optional name for the duplicated layer
                
            Returns:
                Dict containing layer duplication results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response(f"Invalid output path: {output_path}")
                
                if layer_index < 0:
                    return self.create_error_response("Layer index must be non-negative")
                
                # Generate name if not provided
                if not new_name:
                    new_name = f"Copy of Layer {layer_index}"
                
                # Create GIMP script for layer duplication
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers)))
                    
                    ; Check if layer index is valid
                    (if (>= {layer_index} num-layers)
                        (gimp-message "Invalid layer index")
                        (let* (
                            (source-layer (aref layer-array {layer_index}))
                            (duplicate (car (gimp-layer-copy source-layer TRUE))))
                            
                            ; Add duplicated layer to image
                            (gimp-image-insert-layer image duplicate 0 0)
                            
                            ; Set layer name
                            (gimp-layer-set-name duplicate "{new_name}")
                            
                            ; Save the result
                            (gimp-file-save RUN-NONINTERACTIVE image duplicate "{output_path}" "{output_path}")
                        )
                    )
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message=f"Layer {layer_index} duplicated successfully",
                    details={
                        "original_layer_index": layer_index,
                        "new_layer_name": new_name,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Layer duplication failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Layer duplication failed: {str(e)}")
        
        @app.tool()
        async def delete_layer(
            input_path: str,
            output_path: str,
            layer_index: int = 0
        ) -> Dict[str, Any]:
            """
            Delete a layer from an image.
            
            Args:
                input_path: Source image file path
                output_path: Destination file path
                layer_index: Index of layer to delete (0-based)
                
            Returns:
                Dict containing layer deletion results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response(f"Invalid output path: {output_path}")
                
                if layer_index < 0:
                    return self.create_error_response("Layer index must be non-negative")
                
                # Create GIMP script for layer deletion
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers)))
                    
                    ; Check if layer index is valid
                    (if (>= {layer_index} num-layers)
                        (gimp-message "Invalid layer index")
                        (let* (
                            (target-layer (aref layer-array {layer_index})))
                            
                            ; Delete the layer
                            (gimp-image-remove-layer image target-layer)
                            
                            ; Save the result
                            (gimp-file-save RUN-NONINTERACTIVE image 
                                (car (gimp-image-get-active-layer image)) 
                                "{output_path}" "{output_path}")
                        )
                    )
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message=f"Layer {layer_index} deleted successfully",
                    details={
                        "deleted_layer_index": layer_index,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Layer deletion failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Layer deletion failed: {str(e)}")
        
        @app.tool()
        async def reorder_layer(
            input_path: str,
            output_path: str,
            layer_index: int,
            new_position: int
        ) -> Dict[str, Any]:
            """
            Reorder a layer to a new position in the layer stack.
            
            Args:
                input_path: Source image file path
                output_path: Destination file path
                layer_index: Current index of the layer to move
                new_position: New position for the layer (0-based)
                
            Returns:
                Dict containing layer reordering results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response(f"Invalid output path: {output_path}")
                
                if layer_index < 0 or new_position < 0:
                    return self.create_error_response("Layer indices must be non-negative")
                
                # Create GIMP script for layer reordering
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers)))
                    
                    ; Check if indices are valid
                    (if (and (< {layer_index} num-layers) (< {new_position} num-layers))
                        (let* (
                            (target-layer (aref layer-array {layer_index}))
                            (current-pos {layer_index})
                            (target-pos {new_position}))
                            
                            ; Move layer to new position
                            (cond
                                ((< current-pos target-pos)
                                 ; Moving down - raise layer multiple times
                                 (let loop ((i current-pos))
                                   (if (< i target-pos)
                                       (begin
                                         (gimp-image-raise-layer image target-layer)
                                         (loop (+ i 1))))))
                                ((> current-pos target-pos)
                                 ; Moving up - lower layer multiple times
                                 (let loop ((i current-pos))
                                   (if (> i target-pos)
                                       (begin
                                         (gimp-image-lower-layer image target-layer)
                                         (loop (- i 1))))))
                            )
                            
                            ; Save the result
                            (gimp-file-save RUN-NONINTERACTIVE image 
                                (car (gimp-image-get-active-layer image)) 
                                "{output_path}" "{output_path}")
                        )
                        (gimp-message "Invalid layer indices")
                    )
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message=f"Layer moved from position {layer_index} to {new_position}",
                    details={
                        "original_position": layer_index,
                        "new_position": new_position,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Layer reordering failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Layer reordering failed: {str(e)}")
        
        @app.tool()
        async def set_layer_properties(
            input_path: str,
            output_path: str,
            layer_index: int = 0,
            opacity: Optional[float] = None,
            blend_mode: Optional[str] = None,
            visible: Optional[bool] = None,
            locked: Optional[bool] = None
        ) -> Dict[str, Any]:
            """
            Set properties of a specific layer.
            
            Args:
                input_path: Source image file path
                output_path: Destination file path
                layer_index: Index of layer to modify (0-based)
                opacity: New opacity value (0-100, None to keep current)
                blend_mode: New blend mode (None to keep current)
                visible: Layer visibility (None to keep current)
                locked: Layer lock status (None to keep current)
                
            Returns:
                Dict containing layer property update results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response(f"Invalid output path: {output_path}")
                
                if layer_index < 0:
                    return self.create_error_response("Layer index must be non-negative")
                
                if opacity is not None and not (0 <= opacity <= 100):
                    return self.create_error_response("Opacity must be between 0 and 100")
                
                if blend_mode is not None:
                    valid_blend_modes = [
                        "normal", "multiply", "screen", "overlay", "darken", "lighten",
                        "color-dodge", "color-burn", "hard-light", "soft-light",
                        "difference", "exclusion", "hue", "saturation", "color", "value"
                    ]
                    if blend_mode.lower() not in valid_blend_modes:
                        return self.create_error_response(
                            f"Invalid blend mode. Must be one of: {valid_blend_modes}")
                
                # Build property update script
                property_updates = []
                if opacity is not None:
                    property_updates.append(f'(gimp-layer-set-opacity target-layer {opacity})')
                
                if blend_mode is not None:
                    property_updates.append(f'(gimp-layer-set-mode target-layer {blend_mode})')
                
                if visible is not None:
                    if visible:
                        property_updates.append('(gimp-layer-set-visible target-layer TRUE)')
                    else:
                        property_updates.append('(gimp-layer-set-visible target-layer FALSE)')
                
                if locked is not None:
                    if locked:
                        property_updates.append('(gimp-layer-set-lock-alpha target-layer TRUE)')
                    else:
                        property_updates.append('(gimp-layer-set-lock-alpha target-layer FALSE)')
                
                if not property_updates:
                    return self.create_error_response("No properties specified for update")
                
                # Create GIMP script for property updates
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers))
                    (layer-array (cadr layers)))
                    
                    ; Check if layer index is valid
                    (if (>= {layer_index} num-layers)
                        (gimp-message "Invalid layer index")
                        (let* (
                            (target-layer (aref layer-array {layer_index})))
                            
                            ; Apply property updates
                            {' '.join(property_updates)}
                            
                            ; Save the result
                            (gimp-file-save RUN-NONINTERACTIVE image target-layer "{output_path}" "{output_path}")
                        )
                    )
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                await self.cli_wrapper.execute_script_fu(script)
                
                # Build response details
                details = {"layer_index": layer_index, "output_path": output_path}
                if opacity is not None:
                    details["opacity"] = opacity
                if blend_mode is not None:
                    details["blend_mode"] = blend_mode
                if visible is not None:
                    details["visible"] = visible
                if locked is not None:
                    details["locked"] = locked
                
                return self.create_success_response(
                    message=f"Layer {layer_index} properties updated successfully",
                    details=details
                )
                
            except Exception as e:
                self.logger.error(f"Layer property update failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Layer property update failed: {str(e)}")
        
        @app.tool()
        async def merge_layers(
            input_path: str,
            output_path: str,
            layer_indices: List[int],
            merge_mode: str = "merge_down"
        ) -> Dict[str, Any]:
            """
            Merge multiple layers into a single layer.
            
            Args:
                input_path: Source image file path
                output_path: Destination file path
                layer_indices: List of layer indices to merge
                merge_mode: How to merge layers (merge_down, merge_visible, flatten)
                
            Returns:
                Dict containing layer merge results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response(f"Invalid output path: {output_path}")
                
                if not layer_indices:
                    return self.create_error_response("No layer indices specified")
                
                if not all(i >= 0 for i in layer_indices):
                    return self.create_error_response("All layer indices must be non-negative")
                
                valid_merge_modes = ["merge_down", "merge_visible", "flatten"]
                if merge_mode not in valid_merge_modes:
                    return self.create_error_response(
                        f"Invalid merge mode. Must be one of: {valid_merge_modes}")
                
                # Create GIMP script for layer merging
                if merge_mode == "flatten":
                    script = f"""
                    (let* (
                        (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                        (flattened (car (gimp-image-flatten image))))
                        
                        ; Save the flattened result
                        (gimp-file-save RUN-NONINTERACTIVE image flattened "{output_path}" "{output_path}")
                        (gimp-image-delete image)
                    ))
                    """
                else:
                    # For merge_down and merge_visible, we need to handle specific layers
                    script = f"""
                    (let* (
                        (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                        (layers (gimp-image-get-layers image))
                        (num-layers (car layers))
                        (layer-array (cadr layers)))
                        
                        ; Validate layer indices
                        (if (and {all(f'(< {i} num-layers)' for i in layer_indices)})
                            (let* (
                                (target-layer (aref layer-array {min(layer_indices)}))
                                (merged-layer))
                                
                                ; Merge layers based on mode
                                (cond
                                    ((string= "{merge_mode}" "merge_down")
                                     (set! merged-layer (car (gimp-image-merge-down image target-layer CLIP-TO-IMAGE))))
                                    ((string= "{merge_mode}" "merge_visible")
                                     (set! merged-layer (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE))))
                                )
                                
                                ; Save the result
                                (gimp-file-save RUN-NONINTERACTIVE image merged-layer "{output_path}" "{output_path}")
                            )
                            (gimp-message "Invalid layer indices")
                        )
                        (gimp-image-delete image)
                    ))
                    """
                
                # Execute the script
                await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message=f"Layers merged successfully using {merge_mode} mode",
                    details={
                        "layer_indices": layer_indices,
                        "merge_mode": merge_mode,
                        "output_path": output_path
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Layer merge failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Layer merge failed: {str(e)}")
        
        @app.tool()
        async def get_layer_info(
            input_path: str,
            layer_index: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Get detailed information about layers in an image.
            
            Args:
                input_path: Source image file path
                layer_index: Specific layer index to query (None for all layers)
                
            Returns:
                Dict containing layer information
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                if layer_index is not None and layer_index < 0:
                    return self.create_error_response("Layer index must be non-negative")
                
                # Create GIMP script for layer info extraction
                if layer_index is not None:
                    script = f"""
                    (let* (
                        (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                        (layers (gimp-image-get-layers image))
                        (num-layers (car layers))
                        (layer-array (cadr layers)))
                        
                        ; Check if layer index is valid
                        (if (>= {layer_index} num-layers)
                            (gimp-message "Invalid layer index")
                            (let* (
                                (target-layer (aref layer-array {layer_index})))
                                
                                ; Get layer information
                                (gimp-message (string-append
                                    "Layer " (number->string {layer_index}) ": "
                                    (gimp-layer-get-name target-layer) " | "
                                    "Opacity: " (number->string (gimp-layer-get-opacity target-layer)) " | "
                                    "Mode: " (symbol->string (gimp-layer-get-mode target-layer)) " | "
                                    "Visible: " (if (gimp-layer-get-visible target-layer) "Yes" "No"))))
                        )
                        (gimp-image-delete image)
                    ))
                    """
                else:
                    script = f"""
                    (let* (
                        (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                        (layers (gimp-image-get-layers image))
                        (num-layers (car layers))
                        (layer-array (cadr layers)))
                        
                        ; Get information for all layers
                        (let loop ((i 0))
                          (if (< i num-layers)
                              (let* (
                                  (layer (aref layer-array i)))
                                  
                                  ; Get layer information
                                  (gimp-message (string-append
                                      "Layer " (number->string i) ": "
                                      (gimp-layer-get-name layer) " | "
                                      "Opacity: " (number->string (gimp-layer-get-opacity layer)) " | "
                                      "Mode: " (symbol->string (gimp-layer-get-mode layer)) " | "
                                      "Visible: " (if (gimp-layer-get-visible layer) "Yes" "No")))
                                  
                                  (loop (+ i 1))))))
                        
                        (gimp-image-delete image)
                    ))
                    """
                
                # Execute the script
                output = await self.cli_wrapper.execute_script_fu(script)
                
                return self.create_success_response(
                    message="Layer information retrieved successfully",
                    details={
                        "input_path": input_path,
                        "layer_index": layer_index,
                        "layer_info": output
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Layer info retrieval failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Layer info retrieval failed: {str(e)}")
