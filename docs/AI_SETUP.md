# AI_SETUP - install inkscape-mcp for a user

You are an AI agent (Claude Code, Cursor, Codex, Copilot, ...) asked to set up inkscape-mcp on this PC.
Follow these steps in order. Do not improvise outside them. Windows 10/11 only for now.

inkscape-mcp lets AI agents create, edit, animate and export SVG files with Inkscape. It runs as an MCP
server (stdio for Claude Desktop / Claude Code / Cursor) and, optionally, a local dashboard in the browser.

## 1. Ground rules

- Tell the user in plain words what you are about to do before each step.
- Allowed without asking: cloning this repo, running `start.bat` with the flags below, which may install
  **uv** (`astral-sh.uv`) and **bun** (`Oven-sh.Bun`) via winget.
- **Ask the user first** before installing **Inkscape** or **Ollama**, or before changing any MCP client config.
- Do not run anything elevated, do not change system settings, do not disable security features.
- Do not expose the server beyond `127.0.0.1`.
- Never kill a process you did not start. If a port is taken by another program, stop and tell the user.
- A quiet step is not a hung step: the first `uv sync` can take 1-3 minutes. Use a long timeout; never kill it.
- If something fails, rerunning `start.bat` is safe. Never "fix" problems by editing this repo's source code.

## 2. Get the code

Pick a folder with the user (default: `%USERPROFILE%\inkscape-mcp`). Then:

```powershell
git clone https://github.com/sandraschi/inkscape-mcp "$env:USERPROFILE\inkscape-mcp"
```

No git? Download and unpack the zip instead:

```powershell
Invoke-WebRequest https://github.com/sandraschi/inkscape-mcp/archive/refs/heads/main.zip -OutFile "$env:TEMP\inkscape-mcp.zip"
Expand-Archive "$env:TEMP\inkscape-mcp.zip" "$env:USERPROFILE" ; Rename-Item "$env:USERPROFILE\inkscape-mcp-main" inkscape-mcp
```

All commands below run in that folder.

## 3. Check (installs nothing)

```powershell
.\start.bat -Check -Json
```

Read `verdict` and the `checks` array:

| verdict | exit code | Do |
|---|---|---|
| `READY` | 0 | Go to step 5 |
| `READY WITH WARNINGS` | 2 | Read each `warn` item, decide with step 4, then continue |
| `BLOCKED: ...` | 1 | Stop. Tell the user the `detail` and `fix` of the `fail` item. Do not work around it |

`status: install` items are fine: step 5 installs them.
If `running` is `true`, inkscape-mcp is already running: skip to step 7.

## 4. Decide

| Situation (from the check) | Choice |
|---|---|
| `inkscape` is `warn` (not found) | Ask: "Inkscape is needed for export/convert/trace. Install it now (free, ~150 MB)?" If yes: `winget install --id Inkscape.Inkscape --exact --source winget`. If no: continue, drawing/animation still works |
| `ollama` is `info` (not running) | Optional, only for AI-generated SVGs from text. Mention it once; do not install unless asked |
| User only wants their AI app to draw SVGs | Stdio connect is enough (step 7a). Step 5 still installs dependencies |
| User wants the dashboard (gallery, animation studio, layers) | Also start the servers (step 6) |
| User uses only Claude Desktop and wants zero setup | Alternative: the `.mcpb` from https://github.com/sandraschi/inkscape-mcp/releases/latest - the user drags it onto Claude Desktop themselves. Then you are done |

## 5. Install

```powershell
.\start.bat -Yes -NoStart
```

Run with a timeout of at least 10 minutes. Ends with `Install OK.` and exit code 0. Prints the fix next to
any error. On failure: rerun once (it resumes); if it fails again, go to step 8.

## 6. Start and verify (dashboard only)

```powershell
.\start.bat -Yes -Detach -NoBrowser
```

Returns in about 10-30 s once healthy. Verify:

```powershell
Invoke-RestMethod http://127.0.0.1:11028/api/health   # expect status=ok, server=inkscape-mcp
```

Tell the user: dashboard at http://127.0.0.1:11029/ . Stop with `.\stop.bat` (or `.\start.bat -Stop`).
The servers keep running after you exit; tell the user how to stop them.

## 7. Connect the user's AI app

Ask which app, show the user the change, then apply it. Replace `C:\path\to\inkscape-mcp` with the real folder.

**a) Stdio (recommended; the app starts the server itself, nothing needs to be running):**

Claude Code:

```powershell
claude mcp add inkscape --scope user -- uv --directory "C:\path\to\inkscape-mcp" run inkscape-mcp --mode stdio
```

Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`) or Cursor (`%USERPROFILE%\.cursor\mcp.json`),
merged into the existing `mcpServers` object, never replacing it:

```json
{
  "mcpServers": {
    "inkscape": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\inkscape-mcp", "run", "inkscape-mcp", "--mode", "stdio"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

Claude Desktop must be restarted (fully quit from the tray) to pick it up.

**b) HTTP (only while step 6 servers are running):** `http://127.0.0.1:11028/mcp`
(Claude Code: `claude mcp add --transport http inkscape http://127.0.0.1:11028/mcp`).

**Verify:** in the app, ask: "Run inkscape_system with operation=status." It should list the tools and
report whether Inkscape was found.

## 8. Stop conditions and logs

Stop and hand back to the user, quoting the relevant lines, when:

- the check says `BLOCKED`,
- `start.bat` fails twice in a row,
- a step needs elevation, a driver, or a change you were not allowed to make in step 1.

Logs (one set per run, overwritten each run):

| File | Contains |
|---|---|
| `logs\start.log` | Everything `start.bat` printed |
| `logs\backend.log`, `logs\backend.log.err` | Server output |
| `logs\frontend.log`, `logs\frontend.log.err` | Dashboard output |

Problems and fixes: [TROUBLESHOOTING.md](TROUBLESHOOTING.md). To report a bug, open an issue at
https://github.com/sandraschi/inkscape-mcp/issues and attach `logs\start.log` and `logs\backend.log.err`.
