"""
Inkscape MCP Extension System

This module provides an extension architecture for Inkscape MCP functionality.
Extensions are Python scripts that use the inkex library to manipulate SVG documents.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..config import InkscapeConfig
from ..cli_wrapper import InkscapeCliWrapper

logger = logging.getLogger(__name__)


@dataclass
class ExtensionParameter:
    """Represents a parameter for an Inkscape extension."""
    name: str
    type: str
    default: Any = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    description: str = ""
    required: bool = False


@dataclass
class InkscapeExtension:
    """Represents an Inkscape extension with its metadata and parameters."""
    id: str
    name: str
    description: str
    python_file: Path
    inx_file: Path
    parameters: List[ExtensionParameter]
    category: str = "general"


class ExtensionManager:
    """Manages discovery, loading, and execution of Inkscape extensions."""

    def __init__(self, cli_wrapper: InkscapeCliWrapper, config: InkscapeConfig):
        """Initialize the extension manager.

        Args:
            cli_wrapper: Inkscape CLI wrapper instance
            config: Server configuration
        """
        self.cli_wrapper = cli_wrapper
        self.config = config
        self.extensions: Dict[str, InkscapeExtension] = {}
        self.logger = logging.getLogger(__name__)

    def discover_extensions(self, extension_dirs: Optional[List[str]] = None) -> None:
        """Discover and load extensions from specified directories.

        Args:
            extension_dirs: List of directories to search for extensions.
                          If None, uses default Inkscape extension directories.
        """
        if extension_dirs is None:
            # Default Inkscape extension directories
            import platform
            system = platform.system().lower()

            if system == "windows":
                extension_dirs = [
                    Path.home() / "AppData" / "Roaming" / "inkscape" / "extensions",
                    Path.cwd() / "extensions"
                ]
            elif system == "linux":
                extension_dirs = [
                    Path.home() / ".config" / "inkscape" / "extensions",
                    Path("/usr/share/inkscape/extensions"),
                    Path.cwd() / "extensions"
                ]
            elif system == "darwin":  # macOS
                extension_dirs = [
                    Path.home() / "Library" / "Application Support" / "org.inkscape.Inkscape" / "config" / "extensions",
                    Path.cwd() / "extensions"
                ]
            else:
                extension_dirs = [Path.cwd() / "extensions"]

        for ext_dir in extension_dirs:
            self._discover_extensions_in_directory(Path(ext_dir))

    def _discover_extensions_in_directory(self, ext_dir: Path) -> None:
        """Discover extensions in a specific directory.

        Args:
            ext_dir: Directory to search for .inx files
        """
        if not ext_dir.exists() or not ext_dir.is_dir():
            self.logger.debug(f"Extension directory not found: {ext_dir}")
            return

        self.logger.info(f"Scanning extensions in: {ext_dir}")

        # Find all .inx files
        for inx_file in ext_dir.glob("*.inx"):
            try:
                extension = self._parse_inx_file(inx_file)
                if extension:
                    self.extensions[extension.id] = extension
                    self.logger.info(f"Loaded extension: {extension.name} ({extension.id})")
            except Exception as e:
                self.logger.error(f"Error parsing extension {inx_file}: {e}")

    def _parse_inx_file(self, inx_file: Path) -> Optional[InkscapeExtension]:
        """Parse an .inx file to extract extension metadata.

        Args:
            inx_file: Path to the .inx file

        Returns:
            InkscapeExtension instance or None if parsing failed
        """
        try:
            tree = ET.parse(inx_file)
            root = tree.getroot()

            # Extract basic metadata
            ext_id = root.find(".//id")
            if ext_id is None or not ext_id.text:
                return None

            name_elem = root.find(".//name")
            name = name_elem.text if name_elem is not None else ext_id.text

            # Find the Python script file
            script_elem = root.find(".//script/command")
            if script_elem is None:
                return None

            script_path = inx_file.parent / script_elem.text
            if not script_path.exists():
                return None

            # Parse parameters
            parameters = []
            for param in root.findall(".//param"):
                param_name = param.get("name")
                param_type = param.get("type", "string")
                param_default = param.text or param.get("default")

                # Convert default values based on type
                if param_type == "int":
                    param_default = int(param_default) if param_default else 0
                elif param_type == "float":
                    param_default = float(param_default) if param_default else 0.0
                elif param_type == "bool":
                    param_default = param_default.lower() in ('true', '1', 'yes') if param_default else False

                parameters.append(ExtensionParameter(
                    name=param_name,
                    type=param_type,
                    default=param_default,
                    min_val=float(param.get("min", 0)) if param.get("min") else None,
                    max_val=float(param.get("max", 0)) if param.get("max") else None,
                    description=param.get("gui-text", ""),
                    required=param.get("required", "false").lower() == "true"
                ))

            # Determine category from menu path
            category = "general"
            menu_elem = root.find(".//effects-menu/submenu")
            if menu_elem is not None and menu_elem.text:
                category = menu_elem.text.lower().replace(" ", "_")

            return InkscapeExtension(
                id=ext_id.text,
                name=name,
                description=name,  # Could be enhanced to parse description
                python_file=script_path,
                inx_file=inx_file,
                parameters=parameters,
                category=category
            )

        except Exception as e:
            self.logger.error(f"Error parsing {inx_file}: {e}")
            return None

    async def execute_extension(
        self,
        extension_id: str,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an Inkscape extension.

        Args:
            extension_id: ID of the extension to execute
            input_file: Input SVG file path
            output_file: Output file path
            parameters: Extension parameters

        Returns:
            Dictionary with execution results
        """
        if extension_id not in self.extensions:
            return {
                "success": False,
                "error": f"Extension '{extension_id}' not found",
                "available_extensions": list(self.extensions.keys())
            }

        extension = self.extensions[extension_id]

        try:
            # Build inkscape command
            cmd = [str(self.config.inkscape_executable)]

            if input_file:
                cmd.append(input_file)

            # Add extension parameter
            cmd.extend(["--extension", extension_id])

            # Add custom parameters
            if parameters:
                for param_name, param_value in parameters.items():
                    cmd.extend([f"--{param_name}", str(param_value)])

            # Add output handling
            if output_file:
                cmd.extend(["--export-filename", output_file, "--export-do"])

            # Execute the command
            result = await self.cli_wrapper._execute_command(cmd, timeout=60)

            return {
                "success": True,
                "extension_id": extension_id,
                "extension_name": extension.name,
                "output": result,
                "input_file": input_file,
                "output_file": output_file,
                "parameters": parameters
            }

        except Exception as e:
            self.logger.error(f"Error executing extension {extension_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "extension_id": extension_id
            }

    def list_extensions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available extensions.

        Args:
            category: Optional category filter

        Returns:
            List of extension information
        """
        extensions = self.extensions.values()

        if category:
            extensions = [ext for ext in extensions if ext.category == category]

        return [
            {
                "id": ext.id,
                "name": ext.name,
                "description": ext.description,
                "category": ext.category,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type,
                        "default": param.default,
                        "description": param.description,
                        "required": param.required
                    }
                    for param in ext.parameters
                ]
            }
            for ext in extensions
        ]

    def get_extension(self, extension_id: str) -> Optional[InkscapeExtension]:
        """Get extension by ID.

        Args:
            extension_id: Extension ID to retrieve

        Returns:
            InkscapeExtension instance or None
        """
        return self.extensions.get(extension_id)