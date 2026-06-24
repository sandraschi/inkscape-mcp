# Build Log

## 2026-06-23 — Initial fleet conformance

- **PR #4 fix**: Inkscape detector GIMP→Inkscape (winreg guard, env var, all platforms)
- **Stale cleanup**: Removed `tools_legacy/`, `.bak`/`.backup` files, stale egg-info, old `py.typed`
- **tauri.conf.json**: Removed Tauri 1.x deprecated keys (`createDesktopShortcut`, `createStartMenuShortcut`), targets→`["nsis"]`, version→2.6.0
- **backend.rs**: Added TCP health check polling loop (30 attempts)
- **main.rs**: Added `start_backend` command + invoke_handler, async spawn in setup
- **build-desktop.ps1**: Replaced stub with real frontend build
- **glama.json**: Version→2.6.0, tools→16, framework→FastMCP 3.4+
- **llms.txt**: Ports→11028/11029, FastMCP→3.4+
- **justfile**: `build-native` calls `build.ps1`, added `build-sidecar`, fixed `{{REPO}}`→`justfile_directory()`
- **MCPB**: Cleaned `__pycache__`, pack configured
- **Lint**: ruff green on `src/`, biome config on 2.5.0 with Tailwind CSS support
