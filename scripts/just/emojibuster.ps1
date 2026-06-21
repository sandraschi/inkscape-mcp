param([string]$Path = ".")
$ErrorActionPreference = "Stop"
$pyFiles = Get-ChildItem -Recurse -Filter "*.py" -Path $Path -ErrorAction SilentlyContinue
$found = 0
foreach ($f in $pyFiles) {
    $content = Get-Content $f -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    $lines = $content -split "`n"
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '[^\x00-\x7F]' -and ($line -match 'logger\.' -or $line -match '\bprint\(')) {
            Write-Host "  $($f.FullName):$($i+1) $($line.Trim())" -ForegroundColor Yellow
            $found++
        }
    }
}
if ($found -eq 0) { Write-Host "  No Unicode issues found." -ForegroundColor Green }
else { Write-Host "  $found issue(s) found." -ForegroundColor Red }
