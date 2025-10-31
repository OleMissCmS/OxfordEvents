# Automatic Git Commit and Push Script
# This script watches for file changes and automatically commits/pushes them

param(
    [string]$WatchPath = ".",
    [int]$CommitInterval = 30  # Seconds to wait after last change before committing
)

Write-Host "Starting automatic commit watcher..." -ForegroundColor Cyan
Write-Host "Watching: $WatchPath" -ForegroundColor Cyan
Write-Host "Commit interval: $CommitInterval seconds" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Check if Git is installed
try {
    git --version | Out-Null
} catch {
    Write-Host "✗ Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if this is a git repository
if (-not (Test-Path ".git")) {
    Write-Host "✗ This is not a git repository" -ForegroundColor Red
    Write-Host "Please run the setup first or initialize git with: git init" -ForegroundColor Yellow
    exit 1
}

# Check if remote is configured
$remoteUrl = git remote get-url origin 2>$null
if (-not $remoteUrl) {
    Write-Host "⚠ No remote 'origin' configured" -ForegroundColor Yellow
    Write-Host "Add a remote with: git remote add origin <your-github-url>" -ForegroundColor Yellow
}

$lastCommit = Get-Date
$pendingChanges = $false
$watcher = $null

function Commit-And-Push {
    $status = git status --porcelain
    if (-not $status) {
        return  # No changes to commit
    }
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Changes detected, committing..." -ForegroundColor Cyan
    
    try {
        # Stage all changes
        git add . 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Failed to stage files" -ForegroundColor Red
            return
        }
        
        # Create commit with timestamp
        $commitMessage = "Auto-commit: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        git commit -m $commitMessage 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ⚠ No changes to commit or commit failed" -ForegroundColor Yellow
            return
        }
        
        Write-Host "  ✓ Committed: $commitMessage" -ForegroundColor Green
        
        # Push to GitHub
        if ($remoteUrl) {
            Write-Host "  Pushing to GitHub..." -ForegroundColor Cyan
            git push 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Pushed to GitHub" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ Push failed (may need authentication)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ⚠ Skipping push (no remote configured)" -ForegroundColor Yellow
        }
        
        $script:lastCommit = Get-Date
        
    } catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
    }
}

function Start-FileWatcher {
    Write-Host "Setting up file system watcher..." -ForegroundColor Cyan
    
    # Create FileSystemWatcher
    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = Resolve-Path $WatchPath
    $watcher.IncludeSubdirectories = $true
    $watcher.EnableRaisingEvents = $true
    
    # Exclude .git directory
    $excludePatterns = @(".git", "__pycache__", ".venv", "venv")
    
    # Register event handlers
    $action = {
        $filePath = $event.SourceEventArgs.FullPath
        $fileName = Split-Path $filePath -Leaf
        
        # Skip if in excluded directories
        $shouldExclude = $false
        foreach ($pattern in $script:excludePatterns) {
            if ($filePath -like "*\$pattern\*" -or $filePath -like "*\$pattern") {
                $shouldExclude = $true
                break
            }
        }
        
        if (-not $shouldExclude) {
            $script:pendingChanges = $true
            $script:lastChange = Get-Date
        }
    }
    
    Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action | Out-Null
    Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action | Out-Null
    Register-ObjectEvent -InputObject $watcher -EventName "Deleted" -Action $action | Out-Null
    Register-ObjectEvent -InputObject $watcher -EventName "Renamed" -Action $action | Out-Null
    
    return $watcher
}

# Start the watcher
$watcher = Start-FileWatcher
Write-Host "✓ File watcher started" -ForegroundColor Green
Write-Host ""

# Main loop
$lastChange = Get-Date
while ($true) {
    Start-Sleep -Seconds 5
    
    if ($pendingChanges) {
        $timeSinceChange = (Get-Date) - $lastChange
        
        if ($timeSinceChange.TotalSeconds -ge $CommitInterval) {
            Commit-And-Push
            $pendingChanges = $false
        }
    }
}

