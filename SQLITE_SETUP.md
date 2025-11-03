# SQLite Setup (Free - No Database Subscription Needed!)

## ✅ Good News: SQLite is Already Configured!

The app **already uses SQLite by default** - no setup required! Here's how it works:

## How It Works

### Priority Order:
1. **PostgreSQL** (if `DATABASE_URL` is set) - **You can ignore this!**
2. **SQLite on persistent disk** - ✅ **AUTOMATIC (FREE)**
3. **SQLite in local `data/`** - Development fallback

### What You Get:
- ✅ **100% Free** - No database subscription needed
- ✅ **Persistent** - If you enable Render Persistent Disk
- ✅ **Fast** - Local SQLite database
- ✅ **Automatic** - Works out of the box

## Current Status

**Right now, without any changes:**
- ✅ SQLite database will be created automatically
- ✅ Stored in `data/oxford_events.db` (local) or persistent disk
- ✅ All images and metadata stored in SQLite
- ✅ Works on first deploy!

## Optional: Make It Persistent (Recommended)

To make data survive redeploys, enable Render Persistent Disk:

### Step 1: Enable Persistent Disk
1. Go to Render Dashboard → Your Web Service
2. Click **"Settings"** tab
3. Scroll to **"Persistent Disk"**
4. Click **"Add Persistent Disk"**
5. Configure:
   - **Mount Path**: `/opt/render/project/src/persistent`
   - **Size**: 1GB (free tier)
6. Click **"Save Changes"**

### Step 2: That's It!
The code automatically detects persistent disk and uses it. You'll see in logs:
```
[Storage] Persistent disk: ✅ Enabled
[Database] Using SQLite on persistent disk: /opt/render/project/src/persistent/data/oxford_events.db
```

## What Gets Stored in SQLite

### Tables:
- **team_logos** - Team logo URLs and metadata
- **venue_images** - Venue image URLs and metadata  
- **image_cache** - Cached generated images

### Images:
- Stored in `static/images/cache/` (or persistent disk)
- Metadata stored in SQLite database

## Verification

After deployment, check Render logs. You should see:
```
[Storage] Base path: data (or /opt/render/project/src/persistent if enabled)
[Storage] Database dir: data (or /persistent/data if enabled)
[Storage] Persistent disk: ❌ Using local filesystem (or ✅ Enabled)
[Database] Using SQLite (local): /path/to/oxford_events.db
[Database] Tables created/verified
```

## Local Development

Works automatically! Just run:
```bash
python app.py
```

SQLite database will be created in `data/oxford_events.db` automatically.

## Cost

| Solution | Cost | Status |
|----------|------|--------|
| **SQLite (Current)** | **$0** | ✅ **ACTIVE** |
| PostgreSQL | $7/month after 30 days | Not needed |

## Summary

**You don't need to do anything!** SQLite is:
- ✅ Already configured
- ✅ Already active
- ✅ Already free
- ✅ Already working

Just deploy and it works! Enable persistent disk if you want data to survive redeploys (recommended but optional).

