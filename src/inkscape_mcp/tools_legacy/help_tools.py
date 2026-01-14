from __future__ import annotations

"""
Help Tools for GIMP MCP Server.

Provides documentation and help information about the GIMP MCP tools
at different technical levels for users, developers, and AI systems.
"""

import logging
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any, Dict, List, Literal, Optional, Type, TypedDict, Union, 
    get_type_hints, cast
)

from fastmcp import FastMCP

from .base import BaseToolCategory

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

logger = logging.getLogger(__name__)

# Type aliases
HelpLevel = Literal["basic", "intermediate", "advanced"]
ToolName: TypeAlias = str
CategoryName: TypeAlias = str
HelpContent: TypeAlias = Dict[HelpLevel, str]

class HelpSection(TypedDict):
    """Structure for help documentation sections."""
    basic: str
    intermediate: str
    advanced: str
    examples: List[Dict[str, str]]
    parameters: Dict[str, Dict[str, Any]]

@dataclass
class ToolDocumentation:
    """Complete documentation for a tool."""
    name: str
    description: str
    category: str
    help_levels: HelpContent
    examples: List[Dict[str, str]] = field(default_factory=list)
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "help_levels": self.help_levels,
            "examples": self.examples,
            "parameters": self.parameters
        }

class HelpTools(BaseToolCategory):
    """
    Comprehensive multilevel help system for GIMP MCP Server.

    Provides detailed documentation, usage examples, and guidance at multiple
    technical levels (beginner, intermediate, advanced, expert) for all GIMP
    image editing capabilities through MCP tools.
    """
    
    def __init__(self, cli_wrapper, config, tool_categories):
        """
        Initialize help tools with references to other tool categories.
        
        Args:
            cli_wrapper: GIMP CLI wrapper instance
            config: Server configuration
            tool_categories: Dictionary of all tool categories
        """
        super().__init__(cli_wrapper, config)
        self.tool_categories = tool_categories
        self._help_data = self._initialize_help_data()
    
    def _initialize_help_data(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive help documentation structure."""
        return {
            "overview": {
                "beginner": "GIMP MCP Server lets you edit images using simple instructions. "
                           "Just tell me what you want to do with your images!",
                "intermediate": "Professional image editing through natural language. "
                               "Supports resizing, filters, color adjustments, layers, and batch processing.",
                "advanced": "Full GIMP automation with Script-Fu integration. "
                          "Access all GIMP tools and effects programmatically.",
                "expert": "Complete GIMP API access with advanced scripting capabilities, "
                        "custom filters, and automation workflows."
            },
            "categories": {
                "file_operations": {
                    "description": "Load, save, and convert image files",
                    "tools": {
                        "load_image": {
                            "description": "Open an image file for editing",
                            "parameters": {"file_path": "Path to image file"},
                            "usage": "Load any supported image format (JPG, PNG, TIFF, etc.)"
                        },
                        "save_image": {
                            "description": "Save edited image to disk",
                            "parameters": {"output_path": "Save location", "format": "Output format"},
                            "usage": "Preserve your work in various formats"
                        }
                    }
                },
                "transforms": {
                    "description": "Resize, crop, rotate, and flip images",
                    "tools": {
                        "resize_image": {
                            "description": "Change image dimensions",
                            "parameters": {"width": "New width", "height": "New height", "maintain_aspect": "Keep proportions"},
                            "usage": "Scale images for web, print, or specific requirements"
                        },
                        "crop_image": {
                            "description": "Cut out rectangular region",
                            "parameters": {"x": "Left edge", "y": "Top edge", "width": "Crop width", "height": "Crop height"},
                            "usage": "Remove unwanted areas or create specific aspect ratios"
                        },
                        "rotate_image": {
                            "description": "Rotate image by degrees",
                            "parameters": {"degrees": "Rotation angle", "fill_color": "Background color"},
                            "usage": "Correct orientation or create artistic effects"
                        },
                        "flip_image": {
                            "description": "Mirror image horizontally or vertically",
                            "parameters": {"direction": "horizontal/vertical"},
                            "usage": "Create mirror effects or correct upside-down images"
                        }
                    }
                },
                "color_adjustments": {
                    "description": "Adjust brightness, contrast, and color balance",
                    "tools": {
                        "adjust_brightness_contrast": {
                            "description": "Modify image brightness and contrast",
                            "parameters": {"brightness": "-100 to +100", "contrast": "-100 to +100"},
                            "usage": "Fix underexposed/overexposed images"
                        },
                        "adjust_hue_saturation": {
                            "description": "Change color hue and saturation",
                            "parameters": {"hue": "Color shift", "saturation": "Color intensity"},
                            "usage": "Color correction and creative effects"
                        },
                        "adjust_levels": {
                            "description": "Precise tonal adjustments",
                            "parameters": {"input_levels": "Input range", "output_levels": "Output range"},
                            "usage": "Professional photo editing and color grading"
                        },
                        "adjust_curves": {
                            "description": "Advanced tonal curve adjustments",
                            "parameters": {"channel": "RGB/R/G/B", "curve_points": "Control points"},
                            "usage": "Fine-tune image tones and contrast"
                        },
                        "adjust_threshold": {
                            "description": "Convert to black and white",
                            "parameters": {"threshold": "Cutoff value 0-255"},
                            "usage": "Create masks or high-contrast effects"
                        },
                        "adjust_posterize": {
                            "description": "Reduce color levels",
                            "parameters": {"levels": "Number of colors"},
                            "usage": "Create poster/artistic effects"
                        },
                        "desaturate": {
                            "description": "Remove color (convert to grayscale)",
                            "parameters": {"mode": "Conversion method"},
                            "usage": "Convert to black and white"
                        }
                    }
                },
                "layer_management": {
                    "description": "Work with image layers",
                    "tools": {
                        "create_layer": {
                            "description": "Add new layer to image",
                            "parameters": {"name": "Layer name", "opacity": "Transparency 0-100"},
                            "usage": "Build complex compositions with multiple elements"
                        },
                        "duplicate_layer": {
                            "description": "Copy existing layer",
                            "parameters": {"layer_index": "Which layer to copy"},
                            "usage": "Create variations or backups"
                        },
                        "delete_layer": {
                            "description": "Remove layer from image",
                            "parameters": {"layer_index": "Which layer to delete"},
                            "usage": "Clean up composition"
                        },
                        "merge_layers": {
                            "description": "Combine multiple layers",
                            "parameters": {"layer_indices": "Which layers to merge"},
                            "usage": "Flatten composition or combine elements"
                        },
                        "set_layer_properties": {
                            "description": "Change layer settings",
                            "parameters": {"opacity": "Transparency", "blend_mode": "Blending method"},
                            "usage": "Adjust layer appearance and interaction"
                        }
                    }
                },
                "filters": {
                    "description": "Apply artistic and corrective filters",
                    "tools": {
                        "apply_blur": {
                            "description": "Blur image or selection",
                            "parameters": {"radius": "Blur amount", "method": "Blur type"},
                            "usage": "Soften images or create depth of field effects"
                        },
                        "apply_sharpen": {
                            "description": "Increase image sharpness",
                            "parameters": {"amount": "Sharpen strength", "radius": "Sharpen radius"},
                            "usage": "Fix blurry images or enhance details"
                        },
                        "apply_noise": {
                            "description": "Add texture or grain",
                            "parameters": {"amount": "Noise intensity", "type": "Noise pattern"},
                            "usage": "Create texture effects or reduce banding"
                        },
                        "apply_edge_detect": {
                            "description": "Highlight edges in image",
                            "parameters": {"algorithm": "Edge detection method"},
                            "usage": "Create line art or technical illustrations"
                        },
                        "apply_emboss": {
                            "description": "Create 3D embossed effect",
                            "parameters": {"azimuth": "Light direction", "elevation": "Light height"},
                            "usage": "Add depth and texture to flat images"
                        }
                    }
                },
                "image_analysis": {
                    "description": "Analyze image properties and quality",
                    "tools": {
                        "analyze_image_quality": {
                            "description": "Assess image quality metrics",
                            "parameters": {"analysis_type": "Type of analysis"},
                            "usage": "Check image sharpness, noise, and compression artifacts"
                        },
                        "extract_image_statistics": {
                            "description": "Get numerical image data",
                            "parameters": {"include_histogram": "Include color distribution"},
                            "usage": "Technical analysis of image properties"
                        },
                        "detect_image_issues": {
                            "description": "Find common image problems",
                            "parameters": {"check_types": "Issues to look for"},
                            "usage": "Identify compression artifacts, noise, or exposure issues"
                        },
                        "compare_images": {
                            "description": "Compare two images",
                            "parameters": {"image1": "First image", "image2": "Second image"},
                            "usage": "Find differences between versions"
                        }
                    }
                },
                "batch_processing": {
                    "description": "Process multiple images simultaneously",
                    "tools": {
                        "batch_resize": {
                            "description": "Resize multiple images",
                            "parameters": {"input_dir": "Source folder", "output_dir": "Destination folder"},
                            "usage": "Prepare image sets for web or consistent sizing"
                        },
                        "batch_convert": {
                            "description": "Convert multiple images to new format",
                            "parameters": {"input_dir": "Source folder", "output_format": "New format"},
                            "usage": "Format conversion for different use cases"
                        }
                    }
                },
                "performance": {
                    "description": "Optimize processing and monitor system",
                    "tools": {
                        "optimize_image_processing": {
                            "description": "Enhance processing speed",
                            "parameters": {"input_path": "Image to optimize", "level": "Optimization level"},
                            "usage": "Speed up image operations and reduce memory usage"
                        },
                        "clear_cache": {
                            "description": "Free up system resources",
                            "parameters": {"cache_type": "What to clear"},
                            "usage": "Improve system performance"
                        },
                        "get_performance_metrics": {
                            "description": "Monitor system performance",
                            "parameters": {"operation_type": "Specific operation"},
                            "usage": "Track processing efficiency"
                        },
                        "get_system_performance_info": {
                            "description": "System resource information",
                            "parameters": {},
                            "usage": "Monitor CPU, memory, and disk usage"
                        }
                    }
                },
                "status": {
                    "description": "Monitor system status and diagnostics",
                    "tools": {
                        "get_server_status": {
                            "description": "Get comprehensive server status",
                            "parameters": {},
                            "usage": "Check server health, uptime, and resource usage"
                        },
                        "get_system_info": {
                            "description": "Get system information and capabilities",
                            "parameters": {},
                            "usage": "View system specs, GIMP status, and configuration"
                        },
                        "check_tool_health": {
                            "description": "Perform tool health checks",
                            "parameters": {},
                            "usage": "Verify all tools are functioning properly"
                        },
                        "get_performance_metrics": {
                            "description": "Get performance statistics",
                            "parameters": {"time_range": "Time period to analyze"},
                            "usage": "Monitor operation counts, error rates, and efficiency"
                        },
                        "diagnose_issues": {
                            "description": "Run diagnostic checks",
                            "parameters": {},
                            "usage": "Identify potential issues and get recommendations"
                        },
                        "get_operational_log": {
                            "description": "View recent log entries",
                            "parameters": {"level": "Minimum log level", "limit": "Max entries"},
                            "usage": "Review recent server activity and errors"
                        }
                    }
                }
            },
            "usage_examples": {
                "beginner": [
                    "Make my photo brighter",
                    "Resize this image to 800x600",
                    "Add a blur effect to the background",
                    "Convert this JPG to PNG"
                ],
                "intermediate": [
                    "Apply unsharp mask sharpening with radius 1.0 and amount 0.8",
                    "Create a high-contrast black and white version",
                    "Batch resize all images in folder to web dimensions",
                    "Adjust color balance for better skin tones"
                ],
                "advanced": [
                    "Chain resize -> sharpen -> save operations",
                    "Apply selective color adjustments to specific image regions",
                    "Create custom filter pipelines for consistent processing",
                    "Use layer masks for complex image compositions"
                ],
                "expert": [
                    "Execute custom GIMP Script-Fu procedures",
                    "Implement advanced color grading with curves",
                    "Create automated workflows with conditional processing",
                    "Use advanced blending modes for professional composites"
                ]
            },
            "troubleshooting": {
                "common_issues": [
                    "Out of memory: Reduce image size or use batch processing",
                    "File not found: Check file paths and permissions",
                    "Invalid format: Ensure supported image formats",
                    "Processing slow: Enable optimization or reduce quality settings"
                ],
                "best_practices": [
                    "Use appropriate file formats for your use case",
                    "Save incrementally to avoid losing work",
                    "Test operations on small images first",
                    "Monitor system resources during batch processing"
                ]
            }
        }
    
    def register_tools(self, app: FastMCP) -> None:
        """Register comprehensive help tools with FastMCP."""

        # Store instance reference for closures
        instance = self

        @app.tool()
        async def get_help_overview(level: str = "beginner") -> Dict[str, Any]:
            """
            Get an overview of GIMP MCP Server capabilities at different skill levels.

            Args:
                level: Skill level (beginner, intermediate, advanced, expert)

            Returns:
                Overview content tailored to the specified skill level
            """
            try:
                level = level.lower()
                if level not in ["beginner", "intermediate", "advanced", "expert"]:
                    return instance.create_error_response(
                        "Invalid skill level. Must be 'beginner', 'intermediate', 'advanced', or 'expert'"
                    )

                return instance.create_success_response({
                    "level": level,
                    "overview": instance._help_data["overview"][level],
                    "available_categories": list(instance._help_data["categories"].keys()),
                    "usage_examples": instance._help_data["usage_examples"][level][:3]  # Top 3 examples
                })

            except Exception as e:
                logger.error(f"Error getting help overview: {e}", exc_info=True)
                return instance.create_error_response("Failed to get help overview")

        @app.tool()
        async def get_category_help(category: str, include_tools: bool = True) -> Dict[str, Any]:
            """
            Get detailed help for a specific tool category.

            Args:
                category: Tool category name (file_operations, transforms, color_adjustments, etc.)
                include_tools: Whether to include detailed tool information

            Returns:
                Category description and available tools
            """
            try:
                category = category.lower()
                if category not in instance._help_data["categories"]:
                    return instance.create_error_response(
                        f"Unknown category '{category}'. Available categories: {', '.join(instance._help_data['categories'].keys())}"
                    )

                cat_data = instance._help_data["categories"][category]
                response = {
                    "category": category,
                    "description": cat_data["description"],
                    "tool_count": len(cat_data["tools"])
                }

                if include_tools:
                    response["tools"] = {
                        name: {
                            "description": info["description"],
                            "usage": info["usage"]
                        }
                        for name, info in cat_data["tools"].items()
                    }

                return instance.create_success_response(response)

            except Exception as e:
                logger.error(f"Error getting category help: {e}", exc_info=True)
                return instance.create_error_response("Failed to get category help")

        @app.tool()
        async def get_tool_help(tool_name: str, category: Optional[str] = None) -> Dict[str, Any]:
            """
            Get detailed help for a specific tool.

            Args:
                tool_name: Name of the tool to get help for
                category: Optional category to search in (speeds up search)

            Returns:
                Detailed tool information including parameters and usage
            """
            try:
                # Search for tool in categories
                found_tool = None
                found_category = None

                search_categories = [category] if category else instance._help_data["categories"].keys()

                for cat_name in search_categories:
                    if cat_name in instance._help_data["categories"]:
                        cat_tools = instance._help_data["categories"][cat_name]["tools"]
                        if tool_name in cat_tools:
                            found_tool = cat_tools[tool_name]
                            found_category = cat_name
                            break

                if not found_tool:
                    return instance.create_error_response(
                        f"Tool '{tool_name}' not found. Use list_all_tools to see available tools."
                    )

                return instance.create_success_response({
                    "tool": tool_name,
                    "category": found_category,
                    "description": found_tool["description"],
                    "parameters": found_tool["parameters"],
                    "usage": found_tool["usage"]
                })

            except Exception as e:
                logger.error(f"Error getting tool help: {e}", exc_info=True)
                return instance.create_error_response("Failed to get tool help")

        @app.tool()
        async def list_all_tools() -> Dict[str, Any]:
            """
            List all available tools organized by category.

            Returns:
                Complete tool inventory with descriptions
            """
            try:
                tools = {}
                total_count = 0

                for category_name, category in instance._help_data["categories"].items():
                    tools[category_name] = {
                        "description": category["description"],
                        "tools": {
                            name: info["description"]
                            for name, info in category["tools"].items()
                        }
                    }
                    total_count += len(category["tools"])

                return instance.create_success_response({
                    "total_tools": total_count,
                    "categories": tools,
                    "categories_count": len(tools)
                })

            except Exception as e:
                logger.error(f"Error listing tools: {e}", exc_info=True)
                return instance.create_error_response("Failed to list tools")

        @app.tool()
        async def get_usage_examples(level: str = "beginner", category: Optional[str] = None) -> Dict[str, Any]:
            """
            Get usage examples for different skill levels.

            Args:
                level: Skill level (beginner, intermediate, advanced, expert)
                category: Optional category to filter examples

            Returns:
                Usage examples appropriate for the skill level
            """
            try:
                level = level.lower()
                if level not in ["beginner", "intermediate", "advanced", "expert"]:
                    return instance.create_error_response(
                        "Invalid skill level. Must be 'beginner', 'intermediate', 'advanced', or 'expert'"
                    )

                examples = instance._help_data["usage_examples"][level]

                if category:
                    category = category.lower()
                    # Filter examples that might relate to the category
                    filtered_examples = [
                        ex for ex in examples
                        if category in ex.lower() or any(cat in ex.lower() for cat in instance._help_data["categories"])
                    ]
                    examples = filtered_examples or examples

                return instance.create_success_response({
                    "level": level,
                    "category_filter": category,
                    "examples": examples,
                    "count": len(examples)
                })

            except Exception as e:
                logger.error(f"Error getting usage examples: {e}", exc_info=True)
                return instance.create_error_response("Failed to get usage examples")

        @app.tool()
        async def get_troubleshooting_help() -> Dict[str, Any]:
            """
            Get troubleshooting information and best practices.

            Returns:
                Common issues, solutions, and best practices
            """
            try:
                return instance.create_success_response({
                    "common_issues": instance._help_data["troubleshooting"]["common_issues"],
                    "best_practices": instance._help_data["troubleshooting"]["best_practices"],
                    "tips": [
                        "Always save your work before complex operations",
                        "Use smaller test images for experimenting",
                        "Check file permissions and paths",
                        "Monitor system resources during batch processing"
                    ]
                })

            except Exception as e:
                logger.error(f"Error getting troubleshooting help: {e}", exc_info=True)
                return instance.create_error_response("Failed to get troubleshooting help")
