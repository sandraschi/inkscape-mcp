"""PyInstaller entry point — dual transport.

Detects MCP_PORT env var (set by Tauri backend.rs) and switches to HTTP mode.
When no env vars are set, runs stdio mode (Claude Desktop).
"""
import os
import sys
from pathlib import Path

# File-based debug: log to a known path so we can see when/if this code runs.
# Uses the current user's own LOCALAPPDATA rather than a path hardcoded to the
# original author's machine (was "C:\Users\sandr\...", which doesn't exist on
# other machines and crashed startup before main() ever ran).
_LOG_DIR = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "ai.fleet.inkscape-mcp"
try:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
_DBG = _LOG_DIR / "run_server_debug.log"
_CRASH = _LOG_DIR / "run_server_crash.log"

try:
    with open(_DBG, "a") as f:
        f.write(f"\n=== run_server.py started PID={os.getpid()} at {__import__('datetime').datetime.now()} ===\n")
        f.write(f"  CWD: {os.getcwd()}\n")
        f.write(f"  MCP_PORT: {os.environ.get('MCP_PORT', '(unset)')}\n")
        f.write(f"  MCP_HOST: {os.environ.get('MCP_HOST', '(unset)')}\n")
        f.write(f"  INKSCAPE_TAURI: {os.environ.get('INKSCAPE_TAURI', '(unset)')}\n")
        f.write(f"  sys.argv: {sys.argv}\n")
        f.flush()
except Exception as exc:
    try:
        with open(_CRASH, "a") as cf:
            cf.write(f"run_server.py PID={os.getpid()} debug log ERROR: {exc}\n")
            cf.flush()
    except Exception:
        pass  # never let debug logging itself crash startup

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

port = os.environ.get("MCP_PORT")
if port:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    sys.argv = ["run_server.py", "--mode", "http", "--host", host, "--port", str(port)]
try:
    with open(_DBG, "a") as f:
        f.write(f"  calling main() with sys.argv={sys.argv}\n")
except Exception:
    pass

try:
    main()
except BaseException as exc:
    # Log the full traceback so a crash here is diagnosable from the log file
    # instead of disappearing into whatever swallows this process's stderr.
    import traceback
    try:
        with open(_DBG, "a") as f:
            f.write(f"  main() RAISED {type(exc).__name__}: {exc}\n")
            f.write(traceback.format_exc())
            f.write("\n")
    except Exception:
        pass
    raise

try:
    with open(_DBG, "a") as f:
        f.write(f"  main() returned\n")
except Exception:
    pass
