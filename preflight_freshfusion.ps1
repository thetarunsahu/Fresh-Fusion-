$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Check($Label, $Ok, $Detail) {
    $mark = if ($Ok) { '[PASS]' } else { '[CHECK]' }
    $color = if ($Ok) { 'Green' } else { 'Yellow' }
    Write-Host ("{0,-8} {1,-28} {2}" -f $mark, $Label, $Detail) -ForegroundColor $color
}

Write-Host ''
Write-Host 'FreshFusion Preflight' -ForegroundColor Cyan
Write-Host '---------------------' -ForegroundColor DarkGray

$git = Get-Command git.exe -ErrorAction SilentlyContinue
Check 'Git' ($null -ne $git) $(if ($git) { (& git --version) } else { 'not found' })

$node = Get-Command node.exe -ErrorAction SilentlyContinue
Check 'Node.js' ($null -ne $node) $(if ($node) { (& node --version) } else { 'not found' })

$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
Check 'npm' ($null -ne $npm) $(if ($npm) { (& npm.cmd --version) } else { 'not found' })

$venvPython = Join-Path $Root 'backend\.venv\Scripts\python.exe'
Check 'Backend venv' (Test-Path $venvPython) $venvPython

if (Test-Path $venvPython) {
    & $venvPython -c "import fastapi, sqlalchemy, httpx" 2>$null
    Check 'Backend imports' ($LASTEXITCODE -eq 0) 'FastAPI / SQLAlchemy / httpx'
    & $venvPython -c "import alembic" 2>$null
    Check 'Alembic' ($LASTEXITCODE -eq 0) 'migration dependency'
}

Check 'Frontend packages' (Test-Path (Join-Path $Root 'frontend\node_modules')) 'frontend/node_modules'

$db = Join-Path $Root 'freshfusion.db'
Check 'Primary database' (Test-Path $db) $(if (Test-Path $db) { $db } else { 'will be created on first run' })

$reference = Join-Path $Root 'models\public_reference_index.json'
Check 'Reference index' (Test-Path $reference) $(if (Test-Path $reference) { 'available' } else { 'optional: run setup_reference_data.ps1' })

$ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
Check 'Ollama' ($null -ne $ollama) $(if ($ollama) { (& ollama --version) } else { 'not found; core verdict still works' })

if ($ollama) {
    $modelText = (& ollama list 2>$null | Out-String)
    $hasGemma = $modelText -match 'gemma3:4b'
    Check 'Gemma3 4B' $hasGemma $(if ($hasGemma) { 'installed locally' } else { 'optional explanation model missing' })
    try {
        $tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -Method Get -TimeoutSec 3
        Check 'Ollama API' $true 'http://127.0.0.1:11434'
    } catch {
        Check 'Ollama API' $false 'service not responding; setup_ollama.ps1 can start it'
    }
}

Write-Host ''
Write-Host 'Interpretation:' -ForegroundColor White
Write-Host '- [PASS] means the local prerequisite was found.' -ForegroundColor DarkGray
Write-Host '- [CHECK] is not always fatal; reference data and Gemma are optional for the deterministic verdict.' -ForegroundColor DarkGray
Write-Host '- Run .\start_freshfusion.ps1 after preflight. Use -LocalOnly if the phone tunnel is unavailable.' -ForegroundColor DarkGray
Write-Host ''
