"""PyInstaller entry point — dual transport.

Detects MCP_PORT env var (set by Tauri backend.rs) and switches to HTTP mode.
When no env vars are set, runs stdio mode (Claude Desktop).
"""
import os
import sys

# File-based debug: log to a known path so we can see when/if this code runs
_DBG = r"C:\Users\sandr\AppData\Local\ai.fleet.inkscape-mcp\run_server_debug.log"
try:
    with open(_DBG, "a") as f:
        f.write(f"run_server.py started at {__import__('datetime').datetime.now()}\n")
        f.write(f"  CWD: {os.getcwd()}\n")
        f.write(f"  MCP_PORT: {os.environ.get('MCP_PORT', '(unset)')}\n")
        f.write(f"  MCP_HOST: {os.environ.get('MCP_HOST', '(unset)')}\n")
        f.write(f"  INKSCAPE_TAURI: {os.environ.get('INKSCAPE_TAURI', '(unset)')}\n")
        f.write(f"  sys.argv: {sys.argv}\n")
except Exception as exc:
    pass  # Can't log early — file may not be writable

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
try:
    with open(_DBG, "a") as f:
        f.write(f"  calling main() with sys.argv={sys.argv}\n")
except Exception:
    pass
main()
try:
    with open(_DBG, "a") as f:
        f.write(f"  main() returned\n")
except Exception:
    pass
