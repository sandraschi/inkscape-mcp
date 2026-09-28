# Run CUA-NSIS smoke test (install -> launch -> nav walk -> uninstall)
# Self-contained: resolves repo root from its own location (scripts/just/.. = repo root).
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path (Join-Path $PSScriptRoot "..") "..")).Path
Set-Location $repoRoot
if (Test-Path ".venv\Scripts\python.exe") {
    & ".venv\Scripts\python.exe" scripts/cua-smoke.py
} else {
    & py scripts/cua-smoke.py
}
exit $LASTEXITCODE
