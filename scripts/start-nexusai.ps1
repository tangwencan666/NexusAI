[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot 'backend'
$FrontendDir = Join-Path $ProjectRoot 'frontend'
$PythonExe = Join-Path $BackendDir '.venv\Scripts\python.exe'
$DockerDesktop = 'D:\Docker\DockerDesktop\Docker Desktop.exe'
$PreferredDockerCli = 'D:\Docker\DockerDesktop\resources\bin\docker.exe'
$WorkDir = Join-Path $ProjectRoot 'work'
$LogDir = Join-Path $ProjectRoot 'logs'
$BackendPidFile = Join-Path $WorkDir 'backend.pid'
$FrontendPidFile = Join-Path $WorkDir 'frontend.pid'

function Get-DockerCli {
    if (Test-Path -LiteralPath $PreferredDockerCli) { return $PreferredDockerCli }
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw 'Docker CLI was not found.'
}

function Test-PortListening([int]$Port) {
    return $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
}

function Get-ListeningPid([int]$Port) {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($connection) { return [int]$connection.OwningProcess }
    return $null
}

function Get-SavedPid([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $value = (Get-Content -LiteralPath $Path -Raw).Trim()
    $parsed = 0
    if ([int]::TryParse($value, [ref]$parsed)) { return $parsed }
    return $null
}

function Test-ManagedProcess([int]$ProcessId, [ValidateSet('backend','frontend')] [string]$Kind) {
    if (-not (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) { return $false }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if (-not $process) { return $false }
    $commandLine = [string]$process.CommandLine
    if ($Kind -eq 'backend') {
        return $process.ExecutablePath -eq $PythonExe -and $commandLine -match 'uvicorn' -and $commandLine -match 'app\.main:app'
    }
    return $commandLine -match '(npm|vite)' -and $commandLine -match 'run\s+dev' -and $commandLine -match '--port\s+5173' -and $commandLine -match '--strictPort'
}

function Wait-Until([scriptblock]$Condition, [int]$TimeoutSeconds, [string]$Description) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        if (& $Condition) { return }
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $deadline)
    throw "Timed out waiting for $Description after $TimeoutSeconds seconds."
}

function Test-BackendHealth {
    try {
        $response = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 3
        if ($response.status -notin @('ok', 'healthy')) { return $false }
        $openApi = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/openapi.json' -TimeoutSec 3
        return $openApi.info.title -eq 'NexusAI'
    } catch { return $false }
}

function Test-FrontendHealth {
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:5173/' -TimeoutSec 3 -UseBasicParsing
        return $response.StatusCode -eq 200
    } catch { return $false }
}

function Write-FrontendDiagnostics([int]$ProcessId) {
    $processExists = $ProcessId -gt 0 -and $null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)
    $portListening = Test-PortListening 5173
    Write-Host "Frontend PID: $ProcessId (running: $processExists)"
    Write-Host "Port 5173 listening: $portListening"
    foreach ($logName in @('frontend.log', 'frontend.error.log')) {
        $logPath = Join-Path $LogDir $logName
        Write-Host "--- $logName (last 40 lines) ---"
        if (Test-Path -LiteralPath $logPath) {
            Get-Content -LiteralPath $logPath -Tail 40 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
        } else {
            Write-Host '(log file not found)'
        }
    }
}

