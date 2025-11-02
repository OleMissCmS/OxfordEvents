# Running Oxford Events Locally

## Prerequisites

Install Python 3.9 or higher from [python.org](https://www.python.org/downloads/)

During installation, check:
- ✅ "Add Python to PATH"
- ✅ "Install pip"

## Setup Instructions

1. Open PowerShell or Command Prompt in this directory

2. Create a virtual environment:
   ```powershell
   python -m venv venv
   ```

3. Activate the virtual environment:
   
   **PowerShell:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   **If you get an execution policy error:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\venv\Scripts\Activate.ps1
   ```
   
   **Command Prompt:**
   ```cmd
   venv\Scripts\activate
   ```

4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

5. Run the Streamlit app:
   ```powershell
   streamlit run streamlit_app.py
   ```

6. Open your browser to the URL shown (usually http://localhost:8501)

## Quick Test

To test with the minimal app first:
```powershell
streamlit run streamlit_app_minimal.py
```

## Troubleshooting

**Python not found:**
- Reinstall Python and ensure "Add to PATH" is checked
- Restart your terminal after installation

**Streamlit command not found:**
- Make sure venv is activated (you should see `(venv)` in your prompt)
- Run `pip install -r requirements.txt` again

**Port already in use:**
- Use: `streamlit run streamlit_app.py --server.port 8502`

## Benefits of Running Locally

- ✅ No wait for Cloud deployments (instant feedback)
- ✅ See errors in terminal immediately
- ✅ Faster development cycle
- ✅ Can debug with print statements
- ✅ Works offline

