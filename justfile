# Inkscape MCP — fleet recipes (see mcp-central-docs PACKAGING_STANDARDS.md §5)

default:
    @just --list

sync-mcpb-src:
    uv run python tools/sync_mcpb_src.py

# Requires Node.js (npx-cli.js resolved via `node`). Writes dist/inkscape-mcp-v<version>.mcpb
mcpb-pack:
    uv run python tools/pack_mcpb.py

test:
    uv run pytest

lint:
    uv run ruff check .
    uv run ruff format --check .

fmt:
    uv run ruff format .
    uv run ruff check --fix .
