"""
Inkscape MCP Server implementation.

This module provides the main FastMCP server class that registers and handles
all Inkscape vector graphics tools via the Model Context Protocol.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from .cli_wrapper import InkscapeCliWrapper
from .config import InkscapeConfig

logger = logging.getLogger(__name__)

# Module-level app for ASGI compatibility
app = None

CORE_PLUGINS: list = []


class InkscapeMcpServer:
    """
    Main Inkscape MCP Server class.

    Handles tool registration, Inkscape CLI integration, and lifecycle management.
    """

    def __init__(self, config: InkscapeConfig | None = None):
        """
        Initialize Inkscape MCP Server.

        Args:
            config: Optional configuration instance
        """
        self.config = config or InkscapeConfig()
        self.mcp = FastMCP("Inkscape MCP", version="1.2.0")
        self.app = self.mcp  # Add app attribute for ASGI compatibility

        # Set module-level app for ASGI loader
        import inkscape_mcp.server

        inkscape_mcp.server.app = self.mcp

        self.tools = {}  # Store tool instances for later reference
        self.inkscape = InkscapeCliWrapper(self.config)
        self.logger = logging.getLogger(__name__)
        self.cli_wrapper: Any | None = None

        self._register_tools()
        logger.info("Inkscape MCP Server initialized")

    def _register_tools(self) -> None:
        """Register all Inkscape tools with FastMCP."""
        # Portmanteau tools are registered here
        from .tools import register_all_tools

        register_all_tools(self.mcp, self.inkscape, self.config)

    async def health_check(self) -> dict[str, Any]:
        """
        Check the health of the server and Inkscape connection.

        Returns:
            Dict containing health status and diagnostic info
        """
        inkscape_ok = await self._test_inkscape_connection()

        return {
            "status": "healthy" if inkscape_ok else "degraded",
            "inkscape_connection": inkscape_ok,
            "config": {
                "inkscape_executable": self.config.inkscape_executable,
                "temp_directory": self.config.temp_directory,
            },
        }

    async def _test_inkscape_connection(self) -> bool:
        """
        Test if Inkscape can be executed.

        Returns:
            bool: True if connection is successful
        """
        try:
            # Simple version check to test connectivity
            result = await self.inkscape._execute_command(
                [self.config.inkscape_executable, "--version"], timeout=5
            )
            return "Inkscape" in result
        except Exception as e:
            logger.error(f"Inkscape connection test failed: {e}")
            return False
