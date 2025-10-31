# GitHub Repository Setup Script
# Run this script AFTER installing Git

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubRepoUrl
)

Write-Host "Setting up GitHub integration..." -ForegroundColor Cyan

# Check if Git is installed
try {
    $gitVersion = git --version
    Write-Host "✓ Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if already a git repository
if (Test-Path ".git") {
    Write-Host "⚠ Git repository already initialized" -ForegroundColor Yellow
    $response = Read-Host "Do you want to continue? (y/n)"
    if ($response -ne "y") {
        exit 0
    }
} else {
    # Initialize Git repository
    Write-Host "Initializing Git repository..." -ForegroundColor Cyan
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to initialize Git repository" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Repository initialized" -ForegroundColor Green
}

# Check if remote already exists
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "⚠ Remote 'origin' already exists: $existingRemote" -ForegroundColor Yellow
    $response = Read-Host "Do you want to update it? (y/n)"
    if ($response -eq "y") {
        git remote set-url origin $GitHubRepoUrl
        Write-Host "✓ Remote updated" -ForegroundColor Green
    }
} else {
    # Add remote
    Write-Host "Adding GitHub remote..." -ForegroundColor Cyan
    git remote add origin $GitHubRepoUrl
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to add remote" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Remote added" -ForegroundColor Green
}

# Add all files
Write-Host "Staging files..." -ForegroundColor Cyan
git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to stage files" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Files staged" -ForegroundColor Green

# Check if there are changes to commit
$status = git status --porcelain
if (-not $status) {
    Write-Host "⚠ No changes to commit" -ForegroundColor Yellow
} else {
    # Create initial commit
    Write-Host "Creating initial commit..." -ForegroundColor Cyan
    git commit -m "Initial commit: OxfordEvents project"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to create commit" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Initial commit created" -ForegroundColor Green
}

# Set main branch
Write-Host "Setting up main branch..." -ForegroundColor Cyan
git branch -M main 2>$null

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
Write-Host "Note: You may be prompted for GitHub credentials" -ForegroundColor Yellow
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to push to GitHub" -ForegroundColor Red
    Write-Host "You may need to authenticate. Try:" -ForegroundColor Yellow
    Write-Host "  - Using a Personal Access Token instead of password" -ForegroundColor Yellow
    Write-Host "  - Or configure SSH keys for GitHub" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✓ Successfully connected to GitHub!" -ForegroundColor Green
Write-Host "Repository URL: $GitHubRepoUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  - Make changes to your code" -ForegroundColor White
Write-Host "  - I can help you commit and push changes with:" -ForegroundColor White
Write-Host "    git add ." -ForegroundColor Gray
Write-Host "    git commit -m 'Description'" -ForegroundColor Gray
Write-Host "    git push" -ForegroundColor Gray

