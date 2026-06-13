# FleetStartMode.ps1 - vendored per-repo copy (no mcp-central-docs required at runtime)
# Canonical upstream: mcp-central-docs standards/FleetStartMode.ps1
# FleetStartMode.ps1 - shared launch modes for webapp/start.ps1 launchers
# Vendored per-repo under scripts/FleetStartMode.ps1 (no mcp-central-docs runtime path).
# Port clearing uses per-port netstat+findstr (fast); never Get-NetTCPConnection or global python scan.

function Initialize-FleetStartMode {
    param(
        [switch]$Headless,
        [switch]$BackendOnly,
        [switch]$FrontendOnly,
        [switch]$NoBrowser
    )

    if ($FrontendOnly -and $BackendOnly) {
        Write-Error "Cannot combine -FrontendOnly and -BackendOnly."
        exit 1
    }

    $runBackend = -not $FrontendOnly
    $runFrontend = (-not $BackendOnly) -and (-not $Headless) -and (-not $FrontendOnly)
    $skipBrowser = $NoBrowser -or $Headless -or $BackendOnly

    return [pscustomobject]@{
        RunBackend  = $runBackend
        RunFrontend = $runFrontend
        SkipBrowser = $skipBrowser
        WindowStyle = if ($Headless) { "Hidden" } else { "Normal" }
    }
}

function Enter-FleetHeadlessConsole {
    param(
        [switch]$Headless,
        [switch]$BackendOnly
    )

    if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
        $spawnArgs = @(
            '-NoProfile', '-File', $PSCommandPath,
            '-Headless', '-BackendOnly'
        )
        Start-Process powershell.exe -ArgumentList $spawnArgs -WindowStyle Hidden
        exit
    }
}

function Get-FleetPortListenerPids {
    param([Parameter(Mandatory)][int]$Port)

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

function Get-FleetPortsStillListening {
    param([Parameter(Mandatory)][int[]]$Ports)

    $still = @{}
    foreach ($port in @($Ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)) {
        $pids = @(Get-FleetPortListenerPids -Port $port)
        if ($pids.Count -gt 0) {
            $still[$port] = $pids
        }
    }
    return $still
}

function Stop-FleetPortSquatters {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet"
    )

    $uniquePorts = @($Ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)
    if ($uniquePorts.Count -eq 0) { return }

    $targetPids = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($port in $uniquePorts) {
        foreach ($procId in @(Get-FleetPortListenerPids -Port $port)) {
            [void]$targetPids.Add($procId)
        }
    }
    if ($targetPids.Count -eq 0) { return }

    Write-Host "[$Label] Clearing port listeners on $($uniquePorts -join ', ') ..." -ForegroundColor Yellow
    foreach ($procId in $targetPids) {
        if ($procId -eq $PID) { continue }
        Write-Host "  stop PID $procId" -ForegroundColor DarkGray
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 200
}

function Assert-FleetPortsAvailable {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet"
    )

    $still = Get-FleetPortsStillListening -Ports $Ports
    if ($still.Count -eq 0) { return $true }

    $liveBlockers = @()
    $ghostBlockers = @()
    foreach ($entry in $still.GetEnumerator()) {
        foreach ($procId in $entry.Value) {
            if ($null -ne (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
                $liveBlockers += "port $($entry.Key) PID $procId"
            } else {
                $ghostBlockers += "port $($entry.Key) ghost PID $procId"
            }
        }
    }

    if ($liveBlockers.Count -gt 0) {
        Write-Host "[$Label] ERROR: ports still held by live process(es): $($liveBlockers -join '; ')" -ForegroundColor Red
        Write-Host "Close those processes, then re-run start.bat." -ForegroundColor Yellow
        return $false
    }

    if ($ghostBlockers.Count -gt 0) {
        Write-Host "[$Label] WARNING: stale sockets remain ($($ghostBlockers -join '; '))." -ForegroundColor Yellow
        Write-Host "Windows may still block bind until TIME_WAIT clears or after reboot." -ForegroundColor Yellow
    }

    return $true
}

function Start-FleetDetachedShell {
    <#
      Launch a background shell. When FLEET_PROBE_RUN=1, redirect stdout/stderr to
      FLEET_PROBE_LOG_DIR (no visible console; probe parses logs after teardown).
    #>
    param(
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][string]$Exe,
        [Parameter(Mandatory)][string[]]$Args,
        [string]$WorkingDirectory = "",
        [string]$WindowStyle = "Normal"
    )

    $probeRun = ($env:FLEET_PROBE_RUN -eq '1')
    if ($probeRun) {
        $logDir = if ($env:FLEET_PROBE_LOG_DIR) { $env:FLEET_PROBE_LOG_DIR } else { $env:TEMP }
        if (-not (Test-Path -LiteralPath $logDir)) {
            New-Item -ItemType Directory -Force -Path $logDir | Out-Null
        }
        $outLog = Join-Path $logDir "$Label.stdout.log"
        $errLog = Join-Path $logDir "$Label.stderr.log"
        $psi = @{
            FilePath               = $Exe
            ArgumentList           = $Args
            PassThru               = $true
            NoNewWindow            = $true
            WindowStyle            = 'Hidden'
            RedirectStandardOutput = $outLog
            RedirectStandardError  = $errLog
        }
        if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }
        return Start-Process @psi
    }

    $normal = @{
        FilePath     = $Exe
        ArgumentList = $Args
        PassThru     = $true
        WindowStyle  = $WindowStyle
    }
    if ($WorkingDirectory) { $normal.WorkingDirectory = $WorkingDirectory }
    return Start-Process @normal
}

