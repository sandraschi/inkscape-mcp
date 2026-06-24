$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RepoName = Split-Path -Leaf $Root
$Triple = "x86_64-pc-windows-msvc"
$ResourceDir = "$PSScriptRoot\resources"
$DevDir = "$PSScriptRoot\binaries"
New-Item -ItemType Directory -Force -Path $ResourceDir, $DevDir | Out-Null

# Step 0: Kill stale backend processes that hold file locks
Get-Process "${RepoName}-backend" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "=== ${RepoName} Tauri Release Build ===" -ForegroundColor Cyan

# Step 0: Verify API_BASE matches backend port (catches "Failed to fetch" before Tauri build)
$apiFile = Join-Path $Root "web_sota\src\lib\api.ts"
if (Test-Path $apiFile) {
    $apiContent = Get-Content $apiFile -Raw
    if ($apiContent -match "127.0.0.1:(\d+)") {
        $apiPort = [int]$Matches[1]
        if ($apiPort -ne 11028) {
            throw "API_BASE in $apiFile points to port $apiPort but backend serves on 11028. Fix before building — dev proxy masks this, prod will FAIL."
        }
        Write-Host "  API_BASE port: $apiPort (matches backend) ✓" -ForegroundColor Green
    }
}

# Step 1: TypeScript lint gate + frontend build
$frontendDirs = @("web_sota", "webapp/frontend", "webapp")
foreach ($dir in $frontendDirs) {
    $frontend = Join-Path $Root $dir
    if (Test-Path "$frontend\package.json") {
        Write-Host "-> [1/4] Building frontend ($dir)..." -ForegroundColor Yellow
        Push-Location $frontend
        npm install --silent 2>$null

        Write-Host "  tsc --noEmit..." -ForegroundColor Gray
        $tscOut = npx tsc --noEmit 2>&1
        $tscExit = $LASTEXITCODE
        if ($tscExit -ne 0) {
            Write-Host "  TypeScript compilation FAILED — fix errors before building NSIS" -ForegroundColor Red
            Write-Host $tscOut
            throw "TypeScript compilation failed — fix all errors before building NSIS installer"
        }

        npm run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
        Pop-Location
        break
    }
}

# Step 2: PyInstaller backend (onefile)
Write-Host "-> [2/4] PyInstaller backend..." -ForegroundColor Yellow
$specFile = "$Root\${RepoName}-backend.spec"
if (Test-Path $specFile) {
    Push-Location $Root
    # Patch fastmcp to not crash on missing metadata (dist-info stripped below)
    $fm = "$Root\.venv\Lib\site-packages\fastmcp\__init__.py"
    if (Test-Path $fm) {
        $c = Get-Content $fm -Raw
        if ($c -match 'except PackageNotFoundError:\s+    __version__ = _version\("fastmcp"\)') {
            $c = $c -replace 'except PackageNotFoundError:\s+    __version__ = _version\("fastmcp"\)', 'except PackageNotFoundError:
    try:
        __version__ = _version("fastmcp")
    except PackageNotFoundError:
        __version__ = "0.0.0"'
            Set-Content $fm -Value $c -Encoding utf8
            Write-Host "  Patched fastmcp metadata fallback" -ForegroundColor Yellow
        }
    }
    # Ensure pyinstaller runs in the project venv, not the global tool environment
    # (uv run pyinstaller resolves to the global uv tool, missing all project deps)
    $pyiExe = "$Root\.venv\Scripts\pyinstaller.exe"
    if (-not (Test-Path $pyiExe)) {
        Write-Host "  Installing pyinstaller in project venv..." -ForegroundColor Yellow
        uv add --dev pyinstaller
    }
    # Pre-clean stale exe to avoid PermissionError on rebuild
    Remove-Item "$Root\dist\${RepoName}-backend.exe" -Force -ErrorAction SilentlyContinue
    & $pyiExe "$specFile" --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

    # Gate: smoke-test the frozen binary (catches ALL import crashes generically)
    $frozenExe = "$Root\dist\${RepoName}-backend.exe"
    Write-Host "  Smoke-testing frozen binary..." -ForegroundColor Yellow
    $testPort = 11999  # ephemeral port to avoid collision
    $oldPort = $env:MCP_PORT
    $oldHost = $env:MCP_HOST
    $env:MCP_PORT = "$testPort"
    $env:MCP_HOST = "127.0.0.1"
    $testProc = Start-Process -FilePath $frozenExe -NoNewWindow -PassThru -RedirectStandardError "$Root\dist\pyi-crash.log"
    Start-Sleep -Seconds 5
    $env:MCP_PORT = $oldPort
    $env:MCP_HOST = $oldHost
    if ($testProc.HasExited) {
        $crash = Get-Content "$Root\dist\pyi-crash.log" -Raw
        throw "Frozen binary crashed on launch (exit $($testProc.ExitCode)):`n$crash"
    }
    # Clean up test process
    $testProc.Kill()
    $testProc.Dispose()
    Remove-Item "$Root\dist\pyi-crash.log" -Force -ErrorAction SilentlyContinue
    Write-Host "  Frozen binary smoke test PASSED" -ForegroundColor Green
} else {
    Write-Host "  WARNING: spec file not found at $specFile — using existing backend exe if present" -ForegroundColor DarkYellow
}

