param(
    [int]$FrontendPort = 5173,
    [int]$BackendPort = 8000,
    [switch]$LocalOnly
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $Root 'frontend'
$BackendDir = Join-Path $Root 'backend'
$RuntimeDir = Join-Path $Root '.runtime'
$ToolsDir = Join-Path $Root '.tools'
New-Item -ItemType Directory -Force -Path $RuntimeDir, $ToolsDir | Out-Null

$frontendProcess = $null
$backendProcess = $null
$tunnelProcess = $null

function Test-Port([int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $result = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $result.AsyncWaitHandle.WaitOne(450)) { return $false }
        $client.EndConnect($result)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Get-FreePort([int]$PreferredPort, [int]$MaxAttempts = 50) {
    for ($offset = 0; $offset -lt $MaxAttempts; $offset++) {
        $candidate = $PreferredPort + $offset
        if (-not (Test-Port $candidate)) { return $candidate }
    }
    throw "Could not find a free port near $PreferredPort."
}

function Wait-Port([int]$Port, [string]$Name, [int]$TimeoutSeconds = 50) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Port $Port) { return }
        Start-Sleep -Milliseconds 400
    }
    throw "$Name did not start on port $Port within $TimeoutSeconds seconds."
}

function Stop-Tree($Process) {
    if ($null -ne $Process) {
        try {
            if (-not $Process.HasExited) {
                $previous = $ErrorActionPreference
                $ErrorActionPreference = 'Continue'
                & taskkill.exe /PID $Process.Id /T /F 2>$null | Out-Null
                $ErrorActionPreference = $previous
            }
        } catch {}
    }
}

function Get-LanIp {
    try {
        $config = Get-NetIPConfiguration | Where-Object {
            $_.IPv4DefaultGateway -ne $null -and $_.IPv4Address -ne $null
        } | Select-Object -First 1
        if ($config) { return $config.IPv4Address.IPAddress }
    } catch {}
    return 'YOUR_LAPTOP_IP'
}

function Test-PythonDependencies([string]$PythonPath) {
    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $PythonPath -c "import importlib.util,sys; names=['fastapi','sqlalchemy','alembic','httpx']; sys.exit(0 if all(importlib.util.find_spec(x) is not None for x in names) else 1)" 2>$null
        return ($LASTEXITCODE -eq 0)
    } finally {
        $ErrorActionPreference = $previous
    }
}

function Install-BackendDependencies([string]$PythonPath) {
    Write-Host '[setup] Installing/updating backend dependencies...' -ForegroundColor Cyan
    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $PythonPath -m pip install --upgrade pip 2>&1 | Out-Host
        $pipUpgradeExit = $LASTEXITCODE
        if ($pipUpgradeExit -ne 0) { throw 'pip upgrade failed.' }

        & $PythonPath -m pip install -r (Join-Path $BackendDir 'requirements.txt') 2>&1 | Out-Host
        $pipInstallExit = $LASTEXITCODE
        if ($pipInstallExit -ne 0) { throw 'Backend dependency installation failed.' }
    } finally {
        $ErrorActionPreference = $previous
    }
}

function Ensure-PythonEnvironment {
    $venvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
    $created = $false

    if (-not (Test-Path $venvPython)) {
        Write-Host '[setup] Creating Python virtual environment...' -ForegroundColor Cyan
        $py = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($py) {
            & $py.Source -3 -m venv (Join-Path $BackendDir '.venv') | Out-Host
        } else {
            $python = Get-Command python.exe -ErrorAction SilentlyContinue
            if (-not $python) { throw 'Python 3 was not found. Install Python and run this script again.' }
            & $python.Source -m venv (Join-Path $BackendDir '.venv') | Out-Host
        }
        $created = $true
    }

    if ($created -or -not (Test-PythonDependencies $venvPython)) {
        Install-BackendDependencies $venvPython
    } else {
        Write-Host '[setup] Backend dependencies already available.' -ForegroundColor DarkGreen
    }

    if (-not (Test-PythonDependencies $venvPython)) {
        throw 'Backend dependencies are still incomplete after installation.'
    }

    return [string]$venvPython
}

