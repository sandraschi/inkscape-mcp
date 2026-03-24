# Minimal MCP Server (Hello World)

**Confidence**: 🟢 High
**Last validated**: 2025-11-11
**Primary sources**: FastMCP 2.13 docs, Anthropic sample servers, Advanced Memory `server.py`

---

## 1. Project Structure

```
hello-mcp/
├── pyproject.toml
└── src/
    └── hello_mcp/
        ├── __init__.py
        └── server.py
```

- Use `uv init hello-mcp` or `python -m venv .venv && pip install fastmcp>=2.13.0,<2.14.0`.
- Keep the server module thin; add tools in dedicated files or packages as it grows.

---

## 2. Minimal `pyproject.toml`

```toml
[project]
name = "hello-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastmcp>=2.13.0,<2.14.0",
  "uvicorn>=0.29.0"
]

[project.scripts]
hello-mcp = "hello_mcp.server:main"
```

Install dependencies with `uv sync` or `pip install -e .`.

---

## 3. Minimal `server.py`

```python
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastmcp import FastMCP, tool


@asynccontextmanager
async def lifespan(app: FastMCP):
    print("🚀 Hello MCP starting up")
    yield
    print("👋 Hello MCP shutting down")


mcp = FastMCP("hello-mcp", lifespan=lifespan)


@tool()
async def greet(name: str) -> Dict[str, Any]:
    """Return a friendly greeting."""
    return {
        "success": True,
        "message": f"Hello, {name}! Welcome to the Model Context Protocol.",
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
```

Key points:
- Use `@tool()` (FastMCP decorator) to register async functions.
- Return structured dictionaries (`success`, `message`, etc.).
- Lifespan hook enables warm-up/cool-down tasks (initialize clients, load storage).

---

## 4. Local Run & Client Registration

1. `uv run hello-mcp` (default host `127.0.0.1:8000`).
2. In Claude Desktop: `/mcp servers add hello-mcp --url http://127.0.0.1:8000`.
3. In Cursor: update `.cursor/mcp.json`:
   ```json
   {
     "servers": [
       {
         "command": "uv",
         "args": ["run", "hello-mcp"],
         "name": "hello-mcp"
       }
     ]
   }
   ```
4. Ask your client to run the `greet` tool: `/mcp tools call hello-mcp greet --param name="Cursor"`.

---

## 5. Expanding Safely

- **Logging**: integrate `loguru` for structured logs and error capture.
- **Error handling**: wrap tool bodies in try/except returning structured errors (see `.cursorrules`).
- **Configuration**: use environment variables or `pydantic` settings module for API keys.
- **Testing**: add pytest cases hitting tool functions directly.
- **Packaging**: wire into MCPB manifest + npx bootstrap once stable.

Use this template as the smallest viable FastMCP server—grow by adding modules, portmanteau tools, and persistence as needed.***
# Minimal FastMCP “Hello World” Server

**Confidence**: 🟢 High
**Last validated**: 2025-11-11
**Primary sources**: Anthropic FastMCP quick-start (https://docs.anthropic.com/claude/docs/mcp-quickstart), FastMCP 2.13 API reference, Advanced Memory `.cursorrules`

---

## 1. Prerequisites

- Python 3.11+
- `uv` for dependency management (`pip install uv` if missing)
- FastMCP 2.13+ (`fastmcp>=2.13.0,<2.14.0`)
- `loguru` for structured logging (recommended)
- A project folder with `pyproject.toml` (see snippet below)

```toml
# pyproject.toml (minimal example)
[project]
name = "hello-mcp"
version = "0.1.0"
dependencies = ["fastmcp>=2.13.0,<2.14.0", "loguru>=0.7.2"]

[tool.fastmcp]
module = "hello_mcp.server"
```

Install dependencies:

```powershell
uv sync
```

---

## 2. Minimal Server Implementation

```python
# hello_mcp/server.py
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastmcp import FastMCP, tool
from loguru import logger


@tool()
async def hello(operation: str = "greet", name: str = "World") -> Dict[str, Any]:
    """Return a friendly greeting and echo metadata."""
    try:
        if operation != "greet":
            return {
                "success": False,
                "error": f"Unsupported operation '{operation}'. Use 'greet'.",
                "error_code": "UNSUPPORTED_OPERATION",
                "suggestions": ["Call with operation='greet'", "Inspect available operations via metadata"],
            }

        message = f"Hello, {name}! 👋"
        logger.info("hello_success name=%s", name)
        return {
            "success": True,
            "message": message,
            "metadata": {"operation": operation, "echo": name},
        }
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("hello_error name=%s err=%s", name, exc, exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected failure while greeting {name}: {exc}",
            "error_code": "HELLO_FAILURE",
            "suggestions": [
                "Retry with a different name.",
                "Check server logs for stack trace.",
            ],
        }


@asynccontextmanager
async def lifespan(app: FastMCP):
    logger.info("hello_mcp_start")
    yield
    logger.info("hello_mcp_stop")


mcp = FastMCP(
    name="hello-mcp",
    version="0.1.0",
    description="Minimal FastMCP server that returns warm greetings.",
    lifespan=lifespan,
)
mcp.add_tools([hello])


if __name__ == "__main__":
    mcp.run()
```

Key FastMCP 2.13 features demonstrated:
- `@tool()` decorator with structured error handling.
- Lifespan context for startup/shutdown logs.
- Graceful fallback when unsupported operations are requested.

---

## 3. Running Locally

```powershell
uv run python -m hello_mcp.server --port 3333
```

By default, FastMCP binds to `localhost:3333`. Configure your client (e.g., Claude Desktop, Cursor, Windsurf) to use `http://127.0.0.1:3333`.

---

## 4. Testing the Endpoint

### Via MCP Inspector (recommended)

```powershell
uv run fastmcp inspect http://127.0.0.1:3333
```
- Confirms handshake metadata.
- Lets you invoke `hello` and see responses/structured errors.

### Via Curl (manual JSON-RPC call)

```powershell
curl -X POST http://127.0.0.1:3333/mcp \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\":\"callTool\",\"params\":{\"name\":\"hello\",\"arguments\":{\"operation\":\"greet\",\"name\":\"Sandra\"}}}"
```

Expected JSON:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "success": true,
    "message": "Hello, Sandra! 👋",
    "metadata": {
      "operation": "greet",
      "echo": "Sandra"
    }
  }
}
```

---

## 5. Packaging Checklist

- Add `scripts/testing/test_smoke.py` that imports and calls `hello()` to ensure deterministic output.
- Configure `pyproject.toml` or `fastmcp.toml` with metadata for marketplaces (name, summary, tags).
- Add `README.md` explaining installation steps and `skill_zips/manifest.json` if you intend to publish.

---

### Next Steps

- Extend the server with additional tools following the portmanteau pattern (restrict count to avoid tool explosion).
- Integrate persistent storage (`fastmcp.storage.DiskStore`) if state is required.
- See [modules/distribution-and-installation.md](modules/distribution-and-installation.md) for publishing paths (MCPB, npm/npx).
- Reference [modules/release-readiness.md](modules/release-readiness.md) before shipping.
