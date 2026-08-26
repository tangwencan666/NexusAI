$scriptPath = Join-Path $PSScriptRoot 'scripts\stop-nexusai.ps1'
& $scriptPath @args
exit $LASTEXITCODE
