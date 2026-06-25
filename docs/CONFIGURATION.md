# Configuration

## Environment Variables

Set these in your shell or in `claude_desktop_config.json`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | `11028` | HTTP port for MCP + REST bridge |
| `MCP_HOST` | `127.0.0.1` | Bind address |
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio`, `http`, `dual` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL for SVG generation |
| `OLLAMA_MODEL` | `qwen2.5-coder:latest` | Ollama model for SVG generation |
| `GEMINI_API_KEY` | — | Google Gemini API key (cloud fallback) |
| `ANTHROPIC_API_KEY` | — | Anthropic API key (cloud fallback) |
| `INKSCAPE_PATH` | — | Override Inkscape executable path |
| `INKSCAPE_GUI_WATCH` | `0` | Set to `1` to enable live GUI watch mode |
| `PROMETHEUS_PORT` | `9074` | Metrics server port |
| `INKSCAPE_MCP_METRICS_ENABLED` | `true` | Enable Prometheus metrics |
| `INKSCAPE_TAURI` | — | Set by Tauri launcher; enables desktop-mode CORS |

## Setting Variables

In `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "inkscape-mcp": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\inkscape-mcp", "run", "inkscape-mcp"],
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "GEMINI_API_KEY": "your-key-here"
      }
    }
  }
}
```
