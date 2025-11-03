# PostgreSQL Setup on Render.com

This guide will help you set up PostgreSQL for persistent image storage.

## Why PostgreSQL?

- ✅ **Persistent Storage**: Data survives redeploys (unlike filesystem)
- ✅ **Fast Queries**: Much faster than reading JSON files
- ✅ **Scalable**: Handles growth better
- ✅ **Free Tier**: 90 days free on Render

## Step 1: Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `oxford-events-db`
   - **Database**: `oxfordevents` (or leave default)
   - **User**: (auto-generated)
   - **Region**: Same region as your web service
   - **PostgreSQL Version**: 15 (or latest)
   - **Instance Type**: **Free** ($0/month)
4. Click **"Create Database"**

## Step 2: Connect Database to Web Service

Once the database is created:

1. Go to your **Web Service** (`oxford-events`)
2. Click **"Environment"** tab
3. Click **"Link Database"**
4. Select your `oxford-events-db` PostgreSQL instance
5. Click **"Link"**

This automatically sets the `DATABASE_URL` environment variable!

## Step 3: Verify Connection

The `DATABASE_URL` environment variable will be automatically set. It looks like:
```
postgres://user:password@dpg-xxxxx-a/oxfordevents
```

**Important**: The code automatically converts `postgres://` to `postgresql://` for SQLAlchemy compatibility.

## Step 4: Deploy

After linking the database:

1. Render will automatically redeploy your web service
2. On first request, the database tables will be created automatically
3. Existing JSON data (if any) will be migrated automatically

## Verify It's Working

1. After deployment, check the **Logs** tab in Render
2. You should see:
   ```
   [Database] Tables created/verified
   [Database] Migrated X team logos from JSON
   [Database] Migrated X venue images from JSON
   ```

## What Gets Stored in PostgreSQL?

### Tables Created:

1. **team_logos**
   - `team_name` (primary key)
   - `logo_urls` (JSON array of URLs)
   - `source` (wikipedia, espn, etc.)
   - `fetched_at`, `updated_at`

2. **venue_images**
   - `venue_name` (primary key)
   - `image_url`
   - `source` (wikipedia, duckduckgo, etc.)
   - `fetched_at`, `updated_at`

3. **image_cache**
   - `cache_key` (primary key)
   - `image_data` (Base64 or file path)
   - `content_type`
   - `created_at`, `expires_at`

## Fallback Behavior

If PostgreSQL is **not configured**, the app will:
- ✅ Still work using JSON files (current behavior)
- ✅ Print warning: "PostgreSQL not available, using JSON fallback"
- ✅ All functionality remains the same

So you can deploy first, then add PostgreSQL later without breaking anything!

## Free Tier Limits

- **90 days free** on Render
- After that: $7/month for PostgreSQL
- Or: Use JSON fallback (free but slower)

## Troubleshooting

### "Database connection refused"
- Check that database is linked to web service
- Verify `DATABASE_URL` is set in Environment tab

### "Module not found: psycopg2"
- Check `requirements.txt` includes `psycopg2-binary>=2.9.9`
- Redeploy after adding it

### Migration not running
- Normal if no JSON files exist locally
- Migration only runs if `data/*.json` files exist

## Local Development

For local testing without PostgreSQL:

The code automatically uses **SQLite** if `DATABASE_URL` is not set:
- Creates `data/oxford_events.db` locally
- Works exactly like PostgreSQL
- No setup required!

Just run the app locally and it will create the SQLite database automatically.

