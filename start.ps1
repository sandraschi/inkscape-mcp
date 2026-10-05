#Requires -Version 5.1
<#
.SYNOPSIS
    inkscape-mcp launcher: installs, repairs or starts - whatever is needed next.

.DESCRIPTION
    One front door (ONE_CLICK_INSTALL_UX_STANDARD). Every run detects state:
    prereqs missing -> winget; deps missing -> uv sync / bun install;
    installed -> start; already running -> print the URL and exit 0.
    Rerunning after any failure is always safe.

    Agents: follow docs/AI_SETUP.md. Start with `start.bat -Check -Json`.

.PARAMETER Check
    Diagnose only. Installs nothing, starts nothing. Exit 0 ready, 2 ready with warnings, 1 blocked.
.PARAMETER Json
    With -Check: print one JSON object instead of text.
.PARAMETER Yes
    Never prompt; take the recommended defaults. Implied when stdin is not interactive.
.PARAMETER NoStart
    Install / repair only, then exit.
.PARAMETER Detach
    Start in the background and exit once healthy (for agents). Stop later with stop.bat.
.PARAMETER Stop
    Stop the servers this script started.
.PARAMETER Restart
    Stop our running servers (identified by /api/health), then start fresh. Picks up code changes.
#>
param(
    [switch]$Check,
    [switch]$Json,
    [switch]$Yes,
    [switch]$NoStart,
    [switch]$Detach,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$BackendOnly,
    [switch]$NoBrowser,
    [switch]$Headless  # legacy alias for -NoBrowser
)

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$WebRoot = Join-Path $RepoRoot 'web_sota'
$LogDir = Join-Path $RepoRoot 'logs'
$StartLog = Join-Path $LogDir 'start.log'
$BackendLog = Join-Path $LogDir 'backend.log'
$FrontendLog = Join-Path $LogDir 'frontend.log'
$PidFile = Join-Path $LogDir 'pids.json'
$BackendPort = 11028
$FrontendPort = 11029
$HealthUrl = "http://127.0.0.1:$BackendPort/api/health"
$DashboardUrl = "http://127.0.0.1:$FrontendPort/"
$McpHttpUrl = "http://127.0.0.1:$BackendPort/mcp"
$NeedMB = 1200  # .venv ~470 MB + node_modules ~300 MB + uv/bun caches

if ($Headless) { $NoBrowser = $true }
if ($Json -and -not $Check) { $Check = $true }

function Say([string]$Text, [string]$Color = 'Gray') {
    if (-not $Json) { Write-Host $Text -ForegroundColor $Color }
}

if (-not $Yes -and -not $Check -and [Console]::IsInputRedirected) {
    $Yes = $true
    Say 'No interactive input detected - taking recommended defaults (-Yes).' 'DarkGray'
}

# ---------------------------------------------------------------- helpers

function Find-Exe([string]$Name) {
    # Applications only (.exe before .cmd): a .ps1 shim (e.g. npm's bun.ps1) cannot be run from cmd.exe.
    $cmds = @(Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue)
    $exe = $cmds | Where-Object { $_.Source -like '*.exe' } | Select-Object -First 1
    if (-not $exe) { $exe = $cmds | Select-Object -First 1 }
    if ($exe) { return $exe.Source }
    return $null
}

function Update-SessionPath {
    $env:PATH = [Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' +
        [Environment]::GetEnvironmentVariable('PATH', 'User')
}

function Find-Inkscape {
    if ($env:INKSCAPE_PATH -and (Test-Path -LiteralPath $env:INKSCAPE_PATH)) { return $env:INKSCAPE_PATH }
    $onPath = Find-Exe 'inkscape'
    if ($onPath) { return $onPath }
    $candidates = @(
        'C:\Program Files\Inkscape\bin\inkscape.exe',
        'C:\Program Files (x86)\Inkscape\bin\inkscape.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\Inkscape\bin\inkscape.exe')
    )
    foreach ($c in $candidates) { if (Test-Path -LiteralPath $c) { return $c } }
    return $null
}

