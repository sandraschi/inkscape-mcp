# FleetStartMode.ps1 - vendored per-repo copy (no mcp-central-docs required at runtime)
# Canonical upstream: mcp-central-docs/scripts/FleetStartMode.ps1 (private fleet docs)

# FleetStartMode.ps1 - shared launch modes for webapp/start.ps1 launchers
# Canonical upstream: mcp-central-docs/scripts/FleetStartMode.ps1
# Port clearing uses port-scoped netstat+findstr; Session 0 checks protect Windows services.

function Get-FleetStartModeBoundParameters {
    param([hashtable]$BoundParameters)

    $filtered = @{}
    foreach ($key in @('Headless', 'BackendOnly', 'FrontendOnly', 'NoBrowser', 'SkipRestart')) {
        if ($BoundParameters.ContainsKey($key)) {
            $filtered[$key] = $BoundParameters[$key]
        }
    }
    return $filtered
}

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
    $probeRun = ($env:FLEET_PROBE_RUN -eq '1')
    $runFrontend = (-not $BackendOnly) -and ($FrontendOnly -or (-not $Headless) -or $probeRun)
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
        [switch]$BackendOnly,
        [switch]$FrontendOnly,
        [string]$StartScriptPath = ''
    )

    if ($env:FLEET_PROBE_RUN -eq '1') { return }
    if (-not $Headless) { return }

    if ($env:FLEET_HEADLESS_REENTERED -eq '1') { return }
    $env:FLEET_HEADLESS_REENTERED = '1'

    $scriptPath = $StartScriptPath
    if (-not $scriptPath -or -not (Test-Path -LiteralPath $scriptPath)) {
        Write-Host "ERROR: Headless launcher script not found: $scriptPath" -ForegroundColor Red
        exit 1
    }

    $spawnArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $scriptPath,
        '-Headless'
    )
    if ($FrontendOnly) {
        $spawnArgs += '-FrontendOnly'
    } elseif ($BackendOnly) {
        $spawnArgs += '-BackendOnly'
    }
    Start-Process powershell.exe -ArgumentList $spawnArgs -WindowStyle Hidden
    exit
}

function Get-FleetPortListenerPids {
    param([Parameter(Mandatory)][int]$Port)

    $pids = [System.Collections.Generic.HashSet[int]]::new()
    $portNeedle = ":$Port "
    $raw = cmd /c "netstat -ano -p TCP 2>nul | findstr LISTENING | findstr `"$portNeedle`""
    if (-not $raw) { return @() }

    $lines = if ($raw -is [System.Array]) { @($raw) } else { @($raw -split "`r?`n") }
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = ($line.Trim() -split '\s+')
        if ($parts.Count -lt 5) { continue }
        $localAddr = $parts[1]
        if ($localAddr -notmatch ':(\d+)$') { continue }
        if ([int]$Matches[1] -ne $Port) { continue }
        $procId = 0
        if ([int]::TryParse($parts[-1], [ref]$procId) -and $procId -gt 4) {
            [void]$pids.Add($procId)
        }
    }
    return @($pids)
}

$script:FleetProtectedPidResults = @{}

function Clear-FleetProtectedServicePidCache {
    $script:FleetProtectedPidResults = @{}
}

function Test-FleetProcessProtectedByService {
    param([Parameter(Mandatory)][int]$ProcessId)

    if ($ProcessId -le 4) { return $false }
    if ($script:FleetProtectedPidResults.ContainsKey($ProcessId)) {
        return [bool]$script:FleetProtectedPidResults[$ProcessId]
    }

    # On Windows, all Windows Services (and their spawned children) execute in Session 0.
    # Standard user dev processes execute in interactive Session > 0.
    $isService = $false
    try {
        $proc = Get-Process -Id $ProcessId -ErrorAction Stop
        $isService = ($proc.SessionId -eq 0)
    } catch {
        $isService = $false
    }

    $script:FleetProtectedPidResults[$ProcessId] = $isService
    return $isService
}

function Test-FleetPortHeldByService {
    param([Parameter(Mandatory)][int]$Port)

    foreach ($procId in @(Get-FleetPortListenerPids -Port $Port)) {
        if (Test-FleetProcessProtectedByService -ProcessId $procId) {
            return $true
        }
    }
    return $false
}

function Get-FleetPortsStillListening {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [switch]$ExcludeProtectedServiceProcesses
    )

    $still = @{}
    foreach ($port in @($Ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)) {
        $pids = @(Get-FleetPortListenerPids -Port $port)
        if ($ExcludeProtectedServiceProcesses) {
            $pids = @($pids | Where-Object { -not (Test-FleetProcessProtectedByService -ProcessId $_) })
        }
        if ($pids.Count -gt 0) {
            $still[$port] = $pids
        }
    }
    return $still
}

function Get-FleetProcessBrief {
    param([Parameter(Mandatory)][int]$ProcessId)

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) { return $null }

    return [pscustomobject]@{
        Id        = $ProcessId
        Name      = $proc.ProcessName
        SessionId = $proc.SessionId
        ParentId  = 0
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

    # Never attempt to kill Session 0 service processes from dev scripts
    if ($before.SessionId -eq 0) {
        return [pscustomobject]@{ Ok = $false; Name = $before.ProcessName; SessionId = 0; Error = 'Windows Service process (Session 0)' }
    }

    # Terminate process tree directly using taskkill /F /T
    $null = Start-Process -FilePath "taskkill.exe" -ArgumentList @("/F", "/T", "/PID", "$ProcessId") `
        -Wait -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue

    Start-Sleep -Milliseconds 80
    $after = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($after) {
        try { Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue } catch { }
        Start-Sleep -Milliseconds 50
        $after = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    }

    return [pscustomobject]@{ Ok = ($null -eq $after) }
}

