# PortHelpers.ps1 - fast port listener teardown (no Get-NetTCPConnection, no global python scan)
# Vendored per-repo under scripts/PortHelpers.ps1 - no mcp-central-docs runtime path required.

function Get-PortListenerPidsFast {
    param([int]$Port)
    $pids = [System.Collections.Generic.HashSet[int]]::new()
    $needle = ":$Port"
    $raw = cmd /c "netstat -ano -p TCP 2>nul | findstr `"$needle`" | findstr LISTENING"
    if (-not $raw) { return @() }
    foreach ($line in ($raw -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = ($line.Trim() -split '\s+')
        if ($parts.Count -lt 5) { continue }
        $procId = 0
        if ([int]::TryParse($parts[-1], [ref]$procId) -and $procId -gt 4) {
            [void]$pids.Add($procId)
        }
    }
    return @($pids)
}

function Stop-PortListeners {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet"
    )
    $targetPids = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($port in ($Ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)) {
        foreach ($procId in (Get-PortListenerPidsFast -Port $port)) {
            [void]$targetPids.Add($procId)
        }
    }
    if ($targetPids.Count -eq 0) { return }

    Write-Host "[$Label] Stopping $($targetPids.Count) listener(s) on ports $($Ports -join ', ') ..." -ForegroundColor Yellow
    foreach ($procId in $targetPids) {
        if ($procId -eq $PID) { continue }
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 200
}

function Stop-RepoConsoleScriptLock {
    param(
        [Parameter(Mandatory)][string]$RepoRoot,
        [string[]]$ScriptNames = @()
    )
    $venvScripts = Join-Path $RepoRoot ".venv\Scripts"
    if (-not (Test-Path -LiteralPath $venvScripts)) { return }
    if ($ScriptNames.Count -eq 0) {
        $ScriptNames = @(Get-ChildItem -LiteralPath $venvScripts -Filter '*.exe' -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch '^(python|uv|uvicorn|pip|activate)\.exe$' } |
            ForEach-Object { [System.IO.Path]::GetFileNameWithoutExtension($_.Name) })
    }
    foreach ($name in $ScriptNames) {
        Get-Process -Name $name -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Path -and $_.Path.StartsWith($venvScripts, [StringComparison]::OrdinalIgnoreCase)) {
                Write-Host "  Stopping stale $name PID $($_.Id)" -ForegroundColor Yellow
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}
