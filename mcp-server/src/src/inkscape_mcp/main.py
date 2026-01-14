"""
Inkscape MCP Server - FastMCP 2.13+ Portmanteau Architecture

This module serves as the main entry point for the Inkscape MCP server, providing
an interface between the MCP protocol and Inkscape's vector graphics functionality.

PORTMANTEAU ARCHITECTURE (v1.0.0):
Instead of 50+ individual tools, Inkscape MCP consolidates related operations into 8
master portmanteau tools. Each tool handles a specific domain with multiple operations.

Tools:
- inkscape_file: File operations (load, save, convert, info)
- inkscape_transform: Geometric transforms (resize, rotate, scale)
- : Object management (create, group, align)
- inkscape_path: Path operations (edit, boolean, stroke/fill)
- inkscape_text: Text handling (create, edit, style)
- inkscape_export: Export operations (PNG, PDF, EPS, SVG variants)
- inkscape_analysis: Document analysis (quality, statistics, validation)
- inkscape_system: System operations (status, help, diagnostics)
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from fastmcp import FastMCP

from .config import InkscapeConfig, load_config
from .inkscape_detector import InkscapeDetector
from .logging_config import setup_logging

# Import portmanteau tools (v3.0.0 architecture)
from .tools import (
    PORTMANTEAU_TOOLS,
)

# Legacy imports for backwards compatibility

# Configure structured logging
logger = setup_logging(component="main")


class InkscapeMCPServer:
    """Main server class for GIMP MCP integration."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the Inkscape MCP Server.

        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path) if config_path else InkscapeConfig()

        # Initialize FastMCP with the server name
        self.mcp = FastMCP("Inkscape MCP Server")

        # Set up tool registration
        self.tools = {}  # Store tool instances for later reference

        # Set up logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        self.logger = logging.getLogger(__name__)
        self.cli_wrapper: Optional[GimpCliWrapper] = None

    def _validate_configuration(self) -> bool:
        """
        Validate server configuration for critical settings.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            # Check required configuration attributes
            required_attrs = ["allowed_directories", "max_file_size_mb"]
            for attr in required_attrs:
                if not hasattr(self.config, attr):
                    logger.error(f"Missing required configuration attribute: {attr}")
                    return False

            # Validate allowed directories exist and are accessible
            allowed_dirs = getattr(self.config, "allowed_directories", [])
            if not allowed_dirs:
                logger.warning("No allowed directories configured - this may limit functionality")
            else:
                for dir_path in allowed_dirs:
                    path = Path(dir_path)
                    if not path.exists():
                        logger.warning(f"Allowed directory does not exist: {path}")
                    elif not path.is_dir():
                        logger.error(f"Allowed path is not a directory: {path}")
                        return False

            # Validate max file size is reasonable
            max_size = getattr(self.config, "max_file_size_mb", 100)
            if not isinstance(max_size, (int, float)) or max_size <= 0:
                logger.error(f"Invalid max_file_size_mb: {max_size}")
                return False

            logger.info("Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False

    def _safe_register_tool_category(self, category_name: str, tool_class, init_args: list) -> bool:
        """
        Safely register a tool category with comprehensive error handling.

        Args:
            category_name: Name of the tool category
            tool_class: Tool class to instantiate
            init_args: Arguments for tool initialization

        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            logger.info(f"Initializing {category_name} tools...")

            # Create tool instance with error handling
            tool_instance = tool_class(*init_args)
            logger.info(f"Created {category_name} tool instance")

            # Register tools with the MCP app
            tool_instance.register_tools(self.mcp)
            logger.info(f"Registered {category_name} tools successfully")

            # Store reference for status tracking
            self.tools[category_name] = tool_instance

            return True

        except Exception as e:
            logger.error(f"Failed to register {category_name} tools: {e}", exc_info=True)
            # Don't crash - continue with other categories
            return False

    async def initialize(self) -> bool:
        """
        Initialize the Inkscape MCP Server with comprehensive error handling and recovery.

        This method sets up all portmanteau tools (v3.0.0 architecture) with robust
        error handling to ensure the server can continue operating even if some
        components fail to initialize.

        Returns:
            bool: True if initialization successful, False if critical failure
        """
        try:
            logger.info("Starting Inkscape MCP Server v3.0.0 (Portmanteau Architecture)...")

            # Validate configuration first
            if not self._validate_configuration():
                logger.error("Configuration validation failed - aborting initialization")
                return False

            # Initialize GIMP detector
            self.gimp_detector = InkscapeDetector()

            # Try to detect GIMP installation
            gimp_path = None
            try:
                gimp_path = self.gimp_detector.detect_gimp_installation()
            except Exception as e:
                logger.warning(f"Error detecting GIMP installation: {e}")

            if gimp_path:
                logger.info(f"Found GIMP at: {gimp_path}")
                self.config.gimp_executable = str(gimp_path)

                # Initialize CLI wrapper
                try:
                    self.cli_wrapper = GimpCliWrapper(self.config)
                    logger.info("Initialized GIMP CLI wrapper")
                except Exception as e:
                    logger.error(f"Failed to initialize GIMP CLI wrapper: {e}")
                    self.cli_wrapper = None
            else:
                logger.warning("GIMP not found. Running in limited functionality mode")
                self.cli_wrapper = None

            # Register portmanteau tools (v3.0.0 architecture)
            logger.info("Registering portmanteau tools...")
            portmanteau_registered = self._register_portmanteau_tools()

            if portmanteau_registered:
                logger.info(f"Successfully registered {len(PORTMANTEAU_TOOLS)} portmanteau tools")
                # Count total operations
                total_ops = sum(len(t["operations"]) for t in PORTMANTEAU_TOOLS)
                logger.info(f"Total operations available: {total_ops}")
            else:
                logger.warning("Portmanteau registration failed, falling back to legacy tools")
                # Fall back to legacy tool registration
                return await self._initialize_legacy_tools()

            return True

        except Exception as e:
            logger.error(f"Critical error during initialization: {e}", exc_info=True)
            return False

    def _register_portmanteau_tools(self) -> bool:
        """
        Register all portmanteau tools with FastMCP.

        Returns:
            bool: True if registration successful
        """
        try:
            # Register each portmanteau tool with the MCP instance
            # We wrap them to inject cli_wrapper and config

            @self.mcp.tool()
            async def gimp_file_tool(
                operation: str,
                input_path: str = None,
                output_path: str = None,
                format: str = None,
                quality: int = 95,
                compression: int = 6,
                progressive: bool = False,
            ) -> Dict[str, Any]:
                """File operations: load, save, convert, info, validate, list_formats."""
                return await gimp_file(
                    operation=operation,
                    input_path=input_path,
                    output_path=output_path,
                    format=format,
                    quality=quality,
                    compression=compression,
                    progressive=progressive,
                    cli_wrapper=self.cli_wrapper,
                    config=self.config,
                )

            @self.mcp.tool()
            async def gimp_transform_tool(
                operation: str,
                input_path: str,
                output_path: str,
                width: int = None,
                height: int = None,
                maintain_aspect: bool = True,
                x: int = 0,
                y: int = 0,
                degrees: float = 0.0,
                direction: str = "horizontal",
                fill_color: str = "transparent",
            ) -> Dict[str, Any]:
                """Transforms: resize, crop, rotate, flip, scale, perspective, autocrop."""
                return await gimp_transform(
                    operation=operation,
                    input_path=input_path,
                    output_path=output_path,
                    width=width,
                    height=height,
                    maintain_aspect=maintain_aspect,
                    x=x,
                    y=y,
                    degrees=degrees,
                    direction=direction,
                    fill_color=fill_color,
                    cli_wrapper=self.cli_wrapper,
                    config=self.config,
                )

            @self.mcp.tool()
            async def gimp_color_tool(
                operation: str,
                input_path: str,
                output_path: str,
                brightness: float = 0.0,
                contrast: float = 0.0,
                hue: float = 0.0,
                saturation: float = 0.0,
                lightness: float = 0.0,
                gamma: float = 1.0,
                levels: int = 8,
                threshold: float = 0.5,
                mode: str = "luminosity",
            ) -> Dict[str, Any]:
                """Color adjustments: brightness_contrast, levels, curves, hue_saturation, etc."""
                return await gimp_color(
                    operation=operation,
                    input_path=input_path,
                    output_path=output_path,
                    brightness=brightness,
                    contrast=contrast,
                    hue=hue,
                    saturation=saturation,
                    lightness=lightness,
                    gamma=gamma,
                    levels=levels,
                    threshold=threshold,
                    mode=mode,
                    cli_wrapper=self.cli_wrapper,
                    config=self.config,
                )

            @self.mcp.tool()
            async def gimp_filter_tool(
                operation: str,
                input_path: str,
                output_path: str,
                radius: float = 1.0,
                amount: float = 0.5,
                method: str = "gaussian",
                effect: str = "oilify",
            ) -> Dict[str, Any]:
                """Filters: blur, sharpen, noise, edge_detect, artistic, enhance, distort."""
                return await gimp_filter(
                    operation=operation,
                    input_path=input_path,
                    output_path=output_path,
                    radius=radius,
                    amount=amount,
                    method=method,
                    effect=effect,
                    cli_wrapper=self.cli_wrapper,
                    config=self.config,
                )

            @self.mcp.tool()
            async def gimp_layer_tool(
                operation: str,
                input_path: str,
                output_path: str,
                layer_name: str = "New Layer",
                layer_index: int = 0,
                opacity: float = 100.0,
                blend_mode: str = "normal",
                visible: bool = True,
            ) -> Dict[str, Any]:
                """Layer management: create, duplicate, delete, merge, flatten, reorder, info."""
                return await gimp_layer(
                    operation=operation,
                    input_path=input_path,
                    output_path=output_path,
                    layer_name=layer_name,
                    layer_index=layer_index,
                    opacity=opacity,
                    blend_mode=blend_mode,
                    visible=visible,
                    cli_wrapper=self.cli_wrapper,
                    config=self.config,
                )

            @self.mcp.tool()
            async def gimp_analysis_tool(
                operation: str,
                input_path: str,
                compare_path: str = None,
                include_histogram: bool = True,
                analysis_type: str = "comprehensive",
                report_format: str = "detailed",
            ) -> Dict[str, Any]:
                """Image analysis: quality, statistics, histogram, compare, detect_issues, report."""
                return await gimp_analysis(
                    operation=operation,
                    input_path=input_path,
                    compare_path=compare_path,
                    include_histogram=include_histogram,
                    analysis_type=analysis_type,
                    report_format=report_format,
                    cli_wrapper=self.cli_wrapper,
                    config=self.config,
                )

            @self.mcp.tool()
            async def gimp_batch_tool(
                operation: str,
                input_directory: str,
                output_directory: str,
                width: int = None,
                height: int = None,
                output_format: str = "jpg",
                quality: int = 90,
                file_pattern: str = "*.jpg",
                max_workers: int = 4,
            ) -> Dict[str, Any]:
                """Batch processing: resize, convert, process, watermark, rename, optimize."""
                return await gimp_batch(
                    operation=operation,
                    input_directory=input_directory,
                    output_directory=output_directory,
                    width=width,
                    height=height,
                    output_format=output_format,
                    quality=quality,
                    file_pattern=file_pattern,
                    max_workers=max_workers,
                    cli_wrapper=self.cli_wrapper,
                    config=self.config,
                )

            @self.mcp.tool()
            async def gimp_system_tool(
                operation: str,
                topic: str = None,
                level: str = "basic",
                cache_action: str = "status",
            ) -> Dict[str, Any]:
                """System: status, help, diagnostics, cache, config, performance, tools, version."""
                return await gimp_system(
                    operation=operation,
                    topic=topic,
                    level=level,
                    cache_action=cache_action,
                    cli_wrapper=self.cli_wrapper,
                    config=self.config,
                )

            # Track registered tools
            self.tools = {
                "gimp_file": gimp_file_tool,
                "gimp_transform": gimp_transform_tool,
                "gimp_color": gimp_color_tool,
                "gimp_filter": gimp_filter_tool,
                "gimp_layer": gimp_layer_tool,
                "gimp_analysis": gimp_analysis_tool,
                "gimp_batch": gimp_batch_tool,
                "gimp_system": gimp_system_tool,
            }

            return True

        except Exception as e:
            logger.error(f"Failed to register portmanteau tools: {e}", exc_info=True)
            return False

    async def _initialize_legacy_tools(self) -> bool:
        """
        Fall back to legacy tool registration (for backwards compatibility).

        Returns:
            bool: True if initialization successful
        """
        try:
            # Import all tool categories from the legacy tools package
            from .tools_legacy import (
                HelpTools,
                StatusTools,
                FileOperationTools,
                TransformTools,
                ColorAdjustmentTools,
                LayerManagementTools,
                ImageAnalysisTools,
                FilterTools,
                BatchProcessingTools,
                PerformanceTools,
            )

            # Define tool categories with their constructors
            tool_categories = [
                ("help", HelpTools, [self.cli_wrapper, self.config, {}]),
                ("status", StatusTools, [self.cli_wrapper, self.config]),
                ("file", FileOperationTools, [self.cli_wrapper, self.config]),
                ("transform", TransformTools, [self.cli_wrapper, self.config]),
                ("color", ColorAdjustmentTools, [self.cli_wrapper, self.config]),
                ("layer", LayerManagementTools, [self.cli_wrapper, self.config]),
                ("image", ImageAnalysisTools, [self.cli_wrapper, self.config]),
                ("filter", FilterTools, [self.cli_wrapper, self.config]),
                ("batch", BatchProcessingTools, [self.cli_wrapper, self.config]),
                ("performance", PerformanceTools, [self.cli_wrapper, self.config]),
            ]

            # Register tool categories with safe error handling
            registration_results = {}
            for category_name, tool_class, init_args in tool_categories:
                success = self._safe_register_tool_category(category_name, tool_class, init_args)
                registration_results[category_name] = success

            # Log registration summary
            successful_count = sum(registration_results.values())
            total_count = len(registration_results)
            logger.info(
                f"Legacy tool registration: {successful_count}/{total_count} categories registered"
            )

            return successful_count > 0

        except Exception as e:
            logger.error(f"Legacy tool initialization failed: {e}", exc_info=True)
            return False

    def run_http(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Run the server in HTTP mode.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        # Check if we have tool categories registered
        if not self.tools:
            logger.warning(
                "No tool categories were registered. Running in limited functionality mode."
            )
        else:
            tool_count = len(self.tools)
            logger.info(f"Starting HTTP server with {tool_count} tool categories registered")

        # Start the server
        logger.info(f"Starting HTTP server on {host}:{port}")
        self.mcp.run(transport="http", host=host, port=port)

    def run_stdio(self) -> None:
        """Run the server in stdio mode."""
        # Check if we have tool categories registered
        if not self.tools:
            logger.warning(
                "No tool categories were registered. Running in limited functionality mode."
            )
        else:
            tool_count = len(self.tools)
            logger.info(f"Starting stdio server with {tool_count} tool categories registered")

        # Start the server
        logger.info("Starting stdio server")
        self.mcp.run(transport="stdio")


def main():
    # Configure basic logging first to capture early messages
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
        handlers=[
            logging.StreamHandler(sys.stderr)  # Ensure logs go to stderr
        ],
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Inkscape MCP Server...")

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Inkscape MCP Server")
    parser.add_argument("--config", type=str, help="Path to config file", default=None)
    parser.add_argument(
        "--mode", choices=["stdio", "http"], default="stdio", help="Server mode (default: stdio)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port for HTTP server (default: 8000)"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    args = parser.parse_args()
    logger.debug(f"Command line arguments: {args}")

    # Configure logging
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,  # Force reconfiguration of root logger
    )

    logger.debug(f"Logging configured at level: {args.log_level}")
    logger.info(f"Starting Inkscape MCP Server with log level: {args.log_level}")

    # Initialize server
    logger.debug("Initializing server...")
    try:
        server = InkscapeMCPServer(config_path=Path(args.config) if args.config else None)
        logger.debug("Server instance created")
    except Exception as e:
        logger.error(f"Error creating server: {e}")
        raise

    # Initialize server components
    logger.debug("Initializing server components...")
    try:
        init_result = asyncio.run(server.initialize())
        logger.debug(f"Server initialization result: {init_result}")
        if not init_result:
            logger.error("Failed to initialize Inkscape MCP Server")
            return 1
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        logger.exception("Failed to initialize Inkscape MCP Server")
        return 1

    try:
        if args.mode == "http":
            logger.info(f"Starting HTTP server on {args.host}:{args.port}")
            server.run_http(host=args.host, port=args.port)
        else:
            logger.info("Starting stdio server")
            server.run_stdio()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Server error:")
        logger.error(f"Server error: {e}")
        return 1

    logger.info("Server shutdown complete")
    return 0


if __name__ == "__main__":
    main()
