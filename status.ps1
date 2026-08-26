$scriptPath = Join-Path $PSScriptRoot 'scripts\status-nexusai.ps1'
& $scriptPath @args
exit $LASTEXITCODE
