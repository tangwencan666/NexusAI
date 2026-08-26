$scriptPath = Join-Path $PSScriptRoot 'scripts\start-nexusai.ps1'
& $scriptPath @args
exit $LASTEXITCODE
