# Fleet Standard Recipes
# Import this file in any repo's justfile:
#     import 'scripts/just/fleet.just'
# Parent justfile must set windows-shell; do not duplicate here.
# Defines only recipes repos typically don't ship themselves.
# build-native/build-sidecar are NOT here - repos define their own with VC vars.

REPO_DIR := justfile_directory()

# --- Build & Release ---------------------------------------------------------

# Build .mcpb bundle for Claude Desktop (sync src into mcpb/, validate, pack)
# Path is scripts/mcpb-pack.ps1 per MCPB_PACKAGING_STANDARDS.md -- do not repoint at mcpb/pack.ps1.
mcpb-pack:
    powershell.exe -NoProfile -File "{{REPO_DIR}}/scripts/mcpb-pack.ps1"

# Run CUA-NSIS smoke test (install -> launch -> verify -> uninstall)
# Syncs reports/cua-<repo>-<date>.md to mcd when the smoke script writes one.
cua-nsis-test:
    powershell.exe -NoProfile -File "{{REPO_DIR}}/scripts/just/cua-nsis-test.ps1"
    $md = "reports/cua-{{file_name(REPO_DIR)}}-$(Get-Date -Format 'yyyy-MM-dd').md"; if (Test-Path $md) { Copy-Item $md "D:/Dev/repos/mcp-central-docs/reports/" -Force; Write-Host "Synced $md to mcd" }

# Run CUA webapp test (pre-Tauri: start.ps1 stack + nav walk in browser)
# Syncs reports/cua-<repo>-<date>.md to mcd when the test script writes one.
cua-webapp-test:
    powershell.exe -NoProfile -File "{{REPO_DIR}}/scripts/just/cua-webapp-test.ps1"
    $md = "reports/cua-{{file_name(REPO_DIR)}}-$(Get-Date -Format 'yyyy-MM-dd').md"; if (Test-Path $md) { Copy-Item $md "D:/Dev/repos/mcp-central-docs/reports/" -Force; Write-Host "Synced $md to mcd" }

# --- Utilities ---------------------------------------------------------------

# Scan repository for Unicode issues in logger/print calls
emojibuster:
    powershell.exe -NoProfile -File "{{REPO_DIR}}/scripts/just/emojibuster.ps1" -Path "{{REPO_DIR}}"

# Audit Tauri-wrapped repos for missing zoom + restart/status features
tauri-audit:
    powershell.exe -NoProfile -File "{{REPO_DIR}}/scripts/retrofit-tauri2-api.ps1" -Audit

# Retrofit a single Tauri-wrapped repo with zoom + restart/status (use: just tauri-fix name=calibre-mcp)
tauri-fix name:
    powershell.exe -NoProfile -File "{{REPO_DIR}}/scripts/retrofit-tauri2-api.ps1" -Apply -RepoName {{name}}

# --- Fleet Overview ----------------------------------------------------------

# Start the fleet overview webapp (http://localhost:11040)
fleet-overview:
    powershell.exe -NoProfile -Command "npm --prefix '{{REPO_DIR}}/fleet-overview' run dev"

# --- Emergency Kill ----------------------------------------------------------

# Emergency stop: kill all fleet servers and pause supervisor auto-restart
fleet-stop:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO_DIR}}/scripts/just/fleet-stop.ps1"

# --- Port Zombies ------------------------------------------------------------

# Show stale listeners on fleet-registered ports (dry run, touches nothing)
zombies:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO_DIR}}/scripts/just/clear-port-zombies.ps1" -DryRun

# Kill stale listeners on fleet-registered ports (labeled port -> product)
zombie-clean:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO_DIR}}/scripts/just/clear-port-zombies.ps1"

# Restrict to specific ports: just zombie-clean-ports ports=11154,11155
zombie-clean-ports ports:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{{REPO_DIR}}/scripts/just/clear-port-zombies.ps1" -Ports "{{ports}}"

# --- GPU Arbitration (4090 between InvokeAI and local dev models) -----------

# Kick InvokeAI web + unload Ollama models so muse-glimmer/qwen3.8 get the VRAM
gpu-free:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Dev\repos\mcp-central-docs\scripts\just\gpu-arbitration.ps1" -Action Kick

# Bring InvokeAI web back up after dev work
invokeai-up:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Dev\repos\mcp-central-docs\scripts\just\gpu-arbitration.ps1" -Action Restore

# Show who holds the 4090 right now
gpu-status:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Dev\repos\mcp-central-docs\scripts\just\gpu-arbitration.ps1" -Action Status
