# Deployment Instructions for Oxford Events on Render.com

## Current Status: 404 Error

The site is showing 404, which means either:
1. The service hasn't been created yet on Render
2. The service exists but needs repair
3. There's a configuration issue

## Step-by-Step Deployment Instructions

### 1. Log into Render Dashboard

Go to: https://dashboard.render.com

### 2. Create New Web Service

Click **"New"** → **"Web Service"**

### 3. Connect Your GitHub Repository

- If not connected, click "Connect GitHub" and authorize
- Select repository: **OxfordEvents**
- Click "Connect"

### 4. Configure Web Service

Use these **exact** settings:

**Name:** `oxford-events`

**Region:** Choose closest to you (e.g., Oregon US West)

**Branch:** `main`

**Root Directory:** (leave empty - this is important!)

**Environment:** `Python 3`

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn app:app
```

**Instance Type:** `Free`

### 5. Advanced Settings

Click "Advanced" at the bottom:

**Health Check Path:** (leave empty)

### 6. Create Web Service

Click **"Create Web Service"** button

### 7. Wait for Deployment

Render will:
- Clone your repository
- Install dependencies
- Start gunicorn
- Show you a URL

This takes 5-10 minutes.

### 8. Add Environment Variables (After Deployment)

Once deployed, go to **"Environment"** tab and add:

**Key:** `TICKETMASTER_API_KEY`
**Value:** (your Ticketmaster API key)

Click "Save Changes" - Render will automatically redeploy.

## Troubleshooting

### If You Get Status 127

This means gunicorn isn't found. Make sure:
- `requirements.txt` includes `gunicorn>=21.2.0`
- Build command is: `pip install -r requirements.txt`

### If You Get 404 After Deployment

1. Check "Logs" tab in Render dashboard
2. Look for Python errors
3. Common issues:
   - Missing dependencies
   - Import errors
   - Port binding issues

### If Build Fails

Check the logs. Common fixes:
- Make sure `Procfile` exists with `web: gunicorn app:app`
- Make sure `requirements.txt` has all dependencies
- Make sure `runtime.txt` has `python-3.11.13`

## Verify Deployment

After deployment succeeds, visit your URL (e.g., `https://oxford-events.onrender.com`)

You should see:
- "Concerts & Events in Oxford" header
- Pastel-colored filter pills
- Event cards with images
- ~49 events from various sources

## Check Logs

If something isn't working, go to Render dashboard → your service → "Logs" tab.

Look for:
- Python tracebacks
- Import errors
- Missing module errors

## Next Steps

Once the site is live:
1. Test all filter categories
2. Test search functionality
3. Verify images are loading
4. Check calendar links work
5. Submit real event sources

## Your Repository

All code is in GitHub: https://github.com/OleMissCmS/OxfordEvents

Branch: `main`

## Support

If deployment fails after following these steps exactly:
1. Copy error messages from Logs tab
2. Check that all files exist in repository
3. Verify Procfile doesn't have extra blank lines
4. Try manual redeploy from Render dashboard

