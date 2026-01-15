"""
Inkscape MCP Server implementation.

This module provides the main FastMCP server class that registers and handles
all Inkscape vector graphics tools via the Model Context Protocol.
"""

import logging
import os
from typing import Any, Dict

from fastmcp import FastMCP

from .cli_wrapper import InkscapeCliWrapper
from .config import InkscapeConfig
# from .plugins import PluginManager

# Import all tool categories from legacy tools
# from .tools_legacy.file_operations_tools import FileOperationTools
# from .tools_legacy.transforms import TransformTools
# from .tools_legacy.color_adjustments import ColorAdjustmentTools
# from .tools_legacy.filters import FilterTools
# from .tools_legacy.batch_processing import BatchProcessingTools
# from .tools_legacy.help_tools import HelpTools
# from .tools_legacy.layer_management import LayerManagementTools
# from .tools_legacy.image_analysis import ImageAnalysisTools
# from .tools_legacy.performance_tools import # PerformanceTools

logger = logging.getLogger(__name__)

# Core plugin classes that should always be loaded
CORE_PLUGINS = [
    #    # ,
    # ,
    # ,
    # ,
    # ,
    # ,
    # ,
    # ,
    # PerformanceTools           # New: Performance optimization tools
]


class InkscapeMcpServer:
    """
    Main GIMP MCP Server class.

    Coordinates all GIMP operations and provides MCP tool registration.
    """

    def __init__(self, config: InkscapeConfig):
        """
        Initialize GIMP MCP Server.

        Args:
            config: Server configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize GIMP CLI wrapper
        self.cli_wrapper = InkscapeCliWrapper(config)

        # Initialize plugin manager
        self.plugin_manager = PluginManager(self.cli_wrapper, config)

        # Register core plugins
        self._register_core_plugins()

        # Load additional plugins from configured directories
        self._load_additional_plugins()

        # Initialize help tools after all plugins are loaded
        self._initialize_help_tools()

        self.logger.info("GIMP MCP Server initialized")

    def _register_core_plugins(self) -> None:
        """Register core plugins that are part of the main package."""
        self.logger.info("Registering core plugins...")

        # Create instances of core plugins and add them to the plugin manager
        for plugin_class in CORE_PLUGINS:
            try:
                plugin_name = plugin_class.get_plugin_name()
                plugin_instance = plugin_class(self.cli_wrapper, self.config)
                self.plugin_manager.plugins[plugin_name] = plugin_instance
                self.logger.debug(f"Registered core plugin: {plugin_name}")
            except Exception as e:
                self.logger.error(
                    f"Failed to register core plugin {plugin_class.__name__}: {e}", exc_info=True
                )

    def _load_additional_plugins(self) -> None:
        """Load additional plugins from configured directories."""
        if not hasattr(self.config, "plugin_dirs"):
            return

        plugin_dirs = self.config.plugin_dirs or []

        # Add default plugins directory if it exists
        default_plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        if os.path.isdir(default_plugin_dir) and default_plugin_dir not in plugin_dirs:
            plugin_dirs.append(default_plugin_dir)

        # Load plugins from all specified directories
        for plugin_dir in plugin_dirs:
            try:
                if os.path.isdir(plugin_dir):
                    self.plugin_manager.load_plugins([plugin_dir])
                    self.logger.info(f"Loaded plugins from: {plugin_dir}")
                else:
                    self.logger.warning(f"Plugin directory not found: {plugin_dir}")
            except Exception as e:
                self.logger.error(f"Error loading plugins from {plugin_dir}: {e}", exc_info=True)

    def _initialize_help_tools(self) -> None:
        """Initialize help tools with references to all loaded plugins."""
        # Get all tool categories from loaded plugins
        tool_categories = {}
        for plugin_name, plugin in self.plugin_manager.plugins.items():
            # Skip the help tools plugin itself to avoid circular reference
            if plugin_name == "help_tools":
                self.help_tools = plugin
                continue

            # Add plugin to tool categories for help system
            tool_categories[plugin_name] = plugin

        # If help tools weren't loaded as a plugin, create a default instance
        if not hasattr(self, "help_tools"):
            self.help_tools = HelpTools(
                self.cli_wrapper, self.config, tool_categories=tool_categories
            )

            # Add help tools to the plugin manager
            self.plugin_manager.plugins["help_tools"] = self.help_tools

        self.logger.info(f"Initialized help tools with {len(tool_categories)} tool categories")

    def register_tools(self, app: FastMCP) -> None:
        """
        Register all GIMP tools with the FastMCP app.

        Args:
            app: FastMCP application instance
        """
        self.logger.info("Registering GIMP MCP tools...")

        # Register tools from all plugins
        self.plugin_manager.register_tools(app)

        # Register batch processing tools (if enabled)
        if hasattr(self.config, "enable_batch_operations") and self.config.enable_batch_operations:
            if "batch_processing" in self.plugin_manager.plugins:
                self.plugin_manager.plugins["batch_processing"].register_tools(app)

        # Register performance tools (if enabled)
        if (
            hasattr(self.config, "enable_performance_optimization")
            and self.config.enable_performance_optimization
        ):
            if "performance_tools" in self.plugin_manager.plugins:
                self.plugin_manager.plugins["performance_tools"].register_tools(app)

        self.logger.info(f"Registered tools from {len(self.plugin_manager.plugins)} plugins")

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform server health check.

        Returns:
            Dict[str, Any]: Health status information
        """
        try:
            # Test GIMP CLI wrapper
            test_result = await self._test_gimp_connection()

            # Get plugin information
            plugin_info = {}
            for plugin_name, plugin in self.plugin_manager.plugins.items():
                try:
                    if hasattr(plugin, "get_plugin_info"):
                        plugin_info[plugin_name] = plugin.get_plugin_info()
                    else:
                        plugin_info[plugin_name] = {"status": "active", "tools": "unknown"}
                except Exception as e:
                    plugin_info[plugin_name] = {"status": "error", "error": str(e)}

            return {
                "status": "healthy" if test_result else "unhealthy",
                "gimp_executable": self.config.gimp_executable,
                "gimp_available": test_result,
                "temp_directory": self.config.temp_directory,
                "supported_formats": len(self.config.supported_formats),
                "max_concurrent_processes": self.config.max_concurrent_processes,
                "batch_operations_enabled": self.config.enable_batch_operations,
                "performance_optimization_enabled": getattr(
                    self.config, "enable_performance_optimization", False
                ),
                "plugins": plugin_info,
                "total_plugins": len(self.plugin_manager.plugins),
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _test_gimp_connection(self) -> bool:
        """
        Test GIMP connection with a simple operation.

        Returns:
            bool: True if GIMP is responsive
        """
        try:
            # Simple Script-Fu test
            test_script = '(gimp-message "GIMP_MCP_TEST:OK")'
            output = await self.cli_wrapper.execute_script_fu(test_script, timeout=10)
            return "GIMP_MCP_TEST:OK" in output

        except Exception as e:
            self.logger.error(f"GIMP connection test failed: {e}")
            return False
