# Onboarding — inkscape-mcp

Get from zero to "agent edits SVGs via Inkscape" in ~10 minutes.

## What this is for

`inkscape-mcp` lets an AI agent create, edit, layer, animate, and export SVG files
through a real Inkscape installation. Without Inkscape on the machine, the server
starts but every operation degrades — **Inkscape is the wrappee, and onboarding it
is mandatory, not optional.**

Optional second wrappee: **Ollama** (local LLM) for AI-assisted SVG generation
(`generate_svg`, chat). Without it, those two tools report "no LLM detected";
everything else works.

## Money / accounts

- Nothing to buy. No accounts, no API keys, no cloud billing.
- Inkscape is free and open source. Ollama is free and local.
- Cloud LLM providers (Gemini, Anthropic, OpenAI, …) are optional, keyed via
  Settings → AI Settings in the dashboard. No key = those providers stay off.

## Steps

1. **Install Inkscape (classic desktop installer only).**
   `winget install Inkscape.Inkscape`, or https://inkscape.org/release/.
   Do NOT use the Microsoft Store version — it is sandboxed and its
   `inkscape.exe` cannot run CLI commands (server fails with "Access Denied").
   Verify: `& "C:\Program Files\Inkscape\bin\inkscape.exe" --version`
   (needs 1.0+; 1.2+ recommended for the Actions API).
   Custom path: set `INKSCAPE_PATH` env var.
2. **Clone + start.** `git clone https://github.com/sandraschi/inkscape-mcp`,
   then double-click `start.bat`. It installs uv/bun/deps, starts the backend
   (port 11028) and opens the dashboard (port 11029).
   First run takes 2–4 minutes while Python packages install — do not close it.
3. **(Optional) Install Ollama** for AI SVG generation: https://ollama.com,
   then `ollama pull <model>` (e.g. `qwen2.5-coder`). The dashboard
   Auto-detects it on mount (green provider dot).
4. **Connect your AI app.** Claude Desktop: drag the `.mcpb` from
   [Releases](https://github.com/sandraschi/inkscape-mcp/releases/latest) onto Claude.
   Others: see `docs/DEVELOPMENT.md` for the `uvx`/stdio config snippet.

## Sanity check

- Dashboard shows backend **Connected** (green dot, top bar).
- `inkscape_system(operation="status")` returns Inkscape available + version line.
- Try: *"Create a bouncing circle animation with a pink fill, then export as PNG."*

## Pitfalls

| Symptom | Cause → fix |
|---|---|
| Export/convert does nothing | Inkscape missing → `winget install Inkscape.Inkscape`, restart |
| "Access Denied" on `--version` | Store version of Inkscape → reinstall via classic installer |
| Port 11028/11029 "held by another program" | Close the holder, rerun `start.bat` |
| `generate_svg` says no LLM | Ollama not running → start Ollama or add a cloud key in Settings |
| `--query-*` garbage on non-ASCII install paths | Fixed in v2.7.1 (issue #8: locale forcing + stderr merge) — update |

## MOCK-until-onboarded

Not applicable as UI: this dashboard shows only live backend data (no sample
KPIs). Until Inkscape is detected, status surfaces report `available: false`
with the installer hint above instead of fake-ready graphics.
