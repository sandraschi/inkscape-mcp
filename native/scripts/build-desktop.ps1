# Build the React frontend before Tauri compilation
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$frontend = Join-Path $Root "web_sota"

if (Test-Path "$frontend\package.json") {
    Write-Host "-> Building frontend (web_sota)..." -ForegroundColor Yellow
    Push-Location $frontend
    npm install --silent 2>$null
    Write-Host "  tsc --noEmit..." -ForegroundColor Gray
    $tscOut = npx tsc --noEmit 2>&1
    $tscExit = $LASTEXITCODE
    if ($tscExit -ne 0) {
        Write-Host "  TypeScript compilation FAILED" -ForegroundColor Red
        Write-Host $tscOut
        throw "TypeScript compilation failed"
    }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
    Pop-Location
} else {
    Write-Host "  WARNING: package.json not found at $frontend" -ForegroundColor DarkYellow
}
