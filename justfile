set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Display the SOTA Industrial Dashboard
default:
    @$lines = Get-Content '{{justfile()}}'; \
    Write-Host ' [SOTA] Industrial Operations Dashboard v1.3.2' -ForegroundColor White -BackgroundColor Cyan; \
    Write-Host '' ; \
    $currentCategory = ''; \
    foreach ($line in $lines) { \
        if ($line -match '^# ── ([^─]+) ─') { \
            $currentCategory = $matches[1].Trim(); \
            Write-Host "`n  $currentCategory" -ForegroundColor Cyan; \
            Write-Host ('  ' + ('─' * 45)) -ForegroundColor Gray; \
        } elseif ($line -match '^# ([^─].+)') { \
            $desc = $matches[1].Trim(); \
            $idx = [array]::IndexOf($lines, $line); \
            if ($idx -lt $lines.Count - 1) { \
                $nextLine = $lines[$idx + 1]; \
                if ($nextLine -match '^([a-z0-9-]+):') { \
                    $recipe = $matches[1]; \
                    $pad = ' ' * [math]::Max(2, (18 - $recipe.Length)); \
                    Write-Host "    $recipe" -ForegroundColor White -NoNewline; \
                    Write-Host "$pad$desc" -ForegroundColor Gray; \
                } \
            } \
        } \
    } \
    Write-Host "`n  [System State: PROD/HARDENED]" -ForegroundColor DarkGray; \
    Write-Host ''

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
run-http port="10847":
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
