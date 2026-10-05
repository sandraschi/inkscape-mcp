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

## Install

### Let your AI set it up

Do you use an AI coding assistant (Claude Code, Cursor, Codex, GitHub Copilot, ...)? Paste this into it:

```text
Set up inkscape-mcp on this PC for me: https://github.com/sandraschi/inkscape-mcp - follow docs/AI_SETUP.md in that repository.
```

It checks your PC first (Inkscape, ports, disk) and installs nothing until that passes. It asks before
installing Inkscape, then sets up the server and connects it to your AI app.

### Or do it yourself

**Claude Desktop only:** download the `.mcpb` from [Releases](https://github.com/sandraschi/inkscape-mcp/releases/latest) and drag it onto Claude.

**Windows, with the dashboard:** `git clone https://github.com/sandraschi/inkscape-mcp`, then double-click
**`start.bat`**. It installs what is missing (uv, bun, dependencies), starts the server and opens the dashboard
at `http://127.0.0.1:11029`. Run it again any time: it resumes or reports that it is already running.
`stop.bat` stops it. `start.bat -Check` tells you whether it will work here, without installing anything.

**Windows desktop app:** the NSIS installer from [Releases](https://github.com/sandraschi/inkscape-mcp/releases/latest).

Every method: [INSTALL.md](INSTALL.md).

> **The first `start.bat` run takes 2-4 minutes** and the window can sit quiet while Python packages
> install. This is normal. Don't close it.

### Something went wrong?

- **It stopped during install.** Run `start.bat` again. It continues where it stopped.
- **"held by another program" on port 11028 or 11029.** Another app uses that port. Close it, then rerun.
- **Export / convert does nothing.** Inkscape is missing. `winget install Inkscape.Inkscape`, then restart.
- **Still stuck?** See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md), or open an
  [issue](https://github.com/sandraschi/inkscape-mcp/issues) and attach `logs\start.log`.

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
- [uv](https://docs.astral.sh/uv/) (fetches Python 3.12+ itself; `start.bat` installs uv for you)
- Optional: Ollama for AI-assisted SVG generation

## License

MIT — see [LICENSE.md](LICENSE.md).