function Get-Listener([int]$PortNum) {
    $conn = Get-NetTCPConnection -LocalPort $PortNum -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $conn) { return $null }
    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    $procName = if ($proc) { $proc.ProcessName } else { 'unknown' }
    return [pscustomobject]@{ ProcId = [int]$conn.OwningProcess; Name = $procName }
}

function Test-OurHealth([string]$Url) {
    try {
        $r = Invoke-RestMethod -Uri $Url -TimeoutSec 3 -UseBasicParsing
        return ($r.server -eq 'inkscape-mcp')
    } catch { return $false }
}

function Test-HttpOk([string]$Url) {
    try {
        $r = Invoke-WebRequest -Uri $Url -TimeoutSec 3 -UseBasicParsing
        return ($r.StatusCode -eq 200)
    } catch { return $false }
}

function Get-RepoVersion {
    $line = Select-String -Path (Join-Path $RepoRoot 'pyproject.toml') -Pattern '^version\s*=\s*"([^"]+)"' |
        Select-Object -First 1
    if ($line) { return $line.Matches[0].Groups[1].Value }
    return 'unknown'
}

function Test-PythonInstalled { Test-Path -LiteralPath (Join-Path $RepoRoot '.venv\Scripts\python.exe') }
function Test-WebInstalled { Test-Path -LiteralPath (Join-Path $WebRoot 'node_modules\vite\package.json') }

# ---------------------------------------------------------------- check

