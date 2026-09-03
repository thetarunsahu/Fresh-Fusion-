param(
    [int]$FrontendPort = 5173,
    [int]$BackendPort = 8000
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
                & taskkill.exe /PID $Process.Id /T /F 2>$null | Out-Null
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

function Ensure-PythonEnvironment {
    $venvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
    if (Test-Path $venvPython) { return $venvPython }

    Write-Host '[setup] Creating Python virtual environment...' -ForegroundColor Cyan
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3 -m venv (Join-Path $BackendDir '.venv')
    } else {
        $python = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $python) { throw 'Python 3 was not found. Install Python and run this script again.' }
        & $python.Source -m venv (Join-Path $BackendDir '.venv')
    }

    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r (Join-Path $BackendDir 'requirements.txt')
    return $venvPython
}

function Ensure-FrontendEnvironment {
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npm) { throw 'Node.js/npm was not found. Install Node.js LTS and run this script again.' }
    if (-not (Test-Path (Join-Path $FrontendDir 'node_modules'))) {
        Write-Host '[setup] Installing frontend packages...' -ForegroundColor Cyan
        Push-Location $FrontendDir
        try { & npm.cmd install } finally { Pop-Location }
    }
}

function Ensure-Cloudflared {
    $exe = Join-Path $ToolsDir 'cloudflared.exe'
    if (Test-Path $exe) { return $exe }

    Write-Host '[setup] Downloading Cloudflare Tunnel (official binary)...' -ForegroundColor Cyan
    $url = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curl) {
        & $curl.Source -L --fail --silent --show-error $url -o $exe
        if ($LASTEXITCODE -ne 0) { throw 'cloudflared download failed with curl.' }
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
    Ensure-FrontendEnvironment
    $cloudflared = Ensure-Cloudflared

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

    $tunnelUrl = $null
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

    if (-not $tunnelUrl) {
        $details = ''
        if (Test-Path $tunnelErr) { $details = Get-Content $tunnelErr -Raw -ErrorAction SilentlyContinue }
        throw "Could not create the trusted phone link. Tunnel output:`n$details"
    }

    $phoneUrl = "$tunnelUrl/phone.html"
    $env:PHONE_DASHBOARD_URL = $phoneUrl

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
    Write-Host "Phone camera     : $phoneUrl" -ForegroundColor Yellow
    Write-Host "ESP32 API        : $esp32Url" -ForegroundColor White
    Write-Host ''
    Write-Host 'FreshFusion automatically moved away from any busy ports.' -ForegroundColor Green
    Write-Host 'Phone does NOT need to be on the same Wi-Fi.' -ForegroundColor Green
    Write-Host 'Open the laptop dashboard and scan its QR code.' -ForegroundColor White
    Write-Host 'On the phone, allow Camera once. If auto-start is blocked, tap Start camera.' -ForegroundColor White
    Write-Host 'Keep this PowerShell window open while FreshFusion is running.' -ForegroundColor DarkYellow
    Write-Host ''

    Start-Process "http://localhost:$FrontendPort"

    while ($true) {
        if ($frontendProcess.HasExited) { throw 'Frontend stopped unexpectedly. Check .runtime/frontend.err.log' }
        if ($backendProcess.HasExited) { throw 'Backend stopped unexpectedly. Check .runtime/backend.err.log' }
        if ($tunnelProcess.HasExited) { throw 'Phone tunnel stopped unexpectedly. Check .runtime/tunnel.err.log' }
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
