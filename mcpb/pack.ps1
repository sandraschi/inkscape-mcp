#Requires -Version 5.1
<#
.SYNOPSIS
Build this repo's .mcpb bundle for Claude Desktop.

Implements the mandatory pipeline from MCPB_PACKAGING_STANDARDS.md section 2.5:
wipe + fresh-copy src -> mcpb/src (never edit the staged copy by hand), ensure
mcpb/.mcpbignore exists (the mcpb CLI reads .mcpbignore from the pack root,
not the repo root), run the required mechanical checks, then pack.

mcpb/src is a build artifact -- regenerated every run, gitignored, never
committed. This script deletes and recreates it each time.

Package name and entry point are read from this repo's own pyproject.toml /
mcpb/manifest.json -- nothing here is hardcoded to a specific repo, so the
same script works unmodified across the fleet.
#>
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$McpbDir = Join-Path $RepoRoot 'mcpb'
$ManifestPath = Join-Path $McpbDir 'manifest.json'
if (-not (Test-Path $ManifestPath)) { throw "No mcpb/manifest.json in $RepoRoot -- cannot pack." }
$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($manifest.name)) { throw "manifest.json has no (or empty) top-level 'name' -- would produce a malformed output filename." }
if ([string]::IsNullOrWhiteSpace($manifest.version)) { throw "manifest.json has no (or empty) top-level 'version' -- would produce a malformed output filename." }
if (-not $manifest.server) { throw "manifest.json has no 'server' section -- cannot resolve entry_point." }

if (-not (Get-Command bunx -ErrorAction SilentlyContinue)) {
    throw "bunx not found on PATH -- install Bun (https://bun.sh) before packing; @anthropic-ai/mcpb is invoked via bunx."
}

function Step($n, $msg) { Write-Host "== $n. $msg ==" -ForegroundColor Cyan }

Step 0 'Detect package name'
# Three signals, in order of authority. A project's pyproject.toml `name`
# (PyPI/distribution name, often hyphenated) does NOT always match the
# importable package directory under src/ - bookmarks-mcp is exactly this
# case (name = "bookmarks-mcp", package = src/browser_bookmarks_tools/).
# Trusting the name-derived guess without checking it exists is how this
# script failed at Step 1 with "Copy source missing" the first time it was
# actually run against a real repo.
$Pkg = $null
$pyprojPath = Join-Path $RepoRoot 'pyproject.toml'

# 1. Most authoritative: hatch's own build target, which must already point
#    at the real package for `uv build`/hatch to work at all.
if (Test-Path $pyprojPath) {
    $hatchMatch = [regex]::Match((Get-Content $pyprojPath -Raw), '(?m)packages\s*=\s*\[\s*"src[\\/]([^"\\/]+)"')
    if ($hatchMatch.Success) { $Pkg = $hatchMatch.Groups[1].Value }
}

# 2. Name-derived guess, only trusted if that directory actually exists.
if (-not $Pkg -and (Test-Path $pyprojPath)) {
    $m = [regex]::Match((Get-Content $pyprojPath -Raw), '(?m)^\s*name\s*=\s*"([^"]+)"')
    if ($m.Success) {
        $guess = $m.Groups[1].Value -replace '-', '_'
        if (Test-Path (Join-Path $RepoRoot "src\$guess")) { $Pkg = $guess }
    }
}

# 3. Last resort: exactly one directory under src/.
if (-not $Pkg) {
    $srcDirs = Get-ChildItem (Join-Path $RepoRoot 'src') -Directory -ErrorAction SilentlyContinue
    if ($srcDirs.Count -eq 1) { $Pkg = $srcDirs[0].Name }
}
if (-not $Pkg) { throw 'Could not detect package name from hatch config, pyproject.toml name, or a single src/<pkg>/ directory.' }
if (-not (Test-Path (Join-Path $RepoRoot "src\$Pkg"))) { throw "Detected package '$Pkg' but src\$Pkg does not exist." }
Write-Host "  package: $Pkg"

