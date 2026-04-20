# Inkscape MCP

[![FastMCP Version](https://img.shields.io/badge/FastMCP-3.2.0-blue?style=flat-square&logo=python&logoColor=white)](https://github.com/sandraschi/fastmcp) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Linted with Biome](https://img.shields.io/badge/Linted_with-Biome-60a5fa?style=flat-square&logo=biome&logoColor=white)](https://biomejs.dev/) [![Built with Just](https://img.shields.io/badge/Built_with-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

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
| [llms.txt](llms.txt) / [llms-full.txt](llms-full.txt) | LLM index + full tool/env/run manifest (fleet) |

More: [Docs index](docs/README.md)  [API](docs/API.md)  [Features](docs/FEATURES.md)  [Troubleshooting](docs/TROUBLESHOOTING.md)  [Changelog](CHANGELOG.md)

[![CI/CD](https://img.shields.io/github/actions/workflow/status/sandraschi/inkscape-mcp/ci.yml)](https://github.com/sandraschi/inkscape-mcp/actions)
[![PyPI](https://img.shields.io/pypi/v/inkscape-mcp)](https://pypi.org/project/inkscape-mcp/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

MIT  see [LICENSE](LICENSE).
