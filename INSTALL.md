# Installation

## 🚀 Quick Start (recommended)

```powershell
git clone https://github.com/sandraschi/inkscape-mcp
cd inkscape-mcp
just
```

The interactive recipe dashboard opens in your browser. From there:

```powershell
just bootstrap   # install all dependencies
just serve       # start the server
just web         # start the frontend (if applicable)
```

> **Why not `pip install`?** MCP servers bundle webapps, configs, project scaffolding, and tooling that a flat Python package can't deliver. PyPI offers no safety advantage — it doesn't audit packages either. `just` gives you the complete, ready-to-run stack.

---

## 🐌 Traditional Setup

If you prefer not to use `just`:

1. Install [Python 3.13+](https://python.org) and [uv](https://docs.astral.sh/uv/)
2. Clone and enter the repo:
   ```powershell
   git clone https://github.com/sandraschi/inkscape-mcp
   cd inkscape-mcp
   ```
3. Install dependencies:
   ```powershell
   uv sync --all-extras
   ```
4. Start the server:
   ```powershell
   # stdio mode (for MCP clients like Claude Desktop)
   uv run python -m inkscape_mcp.server

   # HTTP mode (for web dashboard)
   uv run uvicorn inkscape_mcp.server:app --port 
   ```
5. Open `http://localhost:` or the frontend URL.

---

## ❓ Troubleshooting

| Issue | Fix |
|---|---|
| `just` not found | Install via `winget install Casey.Just`, `scoop install just`, or `brew install just` |
| Port conflict | Run `just kill-all` to clear fleet ports (10700–11000) |
| Dependencies out of sync | `uv sync --all-extras` |
| Something else | [Open a GitHub issue](https://github.com/sandraschi/inkscape-mcp/issues) |

---

*See the main [README](README.md) for feature overview and documentation.

---

## Legacy Documentation

_This INSTALL.md was updated with the standard fleet Quick Start template. The original instructions are preserved below._

# Installation

See **[docs/INSTALL.md](docs/INSTALL.md)** for clone + **uv**, PyPI, and next steps (Inkscape, IDE config, MCPB).

Quick path:

```bash
git clone https://github.com/sandraschi/inkscape-mcp.git
cd inkscape-mcp
uv sync
uv run inkscape-mcp --help
```
