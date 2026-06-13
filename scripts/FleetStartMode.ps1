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
    $raw = cmd /c "netstat -ano -p TCP 2>nul | findstr LISTENING"
    if (-not $raw) { return @() }
    foreach ($line in ($raw -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = ($line.Trim() -split '\s+')
        if ($parts.Count -lt 5) { continue }
        $localAddr = $parts[1]
        if ($localAddr -notmatch ':(\d+)$') { continue }
        $localPort = [int]$Matches[1]
        if ($localPort -ne $Port) { continue }
        $procId = 0
        if ([int]::TryParse($parts[-1], [ref]$procId) -and $procId -gt 4) {
            [void]$pids.Add($procId)
        }
    }
    return @($pids)
}

function Get-FleetProcessBrief {
    param([Parameter(Mandatory)][int]$ProcessId)

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) { return $null }

    $sessionId = $proc.SessionId
    try {
        $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
        if ($cim -and $null -ne $cim.SessionId) { $sessionId = [int]$cim.SessionId }
    } catch { }

    $parentId = 0
    try { $parentId = $proc.Parent.Id } catch { }

    return [pscustomobject]@{
        Id        = $ProcessId
        Name      = $proc.ProcessName
        SessionId = $sessionId
        ParentId  = $parentId
    }
}

function Test-FleetHttpOk {
    param(
        [Parameter(Mandatory)][string]$Url,
        [int]$TimeoutSec = 3
    )

    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        return ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500)
    } catch {
        return $false
    }
}

function Stop-FleetProcessId {
    param(
        [Parameter(Mandatory)][int]$ProcessId,
        [switch]$Elevated
    )

    if ($ProcessId -le 4 -or $ProcessId -eq $PID) {
        return [pscustomobject]@{ Ok = $true; Skipped = $true }
    }

    $before = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $before) {
        return [pscustomobject]@{ Ok = $true; Gone = $true }
    }

    $mySession = (Get-Process -Id $PID).SessionId
    $targetSession = $before.SessionId
    $killError = $null

    if ($Elevated) {
        $null = Invoke-FleetElevatedTaskKill -ProcessIds @($ProcessId)
    } else {
        try {
            Stop-Process -Id $ProcessId -Force -ErrorAction Stop
        } catch {
            $killError = $_.Exception.Message
            $null = Start-Process -FilePath "taskkill.exe" -ArgumentList @("/F", "/T", "/PID", "$ProcessId") `
                -Wait -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue
        }
    }

    Start-Sleep -Milliseconds 120
    $after = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($after) {
        return [pscustomobject]@{
            Ok           = $false
            Name         = $before.ProcessName
            SessionId    = $targetSession
            MySession    = $mySession
            CrossSession = ($targetSession -ne $mySession)
            Error        = $killError
        }
    }

    return [pscustomobject]@{ Ok = $true }
}

function Invoke-FleetElevatedTaskKill {
    param([Parameter(Mandatory)][int[]]$ProcessIds)

    $unique = @($ProcessIds | Where-Object { $_ -gt 4 } | Sort-Object -Unique)
    if ($unique.Count -eq 0) { return $true }

    $lines = @('$ErrorActionPreference = "SilentlyContinue"')
    foreach ($procId in $unique) {
        $lines += "taskkill /F /T /PID $procId 2>`$null | Out-Null"
    }
    $lines += "Start-Sleep -Milliseconds 400"
    foreach ($procId in $unique) {
        $lines += "if (Get-Process -Id $procId -ErrorAction SilentlyContinue) { exit 1 }"
    }
    $scriptText = ($lines -join "; ")
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($scriptText))

    try {
        $proc = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-EncodedCommand", $encoded
        ) -Wait -PassThru -WindowStyle Hidden -ErrorAction Stop
        return ($proc.ExitCode -eq 0)
    } catch {
        return $false
    }
}

function Get-FleetPortListenerPidSet {
    param([Parameter(Mandatory)][int[]]$Ports)

    $targetPids = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($port in @($Ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)) {
        foreach ($procId in @(Get-FleetPortListenerPids -Port $port)) {
            [void]$targetPids.Add($procId)
        }
    }
    return @($targetPids)
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
        [string]$Label = "fleet",
        [switch]$ElevatedFallback
    )

    $uniquePorts = @($Ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)
    if ($uniquePorts.Count -eq 0) { return }

    if ($ElevatedFallback) {
        $targetPids = @(Get-FleetPortListenerPidSet -Ports $uniquePorts)
        if ($targetPids.Count -eq 0) { return }

        Write-Host "[$Label] Clearing port listeners on $($uniquePorts -join ', ') ..." -ForegroundColor Yellow
        foreach ($procId in $targetPids) {
            $result = Stop-FleetProcessId -ProcessId $procId
            if ($result.Ok) {
                Write-Host "  stop PID $procId" -ForegroundColor DarkGray
            }
        }
        Start-Sleep -Milliseconds 300

        $remaining = @(Get-FleetPortListenerPidSet -Ports $uniquePorts)
        if ($remaining.Count -gt 0) {
            Write-Host "  elevated stop PIDs: $($remaining -join ', ')" -ForegroundColor DarkGray
            $null = Invoke-FleetElevatedTaskKill -ProcessIds $remaining
            Start-Sleep -Milliseconds 400
        }
        return
    }

    function Invoke-FleetPortKillPass {
        param([string]$PassLabel)
        $targetPids = Get-FleetPortListenerPidSet -Ports $uniquePorts
        if ($targetPids.Count -eq 0) { return }

        Write-Host "[$PassLabel] Clearing port listeners on $($uniquePorts -join ', ') ..." -ForegroundColor Yellow
        foreach ($procId in $targetPids) {
            $result = Stop-FleetProcessId -ProcessId $procId
            if ($result.Ok) {
                Write-Host "  stop PID $procId" -ForegroundColor DarkGray
            } else {
                $brief = Get-FleetProcessBrief -ProcessId $procId
                $name = if ($brief) { $brief.Name } else { 'process' }
                $sess = if ($brief) { $brief.SessionId } else { '?' }
                Write-Host "  could not stop PID $procId ($name, session $sess)" -ForegroundColor DarkYellow
            }
        }
    }

    Invoke-FleetPortKillPass -PassLabel $Label
    Start-Sleep -Milliseconds 400
    Invoke-FleetPortKillPass -PassLabel "$Label-retry"
    Start-Sleep -Milliseconds 200
}