function Stop-FleetPortSquatters {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet",
        [switch]$ElevatedFallback
    )

    $uniquePorts = @($Ports | Where-Object { $_ -gt 0 } | Sort-Object -Unique)
    if ($uniquePorts.Count -eq 0) { return }

    $killedAny = $false
    foreach ($port in $uniquePorts) {
        $pids = @(Get-FleetPortListenerPids -Port $port)
        foreach ($procId in $pids) {
            if (Test-FleetProcessProtectedByService -ProcessId $procId) {
                $brief = Get-FleetProcessBrief -ProcessId $procId
                $name = if ($brief) { $brief.Name } else { 'process' }
                Write-Host "[$Label] skip PID $procId ($name) on port $port - Windows/NSSM service" -ForegroundColor DarkCyan
                continue
            }
            Write-Host "[$Label] Stopping stale PID $procId on port $port ..." -ForegroundColor DarkGray
            $res = Stop-FleetProcessId -ProcessId $procId
            if ($res.Ok) { $killedAny = $true }
        }
    }
    if ($killedAny) {
        Start-Sleep -Milliseconds 150
    }
}

function Stop-FleetPortListeners {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet"
    )

    Stop-FleetPortSquatters -Ports $Ports -Label $Label
    $still = Get-FleetPortsStillListening -Ports $Ports
    if ($still.Count -eq 0) {
        Write-Host "[$Label] Ports clear: $($Ports -join ', ')" -ForegroundColor Green
        return $true
    }

    $details = @()
    foreach ($entry in $still.GetEnumerator()) {
        foreach ($procId in $entry.Value) {
            $brief = Get-FleetProcessBrief -ProcessId $procId
            $name = if ($brief) { $brief.Name } else { 'process' }
            $svcNote = if (Test-FleetProcessProtectedByService -ProcessId $procId) { ' (Windows service)' } else { '' }
            $details += "port $($entry.Key) $name PID $procId$svcNote"
        }
    }
    Write-Host "[$Label] Ports still active: $($details -join '; ')" -ForegroundColor Yellow
    return ($still.Count -eq 0)
}

