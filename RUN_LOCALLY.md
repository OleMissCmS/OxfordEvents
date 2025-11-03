# How to Run Oxford Events Locally

## Quick Start

**Local URL:** `http://localhost:5000` or `http://127.0.0.1:5000`

## Step-by-Step Instructions

### 1. Make sure you're in the project directory

```powershell
cd C:\Users\chads\Documents\GitHub\OxfordEvents
```

### 2. Activate virtual environment (if using one)

```powershell
.\venv\Scripts\activate
```

### 3. Install dependencies (if not already installed)

```powershell
pip install -r requirements.txt
```

### 4. Run the Flask app

**Option A: Using Python directly**
```powershell
python app.py
```

**Option B: Using Flask CLI**
```powershell
python -m flask --app app run
```

### 5. Open in browser

Once you see "Running on http://127.0.0.1:5000", open your browser and go to:

- http://localhost:5000
- http://127.0.0.1:5000

## Expected Behavior

- First load: May take 10-30 seconds while it scrapes all 14 event sources
- Subsequent loads: Fast (< 1 second) due to caching
- You'll see 47+ events from Ole Miss and community sources

## Troubleshooting

### "Port 5000 is already in use"
Change the port:
```powershell
python app.py
# Then in app.py, change port=5000 to port=5001
```

### "ModuleNotFoundError"
Install missing package:
```powershell
pip install <package-name>
```

### App doesn't start
Check for errors in the terminal output.

## Stop the Server

Press `Ctrl+C` in the terminal running the app.

## Notes

- The app uses Flask-Caching (10-minute cache) to prevent timeouts
- Local instance pulls real data from all configured sources
- Changes to code require restarting the app (Ctrl+C then run again)