function Invoke-DatabaseMigration([string]$PythonPath) {
    $config = Join-Path $BackendDir 'alembic.ini'
    if (-not (Test-Path $config)) {
        Write-Host '[db] Alembic config not found; backend metadata fallback will be used.' -ForegroundColor Yellow
        return
    }

    Write-Host '[db] Applying database migrations...' -ForegroundColor Cyan
    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        Push-Location $BackendDir
        try {
            $migrationOutput = (& $PythonPath -m alembic -c 'alembic.ini' upgrade head 2>&1 | Out-String)
            $migrationExit = $LASTEXITCODE
        } finally {
            Pop-Location
        }
    } finally {
        $ErrorActionPreference = $previous
    }

    if ($migrationExit -ne 0) {
        if ($migrationOutput) { Write-Host $migrationOutput -ForegroundColor Red }
        throw 'Database migration failed. Back up freshfusion.db and inspect the Alembic error above before continuing.'
    }
    Write-Host '[db] Database schema is current.' -ForegroundColor DarkGreen
}

function Ensure-FrontendEnvironment {
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npm) { throw 'Node.js/npm was not found. Install Node.js LTS and run this script again.' }
    if (-not (Test-Path (Join-Path $FrontendDir 'node_modules'))) {
        Write-Host '[setup] Installing frontend packages...' -ForegroundColor Cyan
        Push-Location $FrontendDir
        try {
            $previous = $ErrorActionPreference
            $ErrorActionPreference = 'Continue'
            & npm.cmd install | Out-Host
            $npmExit = $LASTEXITCODE
            $ErrorActionPreference = $previous
            if ($npmExit -ne 0) { throw 'Frontend dependency installation failed.' }
        } finally { Pop-Location }
    }
}

function Get-OllamaTags {
    try {
        return Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3
    } catch {
        return $null
    }
}

function Ensure-OllamaRuntime {
    $model = if ($env:FRESHFUSION_OLLAMA_MODEL) { $env:FRESHFUSION_OLLAMA_MODEL } else { 'gemma3:4b' }
    $tags = Get-OllamaTags

    if ($null -eq $tags) {
        $ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
        if (-not $ollama) {
            Write-Host '[ai] Ollama is not installed. Core FreshFusion will continue without the AI Copilot.' -ForegroundColor Yellow
            return $false
        }

        Write-Host '[ai] Starting installed Ollama runtime...' -ForegroundColor Cyan
        try {
            Start-Process -FilePath $ollama.Source -ArgumentList @('serve') -WindowStyle Hidden | Out-Null
        } catch {
            Write-Host "[ai] Could not start Ollama: $($_.Exception.Message)" -ForegroundColor Yellow
            return $false
        }

        $deadline = (Get-Date).AddSeconds(15)
        while ((Get-Date) -lt $deadline -and $null -eq $tags) {
            Start-Sleep -Milliseconds 500
            $tags = Get-OllamaTags
        }
    }

    if ($null -eq $tags) {
        Write-Host '[ai] Ollama API is unavailable. Core verdict remains available; AI Copilot will stay disabled.' -ForegroundColor Yellow
        return $false
    }

    $installed = $false
    foreach ($item in @($tags.models)) {
        if ($item.name -eq $model -or $item.model -eq $model) {
            $installed = $true
            break
        }
    }

    if (-not $installed) {
        Write-Host "[ai] Ollama is online, but '$model' is missing. Run .\setup_ollama.ps1 once; the launcher will never re-download it automatically." -ForegroundColor Yellow
        return $false
    }

    Write-Host "[ai] Ollama + $model ready. Existing local model reused; no download required." -ForegroundColor DarkGreen
    return $true
}

function Ensure-Cloudflared {
    $exe = Join-Path $ToolsDir 'cloudflared.exe'
    if (Test-Path $exe) { return $exe }

    Write-Host '[setup] Downloading Cloudflare Tunnel (official binary)...' -ForegroundColor Cyan
    $url = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curl) {
        $previous = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        & $curl.Source -L --fail --silent --show-error $url -o $exe | Out-Host
        $curlExit = $LASTEXITCODE
        $ErrorActionPreference = $previous
        if ($curlExit -ne 0) { throw 'cloudflared download failed with curl.' }
    } else {
        Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $exe
    }
    if (-not (Test-Path $exe)) { throw 'cloudflared download failed.' }
    return $exe
}