# LEGACY SHIM (kept for 5 pre-convergence start.ps1 callers: blender, yahboom,
# worldlabs, notebooklm-fleet, podman). New launchers must use the unified
# convergence engine in Invoke-FleetWebappStart.ps1 (Start-FleetWebapp) instead:
# per-component health-check-then-reuse, never a whole-stack verdict.
# This shim NEVER returns ReuseHealthy for a port it did not health-verify
# (unverified service-held ports report ReuseUnverified + Reuse=$false).
function Resolve-FleetPortConflict {
    param(
        [Parameter(Mandatory)][int[]]$Ports,
        [string]$Label = "fleet",
        [hashtable]$HealthChecks = @{},
        [switch]$AllowReuse,
        [switch]$ForceRestart
    )

    # 1. Clear killable non-service listeners
    Stop-FleetPortSquatters -Ports $Ports -Label $Label

    # 2. Inspect remaining listeners
    $stillAll = Get-FleetPortsStillListening -Ports $Ports
    $stillDev = Get-FleetPortsStillListening -Ports $Ports -ExcludeProtectedServiceProcesses

    if ($stillAll.Count -eq 0) {
        return [pscustomobject]@{ Action = 'Cleared'; Reuse = $false }
    }

    # If dev processes still occupy the ports after kill attempt, report blocked
    if ($stillDev.Count -gt 0) {
        $blockers = @()
        foreach ($entry in $stillDev.GetEnumerator()) {
            foreach ($pidVal in $entry.Value) {
                $blockers += "port $($entry.Key) PID $pidVal"
            }
        }
        Write-Host "[$Label] ERROR: ports still held: $($blockers -join '; ')" -ForegroundColor Red
        return [pscustomobject]@{ Action = 'Blocked'; Reuse = $false }
    }

    # All remaining listeners are Windows Services (Session 0).
    # A port counts as verified ONLY if it has a HealthChecks entry that passes.
    # Listening without verification is NOT reuse - it is an unverified squat.
    $allVerified = $true
    $allListening = $true
    foreach ($p in $Ports) {
        if ($p -le 0) { continue }
        $pInt = [int]$p
        if (-not $stillAll.ContainsKey($pInt)) {
            $allListening = $false
            continue
        }
        if ($HealthChecks.ContainsKey($pInt)) {
            if (-not (Test-FleetHttpOk -Url $HealthChecks[$pInt])) {
                Write-Host "[$Label] ERROR: port $pInt held by Windows service but health check failed." -ForegroundColor Red
                Write-Host "Restart the service (services.msc / nssm restart $Label)." -ForegroundColor Yellow
                return [pscustomobject]@{ Action = 'Blocked'; Reuse = $false }
            }
        } else {
            $allVerified = $false
        }
    }

    # If ALL configured ports are listening AND every one passed a health check,
    # the entire stack is reusable. Otherwise NEVER claim ReuseHealthy.
    if ($allListening -and $allVerified) {
        Write-Host "[$Label] All ports active and health-verified - reusing existing stack." -ForegroundColor Green
        return [pscustomobject]@{ Action = 'ReuseHealthy'; Reuse = $true }
    }

    if ($allListening -and -not $allVerified) {
        $unverified = @($Ports | Where-Object { $_ -gt 0 -and $stillAll.ContainsKey([int]$_) -and -not $HealthChecks.ContainsKey([int]$_) })
        Write-Host "[$Label] Port(s) $($unverified -join ', ') held by a Windows service WITHOUT a passing health check - refusing blind reuse." -ForegroundColor Yellow
        Write-Host "[$Label] Remedy: re-run with health checks, or migrate this launcher to Start-FleetWebapp (per-component convergence)." -ForegroundColor Yellow
        return [pscustomobject]@{ Action = 'ReuseUnverified'; Reuse = $false }
    }

    # Partial service (e.g. backend service healthy, frontend free to start)
    Write-Host "[$Label] Service port(s) healthy; remaining port(s) free to start." -ForegroundColor Green
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

    $resolved = Resolve-FleetPortConflict -Ports $Ports -Label $Label -HealthChecks $HealthChecks `
        -AllowReuse:$AllowReuse -ForceRestart:$ForceRestart
    return ($resolved.Action -ne 'Blocked')
}

function Start-FleetDetachedShell {
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
            RedirectStandardOutput = $outLog
            RedirectStandardError  = $errLog
        }
        if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }
        return Start-Process @psi
    }

    # R8: title detached consoles from -Label so taskbar / taskkill can
    # identify backend vs frontend without remembering ports. Probe runs
    # use NoNewWindow + redirect, title is irrelevant there (early return).
    $titledArgs = @($Args)
    $cmdIdx = [Array]::IndexOf($titledArgs, '-Command')
    if ($cmdIdx -ge 0 -and ($cmdIdx + 1) -lt $titledArgs.Count) {
        $safe = ($Label -replace "'", "''")
        $titledArgs[$cmdIdx + 1] = "`$Host.UI.RawUI.WindowTitle='$safe'; " + $titledArgs[$cmdIdx + 1]
    }

    $normal = @{
        FilePath     = $Exe
        ArgumentList = $titledArgs
        PassThru     = $true
        WindowStyle  = $WindowStyle
    }
    if ($WorkingDirectory) { $normal.WorkingDirectory = $WorkingDirectory }
    return Start-Process @normal
}
