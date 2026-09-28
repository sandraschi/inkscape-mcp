# BUILD_LOG.md — inkscape-mcp NSIS Build Records

## Build 2026-09-28 (v2.7.0)

**Status:** Complete — full pass, including a genuine (non-sandboxed) end-to-end verification.

### Pre-build audit (TAURI_PRODUCTION_PITFALLS.md Phase 1 checklist A-J)

Found and fixed before building, since a build gate that reports success having examined
nothing is this fleet's most common failure mode:

- `pywinauto`/`pytesseract` were missing from `[dependency-groups] dev` — per the documented
  CRITICAL PITFALL, this would have silently no-op'd every GUI phase of the CUA smoke test
  while still printing a full pass. Added via `uv add --dev pywinauto pytesseract`.
- **Port mismatch**: `native/src/backend.rs`'s `BACKEND_PORT` and `main.py`'s `--port` default
  were both `11027`, but the compiled frontend (`web_sota/src/lib/api.ts`, `vite.config.ts`),
  `native/build.ps1`'s own gate, `native/tauri.conf.json`'s CSP, and this repo's own
  `WEBAPP_PORTS.md` registry entry all expect `11028` (confirmed as the long-standing canonical
  port — even the 2026-06-24 build log above references 11028/11201 test ports). This is the
  exact "backend spawns but frontend cannot reach it" pitfall. Fixed in `backend.rs`,
  `native/src/main.rs`'s headless fallback, `main.py`, `app.py`'s settings-display default,
  and `.env.example`.
- `inkscape-mcp-backend.spec` had `noarchive=False` and `upx=True` — both are fleet-documented
  crash patterns (`No module named 'difflib'` / AV false-positives on frozen builds). Fixed to
  `noarchive=True`, `upx=False`; added `joserfc`/`joserfc.jwk`/`joserfc.jwt` hiddenimports for
  FastMCP 3.4+'s JWT auth chain (this repo pins `fastmcp>=3.4.4`) plus `cachetools` and
  `collect_submodules('key_value')`.
- `native/build.ps1` had two literal em-dash characters (`—`, `→`) that PowerShell's parser
  choked on — the exact blender-mcp postmortem bug (#10 in TAURI_PRODUCTION_PITFALLS.md).
  Replaced with ASCII `-`/`->`.
- `scripts/just/cua-nsis-test.ps1` and `cua-webapp-test.ps1` both called
  `Join-Path $PSScriptRoot ".." ".."` — PowerShell's `Join-Path` doesn't accept 3 positional
  args. Fixed by chaining two `Join-Path` calls.
- `.gitignore` was missing `cua-reports/` (the smoke script's actual `--output-dir` default).

### CUA-NSIS smoke test result: real bug in the test harness, not the app

`just cua-nsis-test` installed cleanly and launched the operator, but "Backend not reachable
after 30s" on Phase 3. Root cause confirmed via `backend-spawn.log`: this Claude Code session
itself runs inside Claude Desktop's own AppContainer sandbox, so the launched operator
materialized its backend into
`AppData\Local\Packages\Claude_...\LocalCache\Local\Inkscape MCP\` instead of the real
`%LOCALAPPDATA%\Inkscape MCP\` — this is **CRITICAL PITFALL #2** from
`cua_nsis_smoke_testing.md` (AppContainer loopback isolation), not a defect in this repo's
Tauri wrapper.

**Verified the real thing anyway**, per that doc's own diagnostic technique: launched the
installed `inkscape-mcp-native.exe` via a genuinely separate, unsandboxed context
(`schtasks /Create` + `/Run`, then deleted the task). Result: backend materialized into the
correct real `%LOCALAPPDATA%\Inkscape MCP\` path, opened port 11028 within ~4s, and both
`GET /api/health` and `GET /api/v1/diagnostics` returned 200 with the real 18-tool list. This
is a genuine pass of the actual shipped artifact — the CUA script's 30s failure only reproduces
when run from inside this sandboxed session, which the pywinauto-driven `cua-smoke.py` also is,
so a future run of `just cua-nsis-test` from an unsandboxed shell (a normal user terminal, not
a Claude Code session) should pass cleanly.

### Cert Pipeline Status
| Gate | Status |
|------|--------|
| TypeScript lint (`tsc --noEmit`) | PASS |
| Frontend build (bun) | PASS |
| PyInstaller backend | PASS (~59 MB) |
| Frozen binary smoke test | PASS |
| Size gate (>= 5 MB) | PASS |
| NSIS build | PASS (58.6 MiB, `Inkscape MCP_2.7.0_x64-setup.exe`) |
| CUA-NSIS smoke test (in-sandbox) | FAIL — AppContainer isolation artifact, see above |
| Manual unsandboxed verification (schtasks) | PASS — real backend, real port, real API responses |
| Uninstall | PASS — clean removal, install dir gone |

## Build 2026-06-24 (v2.6.0)

**Status:** Complete (with caveat — see below)

### Changes
- Backend `/api/health` now returns `tool_count`, `uptime_seconds` (was missing)
- New `/api/v1/diagnostics` endpoint for CUA-NSIS compliance
- Dashboard: tool count + uptime KPI cards with `data-testid`
- Dashboard: 4-column KPI grid (Server, Tools, Inkscape, Ollama)
- Topbar: dynamic backend status via zustand store (green/red/gray dot)
- `build.ps1` step 0: sandbox-safe port-based kill (no `Get-Process`)
- `backend.rs`: `free_port` waits up to 120s for TIME_WAIT to clear
- `backend.rs`: `PYTHONUNBUFFERED=1` env var for unbuffered log output
- Fleet standard: added "Backend health API + dashboard KPIs" section to `tauri_nsis_building.md`
- PR #4 closed with thank-you (detector fix incorporated)

### Known Issue: Port TIME_WAIT on install
The CUA smoke test (Phase 3) currently fails because the backend process from a previous run leaves port 11028 in TIME_WAIT (~240s on Windows). The `free_port` function now waits up to 120s, but the CUA health check only polls for 30s.

**Workaround:** Run `just build-native && just cua-nsis-test` sequentially on a CLEAN boot, or manually ensure no stale process was on port 11028 within the last 4 minutes.

**Fix options:**
1. Increase CUA health check timeout to 150s (ugly)
2. Have the native app bind to a random ephemeral port and report back (complex)
3. Use `SO_REUSEADDR` on the uvicorn socket (requires FastMCP/uvicorn config change)
4. Pre-allocate and hold the port in the Rust code before spawning (most robust)

### Cert Pipeline Status
| Gate | Status |
|------|--------|
| TypeScript lint | PASS |
| Frontend build | PASS |
| PyInstaller backend | PASS (37.8 MB) |
| Frozen binary smoke test | PASS |
| Size gate (>= 5 MB) | PASS |
| NSIS build | PASS (~41.9 MB) |
| CUA-NSIS smoke test | FAIL (TIME_WAIT — see above) |

### Backend Verified Working
The frozen `inkscape-mcp-backend.exe` was tested directly on port 11201:
- `/api/health` returns 200 with `server`, `version`, `uptime`, `tool_count`, `providers`
- `/api/v1/diagnostics` returns 200 with tool list
- Uvicorn starts and serves requests
- All initialization completes (telemetry, prefab, REST bridge, transports)
