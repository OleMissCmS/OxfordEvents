# How to Add Environment Variables to Render.com

## Quick Steps to Add Your Ticketmaster API Key

1. **Log into Render.com** at https://dashboard.render.com

2. **Click on your Web Service** (`oxford-events`)

3. **Click on "Environment"** in the left sidebar

4. **Click "Add Environment Variable"**

5. **Add your secret:**
   - **Key:** `TICKETMASTER_API_KEY`
   - **Value:** Paste your Ticketmaster API key here
   - **Click "Save Changes"**

6. **Render will automatically redeploy** your app with the new environment variable

## That's It!

The Flask app will automatically pick up the `TICKETMASTER_API_KEY` from Render's environment variables and use it when fetching Ticketmaster events.

## Security Notes

- ✅ Your API key is securely stored by Render
- ✅ It's only accessible to your application
- ✅ Never commit API keys to Git
- ✅ If you regenerate your key, just update it in Render's Environment tab

## Other Environment Variables You Can Add

You can add any other API keys or configuration here:
- `SEATGEEK_API_KEY` (if you get one)
- `DEBUG` (set to `true` for debugging)
- `PORT` (usually not needed, Render handles this)
- Any other secrets your app needs

## Testing Locally

To test with your API key locally, create a `.env` file in your project root:

```
TICKETMASTER_API_KEY=your_api_key_here
```

Then run:
```bash
pip install python-dotenv
```

And in your `app.py`, add at the top:
```python
from dotenv import load_dotenv
load_dotenv()
```

This way you can test locally without hardcoding your key!

