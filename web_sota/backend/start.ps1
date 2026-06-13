param([switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)
$Port = 10999

Write-Host "==> inkscape-mcp Logging Backend" -ForegroundColor Cyan

Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Start-Sleep 1

Write-Host "==> Starting on port $Port..." -ForegroundColor Cyan
$Job = Start-Job -Name "inkscape-logging" -ScriptBlock {
    param($Root, $Port)
    Set-Location $Root
    uv run python -m web_sota.backend.server --port $Port
} -ArgumentList $RepoRoot, $Port

for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { Write-Host "==> Ready" -ForegroundColor Green; break }
    } catch {}
    Start-Sleep 1
}

Write-Host "Logging backend at http://127.0.0.1:$Port" -ForegroundColor Green
while ($true) {
    if ($Job.State -eq "Completed" -or $Job.State -eq "Failed") { Receive-Job $Job; break }
    Start-Sleep 2
}
