# Inkscape MCP — fleet recipes (mcp-central-docs PACKAGING_STANDARDS.md §5)

default:
    @just --list

# --- Quality ---

test:
    uv run pytest

lint:
    uv run ruff check .
    uv run ruff format --check .

fmt:
    uv run ruff format .
    uv run ruff check --fix .

typecheck:
    uv run mypy src/inkscape_mcp

check: lint typecheck test
    @echo check complete

# --- Run (repo root; clone + uv sync first) ---

run:
    uv run inkscape-mcp --mode dual

run-stdio:
    uv run inkscape-mcp --mode stdio

run-http port="10847":
    uv run inkscape-mcp --mode http --port {{port}}

# --- MCPB ---

sync-mcpb-src:
    uv run python tools/sync_mcpb_src.py

expand-mcpb-examples:
    uv run python tools/expand_mcpb_examples.py

# Requires Node.js (npx-cli.js via node). Writes dist/inkscape-mcp-v<version>.mcpb
mcpb-pack: sync-mcpb-src expand-mcpb-examples
    uv run python tools/pack_mcpb.py

# --- Build / publish helpers ---

build-wheel:
    uv build

pre-commit:
    uv run pre-commit run --all-files
