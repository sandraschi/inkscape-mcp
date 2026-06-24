"""PyInstaller entry point — dual transport.

Detects MCP_PORT env var (set by Tauri backend.rs) and switches to HTTP mode.
When no env vars are set, runs stdio mode (Claude Desktop).
"""
import os
import sys
sys.path.insert(0, "src")

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

port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
if port:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    sys.argv = ["run_server.py", "--mode", "http", "--host", host, "--port", str(port)]
main()
