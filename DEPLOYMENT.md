# Deployment Guide for Render.com

## What We Did

Converted the Oxford Events app from **Streamlit** to **Flask** to solve the JavaScript filter pill styling issue.

## Why the Change?

- **Streamlit Problem**: JavaScript is sandboxed in iframes, preventing custom button styling
- **Flask Solution**: Full control over HTML, CSS, and JavaScript
- **Result**: Beautiful pastel-colored filter pills like Bandsintown!

## Files Created

### Core Flask App
- `app.py` - Main Flask application
- `Procfile` - Tells Render how to run the app
- `runtime.txt` - Specifies Python version

### Frontend Files
- `templates/index.html` - Main HTML template
- `static/css/style.css` - All styling with pastel filter pills
- `static/js/main.js` - JavaScript for filtering
- `static/images/placeholder.svg` - Placeholder images

### Dependencies
- `requirements.txt` - Updated with Flask and Gunicorn (removed Streamlit)

## Render Deployment Settings

When setting up your **Web Service** on Render:

**Name:** `oxford-events`

**Configuration:**
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

**Instance Type:** Free

## Deployment Steps

1. **Push to GitHub** ✅ (Already done)
2. **Connect to Render**: In your Render dashboard, click "New Web Service"
3. **Select Repository**: Choose `OxfordEvents` from GitHub
4. **Configure**:
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Instance: Free
5. **Deploy**: Click "Create Web Service"
6. **Wait**: Render will automatically build and deploy

## What You'll Get

- ✅ Beautiful pastel filter pills (blue, purple, orange, green, pink)
- ✅ Fully functional JavaScript filtering and search
- ✅ Clean Bandsintown-inspired design
- ✅ All 6 mock events displaying properly
- ✅ No iframe sandboxing limitations!

## Troubleshooting

### Status 127 Error
This usually means Gunicorn isn't installed. Check that `requirements.txt` includes `gunicorn>=21.2.0`.

### Build Fails
Make sure `Procfile` exists with: `web: gunicorn app:app`

### App Not Loading
Check Render logs in the dashboard to see Python errors.

## Next Steps (After Deployment)

Once the basic Flask app is working:

1. **Add Real Event Scraping**: Integrate your existing event aggregation logic
2. **Sports Logos**: Add the team matchup image generation
3. **Google Calendar**: Implement calendar download feature
4. **Caching**: Add Redis or similar for event caching

## Local Testing (Optional)

To test locally before deploying:

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install Flask and Gunicorn
pip install flask gunicorn

# Run the app
python app.py

# Or with Flask CLI
flask --app app run

# Or with Gunicorn
gunicorn app:app
```

Then visit: http://localhost:5000

