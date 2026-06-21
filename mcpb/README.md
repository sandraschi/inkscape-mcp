# inkscape-mcp (MCPB Bundle)

MCP server for Inkscape-backed SVG and vector operations (FastMCP 3.2.0+)

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "inkscape-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "inkscape_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **list_local_models**: list_local_models
- **test_tool**: test_tool

## Requirements

- Python 3.12+
- uv
