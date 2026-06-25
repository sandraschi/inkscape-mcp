Param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
$BackendPort = 11028
$FrontendPort = 11029

# Port zombie clearing
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Write-Host "=== inkscape-mcp ===" -ForegroundColor Cyan
Write-Host "Backend: http://127.0.0.1:$BackendPort" -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:$FrontendPort" -ForegroundColor Green

# Start backend
$BackendJob = Start-Job -Name "backend" -ScriptBlock {
    param($Root, $Port)
    Set-Location $Root
    uv run inkscape-mcp --mode http --port $Port
} -ArgumentList $ScriptRoot, $BackendPort

# Readiness poll
Write-Host "Waiting for backend..." -ForegroundColor Yellow
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) {
            Write-Host "Backend ready" -ForegroundColor Green
            break
        }
    } catch {}
    Start-Sleep 1
}

if ($BackendOnly) { return }

# Start frontend
$WebRoot = Join-Path $ScriptRoot "web_sota"
Start-Process -NoNewWindow -FilePath "npx" -ArgumentList "vite --port $FrontendPort --host" -WorkingDirectory $WebRoot

Write-Host "Frontend starting on http://127.0.0.1:$FrontendPort" -ForegroundColor Green

if (-not $NoBrowser) {
    Start-Sleep 3
    Start-Process "http://127.0.0.1:$FrontendPort"
}

# Keep-alive
while ($true) {
    if ($BackendJob.State -eq "Completed" -or $BackendJob.State -eq "Failed") {
        Receive-Job $BackendJob; break
    }
    Start-Sleep 2
}
