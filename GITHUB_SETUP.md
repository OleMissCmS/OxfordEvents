# GitHub Integration Setup Guide

## Step 1: Install Git

If Git is not installed on your system:

1. **Download Git for Windows**: https://git-scm.com/download/win
2. **Install Git** with default settings
3. **Restart your terminal/Cursor** after installation
4. **Verify installation** by running: `git --version`

## Step 2: Configure Git (First time only)

After installing Git, configure your identity:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 3: Create GitHub Repository

1. Go to https://github.com and sign in
2. Click the "+" icon → "New repository"
3. Name it `OxfordEvents` (or your preferred name)
4. **Do NOT** initialize with README, .gitignore, or license (we already have files)
5. Click "Create repository"
6. **Copy the repository URL** (it will look like: `https://github.com/yourusername/OxfordEvents.git`)

## Step 4: Initialize and Connect to GitHub

Once Git is installed, run these commands in your terminal:

```powershell
# Navigate to your project folder
cd C:\Users\chads\Documents\GitHub\OxfordEvents

# Initialize Git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: OxfordEvents project"

# Add GitHub remote (replace with your actual repository URL)
git remote add origin https://github.com/yourusername/OxfordEvents.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 5: Set Up Automatic Updates

You have several options for automatic updates:

### Option A: Manual Commits (Recommended)
After making changes, I can help you commit and push:
- `git add .`
- `git commit -m "Description of changes"`
- `git push`

### Option B: Automated Commits (✅ SET UP)
**Automatic commits have been configured!** This will automatically commit and push every change.

**To start automatic commits:**
```powershell
# Quick setup (configures everything)
.\setup_auto_commit.ps1

# Then start the watcher
.\start_auto_commit.ps1
# OR
.\auto_commit.ps1
```

**How it works:**
- Watches all files for changes
- Automatically commits after 30 seconds of no changes
- Automatically pushes to GitHub after each commit
- **Warning**: This commits EVERY change automatically - use with caution!

### Option C: Scheduled Auto-Commits
Set up a scheduled task to automatically commit and push changes periodically.

**Which option would you prefer?** I recommend Option A for safety, but I can set up any of these once Git is installed.

---

## Troubleshooting

### If you see "git is not recognized"
- Git is not installed or not in your PATH
- Restart your terminal after installing Git
- Verify Git is installed: `git --version`

### If push fails with authentication error
- Use a Personal Access Token instead of password
- GitHub Settings → Developer settings → Personal access tokens → Generate new token
- Use the token as your password when prompted

---

## Next Steps

After completing the setup, I can help you:
1. Make changes and commit them
2. Set up automated workflows
3. Create GitHub Actions for CI/CD
4. Configure branch protection rules