function Invoke-Check {
    $checks = New-Object System.Collections.ArrayList
    function Add-Check($Name, $Status, $Detail, $Fix) {
        [void]$checks.Add([ordered]@{ name = $Name; status = $Status; detail = $Detail; fix = $Fix })
    }

    $os = [Environment]::OSVersion.Version
    $psv = $PSVersionTable.PSVersion
    Add-Check 'os' 'ok' "Windows $($os.Major).$($os.Minor) build $($os.Build), PowerShell $psv" $null

    $wingetExe = Find-Exe 'winget'
    if ($wingetExe) { Add-Check 'winget' 'ok' 'present' $null }
    else { Add-Check 'winget' 'warn' 'missing - needed only if uv or bun must be installed' 'Install "App Installer" from the Microsoft Store (Windows 10 1809+)' }

    $prereqs = @(@{ Cmd = 'uv'; Id = 'astral-sh.uv'; Label = 'uv (Python manager; fetches Python itself)' })
    if (-not $BackendOnly) { $prereqs += @{ Cmd = 'bun'; Id = 'Oven-sh.Bun'; Label = 'bun (dashboard dependencies)' } }
    foreach ($p in $prereqs) {
        if (Find-Exe $p.Cmd) { Add-Check $p.Cmd 'ok' 'present' $null }
        elseif ($wingetExe) { Add-Check $p.Cmd 'install' "missing - will install $($p.Id) via winget" $null }
        else { Add-Check $p.Cmd 'fail' 'missing and winget unavailable' "Install $($p.Label) manually: winget id $($p.Id)" }
    }

    $pyOk = Test-PythonInstalled
    $webOk = $BackendOnly -or (Test-WebInstalled)
    if ($pyOk) { Add-Check 'python_env' 'ok' '.venv present' $null }
    else { Add-Check 'python_env' 'install' 'will run uv sync (~470 MB, 1-3 min the first time)' $null }
    if (-not $BackendOnly) {
        if ($webOk) { Add-Check 'web_deps' 'ok' 'web_sota/node_modules present' $null }
        else { Add-Check 'web_deps' 'install' 'will run bun install (~300 MB, about 1 min)' $null }
    }

    $drive = (Get-Item -LiteralPath $RepoRoot).PSDrive
    $freeMB = [int]($drive.Free / 1MB)
    if ($pyOk -and $webOk) { Add-Check 'disk' 'ok' "$freeMB MB free on $($drive.Name):" $null }
    elseif ($freeMB -ge $NeedMB) { Add-Check 'disk' 'ok' "needs ~$NeedMB MB, $freeMB MB free on $($drive.Name):" $null }
    else { Add-Check 'disk' 'fail' "needs ~$NeedMB MB, only $freeMB MB free on $($drive.Name):" 'Free disk space or clone the repo to another drive' }

    $running = $false
    $ports = @(@{ Port = $BackendPort; Role = 'backend'; Probe = $HealthUrl })
    if (-not $BackendOnly) { $ports += @{ Port = $FrontendPort; Role = 'dashboard'; Probe = "http://127.0.0.1:$FrontendPort/api/health" } }
    foreach ($pt in $ports) {
        $owner = Get-Listener $pt.Port
        if (-not $owner) { Add-Check "port_$($pt.Port)" 'ok' "free ($($pt.Role))" $null }
        elseif (Test-OurHealth $pt.Probe) {
            Add-Check "port_$($pt.Port)" 'ok' "inkscape-mcp $($pt.Role) already running (pid $($owner.ProcId))" $null
            if ($pt.Role -eq 'backend') { $running = $true }
        } else {
            Add-Check "port_$($pt.Port)" 'fail' "held by another program: pid $($owner.ProcId) ($($owner.Name))" 'Close that program, or ask the user; never kill it without asking'
        }
    }

    $inkExe = Find-Inkscape
    if ($inkExe) {
        $ver = (Get-Item -LiteralPath $inkExe).VersionInfo.ProductVersion
        Add-Check 'inkscape' 'ok' "Inkscape $ver at $inkExe" $null
    } else {
        Add-Check 'inkscape' 'warn' 'Inkscape not found - server starts, but export/convert/trace operations need it' 'Ask the user, then: winget install --id Inkscape.Inkscape --source winget  (or set INKSCAPE_PATH)'
    }

    if (Test-HttpOk 'http://127.0.0.1:11434/api/tags') { Add-Check 'ollama' 'ok' 'Ollama running - AI SVG generation available' $null }
    else { Add-Check 'ollama' 'info' 'Ollama not running - optional, only for AI-assisted SVG generation' 'Optional: winget install --id Ollama.Ollama --source winget' }

    $fails = @($checks | Where-Object { $_.status -eq 'fail' })
    $warns = @($checks | Where-Object { $_.status -eq 'warn' })
    if ($fails.Count -gt 0) { $verdict = "BLOCKED: $($fails[0].detail)"; $code = 1 }
    elseif ($warns.Count -gt 0) { $verdict = 'READY WITH WARNINGS'; $code = 2 }
    else { $verdict = 'READY'; $code = 0 }

    return [ordered]@{
        repo      = 'inkscape-mcp'
        version   = Get-RepoVersion
        verdict   = $verdict
        exit_code = $code
        installed = ($pyOk -and $webOk)
        running   = $running
        urls      = [ordered]@{ dashboard = $DashboardUrl; health = $HealthUrl; mcp_http = $McpHttpUrl }
        logs      = [ordered]@{ start = $StartLog; backend = $BackendLog; frontend = $FrontendLog }
        checks    = $checks
    }
}

function Show-Report($Report) {
    if ($Json) { $Report | ConvertTo-Json -Depth 5; return }
    Say "=== inkscape-mcp $($Report.version) - check ===" 'Cyan'
    foreach ($c in $Report.checks) {
        $color = switch ($c.status) { 'ok' { 'Green' } 'install' { 'Cyan' } 'warn' { 'Yellow' } 'fail' { 'Red' } default { 'Gray' } }
        Say ('  [{0,-7}] {1,-11} {2}' -f $c.status, $c.name, $c.detail) $color
        if ($c.fix -and $c.status -ne 'ok') { Say "            fix: $($c.fix)" 'DarkGray' }
    }
    $vColor = if ($Report.exit_code -eq 0) { 'Green' } elseif ($Report.exit_code -eq 2) { 'Yellow' } else { 'Red' }
    Say "Verdict: $($Report.verdict)" $vColor
}

