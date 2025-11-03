# Google Custom Search API Setup Guide

This guide will help you set up Google Custom Search API for better image fetching.

## Why Use Google Custom Search API?

- **More Reliable**: Official API instead of web scraping
- **Better Results**: Higher quality image results
- **Rate Limits**: 100 free queries/day, $5 per 1,000 after that
- **No Blocking**: Won't get blocked by Google's anti-scraping measures

## Setup Steps

### 1. Create a Programmable Search Engine (PSE)

1. Go to [Programmable Search Engine Control Panel](https://programmablesearchengine.google.com/controlpanel/all)
2. Click **"Add"** to create a new search engine
3. In **"Sites to search"**, you have two options:
   - **Option A (Recommended)**: Enter `*` to search the entire web
   - **Option B**: Enter specific sites like `wikipedia.org`, `espn.com`, etc.
4. Give it a name like "Oxford Events Image Search"
5. Click **"Create"**
6. **Important**: Copy your **Search Engine ID** (also called `cx`). It looks like: `017576662512468239146:omuauf_lfve`

### 2. Enable Custom Search API in Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Create or Select a Project**:
   - If you don't have one, click "Select a project" → "New Project"
   - Name it (e.g., "Oxford Events") and create it
3. **Enable the API**:
   - Go to **APIs & Services** → **Library**
   - Search for "Custom Search API"
   - Click on it and press **"Enable"**
4. **Create API Key**:
   - Go to **APIs & Services** → **Credentials**
   - Click **"Create Credentials"** → **"API Key"**
   - Copy the API key (looks like: `AIzaSyD...`)
   - **Optional but Recommended**: Click "Restrict key" to:
     - Restrict to "Custom Search API" only
     - Add HTTP referrer restrictions if deploying to a specific domain

### 3. Configure Environment Variables

#### For Local Development:

Create a `.env` file in your project root (or add to existing one):

```env
GOOGLE_CUSTOM_SEARCH_API_KEY=your_api_key_here
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id_here
```

#### For Render.com Deployment:

1. Go to your Render dashboard
2. Select your service
3. Go to **Environment** tab
4. Add two environment variables:
   - `GOOGLE_CUSTOM_SEARCH_API_KEY` = `your_api_key_here`
   - `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` = `your_search_engine_id_here`
5. Save changes (service will redeploy)

### 4. Test the Setup

The code will automatically use the API if these environment variables are set. If not configured, it will fall back to web scraping (less reliable).

## Usage Limits

- **Free Tier**: 100 queries per day
- **Paid**: $5 per 1,000 queries, up to 10,000 queries per day
- **Note**: Image fetching is cached locally, so you won't hit the API for the same venue repeatedly

## Troubleshooting

### "API key not valid" error
- Make sure you copied the full API key
- Check that Custom Search API is enabled in Google Cloud Console
- Verify the API key isn't restricted to wrong IPs/referrers

### "Search engine ID not found" error
- Double-check you copied the full Search Engine ID (cx)
- Make sure the search engine is active in the Control Panel

### "Quota exceeded" error
- You've used your 100 free daily queries
- Wait until the next day or enable billing for more queries
- Consider optimizing: images are cached, so this should be rare

## Cost Optimization Tips

1. **Cache Images**: The system caches images locally, so each venue/team logo is only fetched once
2. **Wikipedia First**: The code tries Wikipedia first (free), then Google API
3. **Rate Limiting**: The code has built-in delays to avoid hitting rate limits

## Security Best Practices

1. **Restrict API Key**: 
   - Limit to "Custom Search API" only
   - Add HTTP referrer restrictions if you have a specific domain
   - Don't commit API keys to git (use `.env` file or environment variables)

2. **Monitor Usage**:
   - Check Google Cloud Console → APIs & Services → Dashboard
   - Set up billing alerts if needed

## Fallback Behavior

If the API key is not configured, the system will:
1. Try Wikipedia first (always free)
2. Fall back to web scraping Google Images (less reliable, may be blocked)

The API is **recommended but optional** - the system works without it, just less reliably.

