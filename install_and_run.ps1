# Oxford Events - Automated Installation and Setup Script
# This script will guide you through installing Python and running the app locally

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Oxford Events - Local Setup Assistant" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonInstalled = $false
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python \d+\.\d+") {
        Write-Host "✅ Python is already installed: $pythonVersion" -ForegroundColor Green
        $pythonInstalled = $true
    }
} catch {
    Write-Host "❌ Python is not installed" -ForegroundColor Red
}

if (-not $pythonInstalled) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "STEP 1: Install Python" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Python needs to be installed before we can continue." -ForegroundColor White
    Write-Host ""
    Write-Host "Please follow these steps:" -ForegroundColor White
    Write-Host ""
    Write-Host "1. Open your web browser" -ForegroundColor Cyan
    Write-Host "2. Go to: https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "3. Click the big yellow 'Download Python' button" -ForegroundColor Cyan
    Write-Host "4. Run the downloaded installer" -ForegroundColor Cyan
    Write-Host "5. IMPORTANT: Check the box 'Add Python to PATH'" -ForegroundColor Yellow
    Write-Host "6. Click 'Install Now'" -ForegroundColor Cyan
    Write-Host "7. Wait for installation to complete" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Once Python is installed, close this window and run this script again." -ForegroundColor White
    Write-Host ""
    
    # Offer to open the download page
    $response = Read-Host "Would you like me to open the Python download page now? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host "Opening Python download page..." -ForegroundColor Cyan
        Start-Process "https://www.python.org/downloads/"
    }
    
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "STEP 2: Create Virtual Environment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if venv exists
if (Test-Path "venv") {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit
    }
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "STEP 3: Activate Environment & Install Dependencies" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

Write-Host "✅ Virtual environment activated" -ForegroundColor Green
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "STEP 4: Launch Streamlit App" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Streamlit app..." -ForegroundColor Cyan
Write-Host ""
Write-Host "The app will open in your browser automatically." -ForegroundColor White
Write-Host "If it doesn't, go to: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server when you're done." -ForegroundColor Yellow
Write-Host ""

# Launch Streamlit
streamlit run streamlit_app.py

