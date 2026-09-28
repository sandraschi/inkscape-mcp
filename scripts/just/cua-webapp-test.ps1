# Run CUA webapp test (pre-Tauri: start.ps1 stack + nav walk in browser)
# Self-contained: resolves repo root from its own location (scripts/just/.. = repo root).
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path (Join-Path $PSScriptRoot "..") "..")).Path
Set-Location $repoRoot
if (Test-Path ".venv\Scripts\python.exe") {
    & ".venv\Scripts\python.exe" scripts/cua-webapp-test.py
} else {
    & py scripts/cua-webapp-test.py
}
exit $LASTEXITCODE
