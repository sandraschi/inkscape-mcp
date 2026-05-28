Param(
    [string]$SvgPath = "D:/Temp/inkscape_mcp/diagram.svg",
    [string]$ProjectPath = "D:/Unity/MyProject",
    [string]$StagingDir = "D:/Temp/fleet_pipeline/inkscape_staging",
    [int]$Dpi = 192,
    [switch]$SkipGimp,
    [switch]$SkipUnity,
    [switch]$StageBlender,
    [switch]$ImportToBlender
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$argsList = @(
    "run", "python", "scripts/fleet_pipeline.py",
    "--svg-path", $SvgPath,
    "--project-path", $ProjectPath,
    "--staging-dir", $StagingDir,
    "--dpi", $Dpi
)

if ($SkipGimp) { $argsList += "--skip-gimp" }
if ($SkipUnity) { $argsList += "--skip-unity" }
if ($StageBlender) { $argsList += "--stage-blender" }
if ($ImportToBlender) { $argsList += "--import-to-blender" }

uv @argsList
