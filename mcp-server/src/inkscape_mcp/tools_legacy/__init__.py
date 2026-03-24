from __future__ import annotations

"""
GIMP MCP Tools Package.

This package contains all the tool categories for the GIMP MCP server,
providing comprehensive image editing capabilities through GIMP integration.
"""

import sys
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

# Set up logging
logger = logging.getLogger(__name__)


# Define base class first
class BaseToolCategory:
    """Base class for all tool categories."""

    pass


# Create type variable for tool categories
ToolCategoryT = TypeVar("ToolCategoryT", bound=BaseToolCategory)

# Import tool categories
try:
    # Import all tool categories
    from .file_operations_tools import FileOperationTools
    from .transforms import TransformTools
    from .color_adjustments import ColorAdjustmentTools
    from .filters import FilterTools
    from .batch_processing import BatchProcessingTools
    from .help_tools import HelpTools
    from .status_tools import StatusTools
    from .layer_management import LayerManagementTools
    from .image_analysis import ImageAnalysisTools
    from .performance_tools import PerformanceTools

    # Define all tool categories
    ALL_TOOL_CATEGORIES = [
        FileOperationTools,
        TransformTools,
        ColorAdjustmentTools,
        FilterTools,
        BatchProcessingTools,
        HelpTools,
        StatusTools,
        LayerManagementTools,
        ImageAnalysisTools,
        PerformanceTools,
    ]

    MISSING_IMPLEMENTATIONS = False

except ImportError as e:
    logger.error(f"Failed to import tool categories: {e}")
    MISSING_IMPLEMENTATIONS = True
    ALL_TOOL_CATEGORIES: List[Type[BaseToolCategory]] = []

# Version information
__version__ = "0.1.0"

# Define tool categories mapping
TOOL_CATEGORIES = {
    "file_operations": FileOperationTools if "FileOperationTools" in globals() else None,
    "transforms": TransformTools if "TransformTools" in globals() else None,
    "color_adjustments": ColorAdjustmentTools if "ColorAdjustmentTools" in globals() else None,
    "filters": FilterTools if "FilterTools" in globals() else None,
    "batch_processing": BatchProcessingTools if "BatchProcessingTools" in globals() else None,
    "help_tools": HelpTools if "HelpTools" in globals() else None,
    "status_tools": StatusTools if "StatusTools" in globals() else None,
    "layer_management": LayerManagementTools if "LayerManagementTools" in globals() else None,
    "image_analysis": ImageAnalysisTools if "ImageAnalysisTools" in globals() else None,
    "performance_tools": PerformanceTools if "PerformanceTools" in globals() else None,
}


def get_tool_category(category_name: str) -> Type[BaseToolCategory]:
    """Get a tool category by name."""
    if MISSING_IMPLEMENTATIONS:
        raise RuntimeError("Some tool categories failed to import. Check logs for details.")

    category = TOOL_CATEGORIES.get(category_name.lower())
    if category is None:
        valid_categories = ", ".join(
            f'"{name}"' for name in TOOL_CATEGORIES if TOOL_CATEGORIES[name] is not None
        )
        raise ValueError(
            f"Unknown tool category: '{category_name}'. Valid categories are: {valid_categories}"
        )
    return category


def list_tool_categories(include_experimental: bool = False) -> List[str]:
    """List all available tool categories."""
    if MISSING_IMPLEMENTATIONS:
        raise RuntimeError("Some tool categories failed to import. Check logs for details.")

    return [
        name
        for name, cls in TOOL_CATEGORIES.items()
        if cls is not None and (include_experimental or not getattr(cls, "EXPERIMENTAL", False))
    ]


def get_tool_category_info(category_name: str) -> Dict[str, Any]:
    """Get information about a specific tool category."""
    category = get_tool_category(category_name)
    return {
        "name": category_name,
        "display_name": getattr(category, "DISPLAY_NAME", category_name.replace("_", " ").title()),
        "description": getattr(category, "DESCRIPTION", ""),
        "version": getattr(category, "VERSION", "0.1.0"),
        "experimental": getattr(category, "EXPERIMENTAL", False),
        "requires_gpu": getattr(category, "REQUIRES_GPU", False),
    }


__all__ = [
    "BaseToolCategory",
    "FileOperationResult",
    "FileOperationTools",
    "TransformTools",
    "ColorAdjustmentTools",
    "FilterTools",
    "BatchProcessingTools",
    "HelpTools",
    "StatusTools",
    "LayerManagementTools",
    "ImageAnalysisTools",
    "PerformanceTools",
    "get_tool_category",
    "list_tool_categories",
    "get_tool_category_info",
]


# Additional metadata for tool categories
@dataclass
class ToolCategoryInfo:
    """Metadata and information about a tool category."""

    name: str
    display_name: str
    description: str
    version: str
    category: str = "general"
    experimental: bool = False
    requires_gpu: bool = False


def get_tool_category(category_name: str) -> Type[BaseToolCategory]:
    """
    Get a tool category class by name.

    Args:
        category_name: Name of the tool category (case-insensitive)

    Returns:
        The tool category class

    Raises:
        ValueError: If the category name is invalid
        RuntimeError: If there are missing implementations
    """
    if MISSING_IMPLEMENTATIONS:
        raise RuntimeError("Some tool categories failed to import. Check logs for details.")

    category_name = category_name.lower().strip()
    if category_name not in TOOL_CATEGORIES:
        valid_categories = ", ".join(f'"{name}"' for name in TOOL_CATEGORIES)
        raise ValueError(
            f"Unknown tool category: '{category_name}'. Valid categories are: {valid_categories}"
        )
    return TOOL_CATEGORIES[category_name]


def list_tool_categories(include_experimental: bool = False) -> List[str]:
    """
    Get a list of all available tool category names.

    Args:
        include_experimental: Whether to include experimental tool categories

    Returns:
        List of tool category names, optionally filtered by experimental status
    """
    if include_experimental:
        return list(TOOL_CATEGORIES.keys())

    # Filter out experimental tools
    return [
        name for name, cls in TOOL_CATEGORIES.items() if not getattr(cls, "EXPERIMENTAL", False)
    ]


def get_tool_category_info(category_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific tool category.

    Args:
        category_name: Name of the tool category

    Returns:
        Dictionary containing category information including:
        - name: Internal name of the category
        - display_name: Human-readable name
        - description: Detailed description
        - version: Version string
        - experimental: Whether this is an experimental feature
        - requires_gpu: Whether GPU acceleration is required
        - tools: List of available tools in this category

    Raises:
        ValueError: If the category name is invalid
    """
    category = get_tool_category(category_name)

    # Get basic metadata from the class
    info: Dict[str, Any] = {
        "name": category_name,
        "display_name": getattr(category, "DISPLAY_NAME", category_name.replace("_", " ").title()),
        "description": (getattr(category, "__doc__", "") or "No description available").strip(),
        "version": getattr(category, "VERSION", "0.1.0"),
        "experimental": getattr(category, "EXPERIMENTAL", False),
        "requires_gpu": getattr(category, "REQUIRES_GPU", False),
        "tools": [],
    }

    # Find all public methods that are marked as tools
    for name in dir(category):
        if name.startswith("_"):
            continue

        method = getattr(category, name)
        if callable(method) and hasattr(method, "_tool_metadata"):
            tool_info = {
                "name": name,
                "description": method._tool_metadata.get("description", ""),
                "parameters": method._tool_metadata.get("parameters", {}),
            }
            info["tools"].append(tool_info)

    return info
