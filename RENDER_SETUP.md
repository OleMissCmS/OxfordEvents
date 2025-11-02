# Quick Render.com Setup Guide

## In Your Render Dashboard

Follow these exact steps:

### 1. Click "New" → "Web Service"

### 2. Connect Repository
- Authenticate with GitHub if needed
- Select repository: **OxfordEvents**
- Branch: **main**

### 3. Configure Service

**Name:** `oxford-events`

**Region:** Oregon (US West) or any region closest to you

**Branch:** `main`

**Root Directory:** (leave empty)

**Environment:** `Python 3`

**Build Command:** 
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn app:app
```

**Instance Type:** `Free` ($0/month)

### 4. Advanced Settings
- **Health Check Path:** (leave empty)
- **Pull Request Previews:** Enabled (optional)

### 5. Deploy!
Click **"Create Web Service"**

## Wait for Deployment

Render will:
1. ✅ Clone your repo
2. ✅ Install all dependencies from requirements.txt
3. ✅ Build the application
4. ✅ Start Gunicorn server
5. ✅ Give you a URL like: `https://oxford-events.onrender.com`

## After Deployment

Visit your URL and you should see:
- ✅ Clean white background
- ✅ "Concerts & Events in Oxford" header
- ✅ 6 colorful pastel filter pills (All, Music, Arts & Culture, Community, Sports)
- ✅ Stats showing 6 total events
- ✅ 6 event cards in a grid
- ✅ Fully functional filtering!

## If It Fails

### Check Logs
1. Go to your service in Render dashboard
2. Click "Logs" tab
3. Look for Python errors

### Common Issues

**Error: "gunicorn: command not found"**
- Fix: Make sure `requirements.txt` includes `gunicorn>=21.2.0`

**Error: "No module named 'flask'"**
- Fix: Make sure `requirements.txt` includes `flask>=3.0.0`

**Error: "Unable to bind to port"**
- Fix: The START command should be `gunicorn app:app` (not `python app.py`)

**Status 127**
- Fix: Usually means a command isn't found. Double-check Build and Start commands.

## Next Render Will Auto-Deploy

Any future `git push` to main will automatically trigger a new deployment on Render!

## Free Tier Limits

- Services sleep after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- 750 compute hours per month
- 100GB bandwidth per month

For a production site, you'd upgrade to a paid tier that:
- Stays awake 24/7
- Has unlimited bandwidth
- Costs ~$7/month

## Questions?

Check `DEPLOYMENT.md` for detailed technical information.

