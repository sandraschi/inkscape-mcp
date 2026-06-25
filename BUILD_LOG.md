# BUILD_LOG.md — inkscape-mcp NSIS Build Records

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
