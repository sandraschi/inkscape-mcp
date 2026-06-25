# Inkscape MCP — AI-powered vector graphics

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://fastmcp.com"><img src="https://img.shields.io/badge/FastMCP-3.4-7c5cfc?style=flat-square" alt="FastMCP"></a>
  <a href="https://github.com/sandraschi/inkscape-mcp/releases"><img src="https://img.shields.io/badge/NSIS%20installer-download-blue?style=flat-square&logo=windows" alt="NSIS"></a>
</p>

MCP server that exposes Inkscape's full vector graphics engine through the Model Context Protocol. Works as an **MCP server** (stdio/HTTP), an **MCPB bundle** for Claude Desktop, a **webapp dashboard** (React/Vite), and a **Tauri Windows desktop app** (NSIS installer).

## Delivery Formats

| Format | How | Use case |
|--------|-----|----------|
| **MCP server** | `uv run inkscape-mcp` | Cursor, Claude Code, any MCP client |
| **MCPB bundle** | `dist/inkscape-mcp-v2.6.0.mcpb` | Claude Desktop single-click install |
| **Webapp** | `http://127.0.0.1:11029` | Dashboard, animation studio, layer manager, agent lab |
| **Tauri NSIS app** | `Inkscape MCP_2.6.0_x64-setup.exe` | One-installer desktop app (embedded backend) |

## What It Does

9 portmanteau tools, 17 MCP tools total, 60+ operations:

| Tool | Operations |
|------|-----------|
| `inkscape_file` | load, save, convert, info, validate |
| `inkscape_vector` | create shapes, text ops, path booleans, LPEs, inspect, trace, optimize, boolean, measure, export, render |
| `inkscape_analysis` | statistics, validate, dimensions, objects, structure, quality |
| `inkscape_render` | export_preview, export_multi_dpi, get_document_summary |
| `inkscape_validation` | validate_svg, check_viewbox, audit_web_svg, stroke/fill, size limits |
| `inkscape_layers` | list, create, rename, hide/show, lock/unlock, reorder |
| `inkscape_animation` | SMIL presets (bounce, fade, slide, rotate, pulse, shake), element/transform/motion animation, CSS keyframes |
| `inkscape_system` | status, diagnostics, hands-in command, extensions, config |
| `inkscape_fleet` / `fab_art` / `sim_art` | cross-MCP handoffs (GIMP, Blender, Unity, Resonite) |

## Quick Start

```powershell
git clone https://github.com/sandraschi/inkscape-mcp
cd inkscape-mcp
just
```

`just serve` — start the HTTP server  
`just dev` — start webapp + backend  
`just build-native` — build the NSIS Windows installer  
`just cua-nsis-test` — CUA smoke test (requires pywinauto + pytesseract + Tesseract OCR)

## Docs

| Doc | What |
|-----|------|
| `docs/INSTALL.md` | Installation guide |
| `docs/USAGE.md` | How to use the tools |
| `llms.txt` / `llms-full.txt` | LLM index + full manifest |
| `CHANGELOG.md` | Release history |

## Infrastructure

- **Python**: FastMCP 3.4.2, dual transport (stdio + streamable HTTP)
- **Webapp**: React 19 + Vite + TailwindCSS + Zustand + Framer Motion + Lucide
- **Desktop**: Tauri 2.0 + NSIS installer (embedded PyInstaller backend)
- **Quality**: Ruff lint, Biome, mypy, pytest, Playwright E2E, CUA-NSIS smoke test
- **Ports**: Backend 11028, Frontend 11029

## License

MIT — see [LICENSE](LICENSE.md).
