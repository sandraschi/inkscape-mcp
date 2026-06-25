# Inkscape MCP — AI-powered vector graphics

AI agents create, edit, layer, animate, and export SVG files using Inkscape. Works as an MCP server (stdio/HTTP), Claude Desktop `.mcpb` bundle, webapp dashboard, or Windows desktop app.

## Preview

| Dashboard | Animation Studio | Layer Manager |
|-----------|-----------------|---------------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Animation Studio](docs/screenshots/animation-studio.png) | ![Layer Manager](docs/screenshots/layer-manager.png) |

*Animated SVG presets render live in the browser — no Inkscape CLI needed.*

## How it runs

| Mode | Inkscape | When |
|------|----------|------|
| **Headless (default)** | CLI via `inkscape --actions` | Batch processing, export, validation, fleet pipelines |
| **Live GUI (optional)** | Open Inkscape manually + `--active-window` | Interactive editing with agent co-pilot |

> **Headless by default** — no GUI needed for most operations.

## Features
- Create and edit SVG files (shapes, text, paths, booleans)
- Layer management — list, create, rename, hide, lock, reorder
- SMIL animation — bounce, fade, slide, rotate, pulse, shake presets
- Live Path Effects — bend, roughen, envelope, spiro, power stroke
- Export to PNG, PDF, EPS, DXF
- Fleet pipeline — hand off to GIMP, Blender, Unity, Resonite
- LPEs, text operations, object inspection, hands-in control

## Quick Install

**Claude Desktop:** download the `.mcpb` from [Releases](https://github.com/sandraschi/inkscape-mcp/releases) and drag it onto Claude.

**Windows desktop app:** download the NSIS installer from [Releases](https://github.com/sandraschi/inkscape-mcp/releases) and run it.

**Manual:** `git clone`, `uv sync`, `just serve`. See [INSTALL.md](INSTALL.md) for all methods.

## What You Can Do

> "Create a bouncing circle animation with a pink fill and 2-second duration, then export as PNG."

> "List all layers in my SVG, hide the background layer, and rename the top layer to 'Hero'."

> "Convert this text element to paths, then apply a roughen LPE with medium intensity."

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | All install methods, prerequisites |
| [Configuration](docs/CONFIGURATION.md) | Env vars, Ollama, Tauri desktop mode |
| [Tool Reference](docs/TOOLS.md) | All 17 tools, 60+ operations |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup, building |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |

## Requirements

- **Windows**, macOS, or Linux
- **Inkscape 1.0+** (1.2+ recommended for Actions API)
- **Python 3.12+** with [uv](https://docs.astral.sh/uv/)
- Optional: Ollama for AI-assisted SVG generation

## License

MIT — see [LICENSE.md](LICENSE.md).