function Stop-FleetPortListeners {
    <#
      Hard stop for dev restart/stop.bat. Normal kill then elevated taskkill (UAC) when needed.
    #>
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet"
    )

    Stop-FleetPortSquatters -Ports $Ports -Label $Label -ElevatedFallback
    $still = Get-FleetPortsStillListening -Ports $Ports
    if ($still.Count -eq 0) {
        Write-Host "[$Label] Ports clear: $($Ports -join ', ')" -ForegroundColor Green
        return $true
    }

    $details = @()
    foreach ($entry in $still.GetEnumerator()) {
        foreach ($procId in $entry.Value) {
            $brief = Get-FleetProcessBrief -ProcessId $procId
            if ($brief) {
                $details += "port $($entry.Key) $($brief.Name) PID $procId (session $($brief.SessionId))"
            } else {
                $details += "port $($entry.Key) PID $procId"
            }
        }
    }
    Write-Host "[$Label] ERROR: could not free ports: $($details -join '; ')" -ForegroundColor Red
    return $false
}

function Resolve-FleetPortConflict {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet",
        [hashtable]$HealthChecks = @{},
        [switch]$AllowReuse,
        [switch]$ForceRestart
    )

    $hardRestart = $ForceRestart -or (-not $AllowReuse)
    Stop-FleetPortSquatters -Ports $Ports -Label $Label -ElevatedFallback:$hardRestart

    $still = Get-FleetPortsStillListening -Ports $Ports
    if ($still.Count -eq 0) {
        return [pscustomobject]@{ Action = 'Cleared'; Reuse = $false }
    }

    $blockedPorts = @($still.Keys | Sort-Object)
    $canReuse = $AllowReuse -and (-not $ForceRestart) -and ($HealthChecks.Count -gt 0)
    if ($canReuse) {
        foreach ($port in $blockedPorts) {
            $portInt = [int]$port
            if (-not $HealthChecks.ContainsKey($portInt)) {
                $canReuse = $false
                break
            }
            if (-not (Test-FleetHttpOk -Url $HealthChecks[$portInt])) {
                $canReuse = $false
                break
            }
        }
    }

    if ($canReuse) {
        Write-Host "[$Label] Ports in use but health checks passed - reusing existing stack (-ReuseIfRunning)." -ForegroundColor Green
        return [pscustomobject]@{ Action = 'ReuseHealthy'; Reuse = $true }
    }

    $liveBlockers = @()
    $ghostBlockers = @()
    foreach ($entry in $still.GetEnumerator()) {
        foreach ($procId in $entry.Value) {
            $brief = Get-FleetProcessBrief -ProcessId $procId
            if ($brief) {
                $liveBlockers += "port $($entry.Key) $($brief.Name) PID $procId (session $($brief.SessionId))"
            } elseif ($null -ne (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
                $liveBlockers += "port $($entry.Key) PID $procId"
            } else {
                $ghostBlockers += "port $($entry.Key) ghost PID $procId"
            }
        }
    }

    if ($liveBlockers.Count -gt 0) {
        Write-Host "[$Label] ERROR: ports still held: $($liveBlockers -join '; ')" -ForegroundColor Red
        Write-Host "Run stop.bat or restart.bat, then start again." -ForegroundColor Yellow
        return [pscustomobject]@{ Action = 'Blocked'; Reuse = $false }
    }

    if ($ghostBlockers.Count -gt 0) {
        Write-Host "[$Label] WARNING: stale sockets remain ($($ghostBlockers -join '; '))." -ForegroundColor Yellow
        Write-Host "Windows may still block bind until TIME_WAIT clears or after reboot." -ForegroundColor Yellow
    }

    return [pscustomobject]@{ Action = 'Cleared'; Reuse = $false }
}

function Assert-FleetPortsAvailable {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet",
        [hashtable]$HealthChecks = @{},
        [switch]$AllowReuse,
        [switch]$ForceRestart
    )

    if ($HealthChecks.Count -gt 0 -or $AllowReuse -or $ForceRestart) {
        $resolved = Resolve-FleetPortConflict -Ports $Ports -Label $Label -HealthChecks $HealthChecks `
            -AllowReuse:$AllowReuse -ForceRestart:$ForceRestart
        return ($resolved.Action -ne 'Blocked')
    }

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
      FLEET_PROBE_LOG_DIR (no visible console; cold-start probe parses logs after teardown).
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
