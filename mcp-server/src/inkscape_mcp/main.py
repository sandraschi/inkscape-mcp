"""
Inkscape MCP Server - FastMCP 2.13+ Portmanteau Architecture

This module serves as the main entry point for the Inkscape MCP server, providing
an interface between the MCP protocol and Inkscape's vector graphics functionality.

PORTMANTEAU ARCHITECTURE (v1.0.0):
Instead of 50+ individual tools, Inkscape MCP consolidates related operations into 4
master portmanteau tools. Each tool handles a specific domain with multiple operations.

Tools:
- inkscape_file: File operations (load, save, convert, info, validate)
- inkscape_vector: Advanced vector operations (trace, boolean, path, optimize)
- inkscape_analysis: Document analysis (quality, statistics, structure)
- inkscape_system: System operations (status, help, version)
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from .transport import run_server_async
from .config import InkscapeConfig, load_config
from .inkscape_detector import InkscapeDetector
from .logging_config import setup_logging

from .tools import (
    inkscape_analysis,
    inkscape_file,
    inkscape_system,
    inkscape_vector,
    list_local_models,
)

# Import agentic workflow tools
try:
    from .agentic import register_agentic_tools

    AGENTIC_TOOLS_AVAILABLE = True
except ImportError:
    register_agentic_tools = None
    AGENTIC_TOOLS_AVAILABLE = False

# Import REST API bridge
try:
    from .app import register_rest_api

    REST_API_AVAILABLE = True
except ImportError:
    register_rest_api = None
    REST_API_AVAILABLE = False

# Configure structured logging
logger = setup_logging(component="main")


class InkscapeMCPServer:
    """Main server class for Inkscape MCP integration."""

    def __init__(self, config_path: Path | None = None):
        """Initialize the Inkscape MCP Server.

        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path) if config_path else InkscapeConfig()
        self.mcp = FastMCP("Inkscape MCP Server")
        self.app = self.mcp  # Add app attribute for ASGI compatibility
        self.tools = {}  # Store tool instances for later reference
        self.logger = logging.getLogger(__name__)
        self.cli_wrapper: Any | None = None

    def _validate_configuration(self) -> bool:
        """Validate server configuration."""
        try:
            required_attrs = ["allowed_directories", "max_file_size_mb"]
            for attr in required_attrs:
                if not hasattr(self.config, attr):
                    logger.error(f"Missing required configuration attribute: {attr}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False

    async def initialize(self) -> bool:
        """Initialize server components and register tools."""
        try:
            logger.info("Initializing Inkscape MCP Server...")

            if not self._validate_configuration():
                return False

            # Initialize Inkscape detector
            self.inkscape_detector = InkscapeDetector()
            inkscape_path = self.inkscape_detector.detect_inkscape_installation()

            if inkscape_path:
                logger.info(f"Found Inkscape at: {inkscape_path}")
                self.config.inkscape_executable = str(inkscape_path)

                try:
                    from .cli_wrapper import InkscapeCliWrapper

                    self.cli_wrapper = InkscapeCliWrapper(self.config)
                    logger.info("Initialized Inkscape CLI wrapper")
                except Exception as e:
                    logger.error(f"Failed to initialize Inkscape CLI wrapper: {e}")
                    self.cli_wrapper = None
            else:
                logger.warning(
                    "Inkscape not found. Running in limited functionality mode"
                )
                self.cli_wrapper = None

            # Register portmanteau tools
            self._register_portmanteau_tools()

            # Register agentic workflow tools
            if AGENTIC_TOOLS_AVAILABLE and register_agentic_tools:
                try:
                    register_agentic_tools(self.mcp)
                    logger.info("Agentic workflow tools registered")
                except Exception as e:
                    logger.warning(f"Failed to register agentic tools: {e}")

            # Mount REST API bridge (/api/*)
            if REST_API_AVAILABLE and register_rest_api:
                try:
                    register_rest_api(self.mcp, config=self.config)
                    logger.info("REST API bridge mounted at /api")
                except Exception as e:
                    logger.warning(f"Failed to mount REST API bridge: {e}")

            return True

        except Exception as e:
            logger.error(f"Critical error during initialization: {e}", exc_info=True)
            return False

    def _register_portmanteau_tools(self) -> None:
        """Register all portmanteau tools with FastMCP."""

        @self.mcp.tool()
        async def inkscape_file(
            operation: str,
            input_path: str = None,
            output_path: str = None,
            format: str = None,
        ) -> dict[str, Any]:
            """File operations: load, save, convert, info, validate, list_formats."""
            return await inkscape_file(
                operation=operation,
                input_path=input_path,
                output_path=output_path,
                format=format,
                cli_wrapper=self.cli_wrapper,
                config=self.config,
            )

        @self.mcp.tool()
        async def inkscape_vector(
            operation: str, input_path: str, output_path: str = None
        ) -> dict[str, Any]:
            """Advanced vector operations: trace, boolean, path, optimize, scour, etc."""
            return await inkscape_vector(
                operation=operation,
                input_path=input_path,
                output_path=output_path,
                cli_wrapper=self.cli_wrapper,
                config=self.config,
            )

        @self.mcp.tool()
        async def inkscape_analysis(
            operation: str, input_path: str
        ) -> dict[str, Any]:
            """Document analysis: quality, statistics, structure, objects, dimensions."""
            return await inkscape_analysis(
                operation=operation,
                input_path=input_path,
                cli_wrapper=self.cli_wrapper,
                config=self.config,
            )

        @self.mcp.tool()
        async def inkscape_system(operation: str) -> dict[str, Any]:
            """System: status, help, diagnostics, version, config."""
            return await inkscape_system(
                operation=operation,
                cli_wrapper=self.cli_wrapper,
                config=self.config,
            )

        @self.mcp.tool()
        async def list_local_models() -> dict[str, Any]:
            """Discover local LLM models from Ollama and LM Studio."""
            return await list_local_models()

        self.tools = {
            "inkscape_file": inkscape_file,
            "inkscape_vector": inkscape_vector,
            "inkscape_analysis": inkscape_analysis,
            "inkscape_system": inkscape_system,
            "list_local_models": list_local_models,
        }


async def main_async():
    """Async entry point."""
    # Configure basic logging first
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
        handlers=[logging.StreamHandler(sys.stderr)],
    )
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Inkscape MCP Server")
    parser.add_argument("--config", type=str, help="Path to config file", default=None)
    parser.add_argument("--mode", choices=["stdio", "http", "dual"], default="dual")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--log-level", default="INFO")

    args = parser.parse_args()

    # Re-setup logging with arg level
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level, force=True)

    try:
        server = InkscapeMCPServer(
            config_path=Path(args.config) if args.config else None
        )
        if await server.initialize():
            # Set module-level app for ASGI compatibility
            import inkscape_mcp
            inkscape_mcp.app = server.mcp
            await run_server_async(server.mcp, server_name="Inkscape MCP Server")
        else:
            return 1
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Server error:")
        return 1

    return 0


# Module-level app for ASGI compatibility
app = None  # Will be set when server is initialized


def main():
    """Main entry point."""
    try:
        return asyncio.run(main_async())
    except Exception as e:
        print(f"Unhandled error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
