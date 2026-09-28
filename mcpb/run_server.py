"""PyInstaller / MCPB entry point - dual transport.

Detects MCP_PORT env var (set by Tauri backend.rs) and switches to HTTP mode.
When no env vars are set, runs stdio mode (Claude Desktop / mcpb bundle).
"""

import os
import sys
from pathlib import Path

# Absolute, not CWD-relative: a bundle can be launched with any working
# directory (Claude Desktop's `uv run --directory ${PWD}` sets cwd to the
# bundle root, but nothing else here should have to assume that holds).
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

# Tell opentelemetry which context implementation to use before any import
# triggers it. Without this, PyInstaller's frozen environment cannot discover
# the contextvars context via entry points, causing StopIteration.
os.environ.setdefault("OTEL_PYTHON_CONTEXT", "contextvars_context")

# Eager-import stdlib C extensions that are lazy-imported by other modules
# and missed by PyInstaller's static analysis (plex-mcp postmortem).
import _strptime  # noqa: F401
import _datetime  # noqa: F401
import cachetools  # noqa: F401

from inkscape_mcp.main import main

# Gated behind __name__ == "__main__" so mcpb/verify_pack.py's import-isolation
# check (runpy.run_path(..., run_name="__mcpb_verify__")) can load this module
# far enough to populate sys.modules["inkscape_mcp"] without actually starting
# the server - which would otherwise block forever on stdio's stdin read loop
# during what is supposed to be a fast, non-interactive packaging check.
if __name__ == "__main__":
    port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
    if port:
        host = os.environ.get("MCP_HOST", "127.0.0.1")
        sys.argv = ["run_server.py", "--mode", "http", "--host", host, "--port", str(port)]

    main()
