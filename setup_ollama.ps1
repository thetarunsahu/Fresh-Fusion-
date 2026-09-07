param(
    [string]$Model = "gemma3:4b"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "FreshFusion Ollama + Gemma Setup" -ForegroundColor Green
Write-Host "--------------------------------" -ForegroundColor DarkGray

$ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "Ollama is not installed." -ForegroundColor Yellow
    Write-Host "Install it in PowerShell with:" -ForegroundColor White
    Write-Host "  irm https://ollama.com/install.ps1 | iex" -ForegroundColor Cyan
    Write-Host "Then close/reopen PowerShell and run this script again." -ForegroundColor White
    exit 1
}

function Test-OllamaApi {
    try {
        $null = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3
        return $true
    } catch {
        return $false
    }
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

Write-Host "[3/4] Ensuring model '$Model' is installed..." -ForegroundColor Cyan
& $ollama.Source pull $Model
if ($LASTEXITCODE -ne 0) {
    throw "Failed to pull model '$Model'."
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
Write-Host "After running start_freshfusion.ps1, open the backend port printed by the launcher:" -ForegroundColor White
Write-Host "  http://localhost:<BACKEND_PORT>/api/v1/ai/ollama/health" -ForegroundColor Cyan
Write-Host ""
