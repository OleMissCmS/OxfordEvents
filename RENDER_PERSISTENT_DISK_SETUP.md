# Free Persistent Storage on Render (No Database Required!)

## Problem

Render's free PostgreSQL database expires after 30 days. This solution uses **Render Persistent Disk** + **SQLite** for completely free persistent storage!

## Solution: Render Persistent Disk + SQLite

### Benefits:
- ✅ **100% Free** - No database subscription needed
- ✅ **Persistent** - Survives redeploys
- ✅ **Fast** - Local filesystem access
- ✅ **1GB Free** - Plenty for images and metadata
- ✅ **No External Dependencies** - Everything stored locally

## Step 1: Enable Persistent Disk on Render

1. Go to your **Web Service** in Render Dashboard
2. Click **"Settings"** tab
3. Scroll to **"Persistent Disk"**
4. Click **"Add Persistent Disk"**
5. Configure:
   - **Mount Path**: `/opt/render/project/src/persistent` (or `/persistent`)
   - **Size**: 1GB (free tier)
6. Click **"Save Changes"**

Render will redeploy your service automatically.

## Step 2: Verify It's Working

After deployment, check logs. You should see:
```
[Storage] Using persistent disk at: /opt/render/project/src/persistent
[Storage] SQLite database initialized
```

## How It Works

### Image Storage:
- Images stored in: `/persistent/images/cache/`
- Survives redeploys ✅
- Fast filesystem access ✅

### Metadata Storage:
- SQLite database: `/persistent/data/oxford_events.db`
- Stores team logos, venue images, cache keys
- No external database needed ✅

### Automatic Detection:
The code automatically detects persistent disk and uses it. If not available, falls back to regular filesystem (works for local dev).

## Directory Structure

```
/persistent/
├── images/
│   └── cache/          # Downloaded team logos, venue images
├── data/
│   ├── oxford_events.db  # SQLite database
│   ├── team_logos.json   # Fallback JSON (optional)
│   └── venue_images.json # Fallback JSON (optional)
```

## Local Development

Works automatically! The code uses `data/` locally:
- Creates `data/oxford_events.db` (SQLite)
- Stores images in `static/images/cache/`
- No configuration needed

## Performance Optimizations

The solution includes:
1. **Aggressive Caching** - Images cached in memory and on disk
2. **Lazy Loading** - Only fetch images when needed
3. **Compression** - Images optimized for web
4. **Fast Lookups** - SQLite indexed queries

## Cost Comparison

| Solution | Cost | Persistence | Speed |
|----------|------|-------------|-------|
| Render PostgreSQL | $7/month after 30 days | ✅ | ⚡⚡⚡ |
| **Persistent Disk + SQLite** | **$0 forever** | ✅ | ⚡⚡ |
| Regular Filesystem | $0 | ❌ (lost on redeploy) | ⚡ |

## Troubleshooting

### "Persistent disk not found"
- Check Settings → Persistent Disk is enabled
- Verify mount path is correct
- Check logs for initialization messages

### "Disk full"
- 1GB should be plenty for images
- Can upgrade to larger disk if needed
- Or use image cleanup/rotation

### "Slow performance"
- Normal on first load (images downloading)
- Subsequent loads are fast (cached)
- Consider upgrading disk size if needed

## Alternative: External Free Services

If persistent disk isn't available, you can also use:
- **Supabase** (free tier, PostgreSQL)
- **PlanetScale** (free tier, MySQL)
- **Cloudinary** (free tier, image CDN)

But Persistent Disk + SQLite is the simplest free solution!

