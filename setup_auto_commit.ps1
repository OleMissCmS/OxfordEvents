# Setup Script for Automatic Git Commits
# This configures your repository for automatic commits on every change

Write-Host "Setting up automatic Git commits..." -ForegroundColor Cyan

# Check if Git is installed
try {
    $gitVersion = git --version
    Write-Host "✓ Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if this is a git repository
if (-not (Test-Path ".git")) {
    Write-Host "✗ This is not a git repository" -ForegroundColor Red
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to initialize repository" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Repository initialized" -ForegroundColor Green
}

# Check if remote is configured
$remoteUrl = git remote get-url origin 2>$null
if (-not $remoteUrl) {
    Write-Host ""
    Write-Host "No GitHub remote configured." -ForegroundColor Yellow
    $repoUrl = Read-Host "Enter your GitHub repository URL (e.g., https://github.com/username/repo.git)"
    
    if ($repoUrl) {
        git remote add origin $repoUrl
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Remote added: $repoUrl" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to add remote" -ForegroundColor Red
        }
    }
} else {
    Write-Host "✓ Remote found: $remoteUrl" -ForegroundColor Green
}

# Configure git for automatic commits
Write-Host ""
Write-Host "Configuring Git..." -ForegroundColor Cyan

# Set up git hooks directory
$hooksDir = ".git\hooks"
if (-not (Test-Path $hooksDir)) {
    New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
}

# Create post-commit hook to auto-push
$postCommitHook = @"
#!/bin/sh
# Auto-push hook - automatically pushes after every commit
git push origin main 2>&1 || git push origin master 2>&1
"@

# For Windows, we'll use a PowerShell version instead
$postCommitHookPs1 = @"
# Auto-push hook - automatically pushes after every commit
git push origin main 2>&1
if (`$LASTEXITCODE -ne 0) {
    git push origin master 2>&1
}
"@

# Write PowerShell hook (Windows)
$hookPath = "$hooksDir\post-commit"
$postCommitHookPs1 | Out-File -FilePath $hookPath -Encoding UTF8
Write-Host "✓ Created post-commit hook" -ForegroundColor Green

# Create a startup script for the file watcher
$startupScript = @"
# Auto-start script for automatic commits
# Run this to start monitoring and auto-committing changes

`$scriptPath = Join-Path `$PSScriptRoot "auto_commit.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-File", "`$scriptPath" -WindowStyle Normal
"@

$startupScript | Out-File -FilePath "start_auto_commit.ps1" -Encoding UTF8
Write-Host "✓ Created start_auto_commit.ps1" -ForegroundColor Green

Write-Host ""
Write-Host "✓ Automatic commit setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Make sure your GitHub credentials are configured" -ForegroundColor White
Write-Host "  2. Run: .\start_auto_commit.ps1" -ForegroundColor White
Write-Host "     OR" -ForegroundColor White
Write-Host "  3. Run: .\auto_commit.ps1" -ForegroundColor White
Write-Host ""
Write-Host "The watcher will:" -ForegroundColor Cyan
Write-Host "  - Monitor all file changes" -ForegroundColor White
Write-Host "  - Auto-commit changes after 30 seconds of inactivity" -ForegroundColor White
Write-Host "  - Auto-push to GitHub after each commit" -ForegroundColor White
Write-Host ""
Write-Host "⚠ WARNING: This will commit ALL changes automatically!" -ForegroundColor Yellow
Write-Host "  Make sure you're okay with this behavior before starting." -ForegroundColor Yellow

