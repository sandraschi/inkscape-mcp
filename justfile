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
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# Inkscape MCP — fleet recipes (mcp-central-docs PACKAGING_STANDARDS.md §5)

stats:
    uv run python tools/repo_stats.py

# --- Quality ---

test:
    uv run pytest

fmt:
    uv run ruff format .
    uv run ruff check --fix .

typecheck:
    uv run mypy src/inkscape_mcp

check: lint typecheck test
    @echo check complete

# --- Run (repo root; clone + uv sync first) ---

run:
    uv run inkscape-mcp --mode dual

run-stdio:
    uv run inkscape-mcp --mode stdio

run-http port="10847":
    uv run inkscape-mcp --mode http --port {{port}}

# --- MCPB ---

sync-mcpb-src:
    uv run python tools/sync_mcpb_src.py

expand-mcpb-examples:
    uv run python tools/expand_mcpb_examples.py

# Requires Node.js (npx-cli.js via node). Writes dist/inkscape-mcp-v<version>.mcpb
mcpb-pack: sync-mcpb-src expand-mcpb-examples
    uv run python tools/pack_mcpb.py

# --- Build / publish helpers ---

build-wheel:
    uv build

pre-commit:
    uv run pre-commit run --all-files