# ---------------------------------------------------------------- stop

function Stop-Tree([int]$ProcId) {
    & taskkill.exe /PID $ProcId /T /F 2>&1 | Out-Null
}

function Invoke-Stop {
    $stopped = 0
    if (Test-Path -LiteralPath $PidFile) {
        $saved = Get-Content -LiteralPath $PidFile -Raw | ConvertFrom-Json
        foreach ($entry in @($saved.backend, $saved.frontend)) {
            if (-not $entry) { continue }
            $proc = Get-Process -Id $entry.pid -ErrorAction SilentlyContinue
            # PID-reuse guard: only stop the exact process we started.
            if ($proc -and $proc.StartTime.ToString('o') -eq $entry.started) {
                Stop-Tree $entry.pid
                $stopped++
            }
        }
        Remove-Item -LiteralPath $PidFile -Force
    }
    # Instances started another way: only stop what identifies itself as inkscape-mcp.
    foreach ($pt in @(@{ Port = $BackendPort; Probe = $HealthUrl }, @{ Port = $FrontendPort; Probe = "http://127.0.0.1:$FrontendPort/api/health" })) {
        $owner = Get-Listener $pt.Port
        if (-not $owner -or -not (Test-OurHealth $pt.Probe)) { continue }
        $parentId = (Get-CimInstance Win32_Process -Filter "ProcessId=$($owner.ProcId)").ParentProcessId
        $parent = Get-Process -Id $parentId -ErrorAction SilentlyContinue
        if ($parent -and $parent.ProcessName -eq 'nssm') {
            Say "Port $($pt.Port) is served by an NSSM service - stop it with sc.exe stop <service>, not here." 'Yellow'
            continue
        }
        Stop-Tree $owner.ProcId
        $stopped++
    }
    Say "Stopped $stopped process tree(s)." 'Green'
}

# ---------------------------------------------------------------- install

function Require-Command([string]$Cmd, [string]$WingetId, [string]$Label) {
    if (Find-Exe $Cmd) { return }
    Say "$Label not found - installing via winget ($WingetId) ..." 'Yellow'
    if (-not (Find-Exe 'winget')) {
        Say "ERROR: winget unavailable. Install $Label manually (winget id $WingetId), then rerun start.bat." 'Red'
        exit 1
    }
    & winget install --id $WingetId --exact --source winget --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
    Update-SessionPath
    if ($Cmd -eq 'bun' -and -not (Find-Exe 'bun')) { $env:PATH += ";$env:USERPROFILE\.bun\bin" }
    if (-not (Find-Exe $Cmd)) {
        Say "Installed $Label but '$Cmd' is not on PATH yet. Open a new terminal and rerun start.bat (safe)." 'Yellow'
        exit 1
    }
}