try {
    Write-Host ''
    Write-Host 'FreshFusion Phone + ESP32 Launcher' -ForegroundColor Green
    Write-Host '---------------------------------' -ForegroundColor DarkGray

    $requestedFrontendPort = $FrontendPort
    $requestedBackendPort = $BackendPort
    $FrontendPort = Get-FreePort $FrontendPort
    $BackendPort = Get-FreePort $BackendPort

    if ($FrontendPort -ne $requestedFrontendPort) {
        Write-Host "[ports] $requestedFrontendPort is busy; dashboard will use $FrontendPort instead." -ForegroundColor Yellow
    }
    if ($BackendPort -ne $requestedBackendPort) {
        Write-Host "[ports] $requestedBackendPort is busy; backend will use $BackendPort instead." -ForegroundColor Yellow
    }

    $env:FRESHFUSION_FRONTEND_PORT = "$FrontendPort"
    $env:FRESHFUSION_BACKEND_PORT = "$BackendPort"

    $venvPython = Ensure-PythonEnvironment
    Invoke-DatabaseMigration $venvPython
    Ensure-FrontendEnvironment
    $aiReady = Ensure-OllamaRuntime

    $frontendOut = Join-Path $RuntimeDir 'frontend.out.log'
    $frontendErr = Join-Path $RuntimeDir 'frontend.err.log'
    Remove-Item $frontendOut, $frontendErr -Force -ErrorAction SilentlyContinue

    Write-Host "[1/3] Starting dashboard on port $FrontendPort..." -ForegroundColor Cyan
    $frontendParams = @{
        FilePath = 'cmd.exe'
        ArgumentList = @('/c', 'npm run dev')
        WorkingDirectory = $FrontendDir
        PassThru = $true
        RedirectStandardOutput = $frontendOut
        RedirectStandardError = $frontendErr
    }
    $frontendProcess = Start-Process @frontendParams
    Wait-Port $FrontendPort 'Frontend'

    $tunnelUrl = $null
    $phoneUrl = $null

    if (-not $LocalOnly) {
        try {
            $cloudflared = Ensure-Cloudflared
            $tunnelOut = Join-Path $RuntimeDir 'tunnel.out.log'
            $tunnelErr = Join-Path $RuntimeDir 'tunnel.err.log'
            Remove-Item $tunnelOut, $tunnelErr -Force -ErrorAction SilentlyContinue

            Write-Host '[2/3] Creating trusted HTTPS phone link...' -ForegroundColor Cyan
            $tunnelParams = @{
                FilePath = $cloudflared
                ArgumentList = @('tunnel', '--url', "http://127.0.0.1:$FrontendPort", '--no-autoupdate')
                PassThru = $true
                RedirectStandardOutput = $tunnelOut
                RedirectStandardError = $tunnelErr
            }
            $tunnelProcess = Start-Process @tunnelParams

            $deadline = (Get-Date).AddSeconds(45)
            while ((Get-Date) -lt $deadline -and -not $tunnelUrl) {
                if ($tunnelProcess.HasExited) { break }
                $text = ''
                if (Test-Path $tunnelOut) { $text += (Get-Content $tunnelOut -Raw -ErrorAction SilentlyContinue) }
                if (Test-Path $tunnelErr) { $text += "`n" + (Get-Content $tunnelErr -Raw -ErrorAction SilentlyContinue) }
                if ($text -match 'https://[a-zA-Z0-9-]+\.trycloudflare\.com') {
                    $tunnelUrl = $Matches[0]
                    break
                }
                Start-Sleep -Milliseconds 500
            }

            if ($tunnelUrl) {
                $phoneUrl = "$tunnelUrl/phone.html"
                $env:PHONE_DASHBOARD_URL = $phoneUrl
            } else {
                Write-Host '[2/3] Phone tunnel unavailable; continuing in local-only recovery mode.' -ForegroundColor Yellow
                Stop-Tree $tunnelProcess
                $tunnelProcess = $null
                Remove-Item Env:PHONE_DASHBOARD_URL -ErrorAction SilentlyContinue
            }
        } catch {
            Write-Host "[2/3] Phone tunnel failed: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host '      Continuing with laptop dashboard + backend. Phone camera may be unavailable.' -ForegroundColor Yellow
            Stop-Tree $tunnelProcess
            $tunnelProcess = $null
            Remove-Item Env:PHONE_DASHBOARD_URL -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host '[2/3] Local-only mode selected; skipping phone tunnel.' -ForegroundColor Yellow
        Remove-Item Env:PHONE_DASHBOARD_URL -ErrorAction SilentlyContinue
    }

    $backendOut = Join-Path $RuntimeDir 'backend.out.log'
    $backendErr = Join-Path $RuntimeDir 'backend.err.log'
    Remove-Item $backendOut, $backendErr -Force -ErrorAction SilentlyContinue

    Write-Host "[3/3] Starting FastAPI backend on port $BackendPort..." -ForegroundColor Cyan
    $backendParams = @{
        FilePath = $venvPython
        ArgumentList = @('-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', "$BackendPort")
        WorkingDirectory = $BackendDir
        PassThru = $true
        RedirectStandardOutput = $backendOut
        RedirectStandardError = $backendErr
    }
    $backendProcess = Start-Process @backendParams
    Wait-Port $BackendPort 'Backend'

    $lanIp = Get-LanIp
    $esp32Url = "http://${lanIp}:$BackendPort/api/v1/sensors/readings"

    Write-Host ''
    Write-Host 'READY' -ForegroundColor Green
    Write-Host "Laptop dashboard : http://localhost:$FrontendPort" -ForegroundColor White
    if ($phoneUrl) {
        Write-Host "Phone camera     : $phoneUrl" -ForegroundColor Yellow
    } else {
        Write-Host 'Phone camera     : unavailable in local-only recovery mode' -ForegroundColor Yellow
    }
    Write-Host "Backend health   : http://localhost:$BackendPort/api/v1/health" -ForegroundColor White
    Write-Host "Ollama health    : http://localhost:$BackendPort/api/v1/ai/ollama/health" -ForegroundColor White
    Write-Host "AI Copilot       : $(if ($aiReady) { 'Gemma ready' } else { 'optional / unavailable' })" -ForegroundColor $(if ($aiReady) { 'Green' } else { 'Yellow' })
    Write-Host "ESP32 API        : $esp32Url" -ForegroundColor White
    Write-Host ''
    Write-Host 'FreshFusion automatically moved away from any busy ports.' -ForegroundColor Green
    if ($phoneUrl) {
        Write-Host 'Phone does NOT need to be on the same Wi-Fi when using the HTTPS tunnel.' -ForegroundColor Green
        Write-Host 'Open the laptop dashboard and scan its QR code.' -ForegroundColor White
        Write-Host 'On the phone, allow Camera once. If auto-start is blocked, tap Start camera.' -ForegroundColor White
    }
    Write-Host 'Keep this PowerShell window open while FreshFusion is running.' -ForegroundColor DarkYellow
    Write-Host ''

    Start-Process "http://localhost:$FrontendPort"

    $tunnelWarned = $false
    while ($true) {
        if ($frontendProcess.HasExited) { throw 'Frontend stopped unexpectedly. Check .runtime/frontend.err.log' }
        if ($backendProcess.HasExited) { throw 'Backend stopped unexpectedly. Check .runtime/backend.err.log' }
        if ($null -ne $tunnelProcess -and $tunnelProcess.HasExited -and -not $tunnelWarned) {
            Write-Host 'Phone tunnel stopped. Dashboard/backend remain online; use local-only recovery mode.' -ForegroundColor Yellow
            $tunnelWarned = $true
            $tunnelProcess = $null
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    Write-Host ''
    Write-Host 'Stopping FreshFusion services...' -ForegroundColor DarkGray
    Stop-Tree $backendProcess
    Stop-Tree $tunnelProcess
    Stop-Tree $frontendProcess
}
