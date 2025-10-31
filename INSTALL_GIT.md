# Installing Git for Windows

## Quick Installation Guide

### Step 1: Download Git
1. Go to: **https://git-scm.com/download/win**
2. The download should start automatically
3. Or click the download button for the latest version

### Step 2: Run the Installer
1. Double-click the downloaded `.exe` file (e.g., `Git-2.x.x-64-bit.exe`)
2. Click "Next" through the installation wizard

### Step 3: Important Settings During Installation

**Text Editor Selection:**
- Choose your preferred editor (VS Code, Notepad++, etc.) or leave as default

**Default Branch Name:**
- Choose **"Let Git decide"** or **"main"** (recommended)

**PATH Environment:**
- ✅ **IMPORTANT**: Select **"Git from the command line and also from 3rd-party software"**
  - This ensures Git commands work in PowerShell/Command Prompt
  - Without this, the automatic commit scripts won't work!

**HTTPS Transport:**
- Choose "Use the OpenSSL library" (default)

**Line Ending Conversions:**
- Choose "Checkout Windows-style, commit Unix-style line endings" (default)

**Terminal Emulator:**
- Choose "Use Windows' default console window" (default)

**Default Behavior:**
- Choose "Default (fast-forward or merge)" (default)

**Credential Helper:**
- Choose "Git Credential Manager" (recommended - helps with GitHub authentication)

**Extra Options:**
- Enable file system caching (recommended for performance)

### Step 4: Complete Installation
1. Click "Install"
2. Wait for installation to complete
3. Click "Finish"

### Step 5: Restart Cursor
**IMPORTANT**: After installing Git, you MUST:
1. **Close Cursor completely**
2. **Reopen Cursor**
3. This ensures the PATH environment variable is updated

### Step 6: Verify Installation
Open a new terminal in Cursor and run:
```powershell
git --version
```

You should see something like: `git version 2.x.x.windows.x`

## Alternative: Use GitHub Desktop's Git

If you have GitHub Desktop installed, it includes Git, but it might not be in your PATH. You can:

1. **Find Git location** in GitHub Desktop:
   - GitHub Desktop → File → Options → Git
   - Note the "Git executable" path

2. **Add to PATH manually** (advanced):
   - Usually located at: `C:\Users\YourName\AppData\Local\GitHubDesktop\app-x.x.x\resources\app\git\cmd\git.exe`
   - Add the `cmd` folder to your Windows PATH

However, **installing Git separately** (as described above) is recommended as it's simpler and ensures everything works correctly.

## After Installation

Once Git is installed and you've restarted Cursor, come back and I'll help you:
1. Configure your Git identity
2. Initialize the repository
3. Connect to GitHub
4. Set up automatic commits