function Invoke-Install {
    Require-Command 'uv' 'astral-sh.uv' 'uv'
    if (-not $BackendOnly) { Require-Command 'bun' 'Oven-sh.Bun' 'bun' }

    if (-not (Find-Inkscape)) {
        $doInstall = $false
        if (-not $Yes) {
            $answer = Read-Host 'Inkscape is not installed. Export/convert/trace need it. Install Inkscape now via winget? [Y/n]'
            $doInstall = ($answer -eq '' -or $answer -match '^[Yy]')
        }
        if ($doInstall) {
            & winget install --id Inkscape.Inkscape --exact --source winget --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
        } else {
            Say 'Skipping Inkscape. Install later: winget install --id Inkscape.Inkscape --source winget' 'Yellow'
        }
    }

    $uvExe = Find-Exe 'uv'
    if (-not (Test-PythonInstalled)) {
        Say 'Installing Python dependencies (uv sync). First time: 1-3 minutes, the window may sit quiet. This is normal.' 'Cyan'
    }
    & $uvExe sync --project $RepoRoot
    if ($LASTEXITCODE -ne 0) {
        Say 'ERROR: uv sync failed (see output above). Rerunning start.bat is safe.' 'Red'
        exit 1
    }

    if (-not $BackendOnly -and -not (Test-WebInstalled)) {
        Say 'Installing dashboard dependencies (bun install). About 1 minute. This is normal.' 'Cyan'
        $bunExe = Find-Exe 'bun'
        Push-Location $WebRoot
        try { & $bunExe install } finally { Pop-Location }
        if ($LASTEXITCODE -ne 0 -or -not (Test-WebInstalled)) {
            Say "ERROR: bun install failed. Delete '$WebRoot\node_modules' and rerun start.bat." 'Red'
            exit 1
        }
    }

    & $uvExe run --project $RepoRoot python -c "import inkscape_mcp.main"
    if ($LASTEXITCODE -ne 0) {
        Say 'ERROR: import check failed - see the traceback above. Attach logs\start.log to an issue.' 'Red'
        exit 1
    }
    Say 'Install OK.' 'Green'
}

# ---------------------------------------------------------------- start

