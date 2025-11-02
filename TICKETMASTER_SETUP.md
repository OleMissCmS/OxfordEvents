# How to Add Your Ticketmaster API Key to Render

## Step-by-Step Instructions

### 1. Log into Render.com
Go to https://dashboard.render.com and sign in with your account

### 2. Navigate to Your Web Service
Click on your **oxford-events** web service in the dashboard

### 3. Go to Environment Tab
- In the left sidebar, click **"Environment"**
- This will show you all environment variables for your app

### 4. Add Your API Key
- Click the **"Add Environment Variable"** button
- In the **Key** field, enter: `TICKETMASTER_API_KEY`
- In the **Value** field, paste your Ticketmaster API key
- Click **"Save Changes"**

### 5. Wait for Redeploy
Render will automatically detect the change and redeploy your app. This usually takes 1-2 minutes.

### 6. Verify It's Working
Once deployed, your app will now fetch events from Ticketmaster for Oxford, MS!

## Where to Get Your Ticketmaster API Key

If you don't have a Ticketmaster API key yet:

1. Go to https://developer.ticketmaster.com/
2. Click "Sign Up" or "Log In"
3. Create a new application
4. Copy your API key

## Security Notes

✅ **Your API key is secure** - Render encrypts it at rest  
✅ **Only your app can see it** - not exposed in code or logs  
✅ **Free tier available** - Ticketmaster offers free API access for developers  
✅ **Never commit to Git** - always use environment variables  

## Testing Locally

To test with your API key locally, create a `.env` file in your project:

```
TICKETMASTER_API_KEY=your_api_key_here
```

Then install python-dotenv:
```bash
pip install python-dotenv
```

And in your `app.py`, add at the top:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Troubleshooting

**Q: My Ticketmaster events aren't showing up**  
A: Check the Render logs for error messages. Make sure your API key is correct.

**Q: How do I know if the API key is working?**  
A: Check the app logs in Render dashboard. Look for "No TICKETMASTER_API_KEY found" or successful event fetching.

**Q: Can I use the same API key for multiple apps?**  
A: Yes, but be mindful of rate limits. Ticketmaster free tier has limits.

## Next Steps After Adding Key

Once your API key is added:
1. ✅ Render will auto-redeploy
2. ✅ Your app will fetch Ticketmaster events for Oxford
3. ✅ Events will appear in the "Community" category
4. ✅ All Ticketmaster features will work (prices, links, etc.)

## Need Help?

If you're having issues:
1. Check Render logs in the dashboard
2. Verify your API key is correct on Ticketmaster's developer site
3. Make sure the environment variable name is exactly `TICKETMASTER_API_KEY`

