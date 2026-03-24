# AI and sampling (agentic tools)

## Portmanteau tools (always)

These work over normal MCP tool calls — no sampling required:

- `inkscape_file`, `inkscape_vector`, `inkscape_analysis`, `inkscape_system`
- `list_local_models` (discovers local endpoints when available)

## Agentic / SEP-1577 sampling

Optional tools in `agentic.py` use **FastMCP 3.1** `ctx.sample()` so the **host client’s LLM** can plan multi-step SVG workflows. They only work when:

1. The MCP client implements **sampling** (e.g. some Cursor/Cline flows), and  
2. The server successfully registers those tools at startup.

If sampling is unavailable, rely on the portmanteau tools step by step.

## Server-side LLM defaults (REST / Ollama helpers)

Code under `app.py` documents defaults such as:

- `OLLAMA_BASE_URL` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `qwen2.5-coder:latest`)

These are used by optional HTTP/REST bridge paths, not a substitute for MCP client sampling. Adjust env vars to match your local Ollama or compatible server.

## Practical workflow

1. Confirm **Inkscape CLI** — [INKSCAPE.md](INKSCAPE.md).  
2. Use direct tools for deterministic edits (export, trace, validate).  
3. Enable agentic tools only when your IDE supports sampling and you want orchestrated plans.  
4. For local LLM listing, call `list_local_models` if Ollama/LM Studio is running.

See source: `src/inkscape_mcp/agentic.py`, `src/inkscape_mcp/app.py`.
