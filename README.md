# Inkscape MCP

**MCP server for Inkscape:** agents call portmanteau tools (`inkscape_file`, `inkscape_vector`, `inkscape_analysis`, `inkscape_system`) that drive the **Inkscape CLI**. Built with **FastMCP 3.1+**.

You need **Python 3.12+**, **[uv](https://docs.astral.sh/uv/)**, and **Inkscape** on the same machine.

| Doc | What |
|-----|------|
| [docs/INSTALL.md](docs/INSTALL.md) | Clone → `uv sync` → run; PyPI / `uvx` |
| [docs/INKSCAPE.md](docs/INKSCAPE.md) | Install Inkscape, PATH, CLI check |
| [docs/IDE_MCP.md](docs/IDE_MCP.md) | Cursor, VS Code, Windsurf, Glama-style config |
| [docs/MCPB.md](docs/MCPB.md) | Claude Desktop `.mcpb` bundle |
| [docs/USAGE.md](docs/USAGE.md) | How to use the tools from an agent |
| [docs/AI_SAMPLING.md](docs/AI_SAMPLING.md) | Agentic tools, `ctx.sample()`, Ollama env |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layout, transports, modules |

More: [Docs index](docs/README.md) · [API](docs/API.md) · [Features](docs/FEATURES.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Changelog](CHANGELOG.md)

[![CI/CD](https://img.shields.io/github/actions/workflow/status/sandraschi/inkscape-mcp/ci.yml)](https://github.com/sandraschi/inkscape-mcp/actions)
[![PyPI](https://img.shields.io/pypi/v/inkscape-mcp)](https://pypi.org/project/inkscape-mcp/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## License

MIT — see [LICENSE](LICENSE).
