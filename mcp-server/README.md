# MCPB bundle root (`mcp-server/`)

Claude Desktop **`.mcpb`** packages are built from this directory. Layout follows [MCPB_PACKAGING_STANDARDS.md](https://github.com/sandraschi/mcp-central-docs/blob/master/standards/MCPB_PACKAGING_STANDARDS.md) in **mcp-central-docs**.

## Layout

- `manifest.json` — MCPB manifest (`manifest_version` 0.2)
- `assets/prompts/` — `system.md`, `user.md`, `examples.json` (100+ mappings), `configuration.md`, `troubleshooting.md`, `quick-start.md`
- `assets/icon.png` — package icon
- `src/inkscape_mcp/` — **synced copy** of the canonical package at repo `src/inkscape_mcp/` (do not edit by hand; run sync)

## Build

From the **repository root**:

```powershell
uv run python tools/sync_mcpb_src.py
uv run python tools/pack_mcpb.py
```

Or: `just mcpb-pack` (runs sync then pack).

Output: `dist/inkscape-mcp-v<pyproject-version>.mcpb` (repo root `dist/`). **`glama.json` stays at repo root** and is not part of the MCPB zip.

## Requirements

- **Python** with project deps installed for running the server (MCPB does not bundle wheels; users install deps per Anthropic MCPB rules).
- **Node.js** for `@anthropic-ai/mcpb` pack (the script calls `node` + `npx-cli.js`).
- **Inkscape** on the target machine for CLI operations.
