"""
GIMP MCP Plugin System

This module provides a plugin architecture for extending GIMP MCP functionality.
"""
from pathlib import Path
from typing import Dict, Type, Optional, List, Any
import importlib.util
import inspect
import logging
from abc import ABC, abstractmethod

from ..config import InkscapeConfig
from ..cli_wrapper import InkscapeCliWrapper

logger = logging.getLogger(__name__)

class InkscapePlugin(ABC):
    """Base class for all GIMP MCP plugins."""
    
    def __init__(self, cli_wrapper: InkscapeCliWrapper, config: InkscapeConfig):
        """Initialize the plugin with dependencies.
        
        Args:
            cli_wrapper: GIMP CLI wrapper instance
            config: Server configuration
        """
        self.cli_wrapper = cli_wrapper
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @classmethod
    @abstractmethod
    def get_plugin_name(cls) -> str:
        """Return the plugin's unique identifier."""
        pass
    
    @classmethod
    @abstractmethod
    def get_plugin_description(cls) -> str:
        """Return a short description of the plugin's functionality."""
        pass
    
    @abstractmethod
    def register_tools(self, app) -> None:
        """Register all tools provided by this plugin with the FastMCP app.
        
        Args:
            app: FastMCP application instance
        """
        pass


class PluginManager:
    """Manages loading and registration of GIMP MCP plugins."""
    
    def __init__(self, cli_wrapper: InkscapeCliWrapper, config: InkscapeConfig):
        """Initialize the plugin manager.
        
        Args:
            cli_wrapper: GIMP CLI wrapper instance
            config: Server configuration
        """
        self.cli_wrapper = cli_wrapper
        self.config = config
        self.plugins: Dict[str, InkscapePlugin] = {}
        self.logger = logging.getLogger(__name__)
    
    def load_plugins(self, plugin_dirs: Optional[List[str]] = None) -> None:
        """Load plugins from the specified directories.
        
        Args:
            plugin_dirs: List of directories to search for plugins.
                        If None, looks in the default plugins directory.
        """
        if plugin_dirs is None:
            # Default to plugins directory in the same folder as this module
            base_dir = Path(__file__).parent
            plugin_dirs = [str(base_dir / "plugins")]
        
        for plugin_dir in plugin_dirs:
            self._load_plugins_from_directory(plugin_dir)
    
    def _load_plugins_from_directory(self, plugin_dir: str) -> None:
        """Load plugins from a specific directory.
        
        Args:
            plugin_dir: Directory path to search for plugins
        """
        plugin_path = Path(plugin_dir)
        
        if not plugin_path.exists() or not plugin_path.is_dir():
            self.logger.warning(f"Plugin directory not found: {plugin_dir}")
            return
        
        self.logger.info(f"Loading plugins from: {plugin_dir}")
        
        for py_file in plugin_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
                
            module_name = f"gimp_mcp.plugins.{py_file.stem}"
            self._load_plugin_from_file(py_file, module_name)
    
    def _load_plugin_from_file(self, file_path: Path, module_name: str) -> None:
        """Load a single plugin from a Python file.
        
        Args:
            file_path: Path to the plugin file
            module_name: Name to give the imported module
        """
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {file_path}")
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all plugin classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, InkscapePlugin) and 
                    obj != InkscapePlugin and 
                    not inspect.isabstract(obj)):
                    
                    plugin_name = obj.get_plugin_name()
                    if plugin_name in self.plugins:
                        self.logger.warning(
                            f"Plugin '{plugin_name}' from {file_path} already loaded. "
                            f"Skipping duplicate."
                        )
                        continue
                    
                    self.logger.info(f"Loading plugin: {plugin_name}")
                    self.plugins[plugin_name] = obj(self.cli_wrapper, self.config)
        
        except Exception as e:
            self.logger.error(f"Error loading plugin from {file_path}: {e}", exc_info=True)
    
    def register_tools(self, app) -> None:
        """Register all tools from all loaded plugins.
        
        Args:
            app: FastMCP application instance
        """
        for plugin_name, plugin in self.plugins.items():
            try:
                self.logger.info(f"Registering tools from plugin: {plugin_name}")
                plugin.register_tools(app)
            except Exception as e:
                self.logger.error(
                    f"Error registering tools from plugin {plugin_name}: {e}", 
                    exc_info=True
                )
    
    def get_plugin(self, plugin_name: str) -> Optional[InkscapePlugin]:
        """Get a loaded plugin by name.
        
        Args:
            plugin_name: Name of the plugin to retrieve
            
        Returns:
            The plugin instance, or None if not found
        """
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """Get information about all loaded plugins.
        
        Returns:
            List of dictionaries containing plugin information
        """
        return [
            {
                "name": name,
                "description": plugin.get_plugin_description(),
                "class": plugin.__class__.__name__,
                "module": plugin.__class__.__module__
            }
            for name, plugin in self.plugins.items()
        ]
