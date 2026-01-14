"""
Base plugin implementation for GIMP MCP tool categories.
"""
from typing import Any, Dict, Optional, Union, List
from pathlib import Path
import logging

from ..cli_wrapper import InkscapeCliWrapper
from ..config import InkscapeConfig
from ..tools.base import BaseToolCategory

class GimpToolPlugin(BaseToolCategory):
    """Base class for all GIMP tool category plugins.
    
    This class extends BaseToolCategory with plugin-specific functionality
    and provides common utilities for tool implementations.
    """
    
    # Class variables that should be overridden by subclasses
    PLUGIN_NAME: str = "unnamed_plugin"
    PLUGIN_DESCRIPTION: str = "No description provided"
    
    def __init__(self, cli_wrapper: InkscapeCliWrapper, config: InkscapeConfig):
        """Initialize the tool plugin with dependencies.
        
        Args:
            cli_wrapper: GIMP CLI wrapper instance
            config: Server configuration
        """
        super().__init__(cli_wrapper, config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @classmethod
    def get_plugin_name(cls) -> str:
        """Return the plugin's unique identifier."""
        return cls.PLUGIN_NAME
    
    @classmethod
    def get_plugin_description(cls) -> str:
        """Return a short description of the plugin's functionality."""
        return cls.PLUGIN_DESCRIPTION
    
    # Common validation methods for all tool plugins
    
    def validate_layer_index(self, num_layers: int, layer_index: int) -> bool:
        """Validate a layer index is within bounds.
        
        Args:
            num_layers: Total number of layers
            layer_index: Index to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(layer_index, int) or layer_index < 0 or layer_index >= num_layers:
            self.logger.error(f"Invalid layer index: {layer_index}")
            return False
        return True
    
    def validate_selection_bounds(self, bounds: Dict[str, int]) -> bool:
        """Validate selection bounds.
        
        Args:
            bounds: Dictionary with 'x', 'y', 'width', 'height' keys
            
        Returns:
            bool: True if valid, False otherwise
        """
        required = {'x', 'y', 'width', 'height'}
        if not all(k in bounds for k in required):
            self.logger.error(f"Missing required selection bounds. Required: {required}")
            return False
            
        if bounds['width'] <= 0 or bounds['height'] <= 0:
            self.logger.error("Selection width and height must be positive")
            return False
            
        return True
    
    def validate_color(self, color: Union[str, List[int]]) -> bool:
        """Validate a color value.
        
        Args:
            color: Color as hex string or RGB/RGBA list
            
        Returns:
            bool: True if valid, False otherwise
        """
        if isinstance(color, str):
            # Hex color validation
            color = color.lstrip('#')
            if len(color) not in (3, 6, 8):
                return False
            try:
                int(color, 16)
                return True
            except ValueError:
                return False
        
        elif isinstance(color, (list, tuple)):
            # RGB or RGBA list validation
            if len(color) not in (3, 4):
                return False
            return all(isinstance(c, (int, float)) and 0 <= c <= 255 for c in color)
        
        return False
    
    # Common response formatters
    
    def format_layer_info(self, layer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format layer information for API responses.
        
        Args:
            layer_data: Raw layer data from GIMP
            
        Returns:
            Formatted layer information
        """
        return {
            "index": layer_data.get("index"),
            "name": layer_data.get("name"),
            "visible": layer_data.get("visible", True),
            "opacity": layer_data.get("opacity", 1.0),
            "mode": layer_data.get("mode", "normal"),
            "width": layer_data.get("width"),
            "height": layer_data.get("height"),
            "type": layer_data.get("type", "raster"),
            "has_alpha": layer_data.get("has_alpha", False)
        }
    
    def format_selection_info(self, selection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format selection information for API responses.
        
        Args:
            selection_data: Raw selection data from GIMP
            
        Returns:
            Formatted selection information
        """
        return {
            "bounds": {
                "x": selection_data.get("x", 0),
                "y": selection_data.get("y", 0),
                "width": selection_data.get("width", 0),
                "height": selection_data.get("height", 0)
            },
            "is_empty": selection_data.get("empty", True),
            "has_selection": not selection_data.get("empty", True)
        }
