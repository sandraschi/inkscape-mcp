param([string]$RepoRoot)
Set-Location $RepoRoot
New-Item -ItemType Directory -Force -Path dist | Out-Null
$proj = Get-Content pyproject.toml -Raw
$name = if ($proj -match '(?m)^name = "(.*)"') { $matches[1] } else { Split-Path -Leaf $PWD }
$ver = if ($proj -match '(?m)^version = "(.*)"') { $matches[1] } else { "0.1.0" }
if (-not (Test-Path manifest.json)) {
    $desc = if ($proj -match '(?m)^description = "(.*)"') { $matches[1] } else { "MCP server: $name" }
    $pkg = $name -replace '-', '_'
    $entry = if (Test-Path run_server.py) { "run_server.py" } `
        elseif (Test-Path "src/$pkg/main.py") { "src/$pkg/main.py" } `
        elseif (Test-Path "src/$pkg/server.py") { "src/$pkg/server.py" } `
        else { "src/$pkg/main.py" }
    $author = if ($proj -match '(?m)authors = \[{ name = "(.*)"') { $matches[1] } else { "sandraschi" }
    $args = if ($entry -eq "run_server.py") { '["run","--directory","${PWD}","run_server.py"]' } `
        else { '["run","--directory","${PWD}","python","-m","' + $pkg + '"]' }
    $json = '{"manifest_version":"0.2","name":"' + $name + '","version":"' + $ver + '","description":"' + $desc + '","author":{"name":"' + $author + '"},"server":{"type":"python","entry_point":"' + $entry + '","mcp_config":{"command":"uv","args":' + $args + ',"env":{"PYTHONPATH":"${PWD}/src","PYTHONUNBUFFERED":"1"}}}}'
    $json | Set-Content manifest.json -Encoding utf8
    Write-Host "  Generated manifest.json" -ForegroundColor Yellow
}
if (-not (Test-Path .mcpbignore)) {
    $lines = "tests/",".git/","__pycache__/","*.pyc",".venv/","dist/","build/","target/"
    $lines += "web_sota/node_modules/","web_sota/dist/","node_modules/"
    $lines += ".ruff_cache/",".pytest_cache/",".coverage",".snapshots/","*.bak"
    $lines | Set-Content .mcpbignore -Encoding utf8
    Write-Host "  Generated .mcpbignore" -ForegroundColor Yellow
}
npx --yes @anthropic-ai/mcpb pack $RepoRoot "$RepoRoot/dist/$name-v$ver.mcpb"
Write-Host "Bundle: $RepoRoot/dist/$name-v$ver.mcpb"
