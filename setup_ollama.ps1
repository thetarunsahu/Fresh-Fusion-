param(
    [string]$Model = "gemma3:4b",
    [switch]$ForcePull
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "FreshFusion Ollama + Gemma Setup" -ForegroundColor Green
Write-Host "--------------------------------" -ForegroundColor DarkGray

$ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "Ollama is not installed." -ForegroundColor Yellow
    Write-Host "Install it once in PowerShell with:" -ForegroundColor White
    Write-Host "  irm https://ollama.com/install.ps1 | iex" -ForegroundColor Cyan
    Write-Host "Then close/reopen PowerShell and run this script again." -ForegroundColor White
    exit 1
}

function Get-OllamaTags {
    try {
        return Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3
    } catch {
        return $null
    }
}

function Test-OllamaApi {
    return $null -ne (Get-OllamaTags)
}

function Test-ModelInstalled([string]$ModelName) {
    $tags = Get-OllamaTags
    if ($null -eq $tags -or $null -eq $tags.models) { return $false }

    foreach ($item in $tags.models) {
        if ($item.name -eq $ModelName -or $item.model -eq $ModelName) {
            return $true
        }
    }
    return $false
}

if (-not (Test-OllamaApi)) {
    Write-Host "[1/4] Starting Ollama service..." -ForegroundColor Cyan
    Start-Process -FilePath $ollama.Source -ArgumentList @("serve") -WindowStyle Hidden | Out-Null
    $deadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline -and -not (Test-OllamaApi)) {
        Start-Sleep -Milliseconds 500
    }
}

if (-not (Test-OllamaApi)) {
    throw "Ollama API did not start on http://127.0.0.1:11434"
}

Write-Host "[2/4] Ollama API is online." -ForegroundColor Green

if ((Test-ModelInstalled $Model) -and -not $ForcePull) {
    Write-Host "[3/4] Model '$Model' is already installed. Skipping download." -ForegroundColor Green
} else {
    if ($ForcePull) {
        Write-Host "[3/4] Force-pulling model '$Model'..." -ForegroundColor Cyan
    } else {
        Write-Host "[3/4] Model '$Model' is missing. Downloading it once..." -ForegroundColor Cyan
    }
    & $ollama.Source pull $Model
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to pull model '$Model'."
    }
}

Write-Host "[4/4] Testing Gemma through Ollama HTTP API..." -ForegroundColor Cyan
$body = @{
    model = $Model
    prompt = "Return exactly this text: FRESHFUSION_GEMMA_READY"
    stream = $false
    options = @{ temperature = 0.1 }
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:11434/api/generate" `
    -ContentType "application/json" `
    -Body $body `
    -TimeoutSec 120

Write-Host ""
Write-Host "READY" -ForegroundColor Green
Write-Host "Ollama URL : http://127.0.0.1:11434" -ForegroundColor White
Write-Host "Model      : $Model" -ForegroundColor White
Write-Host "Gemma test : $($response.response)" -ForegroundColor White
Write-Host ""
Write-Host "FreshFusion backend already defaults to this Ollama URL and model." -ForegroundColor Green
Write-Host "Normal use: run start_freshfusion.ps1. You do NOT need to run setup_ollama.ps1 every time." -ForegroundColor Green
Write-Host "Run setup_ollama.ps1 again only to verify setup or install a missing model." -ForegroundColor White
Write-Host "Use -ForcePull only when you intentionally want to refresh the model." -ForegroundColor DarkGray
Write-Host "After running start_freshfusion.ps1, open the backend port printed by the launcher:" -ForegroundColor White
Write-Host "  http://localhost:<BACKEND_PORT>/api/v1/ai/ollama/health" -ForegroundColor Cyan
Write-Host ""
