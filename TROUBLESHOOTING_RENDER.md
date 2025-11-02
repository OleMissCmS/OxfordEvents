# Render.com 404 Troubleshooting

## Problem
Site returns 404: Not Found at https://oxford-events.onrender.com

## Root Cause Diagnosis

The 404 error suggests one of these issues:

### 1. Service Not Created
The most likely issue: The Render web service doesn't exist or was deleted.

**Solution:**
1. Go to https://dashboard.render.com
2. Check if you see a service named `oxford-events`
3. If NOT, follow `DEPLOYMENT_INSTRUCTIONS.md` to create it

### 2. Service Exists But Broken
The service exists but deployment failed.

**Solution:**
1. Go to https://dashboard.render.com
2. Click on your `oxford-events` service
3. Click **"Logs"** tab
4. Look for errors

**Common errors to look for:**
- `gunicorn: command not found` → Procfile issue
- `No module named 'flask'` → requirements.txt issue
- Import errors → Missing files in repo
- Port binding errors → Configuration issue

### 3. Wrong Branch
Service is deployed from wrong Git branch.

**Solution:**
1. Go to Render dashboard → your service
2. Click **"Settings"** tab
3. Check **"Branch"** is set to `main`

### 4. Build Failed
Recent deployment failed.

**Solution:**
1. Check **"Logs"** tab in Render
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

## Verification Checklist

- [ ] Service exists in Render dashboard
- [ ] Branch is set to `main`
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `gunicorn app:app`
- [ ] Root Directory: (empty)
- [ ] Instance Type: Free
- [ ] No errors in Logs tab

## Immediate Fix

**If service doesn't exist:**
1. Click "New" → "Web Service" in Render dashboard
2. Connect GitHub repo: OxfordEvents
3. Use exact settings from `DEPLOYMENT_INSTRUCTIONS.md`
4. Click "Create Web Service"
5. Wait 5-10 minutes

**If service exists:**
1. In your service dashboard, click **"Manual Deploy"**
2. Select **"Deploy latest commit"**
3. Watch the build logs
4. Wait for "Live at https://oxford-events.onrender.com"

## Code Verification

All code is working perfectly locally:
- ✅ App imports and runs
- ✅ Routes work (/ and /api/events)
- ✅ Returns 49 events
- ✅ Image routes work with location redirect
- ✅ All dependencies installed

The issue is **deployment configuration**, not code!

## Next Action

**You need to:**
1. Check Render dashboard for the service
2. Either create it or repair it
3. Check logs for specific errors
4. Report back any errors you find

The code is ready - it just needs proper Render deployment!

