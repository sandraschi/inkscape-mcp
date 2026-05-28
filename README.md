# Inkscape MCP

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

**MCP server for Inkscape:** agents call portmanteau tools (`inkscape_file`, `inkscape_vector`, `inkscape_analysis`, `inkscape_system`) that drive the **Inkscape CLI**. Built with **FastMCP 3.2.0+**.

You need **Python 3.12+**, **[uv](https://docs.astral.sh/uv/)**, and **Inkscape** on the same machine.

| Doc | What |
|-----|------|
| [docs/INSTALL.md](docs/INSTALL.md) | Clone  `uv sync`  run; PyPI / `uvx` |
| [docs/INKSCAPE.md](docs/INKSCAPE.md) | Install Inkscape, PATH, CLI check |
| [docs/IDE_MCP.md](docs/IDE_MCP.md) | Cursor, VS Code, Windsurf, Glama-style config |
| [docs/MCPB.md](docs/MCPB.md) | Claude Desktop `.mcpb` bundle |
| [docs/USAGE.md](docs/USAGE.md) | How to use the tools from an agent |
| [docs/AI_SAMPLING.md](docs/AI_SAMPLING.md) | Agentic tools, `ctx.sample()`, Ollama env |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layout, transports, modules |
| [docs/COMPETITIVE_ANALYSIS.md](docs/COMPETITIVE_ANALYSIS.md) | Ecosystem comparison and differentiation |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Agent Lab phased improvement plan |
| [llms.txt](llms.txt) / [llms-full.txt](llms-full.txt) | LLM index + full tool/env/run manifest (fleet) |

More: [Docs index](docs/README.md)  [API](docs/API.md)  [Features](docs/FEATURES.md)  [Troubleshooting](docs/TROUBLESHOOTING.md)  [Changelog](CHANGELOG.md)

[![CI/CD](https://img.shields.io/github/actions/workflow/status/sandraschi/inkscape-mcp/ci.yml)](https://github.com/sandraschi/inkscape-mcp/actions)
[![PyPI](https://img.shields.io/pypi/v/inkscape-mcp)](https://pypi.org/project/inkscape-mcp/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Quick Start

```powershell
git clone https://github.com/sandraschi/inkscape-mcp
cd inkscape-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

## Agent Lab (planned)

Following the blender-mcp / gimp-mcp / unity3d-mcp playbook:

| Phase | Focus |
|-------|--------|
| **1** (2.1.0) | Agent vision exports, runtime guidance | **done** |
| **2** (2.2.0) | Webapp `/agent-tools`, SVG validation | **done** |
| **3** (2.3.0) | Fleet handoff (gimp, blender, unity) |
| **4** (2.4.0) | Telemetry, Docker, smoke tests |
| **5** (2.5.0) | Robotics fab art (DXF, laser, Gazebo schematics) |

See [docs/ROADMAP.md](docs/ROADMAP.md) and [docs/COMPETITIVE_ANALYSIS.md](docs/COMPETITIVE_ANALYSIS.md).

### Manual Setup

If you don't have `just` installed:

## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

MIT  see [LICENSE](LICENSE).