function Start-Hidden([string]$Exe, [string[]]$ArgList, [string]$WorkDir, [string]$Log, [hashtable]$EnvVars) {
    # Win32_Process.Create, not Start-Process: Start-Process children inherit the caller's stdout pipe,
    # so an agent running `start.bat -Detach` would block until the servers exit.
    # WMI-created processes get the user's default environment, so env vars are set inside cmd.
    $quoted = ($ArgList | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
    $sets = ($EnvVars.GetEnumerator() | ForEach-Object { "set `"$($_.Key)=$($_.Value)`"" }) -join ' && '
    $cmdLine = "cmd.exe /d /s /c `"$sets && `"$Exe`" $quoted > `"$Log`" 2> `"$Log.err`"`""
    $startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }
    $result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine = $cmdLine; CurrentDirectory = $WorkDir; ProcessStartupInformation = $startup
    }
    if ($result.ReturnValue -ne 0) { throw "Could not start $Exe (Win32_Process.Create returned $($result.ReturnValue))" }
    return Get-Process -Id $result.ProcessId
}

function Wait-Until([scriptblock]$Probe, [int]$Seconds, [System.Diagnostics.Process]$Proc, [string]$What) {
    for ($i = 1; $i -le $Seconds; $i++) {
        if (& $Probe) { return $true }
        if ($Proc.HasExited) { return $false }
        if ($i % 10 -eq 0) { Say "  still waiting for $What ($i s) - first start can take ~30 s ..." 'DarkGray' }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Show-LogTail([string]$Log) {
    foreach ($f in @($Log, "$Log.err")) {
        if (Test-Path -LiteralPath $f) { Get-Content -LiteralPath $f -Tail 15 | ForEach-Object { Say "  | $_" 'DarkGray' } }
    }
}

function Invoke-Start {
    $uvExe = Find-Exe 'uv'
    $backendEnv = @{ MCP_PORT = "$BackendPort"; WEB_PORT = "$BackendPort"; PYTHONUNBUFFERED = '1' }
    if ($env:INKSCAPE_PATH) { $backendEnv.INKSCAPE_PATH = $env:INKSCAPE_PATH }

    Say "Starting backend on 127.0.0.1:$BackendPort ..." 'Cyan'
    $backendArgs = @('run', '--project', $RepoRoot, 'inkscape-mcp', '--mode', 'http', '--host', '127.0.0.1', '--port', "$BackendPort")
    $backend = Start-Hidden $uvExe $backendArgs $RepoRoot $BackendLog $backendEnv
    if (-not (Wait-Until { Test-OurHealth $HealthUrl } 90 $backend 'backend')) {
        Say "ERROR: backend did not become healthy. Last log lines ($BackendLog):" 'Red'
        Show-LogTail $BackendLog
        Stop-Tree $backend.Id
        Say 'Rerunning start.bat is safe. If it fails again, attach logs\backend.log to an issue.' 'Yellow'
        exit 1
    }
    $pidRecord = [ordered]@{ backend = [ordered]@{ pid = $backend.Id; started = $backend.StartTime.ToString('o') } }

    if (-not $BackendOnly) {
        Say "Starting dashboard on 127.0.0.1:$FrontendPort ..." 'Cyan'
        $bunExe = Find-Exe 'bun'
        $frontendArgs = @('--bun', 'run', 'dev', '--port', "$FrontendPort", '--host', '127.0.0.1')
        $frontend = Start-Hidden $bunExe $frontendArgs $WebRoot $FrontendLog @{ BROWSER = 'none' }
        if (-not (Wait-Until { Test-HttpOk $DashboardUrl } 60 $frontend 'dashboard')) {
            Say "ERROR: dashboard did not start. Last log lines ($FrontendLog):" 'Red'
            Show-LogTail $FrontendLog
            Say 'The backend is still running (MCP over HTTP works). Rerunning start.bat is safe.' 'Yellow'
            if (-not $frontend.HasExited) { Stop-Tree $frontend.Id }
            $dashboardUp = $false
        } else {
            $pidRecord.frontend = [ordered]@{ pid = $frontend.Id; started = $frontend.StartTime.ToString('o') }
            $dashboardUp = $true
        }
    } else { $dashboardUp = $false }
    $pidRecord | ConvertTo-Json | Set-Content -LiteralPath $PidFile -Encoding ASCII

    Say ''
    Say '=== inkscape-mcp is running ===' 'Green'
    if ($dashboardUp) { Say "  Dashboard : $DashboardUrl" 'Green' }
    Say "  MCP (HTTP): $McpHttpUrl" 'Green'
    Say "  Health    : $HealthUrl" 'Green'
    Say "  Logs      : $LogDir" 'Gray'
    Say '  Stop      : stop.bat  (or start.bat -Stop)' 'Gray'

    if (-not $NoBrowser -and $dashboardUp) { Start-Process $DashboardUrl }
}

# ---------------------------------------------------------------- main

if ($Check) {
    $report = Invoke-Check
    Show-Report $report
    exit $report.exit_code
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if ($Stop) { Invoke-Stop; exit 0 }

try { Start-Transcript -LiteralPath $StartLog -Force | Out-Null } catch { Say "(could not write $StartLog)" 'DarkGray' }
Say "=== inkscape-mcp $(Get-RepoVersion) ===" 'Cyan'
Say "Log of this run: $StartLog" 'DarkGray'

if ($Restart) { Invoke-Stop }

$report = Invoke-Check
if ($report.running) {
    Say 'inkscape-mcp is already running - nothing to do.' 'Green'
    if (-not $BackendOnly) { Say "  Dashboard : $DashboardUrl" 'Green' }
    Say "  MCP (HTTP): $McpHttpUrl" 'Green'
    Say '  Use start.bat -Restart to restart it (picks up code changes).' 'Gray'
    exit 0
}
if ($report.exit_code -eq 1) {
    Show-Report $report
    Say 'Fix the item above, then rerun start.bat (safe).' 'Yellow'
    exit 1
}

Invoke-Install
if ($NoStart) {
    Say 'Installed. Start it with start.bat (or start.bat -Detach for background).' 'Green'
    exit 0
}

Invoke-Start
if ($Detach) { exit 0 }

Say ''
Say 'Press Ctrl+C to stop. (Closing this window leaves the servers running; stop.bat stops them.)' 'Yellow'
try {
    while ($true) {
        Start-Sleep -Seconds 2
        if (-not (Test-OurHealth $HealthUrl)) {
            Say 'Backend stopped. Last log lines:' 'Red'
            Show-LogTail $BackendLog
            break
        }
    }
} finally {
    Invoke-Stop
}
