# Bugs found running inkscape-mcp from a cloned repo (v2.6.0)

Found while installing on a clean Windows machine (username `monte`, not the
original author's dev machine), via `git clone` + `uv sync` and running
`run_server.py` directly under Claude Desktop. All three prevented or
destabilized startup; none are configuration mistakes on the installer's
part — each reproduces from a stock clone.

Environment: Windows 11, Python 3.12 via `uv`, Inkscape 1.4.2.

---

## Bug 1 — Hardcoded author-machine path crashes startup on any other machine

**File:** `run_server.py` (repo root)

**What happens:** The very first thing `run_server.py` does is open a debug
log at a path hardcoded to the original author's Windows username:

```python
_DBG = r"C:\Users\sandr\AppData\Local\ai.fleet.inkscape-mcp\run_server_debug.log"
try:
    with open(_DBG, "a") as f:
        ...
except Exception as exc:
    with open(r"C:\Users\sandr\AppData\Local\ai.fleet.inkscape-mcp\run_server_crash.log", "a") as cf:
        cf.write(f"run_server.py PID={os.getpid()} debug log ERROR: {exc}\n")
        cf.flush()
```

On any machine where `C:\Users\sandr\...` doesn't exist, the first `open()`
fails — and the fallback exception handler tries to open a file under the
*same nonexistent directory*, so it also throws, this time unhandled. The
script dies before `main()` is ever called.

**Fix:** derive the log directory from `%LOCALAPPDATA%` (or `~` as a
fallback) instead of a hardcoded path, create it if missing, and make the
fallback handler itself exception-safe so a logging failure can never take
down startup. Also wrap the `main()` call itself so any startup exception is
logged with a full traceback before re-raising, instead of disappearing into
whatever swallows this process's stderr under Claude Desktop.

---

## Bug 2 — `sys.path.insert(0, "src")` is CWD-relative, not script-relative

**File:** `run_server.py`

```python
sys.path.insert(0, "src")
```

This resolves relative to the process's current working directory, not the
script's location. When Claude Desktop launches the server, the child
process's CWD is not the project root — so this inserts a nonexistent `src`
path relative to wherever Claude Desktop happens to start the process from.
It didn't manifest as a hard failure for us only because the venv install
also makes `inkscape_mcp` importable via the normal site-packages mechanism
— so this is latent/fragile rather than immediately fatal, but it's clearly
not doing what it's meant to and will bite anyone relying on the `src` layout
without an editable install.

**Fix:**

```python
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
```

---

## Bug 3 — Default transport is `"dual"` (stdio + HTTP on a fixed port), causing bind collisions

**File:** `src/inkscape_mcp/main.py`

```python
parser.add_argument("--mode", choices=["stdio", "http", "dual"], default="dual")
parser.add_argument("--port", type=int, default=11027, ...)
```

and further down (`run_server.py`):

```python
port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
```

When launched by Claude Desktop with no `--mode` flag (the common case for a
typical `command`/`args` MCP config), the transport actually used ends up
depending on whatever `MCP_TRANSPORT` is already present in the *inherited*
process environment, or on a generic `PORT` env var that's extremely common
on dev machines (many unrelated tools set it). Either path can push the
server into HTTP mode and it will try to bind `127.0.0.1:11027` regardless
of intent. With more than one consumer trying to start "their own" instance,
they race for the same hardcoded port:

```
OSError: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 11027):
[winerror 10048] only one usage of each socket address (protocol/network address/port)
is normally permitted
```

...which surfaces to the user as a silent restart-loop (Claude Desktop just
shows "Server disconnected" and retries with backoff) rather than a
diagnosable error.

**Fix applied:**
- Default `--mode` to `"stdio"` instead of `"dual"` in `main.py`, so a
  Claude-Desktop-style launch with no explicit `--mode` is stdio by default.
- Removed the generic `PORT` env var fallback in `run_server.py`, keeping
  only the explicitly-documented `MCP_PORT`.

---

## What we run with now, for reference

Manual clone (`git clone` + `uv sync`), launched via:

```json
{
  "command": "<repo>\\.venv\\Scripts\\python.exe",
  "args": ["<repo>\\run_server.py"]
}
```

No `--mode` flag is needed now that `stdio` is the default.
