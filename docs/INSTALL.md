# Installation

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/install/)** (recommended for this repo)
- **Inkscape** with a working CLI — see [INKSCAPE.md](INKSCAPE.md)

## From GitHub (recommended for development)

```bash
git clone https://github.com/sandraschi/inkscape-mcp.git
cd inkscape-mcp
uv sync
```

Run the server (stdio/dual per your defaults):

```bash
uv run inkscape-mcp --help
```

To run as an MCP server from an IDE, point the client at `uv` with `--directory` set to this repo — see [IDE_MCP.md](IDE_MCP.md).

Do **not** mix `uv sync` with a separate `uv pip install -e .` unless you know why; `uv sync` already installs the project from `pyproject.toml` into the project environment.

## From PyPI (consumers)

```bash
uv tool install inkscape-mcp
```

Or one-shot:

```bash
uvx inkscape-mcp --help
```

Then configure your MCP client to invoke the installed `inkscape-mcp` entry point (see [IDE_MCP.md](IDE_MCP.md), use `command` + `args` your client expects).

## Claude Desktop without a checkout

Use a published **`.mcpb`** or build one — [MCPB.md](MCPB.md).

## Optional web dashboard

Ports **10846** / **10847** (see project webapp / `web_sota` docs). Not required for MCP.

## Next steps

- [INKSCAPE.md](INKSCAPE.md) — verify `inkscape` on PATH  
- [IDE_MCP.md](IDE_MCP.md) — Cursor, Windsurf, Glama  
- [MCPB.md](MCPB.md) — Claude Desktop bundle  
- [USAGE.md](USAGE.md) — calling tools  
- [AI_SAMPLING.md](AI_SAMPLING.md) — sampling / agentic tools  
