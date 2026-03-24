"""
Minimal Inkscape CLI Wrapper for essential vector graphics operations.

This module provides core Inkscape command-line functionality for MCP operations.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class InkscapeCliError(Exception):
    """Base exception for Inkscape CLI operations."""

    pass


class InkscapeTimeoutError(InkscapeCliError):
    """Exception for Inkscape operation timeouts."""

    pass


class InkscapeExecutionError(InkscapeCliError):
    """Exception for Inkscape execution failures."""

    pass


class InkscapeCliWrapper:
    """
    Minimal Inkscape CLI wrapper for essential vector graphics operations.
    """

    def __init__(self, config):
        """
        Initialize wrapper with config.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Basic validation
        if not hasattr(config, "inkscape_executable") or not config.inkscape_executable:
            raise InkscapeCliError("Inkscape executable not configured")

        if not Path(config.inkscape_executable).exists():
            raise InkscapeCliError(f"Inkscape executable not found: {config.inkscape_executable}")

    async def export_file(
        self,
        input_path: str,
        output_path: str,
        export_type: str = "png",
        dpi: int = 300,
        export_area: str = "drawing",
        timeout: Optional[int] = None,
    ) -> str:
        """
        Export SVG file to raster or vector format using Inkscape CLI.

        Args:
            input_path: Input SVG file path
            output_path: Output file path
            export_type: Export format (png, pdf, eps, svg)
            dpi: Resolution for raster exports (ignored for vector formats)
            export_area: Export area (drawing, page, or custom coordinates)
            timeout: Operation timeout in seconds

        Returns:
            str: Inkscape output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout

        # Build command arguments
        cmd_args = [
            self.config.inkscape_executable,
            "--export-type",
            export_type,
            "--export-filename",
            output_path,
        ]

        # Add DPI for raster formats
        if export_type.lower() in ["png", "jpg", "jpeg", "tiff", "bmp"]:
            cmd_args.extend(["--export-dpi", str(dpi)])

        # Add export area
        if export_area == "drawing":
            cmd_args.append("--export-area-drawing")
        elif export_area == "page":
            cmd_args.append("--export-area-page")
        elif export_area.startswith("custom:"):
            # Custom coordinates: "custom:x0:y0:x1:y1"
            coords = export_area.split(":", 1)[1]
            cmd_args.extend(["--export-area", coords])

        # Add input file
        cmd_args.append(input_path)

        return await self._execute_command(cmd_args, timeout)

    async def query_object(
        self,
        input_path: str,
        object_id: str,
        query_type: str = "bbox",
        timeout: Optional[int] = None,
    ) -> str:
        """
        Query object properties from SVG file using Inkscape CLI.

        Args:
            input_path: Input SVG file path
            object_id: ID of object to query
            query_type: Type of query (bbox, x, y, width, height, all)
            timeout: Operation timeout in seconds

        Returns:
            str: Query result output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout

        # Build command arguments
        cmd_args = [self.config.inkscape_executable, "--query-id", object_id]

        # Add specific query type
        if query_type == "bbox":
            cmd_args.append("--query-bbox")
        elif query_type == "x":
            cmd_args.append("--query-x")
        elif query_type == "y":
            cmd_args.append("--query-y")
        elif query_type == "width":
            cmd_args.append("--query-width")
        elif query_type == "height":
            cmd_args.append("--query-height")
        elif query_type == "all":
            # Query all properties
            pass

        # Add input file
        cmd_args.append(input_path)

        return await self._execute_command(cmd_args, timeout)

    async def execute_verbs(
        self,
        input_path: str,
        verbs: List[str],
        output_path: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """
        Execute Inkscape verbs (actions) on an SVG file.

        Args:
            input_path: Input SVG file path
            verbs: List of Inkscape verb IDs to execute
            output_path: Optional output path (will overwrite input if None)
            timeout: Operation timeout in seconds

        Returns:
            str: Inkscape output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout

        # Build command arguments with HEADLESS MODE (prevents GUI flashes)
        cmd_args = [self.config.inkscape_executable, "--batch-process"]

        # Prevent hanging on missing external resources
        cmd_args.append("--no-remote-resources")

        # Add verbs
        for verb in verbs:
            cmd_args.extend(["--verb", verb])

        # Add output if specified
        if output_path:
            cmd_args.extend(["--export-filename", output_path])

        # Add input file
        cmd_args.append(input_path)

        return await self._execute_command(cmd_args, timeout)

    async def _execute_actions(
        self,
        input_path: str,
        actions: list[str],
        output_path: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """
        Execute Inkscape actions using the --actions flag.

        Args:
            input_path: Input SVG file path
            actions: List of Inkscape action IDs to execute
            output_path: Optional output path
            timeout: Operation timeout in seconds

        Returns:
            str: Inkscape output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout

        cmd_args = [self.config.inkscape_executable]

        # Use --batch-process for headless operation (prevents GUI flashes)
        cmd_args.append("--batch-process")

        # Prevent hanging on missing external resources
        cmd_args.append("--no-remote-resources")

        # Construct the actions string
        actions_str = ";".join(actions)

        # Add input file
        cmd_args.append(str(Path(input_path).resolve()))

        # Add the actions flag
        cmd_args.append(f"--actions={actions_str}")

        # If an output path is specified, add an export action to the chain
        if output_path:
            cmd_args.append(f"--export-filename={str(Path(output_path).resolve())}")
            # Ensure an export action is part of the chain if output_path is given
            if "export-do" not in actions_str:
                cmd_args[-1] += ";export-do"  # Append export-do if not already present

        return await self._execute_command(cmd_args, timeout)

    async def execute_actions(
        self,
        input_path: str,
        actions: list[str],
        output_path: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """
        Execute a sequence of Inkscape actions using --batch-process.

        Args:
            input_path: Input file path
            actions: List of action IDs to execute
            output_path: Optional output path
            timeout: Operation timeout in seconds

        Returns:
            str: Inkscape output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        return await self._execute_actions(input_path, actions, output_path, timeout)

    async def get_document_info(self, input_path: str, timeout: Optional[int] = None) -> str:
        """
        Get document information and metadata from SVG file.

        Args:
            input_path: Input SVG file path
            timeout: Operation timeout in seconds

        Returns:
            str: Document information output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout

        # Build command arguments for document info
        cmd_args = [
            self.config.inkscape_executable,
            "--query-all",  # Get all object information
            input_path,
        ]

        return await self._execute_command(cmd_args, timeout)

    async def _execute_command(self, cmd_args: List[str], timeout: int) -> str:
        """
        Execute command with proper error handling and logging.
        """
        try:
            # Use asyncio.create_subprocess_exec for better async handling
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_environment(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

                # Combine stdout and stderr for Inkscape
                output = (stdout + stderr).decode("utf-8", errors="replace")

                if process.returncode != 0:
                    error_msg = (
                        f"Inkscape command failed with return code {process.returncode}: {output}"
                    )
                    raise InkscapeExecutionError(error_msg)

                return output

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise InkscapeTimeoutError(f"Command timed out after {timeout} seconds")

        except FileNotFoundError:
            raise InkscapeExecutionError(
                f"Inkscape executable not found: {self.config.inkscape_executable}"
            )
        except Exception as e:
            raise InkscapeExecutionError(f"Command execution failed: {e}")

    def _get_environment(self) -> Dict[str, str]:
        """
        Get environment variables for subprocess execution.
        """
        env = os.environ.copy()

        # Ensure UTF-8 encoding
        env["LANG"] = "C.UTF-8"
        env["LC_ALL"] = "C.UTF-8"

        return env


# Backward compatibility alias for legacy code
GimpCliWrapper = InkscapeCliWrapper