function Wait-FrontendReady([int]$ProcessId, [int]$TimeoutSeconds = 60) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        if (Test-FrontendHealth) { return }
        if ($ProcessId -gt 0 -and -not (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) {
            Remove-Item -LiteralPath $FrontendPidFile -Force -ErrorAction SilentlyContinue
            Write-FrontendDiagnostics -ProcessId $ProcessId
            throw "Frontend process $ProcessId exited before HTTP readiness."
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    Write-FrontendDiagnostics -ProcessId $ProcessId
    throw "Timed out waiting for Vite frontend after $TimeoutSeconds seconds."
}

function Assert-PortAvailableOrManaged([int]$Port, [string]$PidFile, [ValidateSet('backend','frontend')] [string]$Kind) {
    if (-not (Test-PortListening $Port)) { return $false }
    $listenerPid = Get-ListeningPid $Port
    $savedPid = Get-SavedPid $PidFile
    $managed = ($savedPid -and (Test-ManagedProcess $savedPid $Kind))
    $healthyNexus = if ($Kind -eq 'backend') { Test-BackendHealth } else { Test-FrontendHealth }
    if ($managed -or $healthyNexus) {
        Write-Host "$Kind is already running on port $Port."
        return $true
    }
    throw "Port $Port already in use by PID $listenerPid and is not a verified NexusAI $Kind process."
}

function Get-ContainerHealth([string]$Service) {
    $containerId = (& $script:DockerCli compose --project-directory $ProjectRoot ps -q $Service 2>$null | Select-Object -First 1)
    if (-not $containerId) { return 'missing' }
    $state = (& $script:DockerCli inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $containerId 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $state) { return 'unknown' }
    return ([string]$state).Trim()
}

try {
    foreach ($required in @($ProjectRoot, $BackendDir, $FrontendDir, $PythonExe, (Join-Path $FrontendDir 'package.json'), (Join-Path $ProjectRoot 'docker-compose.yml'))) {
        if (-not (Test-Path -LiteralPath $required)) { throw "Required path not found: $required" }
    }
    New-Item -ItemType Directory -Path $WorkDir, $LogDir -Force | Out-Null
    $script:DockerCli = Get-DockerCli

    & $DockerCli info *> $null
    if ($LASTEXITCODE -ne 0) {
        if (-not (Test-Path -LiteralPath $DockerDesktop)) { throw "Docker Desktop not found: $DockerDesktop" }
        Write-Host 'Docker Engine is not ready. Starting Docker Desktop...'
        Start-Process -FilePath $DockerDesktop | Out-Null
        Wait-Until -TimeoutSeconds 120 -Description 'Docker Engine' -Condition {
            & $script:DockerCli info *> $null
            return $LASTEXITCODE -eq 0
        }
    }
    Write-Host 'Docker Engine is ready.'

    Write-Host 'Starting PostgreSQL/pgvector and Redis...'
    & $DockerCli compose --project-directory $ProjectRoot up -d
    if ($LASTEXITCODE -ne 0) { throw "docker compose up -d failed with exit code $LASTEXITCODE." }
    Wait-Until -TimeoutSeconds 120 -Description 'PostgreSQL and Redis health checks' -Condition {
        return (Get-ContainerHealth 'postgres') -eq 'healthy' -and (Get-ContainerHealth 'redis') -eq 'healthy'
    }
    Write-Host 'PostgreSQL and Redis are healthy.'

    Write-Host 'Applying Alembic migrations...'
    Push-Location $BackendDir
    try { & $PythonExe -m alembic upgrade head } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw "Alembic migration failed with exit code $LASTEXITCODE." }

    $backendAlreadyRunning = Assert-PortAvailableOrManaged -Port 8000 -PidFile $BackendPidFile -Kind backend
    if (-not $backendAlreadyRunning) {
        Write-Host 'Starting FastAPI backend...'
        $backendProcess = Start-Process -FilePath $PythonExe -ArgumentList @('-m','uvicorn','app.main:app','--reload','--host','127.0.0.1','--port','8000') -WorkingDirectory $BackendDir -RedirectStandardOutput (Join-Path $LogDir 'backend.log') -RedirectStandardError (Join-Path $LogDir 'backend.error.log') -WindowStyle Hidden -PassThru
        Set-Content -LiteralPath $BackendPidFile -Value $backendProcess.Id
    }
    Wait-Until -TimeoutSeconds 60 -Description 'FastAPI health endpoint' -Condition { Test-BackendHealth }

    $frontendAlreadyRunning = Assert-PortAvailableOrManaged -Port 5173 -PidFile $FrontendPidFile -Kind frontend
    $frontendProcessId = 0
    if (-not $frontendAlreadyRunning) {
        $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
        if (-not $npmCommand) { throw 'npm.cmd was not found.' }
        Write-Host 'Starting React/Vite frontend...'
        $frontendProcess = Start-Process -FilePath $npmCommand.Source -ArgumentList @('run','dev','--','--host','127.0.0.1','--port','5173','--strictPort') -WorkingDirectory $FrontendDir -RedirectStandardOutput (Join-Path $LogDir 'frontend.log') -RedirectStandardError (Join-Path $LogDir 'frontend.error.log') -WindowStyle Hidden -PassThru
        $frontendProcessId = $frontendProcess.Id
        Set-Content -LiteralPath $FrontendPidFile -Value $frontendProcess.Id
    }
    Wait-FrontendReady -ProcessId $frontendProcessId -TimeoutSeconds 60

    Write-Host ''
    Write-Host 'NexusAI started successfully' -ForegroundColor Green
    Write-Host 'Frontend:   http://127.0.0.1:5173'
    Write-Host 'Backend:    http://127.0.0.1:8000'
    Write-Host 'Swagger:    http://127.0.0.1:8000/docs'
    Write-Host 'PostgreSQL: localhost:5432'
    Write-Host 'Redis:      localhost:6379'
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
