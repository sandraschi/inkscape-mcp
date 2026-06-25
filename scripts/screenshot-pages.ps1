param([switch]$Open)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ScreenshotDir = Join-Path $Root "docs\screenshots"
$BackendPort = 11028
$FrontendPort = 11029

New-Item -ItemType Directory -Force -Path $ScreenshotDir | Out-Null

Write-Host "=== inkscape-mcp screenshot capture ===" -ForegroundColor Cyan

# Start backend if not running
$be = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
if (-not $be) {
    Write-Host "Starting backend..." -ForegroundColor Yellow
    $job = Start-Job -Name "backend" -ScriptBlock {
        param($Root, $Port)
        Set-Location $Root
        uv run inkscape-mcp --mode http --port $Port
    } -ArgumentList $Root, $BackendPort
    Start-Sleep -Seconds 15
}

# Start frontend if not running
$fe = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue
if (-not $fe) {
    Write-Host "Starting frontend..." -ForegroundColor Yellow
    $feJob = Start-Process -NoNewWindow -FilePath "npx" -ArgumentList "vite --port $FrontendPort --host" -WorkingDirectory (Join-Path $Root "web_sota")
    Start-Sleep -Seconds 8
}

Write-Host "Taking screenshots..." -ForegroundColor Cyan

npx playwright test --config web_sota/playwright.config.ts --grep "screenshot" 2>&1

Write-Host "Screenshots saved to $ScreenshotDir" -ForegroundColor Green

if ($Open) {
    Start-Process $ScreenshotDir
}
