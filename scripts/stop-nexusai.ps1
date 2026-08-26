[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WorkDir = Join-Path $ProjectRoot 'work'
$PreferredDockerCli = 'D:\Docker\DockerDesktop\resources\bin\docker.exe'

function Get-DockerCli {
    if (Test-Path -LiteralPath $PreferredDockerCli) { return $PreferredDockerCli }
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    return $null
}

function Stop-ManagedProcess([string]$Name, [string]$PidFile, [string]$RequiredPattern) {
    if (-not (Test-Path -LiteralPath $PidFile)) {
        Write-Host "$Name PID file not found; skipping."
        return
    }
    $rawPid = (Get-Content -LiteralPath $PidFile -Raw).Trim()
    $processId = 0
    if (-not [int]::TryParse($rawPid, [ref]$processId)) {
        Write-Warning "$Name PID file is invalid; removing the stale file."
        Remove-Item -LiteralPath $PidFile -Force
        return
    }
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if (-not $process) {
        Write-Host "$Name process $processId has already exited."
        Remove-Item -LiteralPath $PidFile -Force
        return
    }
    $details = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
    if (-not $details -or ([string]$details.CommandLine) -notmatch $RequiredPattern) {
        Write-Warning "$Name PID $processId does not match a NexusAI process. It will not be stopped."
        Remove-Item -LiteralPath $PidFile -Force
        return
    }
    & taskkill.exe /PID $processId /T /F | Out-Null
    if ($LASTEXITCODE -notin @(0, 128)) { throw "Failed to stop $Name process tree $processId (exit code $LASTEXITCODE)." }
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host "$Name stopped."
}

try {
    $backendPython = Join-Path $ProjectRoot 'backend\.venv\Scripts\python.exe'
    $backendPattern = [regex]::Escape($backendPython) + '.*uvicorn.*app\.main:app'
    $frontendPattern = '(npm|vite).*run\s+dev.*--port\s+5173.*--strictPort'
    Stop-ManagedProcess -Name 'Backend' -PidFile (Join-Path $WorkDir 'backend.pid') -RequiredPattern $backendPattern
    Stop-ManagedProcess -Name 'Frontend' -PidFile (Join-Path $WorkDir 'frontend.pid') -RequiredPattern $frontendPattern

    $dockerCli = Get-DockerCli
    if (-not $dockerCli) { throw 'Docker CLI was not found; Compose services could not be stopped.' }
    & $dockerCli compose --project-directory $ProjectRoot stop
    if ($LASTEXITCODE -ne 0) { throw "docker compose stop failed with exit code $LASTEXITCODE." }
    Write-Host 'NexusAI stopped. Docker volumes were preserved.' -ForegroundColor Green
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
