# Installing Inkscape MCP

## Prerequisites

Install these if you don't have them already:

| Tool | Purpose | Install |
|------|---------|---------|
| Claude Desktop | Required host | [download](https://claude.ai/download) |
| Inkscape 1.0+ | Required for SVG ops | [inkscape.org](https://inkscape.org/release/) |
| Git | Clone repo (manual only) | `winget install Git.Git` |
| Python + uv | Run server (manual only) | `winget install astral-sh.uv` |

> Windows: all installs via [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)  
> macOS: use `brew install` equivalents  
> Linux: use your distro package manager

## Option A — Claude Desktop MCPB (Recommended)

1. Download `inkscape-mcp-v2.6.0.mcpb` from [Releases](https://github.com/sandraschi/inkscape-mcp/releases)
2. Open Claude Desktop → drag the file onto the window
3. Start prompting: *"Create a bouncing circle animation"*

## Option B — Windows Desktop App

Download `Inkscape MCP_2.6.0_x64-setup.exe` from [Releases](https://github.com/sandraschi/inkscape-mcp/releases) and run the installer. The app opens a browser dashboard at `http://127.0.0.1:11029`.

## Option C — Manual Setup

1. Clone and install:
   ```bash
   git clone https://github.com/sandraschi/inkscape-mcp
   cd inkscape-mcp
   uv sync
   ```

2. Add to Claude Desktop config at `%APPDATA%\Claude\claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "inkscape-mcp": {
         "command": "uv",
         "args": ["--directory", "C:\\path\\to\\inkscape-mcp", "run", "inkscape-mcp"],
         "env": { "PYTHONUNBUFFERED": "1" }
       }
     }
   }
   ```

3. Restart Claude Desktop

## Option D — Developer Mode

For contributing or running from source with live reload. See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## LLM Integration

Inkscape MCP can use Ollama for AI-assisted SVG generation:

- **Local (Ollama):** install [Ollama](https://ollama.com) and pull a model: `ollama pull qwen2.5-coder`
- **Cloud (Gemini):** set `GEMINI_API_KEY` in `claude_desktop_config.json` env
- **Cloud (Anthropic):** set `ANTHROPIC_API_KEY`

## Verify Installation

After installing, ask Claude:
> "Run inkscape_system with operation=status to verify everything is working."

You should see a response with tool counts and Inkscape availability.

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.