# Step 3: Embed in Tauri resources (+ dev fallback)
Write-Host "-> [3/5] Embedding backend..." -ForegroundColor Yellow
$src = "$Root\dist\${RepoName}-backend.exe"
if (-not (Test-Path $src)) { throw "Backend exe not found at $src — PyInstaller step failed" }
$sizeMB = (Get-Item $src).Length / 1MB
if ($sizeMB -lt 5) { throw "Backend exe is only $([math]::Round($sizeMB, 1)) MB — PyInstaller produced an empty/broken binary. Check run_server.py and hidden imports." }
Copy-Item $src "$ResourceDir\${RepoName}-backend.exe" -Force
Copy-Item $src "$DevDir\${RepoName}-backend-$Triple.exe" -Force
Write-Host "  Backend exe: $((Get-Item $src).Length / 1MB) MB"

# Bundle .env.example (NOT .env — dev .env has personal API keys)
$envExample = "$Root\.env.example"
if (Test-Path $envExample) {
    Copy-Item $envExample "$ResourceDir\.env.example" -Force
    Write-Host "  Bundled .env.example ✓" -ForegroundColor Green
} else {
    Write-Host "  WARNING: .env.example not found at repo root" -ForegroundColor DarkYellow
}

# Step 4: Single NSIS installer
Write-Host "-> [4/5] Tauri NSIS bundle..." -ForegroundColor Yellow
Push-Location $PSScriptRoot
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
npx @tauri-apps/cli build --bundles nsis
if ($LASTEXITCODE -ne 0) { throw "Tauri build failed with exit code $LASTEXITCODE" }
Pop-Location

# Stage to repo dist/
$distDir = Join-Path $Root "dist"
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
$nsisDir = "$PSScriptRoot\target\release\bundle\nsis"
if (Test-Path $nsisDir) { Copy-Item "$nsisDir\*-setup.exe" "$distDir\" -Force }
$strayExe = "$PSScriptRoot\target\release\inkscape-mcp-backend.exe"
if (Test-Path $strayExe) { Remove-Item $strayExe -Force; Write-Host "  Cleaned stray: $strayExe" -ForegroundColor DarkGray }

# Step 5: Fleet shortcut (Tauri starts launcher)
Write-Host "-> [5/5] Fleet shortcut..." -ForegroundColor Yellow
$launcherDir = "D:\Dev\Tauri starts"
$setupExe = Get-ChildItem "$nsisDir\*-setup.exe" | Select-Object -First 1
if ($setupExe -and (Test-Path $launcherDir)) {
    $shortcutPath = Join-Path $launcherDir "${RepoName}-setup.lnk"
    try {
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $setupExe.FullName
        $shortcut.Save()
        Write-Host "  Shortcut: $shortcutPath → $($setupExe.Name)" -ForegroundColor Green
    } catch {
        Write-Host "  WARNING: Could not create shortcut: $_" -ForegroundColor DarkYellow
    }
} else {
    Write-Host "  WARNING: NSIS installer or launcher dir not found" -ForegroundColor DarkYellow
}

Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "Ship: $nsisDir\*.exe"

