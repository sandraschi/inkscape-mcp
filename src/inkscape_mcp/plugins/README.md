# Inkscape MCP Extensions

This directory contains Inkscape extensions that extend the functionality of the Inkscape MCP server. Extensions are Python scripts that use the `inkex` library to manipulate SVG documents and can be executed via the MCP protocol.

## Extension Structure

An Inkscape extension consists of two files:

1. **`.inx` file**: XML configuration file that describes the extension to Inkscape
2. **`.py` file**: Python script that implements the extension logic using the `inkex` library

### Basic Extension Example

**extension_example.py**:
```python
import inkex
from inkex import PathElement, Style

class ExampleExtension(inkex.EffectExtension):
    """Example extension that demonstrates basic functionality."""

    def add_arguments(self, pars):
        pars.add_argument("--param1", type=str, help="A string parameter")
        pars.add_argument("--param2", type=int, default=42, help="An integer parameter")

    def effect(self):
        """Main extension logic."""
        param1 = self.options.param1
        param2 = self.options.param2

        # Extension logic goes here
        for elem in self.svg.selection:
            if isinstance(elem, PathElement):
                # Modify the selected path
                elem.style['stroke'] = 'red'
                elem.style['stroke-width'] = str(param2)

if __name__ == '__main__':
    ExampleExtension().run()
```

**extension_example.inx**:
```xml
<inkscape-extension xmlns="http://www.inkscape.org/namespace/inkscape/extension">
    <name>Example Extension</name>
    <id>org.inkscape.example</id>
    <param name="param1" type="string" gui-text="String Parameter">example</param>
    <param name="param2" type="int" min="1" max="100" gui-text="Integer Parameter">42</param>
    <effect>
        <object-type>all</object-type>
        <effects-menu>
            <submenu>Project AG</submenu>
        </effects-menu>
    </effect>
    <script>
        <command location="inx" interpreter="python">extension_example.py</command>
    </script>
</inkscape-extension>
```

## Extension Lifecycle

1. **Discovery**: The MCP server scans the extensions directory for `.inx` files
2. **Parsing**: Extension metadata and parameters are extracted from `.inx` files
3. **Registration**: Extensions are registered as MCP tools with appropriate parameter schemas
4. **Execution**: Extensions are executed via Inkscape CLI with `--extension` parameter

## Extension Types

### Built-in Extensions
Inkscape comes with many built-in extensions for:
- **Export/Import**: Various formats (PDF, PNG, DXF, etc.)
- **Render**: Barcode generation, gear creation
- **Text**: Hershey text, lorem ipsum generation
- **Modify**: Path operations, color adjustments

### Custom Extensions
Extensions can be created for specific workflows like:
- **Unity Optimization**: Prepare SVGs for Unity UI import
- **Batch Processing**: Process multiple files automatically
- **Animation**: Create CSS-animated SVGs from layers
- **VRChat Preparation**: Optimize assets for VR environments

## MCP Integration

Extensions are exposed through MCP tools that:
1. Accept extension parameters as tool arguments
2. Execute extensions via Inkscape CLI
3. Return results and status information
4. Handle both GUI and headless execution modes

## Best Practices

### Error Handling
- Always wrap extension logic in try/except blocks
- Provide meaningful error messages
- Log execution details for debugging

### Parameter Design
- Use descriptive parameter names
- Provide sensible defaults
- Validate parameter values
- Support both required and optional parameters

### Performance
- Process selections efficiently
- Avoid unnecessary DOM traversals
- Use appropriate data structures
- Consider memory usage for large documents

## Available Extensions

### Batch Processing
- **AG Batch Trace**: Convert bitmaps to vectors with quantization
- **AG Unity Prep**: Optimize SVGs for Unity import
- **AG Color Quantize**: Reduce color palettes for performance

### Animation
- **AG Layer Animation**: Create CSS-animated SVGs from layers
- **AG SMIL Animation**: Add SMIL animations to elements

### Optimization
- **AG Path Simplify**: Reduce path complexity
- **AG SVG Clean**: Remove metadata and optimize structure
- **AG Coordinate Reset**: Reset document coordinates

## Configuration

Extensions can be configured in the main `config.yaml`:

```yaml
extensions:
  enabled: true
  directories:
    - "~/.config/inkscape/extensions"
    - "./extensions"
  disabled:
    - "some_extension"
  config:
    ag_batch_trace:
      default_colors: 4
      simplify_paths: true
```

## Testing Extensions

1. Place extension files in the extensions directory
2. Restart the Inkscape MCP server
3. Check server logs for extension loading
4. Test via MCP tools with appropriate parameters

## Troubleshooting

- **Extension not loading**: Check `.inx` file syntax and Python imports
- **Parameters not working**: Verify parameter definitions in `.inx` file
- **Execution errors**: Check Inkscape version compatibility and CLI output
- **Permission issues**: Ensure proper file permissions on extension files
