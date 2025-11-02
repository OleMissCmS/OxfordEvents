# Installing Python for Local Development

## Step 1: Download Python

Go to: https://www.python.org/downloads/

Click the big yellow "Download Python 3.x.x" button.

## Step 2: Run the Installer

Double-click the downloaded `.exe` file.

## ⚠️ IMPORTANT: Check These Boxes

During installation, you MUST check these boxes:

✅ **"Add Python to PATH"** - This is the most important checkbox!

✅ **"Install pip"** - Package manager (should be checked by default)

## Step 3: Choose Installation Type

- Click **"Install Now"** (recommended for most users)

OR

- Click **"Customize installation"** if you want to change the location
  - Default location is fine: `C:\Users\[YourUsername]\AppData\Local\Programs\Python\`

## Step 4: Wait for Installation

Let it finish installing. This takes 1-2 minutes.

## Step 5: Verify Installation

1. Close this PowerShell window
2. Open a NEW PowerShell window
3. Type: `python --version`
4. You should see: `Python 3.x.x`

## Step 6: If You See "Microsoft Store" Error

If you still get the Microsoft Store error after installing:

1. Close all terminal/PowerShell windows
2. Search Windows for "App execution aliases"
3. Turn OFF the toggles for:
   - python.exe
   - python3.exe
4. Click "OK"
5. Open a NEW PowerShell window
6. Try `python --version` again

## Step 7: Continue with Setup

Once Python is working, go back to `RUN_LOCALLY.md` and follow the setup instructions.

## Need Help?

Common issues:
- "Python not recognized" = Not in PATH → Reinstall and check the PATH box
- "Permission denied" = Need to run as admin → Right-click PowerShell, "Run as administrator"
- Still seeing Store error = Didn't disable aliases → Do Step 6 above

