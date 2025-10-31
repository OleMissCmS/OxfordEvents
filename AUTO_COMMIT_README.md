# Automatic Git Commits Setup

## Quick Start (Option B - Automatic Commits)

### Step 1: Install Git
If not already installed:
- Download: https://git-scm.com/download/win
- Install with defaults
- Restart Cursor/terminal

### Step 2: Configure Git (First time only)
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 3: Create GitHub Repository
1. Go to https://github.com
2. Create new repository (don't initialize with files)
3. Copy the repository URL

### Step 4: Run Setup
```powershell
# This will configure everything for automatic commits
.\setup_auto_commit.ps1
```

### Step 5: Start Automatic Commits
```powershell
# Start the file watcher (keeps running until you stop it)
.\auto_commit.ps1
```

Or use the helper:
```powershell
.\start_auto_commit.ps1
```

## How It Works

- **File Watcher**: Monitors all files in your project
- **Auto-Commit**: Commits changes after 30 seconds of inactivity
- **Auto-Push**: Pushes to GitHub after each commit
- **Exclusions**: Automatically ignores `.git`, `__pycache__`, `venv`, etc.

## Stopping Auto-Commit

Press `Ctrl+C` in the PowerShell window running the watcher.

## Customization

Edit `auto_commit.ps1` to change:
- `$CommitInterval` - Time to wait before committing (default: 30 seconds)
- `$WatchPath` - Directory to watch (default: current directory)

## Important Notes

⚠️ **WARNING**: This will commit ALL changes automatically!
- Make sure you're okay with automatic commits
- Consider using `.gitignore` to exclude sensitive files
- Review commits before pushing if needed

## Troubleshooting

### "Git is not recognized"
- Git not installed or not in PATH
- Restart terminal after installing Git

### "No remote configured"
- Run `git remote add origin <your-github-url>`
- Or run `setup_auto_commit.ps1` which will prompt for URL

### "Push failed"
- Check GitHub credentials
- Use Personal Access Token instead of password
- GitHub Settings → Developer settings → Personal access tokens

### Files not being committed
- Check if files match patterns in `.gitignore`
- Check if watcher is still running (look for PowerShell window)

