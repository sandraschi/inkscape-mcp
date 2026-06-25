set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
import 'scripts/just/fleet.just'

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome ci .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome check --write .

# Execute pytest suite
test:
    uv run pytest

# Execute mypy type analytics
typecheck:
    uv run mypy src/inkscape_mcp

# Unified quality verification
check: lint typecheck test
    @echo check complete

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    uv run safety check

# ── Operation ─────────────────────────────────────────────────────────────────

# Launch Inkscape MCP (HTTP mode)
serve port="11028":
    uv run inkscape-mcp --mode http --port {{port}}

# Quick fmt alias (calls fix)
fmt: fix
    @echo fmt done

# Quantitative snapshot of repo statistics
stats:
    uv run python tools/repo_stats.py

# Launch Inkscape MCP (Dual Mode)
run:
    uv run inkscape-mcp --mode dual

# Launch Inkscape MCP (Stdio Mode)
run-stdio:
    uv run inkscape-mcp --mode stdio

# Launch Inkscape MCP (HTTP Mode)
run-http port="11028":
    uv run inkscape-mcp --mode http --port {{port}}

# ── Packaging ─────────────────────────────────────────────────────────────────

# Sync MCPB source artifacts
sync-mcpb-src:
    uv run python tools/sync_mcpb_src.py

# Expand MCPB examples
expand-mcpb-examples:
    uv run python tools/expand_mcpb_examples.py

# Build MCPB bundle
mcpb-pack: sync-mcpb-src expand-mcpb-examples
    uv run python tools/pack_mcpb.py

# Build wheel package
build-wheel:
    uv build

# ── Housekeeping ──────────────────────────────────────────────────────────────

# Execute pre-commit checks on all files
pre-commit:
	uv run pre-commit run --all-files

# ── Tauri NSIS ─────────────────────────────────────────────────────────────────

# Build the PyInstaller backend .exe (step before Tauri build)
build-sidecar:
    Set-Location '{{justfile_directory()}}\native'
    pwsh -NoProfile -File .\build.ps1

# Build the Tauri NSIS desktop installer (full pipeline)
build-native:
    Set-Location '{{justfile_directory()}}\native'
    pwsh -NoProfile -File .\build.ps1

# Run the CUA smoke test against the installed NSIS app
cua-nsis-test:
	C:\Windows\py.exe scripts/cua-smoke.py
# ── Playwright E2E ─────────────────────────────────────────────────────

# Install Playwright browsers (one-time)
e2e-install:
    Set-Location '{{justfile_directory()}}\web_sota'
    npx playwright install chromium

# Run Playwright E2E smoke tests (start backend first: just serve)
e2e:
    Set-Location '{{justfile_directory()}}\web_sota'
    npx playwright test

# ── Demo Capture ─────────────────────────────────────────────────────────

# Capture screenshots of all webapp pages
capture-screenshots:
    pwsh -NoProfile -File '{{justfile_directory()}}\scripts\capture-demo.ps1' -Screenshots

# Record video walkthrough of the webapp
capture-video:
    pwsh -NoProfile -File '{{justfile_directory()}}\scripts\capture-demo.ps1' -Video

# Capture both screenshots and video
capture: capture-screenshots capture-video
    @echo Demo materials saved to docs/screenshots/

