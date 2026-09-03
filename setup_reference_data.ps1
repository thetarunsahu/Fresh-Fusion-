param(
    [int]$MaxPerClass = 180,
    [switch]$Refresh
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root 'backend\.venv\Scripts\python.exe'
$Script = Join-Path $Root 'ai\sync_public_reference.py'

if (-not (Test-Path $Python)) {
    throw 'FreshFusion backend virtual environment was not found. Run .\start_freshfusion.ps1 once first.'
}
if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
    throw 'Git was not found on PATH. Install Git for Windows and run again.'
}

Write-Host ''
Write-Host 'FreshFusion Public Reference Setup' -ForegroundColor Green
Write-Host '----------------------------------' -ForegroundColor DarkGray
Write-Host 'Source: zijianchen98/Fruit-freshness-detection-dataset (Apache-2.0)' -ForegroundColor White
Write-Host "Maximum reference images per published class: $MaxPerClass" -ForegroundColor White
Write-Host ''

$argsList = @($Script, '--max-per-class', "$MaxPerClass")
if ($Refresh) { $argsList += '--refresh' }
& $Python @argsList
if ($LASTEXITCODE -ne 0) { throw "Reference setup failed with exit code $LASTEXITCODE" }

Write-Host ''
Write-Host 'DONE' -ForegroundColor Green
Write-Host 'Restart FreshFusion so the dashboard can show the new runtime reference index.' -ForegroundColor White
