[CmdletBinding()]
param()

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PreferredDockerCli = 'D:\Docker\DockerDesktop\resources\bin\docker.exe'

function Get-DockerCli {
    if (Test-Path -LiteralPath $PreferredDockerCli) { return $PreferredDockerCli }
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    return $null
}

function Get-ContainerHealth([string]$DockerCli, [string]$Service) {
    $containerId = (& $DockerCli compose --project-directory $ProjectRoot ps -q $Service 2>$null | Select-Object -First 1)
    if (-not $containerId) { return 'STOPPED' }
    $state = (& $DockerCli inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $containerId 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $state) { return 'UNKNOWN' }
    return ([string]$state).Trim().ToUpperInvariant()
}

function Test-Backend {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 3
        $openApi = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/openapi.json' -TimeoutSec 3
        return $health.status -eq 'ok' -and $openApi.info.title -eq 'NexusAI'
    } catch { return $false }
}

function Test-Frontend {
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:5173/' -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    } catch { return $false }
}

$dockerCli = Get-DockerCli
$dockerStatus = 'STOPPED'
$postgresStatus = 'STOPPED'
$redisStatus = 'STOPPED'
if ($dockerCli) {
    & $dockerCli info *> $null
    if ($LASTEXITCODE -eq 0) {
        $dockerStatus = 'RUNNING'
        $postgresStatus = Get-ContainerHealth $dockerCli 'postgres'
        $redisStatus = Get-ContainerHealth $dockerCli 'redis'
    }
}
$backendStatus = if (Test-Backend) { 'RUNNING' } else { 'STOPPED' }
$frontendStatus = if (Test-Frontend) { 'RUNNING' } else { 'STOPPED' }

Write-Host ('{0,-20} {1}' -f 'Docker Engine', $dockerStatus)
Write-Host ('{0,-20} {1}' -f 'PostgreSQL', $postgresStatus)
Write-Host ('{0,-20} {1}' -f 'Redis', $redisStatus)
Write-Host ('{0,-20} {1}' -f 'Backend :8000', $backendStatus)
Write-Host ('{0,-20} {1}' -f 'Frontend :5173', $frontendStatus)
Write-Host ''
Write-Host 'Frontend: http://127.0.0.1:5173'
Write-Host 'Swagger:  http://127.0.0.1:8000/docs'

$allHealthy = $dockerStatus -eq 'RUNNING' -and $postgresStatus -eq 'HEALTHY' -and $redisStatus -eq 'HEALTHY' -and $backendStatus -eq 'RUNNING' -and $frontendStatus -eq 'RUNNING'
if ($allHealthy) { exit 0 }
exit 1
