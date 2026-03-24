# MCP config for agentic IDEs

These examples assume you either **cloned the repo** and use `uv`, or run a **globally installed** `inkscape-mcp`. Replace paths with yours.

## Cursor

Project or user MCP config (shape may vary by Cursor version; often **Settings → MCP** or `.cursor/mcp.json`):

**Clone + uv (recommended for contributors):**

```json
{
  "mcpServers": {
    "inkscape-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "D:/Dev/repos/inkscape-mcp",
        "run",
        "inkscape-mcp"
      ]
    }
  }
}
```

**PyPI / uv tool install:**

```json
{
  "mcpServers": {
    "inkscape-mcp": {
      "command": "inkscape-mcp",
      "args": []
    }
  }
}
```

**uvx (ephemeral):**

```json
{
  "mcpServers": {
    "inkscape-mcp": {
      "command": "uvx",
      "args": ["inkscape-mcp"]
    }
  }
}
```

On Windows, prefer forward slashes or escaped backslashes inside JSON strings.

## VS Code (MCP-enabled builds)

Same idea as Cursor: `command` / `args` pointing at `uv` + `--directory` + `run` + `inkscape-mcp`, or at the `inkscape-mcp` executable.

## Windsurf

Windsurf/Codeium config location depends on OS; pattern matches the JSON above. Example in repo: `windsurf_config.json` (update paths and descriptions to match your machine).

## Glama / workspace-style clients

This repo includes **`glama.json`** at the root: `python -m inkscape_mcp.main` with `PYTHONPATH` including `${workspaceFolder}/src`. Open the **repository root** as the workspace so that path resolves.

## Environment

- Ensure **Inkscape** is on PATH for the MCP process, or configure the server’s Inkscape path — [INKSCAPE.md](INKSCAPE.md).
- For HTTP/dual transport or extra options, see `inkscape-mcp --help` and [ARCHITECTURE.md](ARCHITECTURE.md).

## Sampling

For `ctx.sample()` / agentic tools, the client must support MCP sampling — [AI_SAMPLING.md](AI_SAMPLING.md).
