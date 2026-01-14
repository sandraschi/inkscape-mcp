# GIMP MCP Plugins

This directory contains plugins that extend the functionality of the GIMP MCP server. Plugins are dynamically loaded at runtime and can add new tools and capabilities to the server.

## Plugin Structure

A GIMP MCP plugin is a Python module that defines one or more plugin classes. Each plugin class must inherit from `GimpToolPlugin` and implement the required methods.

### Basic Plugin Example

```python
from typing import Any, Dict

from fastmcp import tool
from .base_plugin import GimpToolPlugin

class MyPlugin(GimpToolPlugin):
    """Example plugin that demonstrates basic functionality."""
    
    PLUGIN_NAME = "my_plugin"
    PLUGIN_DESCRIPTION = "An example plugin for GIMP MCP"
    
    def register_tools(self, app) -> None:
        """Register all tools provided by this plugin."""
        
        @app.tool()
        async def my_tool(param1: str, param2: int = 42) -> Dict[str, Any]:
            """
            Example tool that demonstrates plugin functionality.
            
            Args:
                param1: A string parameter
                param2: An integer parameter with default value 42
                
            Returns:
                A dictionary with the operation results
            """
            try:
                # Plugin logic goes here
                result = {"status": "success", "message": f"Processed {param1} with {param2}"}
                return self.create_success_response(data=result)
                
            except Exception as e:
                self.logger.error(f"Error in my_tool: {e}", exc_info=True)
                return self.create_error_response(f"Failed to process: {str(e)}")
```

## Plugin Lifecycle

1. **Discovery**: The server scans all `.py` files in the plugin directories (excluding those starting with `_`).
2. **Loading**: Each valid plugin class is instantiated with a reference to the CLI wrapper and config.
3. **Initialization**: The `register_tools()` method is called to register all tools with the FastMCP app.
4. **Execution**: Tools can be called via the MCP protocol.

## Best Practices

### Error Handling
- Always wrap tool logic in try/except blocks
- Use `self.create_error_response()` for consistent error formatting
- Log detailed errors with `self.logger.error()`

### Configuration
- Access plugin-specific config via `self.config.plugin_config.get(self.PLUGIN_NAME, {})`
- Define default values for all configuration options

### Logging
- Use the built-in logger: `self.logger`
- Include relevant context in log messages
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)

## Plugin Configuration

Plugins can be configured in the main `config.yaml` file under the `plugin_config` section:

```yaml
plugin_config:
  my_plugin:
    setting1: value1
    setting2: value2
```

## Available Base Classes

### `GimpToolPlugin`
Base class for all tool plugins. Provides common functionality like logging and error handling.

#### Key Methods
- `register_tools(app)`: Register all tools with the FastMCP app
- `create_success_response(data, message)`: Create a standardized success response
- `create_error_response(message, details=None)`: Create a standardized error response
- `validate_file_path(path, must_exist=True)`: Validate a file path
- `validate_layer_index(num_layers, layer_index)`: Validate a layer index
- `validate_selection_bounds(bounds)`: Validate selection bounds
- `validate_color(color)`: Validate a color value

## Example Plugin: Layer Tools

See `layer_plugin.py` for a complete example of a plugin that provides layer manipulation tools.

## Testing Plugins

1. Place your plugin in the `plugins` directory
2. Restart the GIMP MCP server
3. Verify your plugin is loaded by checking the server logs
4. Test your tools using the MCP client

## Troubleshooting

- **Plugin not loading**: Check server logs for import errors
- **Tools not appearing**: Ensure `register_tools()` is implemented correctly
- **Configuration issues**: Verify your plugin's config section in `config.yaml`
- **Permission errors**: Ensure the server has read access to your plugin files
