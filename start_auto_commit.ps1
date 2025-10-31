# Auto-start script for automatic commits
# Run this to start monitoring and auto-committing changes

$scriptPath = Join-Path $PSScriptRoot 'auto_commit.ps1'
Start-Process powershell -ArgumentList '-NoExit', '-File', $scriptPath -WindowStyle Normal