$SrcPkg = Join-Path $RepoRoot "src\$Pkg"
$StageRoot = Join-Path $McpbDir 'src'
$StagePkg = Join-Path $StageRoot $Pkg
$VerifyScript = Join-Path $McpbDir 'verify_pack.py'

# Entry point comes from this repo's own manifest.json -- whatever it already
# declares. manifest.json describes the BUNDLE (mcpb/ is what gets packed),
# so entry_point resolves relative to mcpb/, not the repo root. The existence
# check runs AFTER Step 1 (wipe + fresh-copy): on a clean checkout mcpb/src/
# does not exist yet, so checking here would fail before the stage is built.
# (Fixed 2026-09-27: check-before-create ordering bug.)
$entryPointRel = $manifest.server.entry_point
if (-not $entryPointRel) { throw 'manifest.json has no server.entry_point.' }

function Assert-EntryPointStaged {
    $entryFile = Join-Path $McpbDir $entryPointRel
    if (-not (Test-Path $entryFile)) { throw "manifest.json entry_point resolves to a missing file: $entryFile" }
    return $entryFile
}

# Two entry-point styles are both real fleet patterns (see
# MCPB_PACKAGING_STANDARDS.md section 2.5): a module living under src/<pkg>/
# (importable by dotted path), or a standalone bootstrap script elsewhere in
# the bundle that does its own sys.path setup and imports the real package
# (e.g. a run_server.py). Only the first case yields a clean relative path
# under mcpb/src; detect which one we have from that. Computed AFTER Step 1
# (see Assert-EntryPointStaged ordering note above).
function Get-EntryRelToSrc($entryFile) {
    # 5.1-safe: [System.IO.Path]::GetRelativePath is .NET Core only and
    # throws MethodNotFound on Framework 4.x. Both paths are absolute and
    # the staged entry always lives under $StageRoot, so a prefix cut
    # suffices (callers only test for a '..' escape).
    if ($entryFile.StartsWith($StageRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $entryFile.Substring($StageRoot.Length).TrimStart('\', '/')
    }
    return '..'
}

Step 1 'Wipe + fresh-copy src -> mcpb/src (never a stale/hand-edited stage)'
if (Test-Path $StageRoot) { Remove-Item -Recurse -Force $StageRoot }
if (-not (Test-Path $SrcPkg)) { throw "Copy source missing: $SrcPkg" }
New-Item -ItemType Directory -Force -Path $StageRoot | Out-Null
Copy-Item -Recurse -Force $SrcPkg $StagePkg
Write-Host "  copied $SrcPkg -> $StagePkg"

Step 1 counting as 'Assert staged entry point (must run after the copy)'
$entryFile = Assert-EntryPointStaged
$entryRelToSrc = Get-EntryRelToSrc $entryFile
if ($entryRelToSrc.StartsWith('..')) {
    # Standalone wrapper script - verify_pack.py runs it directly via runpy.
    $entryModuleOrFile = $entryFile
} else {
    $entryModuleOrFile = ($entryRelToSrc -replace '\.py$', '') -replace '[\\/]', '.'
}

Step 1b 'Sync assets/prompts -> mcpb/assets/prompts (prompts are edited in assets/)'
$SrcPrompts = Join-Path $RepoRoot 'assets\prompts'
$StagePrompts = Join-Path $McpbDir 'assets\prompts'
if (Test-Path $SrcPrompts) {
    New-Item -ItemType Directory -Force -Path $StagePrompts | Out-Null
    Copy-Item (Join-Path $SrcPrompts 'system.md') $StagePrompts -Force
    Copy-Item (Join-Path $SrcPrompts 'user.md') $StagePrompts -Force
    Copy-Item (Join-Path $SrcPrompts 'examples.json') $StagePrompts -Force
    Write-Host '  synced assets/prompts -> mcpb/assets/prompts'
}

Step 2 'Strip pollution from the fresh stage'
Get-ChildItem -Recurse -Path $StageRoot -Include '__pycache__' -Directory -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Path $StageRoot -Include '*.pyc', '*.bak', '*.bak.*', '*.bak-*', '*.orig', '*.rej' -File -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

Step 3 'Sync mcpb/.mcpbignore from repo root (pack root, not repo root, is what mcpb reads)'
$McpbIgnore = Join-Path $McpbDir '.mcpbignore'
$RootIgnore = Join-Path $RepoRoot '.mcpbignore'
if (Test-Path $RootIgnore) {
    Copy-Item $RootIgnore $McpbIgnore -Force
    Write-Host '  synced repo-root .mcpbignore -> mcpb/.mcpbignore'
} elseif (-not (Test-Path $McpbIgnore)) {
    throw 'No .mcpbignore at repo root or mcpb/ -- cannot pack safely.'
}

Step 4 'Required check: import isolation (only mcpb/src on sys.path)'
$env:PYTHONDONTWRITEBYTECODE = '1'
uv run --project $RepoRoot python $VerifyScript import $StageRoot $entryModuleOrFile $Pkg
if ($LASTEXITCODE -ne 0) { throw 'Import-isolation check failed' }

Step 5 'Required check: AST call-site binding (catches missing imports)'
# A staged-module entry point is checked in mcpb/src (where it now lives);
# a standalone wrapper script is checked in place (it's never copied there).
if ($entryRelToSrc.StartsWith('..')) {
    $astCheckFile = $entryFile
} else {
    $astCheckFile = Join-Path $StageRoot $entryRelToSrc
}
uv run --project $RepoRoot python $VerifyScript ast $astCheckFile
if ($LASTEXITCODE -ne 0) { throw 'AST check failed' }
Remove-Item Env:\PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue

Step 6 'Required check: pollution, run AFTER import (which itself writes bytecode)'
uv run --project $RepoRoot python $VerifyScript pollution $McpbDir
if ($LASTEXITCODE -ne 0) { throw 'Pollution check failed (import step above may have written __pycache__)' }

Step 7 '3-4-100 prompt check (report only -- does not block pack)'
$sysWords = 0; $userWords = 0; $exCount = 0
$sysPath = Join-Path $McpbDir 'assets/prompts/system.md'
$userPath = Join-Path $McpbDir 'assets/prompts/user.md'
$exPath = Join-Path $McpbDir 'assets/prompts/examples.json'
if (Test-Path $sysPath) { $sysWords = ((Get-Content -Raw $sysPath) -split '\s+' | Where-Object { $_ }).Count }
if (Test-Path $userPath) { $userWords = ((Get-Content -Raw $userPath) -split '\s+' | Where-Object { $_ }).Count }
if (Test-Path $exPath) { $exCount = (Get-Content -Raw $exPath | ConvertFrom-Json -ErrorAction SilentlyContinue).Count }
if ($sysWords -lt 3000 -or $userWords -lt 4000 -or $exCount -lt 100) {
    Write-Warning "3-4-100 FAIL (non-blocking): system.md=$sysWords/3000 user.md=$userWords/4000 examples.json=$exCount/100 -- runt package per MCPB_PACKAGING_STANDARDS.md 2.3b"
} else {
    Write-Host "  OK: system.md=$sysWords user.md=$userWords examples.json=$exCount"
}

Step 8 'mcpb pack'
$OutDir = Join-Path $RepoRoot 'dist'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
# Name the output after the bundle's own manifest.json name (what `mcpb pack`
# itself calls it, shown in its "Archive Contents" summary), not the detected
# source package name - they can differ (e.g. manifest name "bookmarks-mcp"
# vs. package "browser_bookmarks_tools").
$OutFile = Join-Path $OutDir "$($manifest.name)-v$($manifest.version).mcpb"
if (Test-Path $OutFile) { Remove-Item -Force $OutFile }
bunx @anthropic-ai/mcpb pack $McpbDir $OutFile
if ($LASTEXITCODE -ne 0) { throw 'mcpb pack failed' }

Step 9 'Verify pack output'
if (-not (Test-Path $OutFile)) { throw "Pack did not produce $OutFile" }
$size = (Get-Item $OutFile).Length
Write-Host "  built: $OutFile ($([math]::Round($size / 1kb, 1)) KB)"
bunx @anthropic-ai/mcpb info $OutFile
if ($LASTEXITCODE -ne 0) { throw 'mcpb info failed on the freshly-built bundle' }

Step 10 'Required check: launch the packaged entry point (mcpb info is static, this is not)'
# Unpack to a scratch directory and actually start the entry point from
# there. Its own sys.path.insert(0, .../src) takes priority over anything
# already importable in this dev environment, so this genuinely exercises
# the bundle's own staged code, not a dev editable-install standing in for
# it - the exact failure mode section 2.5 describes ("only appears to work
# on a machine where the package is already installed by other means").
# Note: this still runs inside the repo's own uv-managed Python env (for
# third-party deps), not a fully from-scratch venv built from
# mcpb/pyproject.toml alone - it proves the staged package layout/imports
# are sound, not that the declared dependency list is complete.
$LaunchDir = Join-Path ([System.IO.Path]::GetTempPath()) ("mcpb-launch-check-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
bunx @anthropic-ai/mcpb unpack $OutFile $LaunchDir
if ($LASTEXITCODE -ne 0) { throw 'mcpb unpack failed for the launch check' }

$launchEntry = Join-Path $LaunchDir $entryPointRel
if (-not (Test-Path $launchEntry)) { throw "Unpacked bundle is missing its own entry point: $launchEntry" }

# Launch the venv's python.exe directly, NOT `uv run python ...`. `uv run`
# spawns python as a CHILD process on Windows rather than replacing itself,
# so $proc from `Start-Process -FilePath uv` is the uv wrapper's PID, not
# the server's - Stop-Process on it later kills the wrapper and orphans the
# real server. Confirmed empirically: the first version of this check left
# a live python.exe bound to the probe port well after the script exited.
$VenvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPython)) { throw "No venv python at $VenvPython -- run 'uv sync' first." }

$proc = $null
$prevMcpPort = $env:MCP_PORT
try {
    # Use an arbitrary high port so this never collides with a real dev
    # server the same machine might already have running.
    $env:MCP_PORT = '39812'
    $outLog = Join-Path $LaunchDir 'launch.out.log'
    $errLog = Join-Path $LaunchDir 'launch.err.log'
    $proc = Start-Process -FilePath $VenvPython `
        -ArgumentList @($launchEntry) `
        -WorkingDirectory $LaunchDir -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog
    Start-Sleep -Seconds 4
    if ($proc.HasExited) {
        $errText = Get-Content $errLog -Raw -ErrorAction SilentlyContinue
        throw "Packaged entry point exited immediately (exit code $($proc.ExitCode)) - the bundle does not run standalone.`n$errText"
    }
    # "Still alive" alone can't distinguish a genuinely serving process from
    # one blocked on stdin.readline() (a stdio-transport server with no
    # client attached looks identical for these 4 seconds) or one whose
    # startup failed in a background thread without killing the main
    # process. A traceback on stderr is a real signal either way; scan for
    # one even though the process technically didn't exit.
    $errText = Get-Content $errLog -Raw -ErrorAction SilentlyContinue
    if ($errText -match 'Traceback \(most recent call last\)') {
        throw "Packaged entry point logged a traceback despite staying alive - startup likely failed in a background thread.`n$errText"
    }
    Write-Host "  OK: packaged entry point stayed alive 4s from a clean unpacked copy (pid $($proc.Id))"
    Write-Host "  Note: this proves the bundle starts without crashing, not that it actually serves - a stdio-transport server idling on stdin looks identical to one working correctly." -ForegroundColor DarkGray
} finally {
    if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    if ($null -eq $prevMcpPort) { Remove-Item Env:\MCP_PORT -ErrorAction SilentlyContinue } else { $env:MCP_PORT = $prevMcpPort }
    Remove-Item -Recurse -Force $LaunchDir -ErrorAction SilentlyContinue
}

Step 11 'Clean up staging copy (derived, regenerable, never committed)'
Remove-Item -Recurse -Force $StageRoot

Write-Host "Done: $OutFile" -ForegroundColor Green
