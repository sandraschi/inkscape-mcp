param(
    [switch]$Screenshots,
    [switch]$Video,
    [switch]$Open
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$OutDir = Join-Path $Root "docs\screenshots"
$BackendPort = 11028
$FrontendPort = 11029

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "=== inkscape-mcp demo capture ===" -ForegroundColor Cyan

# Kill stale processes
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Start backend
$job = Start-Job -Name "backend" -ScriptBlock {
    param($Root, $Port)
    Set-Location $Root
    uv run inkscape-mcp --mode http --port $Port
} -ArgumentList $Root, $BackendPort

# Wait for backend
for ($i = 0; $i -lt 30; $i++) {
    try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
          if ($r.StatusCode -eq 200) { break } } catch {}
    Start-Sleep 1
}

# Start frontend
$feDir = Join-Path $Root "web_sota"
$feProc = Start-Process -NoNewWindow -FilePath "npx" -ArgumentList "vite --port $FrontendPort --host" -WorkingDirectory $feDir -PassThru
Start-Sleep -Seconds 10

Write-Host "Frontend ready at http://127.0.0.1:$FrontendPort" -ForegroundColor Green

if ($Screenshots) {
    Write-Host "--- Taking screenshots ---" -ForegroundColor Yellow
    npx playwright test --config "$feDir\playwright.config.ts" e2e\demo-screenshots.spec.ts
    Write-Host "Screenshots saved to $OutDir" -ForegroundColor Green
}

if ($Video) {
    Write-Host "--- Recording video demo ---" -ForegroundColor Yellow
    # Re-run with video recording enabled
    $env:PW_VIDEO = "on"
    npx playwright test --config "$feDir\playwright.config.ts" e2e\demo-video.spec.ts
    # Copy video from test-results
    $vids = Get-ChildItem -Recurse -Filter "*.webm" "$feDir\test-results"
    foreach ($v in $vids) { Copy-Item $v.FullName "$OutDir\demo-walkthrough.webm" -Force }
    Write-Host "Video saved to $OutDir\demo-walkthrough.webm" -ForegroundColor Green
}

# Cleanup
if ($feProc -and -not $feProc.HasExited) { $feProc.Kill() }
Stop-Job $job -ErrorAction SilentlyContinue

if ($Open) { Start-Process $OutDir }
