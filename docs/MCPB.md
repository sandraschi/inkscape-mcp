# Claude Desktop (MCPB)

Claude Desktop can install servers from a **`.mcpb`** file (drag-and-drop in settings).

## Get a bundle

- **Build from this repo** (requires [Node.js](https://nodejs.org/) for `@anthropic-ai/mcpb`):

  ```bash
  just mcpb-pack
  ```

  or:

  ```bash
  uv run python tools/pack_mcpb.py
  ```

  Output: **`dist/inkscape-mcp-v<version>.mcpb`** at the repository root.

- Details and layout rules: [mcp-server/README.md](../mcp-server/README.md) and [mcp-central-docs MCPB standards](https://github.com/sandraschi/mcp-central-docs/blob/master/standards/MCPB_PACKAGING_STANDARDS.md).

## What MCPB contains

- `manifest.json`, prompts under `assets/prompts/`, icon, and **`src/inkscape_mcp/`** (synced from the main package at pack time).

## What stays outside the bundle

- **`glama.json`** is for repo-based clients only — it is **not** inside `.mcpb`.

## Python dependencies

MCPB does not vendor Python wheels. The user’s environment must be able to run the server and satisfy imports (same as other Anthropic MCPB Python servers). If Claude Desktop uses its own Python, follow its docs for dependency install.

## Config fields in Claude

Use the MCPB install UI for path/timeouts. Optional `config.yaml` next to the unpacked layout may apply when referenced by `INKSCAPE_MCP_CONFIG_PATH` in the manifest — see `mcp-server/manifest.json`.
