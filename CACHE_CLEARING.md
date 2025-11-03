# How to Clear Cache

The Oxford Events app uses Flask-Caching with a 10-minute cache timeout. Here are several ways to clear the cache:

## Method 1: Use the Cache Clearing Endpoint (Easiest)

After deploying, visit this URL in your browser or use curl:

**Browser:**
```
https://oxfordevents.onrender.com/api/clear-cache
```

**Command Line (curl):**
```bash
curl https://oxfordevents.onrender.com/api/clear-cache
```

You should see:
```json
{"status": "success", "message": "Cache cleared successfully"}
```

Then refresh the main page to see fresh events.

## Method 2: Wait for Cache to Expire

The cache automatically expires after **10 minutes (600 seconds)**. After that time, visiting the site will fetch fresh events.

## Method 3: Temporary Cache Disable (For Testing)

If you need to temporarily disable caching for testing, edit `app.py`:

**Option A: Comment out the cache decorator**
```python
# @cache.cached(timeout=600, key_prefix='all_events')
def load_events():
    ...
```

**Option B: Set timeout to 0**
```python
@cache.cached(timeout=0, key_prefix='all_events')  # Always fetch fresh
def load_events():
    ...
```

**Option C: Change to very short timeout for testing**
```python
@cache.cached(timeout=60, key_prefix='all_events')  # 1 minute cache
def load_events():
    ...
```

## Method 4: Restart the Service (Render)

In your Render dashboard:
1. Go to your service
2. Click "Manual Deploy" → "Deploy latest commit"
3. This restarts the service and clears the cache

## Current Cache Settings

- **Type**: SimpleCache (in-memory)
- **Timeout**: 600 seconds (10 minutes)
- **Key**: `all_events`

## Testing Cache Clear

After clearing cache, check if events refreshed:

```bash
# Check events count
python check_deployment.py

# Or check directly
curl https://oxfordevents.onrender.com/api/events | python -m json.tool | grep -i "ole miss athletics"
```

## Notes

- Cache is per-process (in-memory), so it clears on service restart
- Each Render worker has its own cache instance
- Cache helps reduce load on external APIs and scrapers

