# OxfordEvents - Technical Architecture Overview

## Technology Stack

### Backend (Primary - Deployed)
- **Language**: Python 3.13
- **Web Framework**: Flask 3.0+
- **WSGI Server**: Gunicorn (2 workers, 120s timeout)
- **Database ORM**: SQLAlchemy 2.0+
- **Database**: PostgreSQL (production on Render) with SQLite fallback (local dev)
- **Caching**: Flask-Caching (in-memory cache for events)
- **Security**: Flask-WTF (CSRF protection), Flask-Limiter (rate limiting)
- **Authentication**: Session-based admin authentication with password hashing

### Frontend (Deployed)
- **Rendering**: Server-side rendering with Jinja2 templates
- **HTML/CSS**: Custom CSS with Oxford/Ole Miss branding
- **JavaScript**: Vanilla JS for filtering, search, and interactivity
- **Styling**: Custom CSS with CSS variables for theming (light/dark mode)

### Frontend (Alternative - Not Currently Deployed)
- **Framework**: React 18.3.1
- **Styling**: Tailwind CSS 3.4+
- **Build Tool**: Create React App (react-scripts)
- **HTTP Client**: Axios

### Backend (Alternative - Not Currently Deployed)
- **Language**: Node.js
- **Framework**: Express.js
- **Purpose**: Image enrichment API (Unsplash, Pexels, Ticketmaster, SeatGeek, Bandsintown)

## Architecture Pattern

**Server-Side Rendered (SSR) Flask Application**
- Flask serves HTML templates directly (no separate frontend build step)
- All event data is fetched server-side and rendered into HTML
- JavaScript handles client-side filtering/search without API calls
- Static assets (CSS, JS, images) served from `/static` directory

## Data Flow

### 1. Event Collection (Server-Side)
```
Sources (YAML config) → Event Scrapers → Event Aggregator → Cache → Database
```

**Event Sources** (`data/sources.yaml`):
- HTML scrapers: Visit Oxford, Chamber of Commerce, local venues
- ICS calendar feeds: University calendars
- RSS feeds: News sites, event listings
- API integrations: SeatGeek, Ticketmaster, Bandsintown

**Scraping Process** (`lib/event_scraper.py`):
- `collect_all_events()` reads `sources.yaml`
- Each source type has a parser (HTML, ICS, RSS, API)
- Events are normalized to common schema:
  ```python
  {
    "title": str,
    "start_iso": str (ISO datetime),
    "location": str,
    "description": str,
    "category": str,
    "source": str,
    "link": str,
    "cost": str,
    "info_url": str (optional)
  }
  ```

**Categorization** (`lib/categorizer.py`):
- AI-powered categorization based on title/description keywords
- Categories: Community, Arts & Culture, Music, Performance, Sports, Ole Miss Athletics, Education, University

### 2. Event Aggregation (`lib/aggregator.py`)
- Deduplicates events (same title + date + location)
- Filters events to next 3 weeks (configurable)
- Sorts by date
- Returns list of event dictionaries

### 3. Caching Strategy
- **Flask-Caching**: In-memory cache with 2-hour TTL
- Cache key: `events_list`
- Cache cleared on admin actions (image reset, etc.)
- Events fetched fresh on cache miss

### 4. Database Storage (SQLAlchemy)
**Tables** (`lib/database.py`):
- `team_logos`: NCAA team logo URLs (ESPN CDN, Wikipedia)
- `venue_images`: Venue image URLs (Wikipedia, Pexels, Google Images)
- `image_cache`: Generated sports matchup images (base64 or file paths)
- `event_images`: Links events to their images (sports, venue, category, custom)
- `submitted_events`: User-submitted events awaiting moderation

**Database Connection**:
- Production: PostgreSQL via `DATABASE_URL` environment variable
- Local: SQLite at `data/oxford_events.db`
- Auto-initialization on first run

### 5. Image Processing Pipeline

**Image Sources** (priority order):
1. **Sports Matchup Images** (`utils/image_processing.py`):
   - Detects team names from event titles (e.g., "Alabama vs Ole Miss")
   - Generates matchup graphics with team logos
   - Uses ESPN CDN for NCAA team logos
   - Cached in `image_cache` table

2. **Source-Provided Images**:
   - Ticketmaster, SeatGeek, Bandsintown provide event images
   - Stored in `event_images` table

3. **Venue Images** (`utils/image_database.py`):
   - Fetches from Wikipedia (first priority)
   - Falls back to Pexels API (if `PEXELS_API_KEY` set)
   - Falls back to Google Images search
   - Cached in `venue_images` table

4. **Category Placeholders** (`utils/placeholder_images.py`):
   - Generated gradient images based on category
   - Fallback if no venue/sports image found

**Image Storage**:
- Persistent disk on Render (`/data/images/cache/`)
- Local: `static/images/cache/`
- Images served via `/static/images/cache/<filename>` route

### 6. Request Flow (User Visits Site)

```
1. User requests "/"
   ↓
2. Flask route handler (`app.py` @app.route('/'))
   ↓
3. Check cache for events
   ↓
4. If cache miss:
   - Call collect_all_events()
   - Scrape all sources
   - Aggregate and deduplicate
   - Store in cache
   ↓
5. Render template (templates/index.html)
   - Pass events list to Jinja2
   - Template loops through events
   - For each event:
     * Check for matchup data (sports events)
     * Check for venue image
     * Check for category placeholder
     * Render appropriate image
   ↓
6. Return HTML with embedded event data
   ↓
7. Client-side JS filters/search without API calls
```

## Key Components

### Flask Application (`app.py`)
- **Routes**:
  - `/`: Main events page (renders `index.html`)
  - `/api/events`: JSON API endpoint (optional, for React frontend)
  - `/api/admin/*`: Admin endpoints (login, dashboard, cache clear, image reset)
  - `/submit-event`: User event submission form
  - `/static/images/cache/<filename>`: Serve cached images
  - `/api/sports-image/<title>`: Generate sports matchup images on-demand

- **Middleware**:
  - CSRF protection (Flask-WTF)
  - Rate limiting (Flask-Limiter)
  - Security headers (CSP, XSS protection)
  - Session management (8-hour sessions)

- **Template Context**:
  - Injects sports helper functions into all templates
  - CSRF token helper
  - Custom Jinja2 filters (date formatting, description truncation)

### Event Scrapers (`lib/event_scraper.py`)
- **HTML Scrapers**: BeautifulSoup4 for parsing
- **ICS Parsers**: icalendar library
- **RSS Parsers**: feedparser library
- **API Clients**: requests library for SeatGeek, Ticketmaster, Bandsintown

### Image Processing (`utils/image_processing.py`)
- `detect_sports_teams()`: Regex-based team name extraction
- `create_team_matchup_image()`: Pillow (PIL) for image generation
- Background thread for async image generation (with timeout)

### Sports Helpers (`utils/sports_helpers.py`)
- Team name normalization
- ESPN logo URL mapping (100+ NCAA teams)
- Opponent extraction from event titles
- Template helper functions

## External APIs & Services

### Image APIs
- **Pexels API**: `PEXELS_API_KEY` environment variable
- **Unsplash API**: `UNSPLASH_ACCESS_KEY` (used by Node.js backend, not Flask)
- **ESPN CDN**: Public team logos (no API key needed)

### Event APIs
- **SeatGeek API**: `SEATGEEK_API_KEY` environment variable
- **Ticketmaster API**: `TICKETMASTER_API_KEY` environment variable
- **Bandsintown API**: Public API (no key needed)

### Search APIs
- **DuckDuckGo Search**: Public (rate-limited)
- **Google Images**: Web scraping (fallback)

## Deployment (Render.com)

### Configuration
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --timeout 120 --workers 2 --preload`
- **Environment**: Python 3
- **Instance Type**: Free tier (can upgrade)

### Environment Variables
- `FLASK_SECRET_KEY`: Session encryption
- `ADMIN_USERNAME`: Admin login username
- `ADMIN_PASSWORD_HASH`: Hashed admin password (or `ADMIN_PASSWORD` for auto-hash)
- `DATABASE_URL`: PostgreSQL connection string
- `PEXELS_API_KEY`: Pexels image API
- `SEATGEEK_API_KEY`: SeatGeek events API
- `TICKETMASTER_API_KEY`: Ticketmaster events API
- `RATE_LIMIT_STORAGE_URI`: Redis URI (optional, defaults to memory)

### Persistent Storage
- Render Persistent Disk mounted at `/data`
- Images cached at `/data/images/cache/`
- Database at `/data/oxford_events.db` (SQLite) or PostgreSQL (external)

## Data Models

### Event Schema
```python
{
    "title": str,              # Event name
    "start_iso": str,          # ISO 8601 datetime
    "location": str,           # Venue/location name
    "description": str,        # Event description
    "category": str,           # Categorized type
    "source": str,             # Source name (e.g., "SeatGeek")
    "link": str,               # Source URL
    "cost": str,               # Price or "Free"
    "info_url": str (optional) # Additional info URL
}
```

### Database Models (SQLAlchemy)
- `TeamLogo`: team_name (PK), logo_urls (JSON), source, timestamps
- `VenueImage`: venue_name (PK), image_url, source, timestamps
- `EventImage`: event_hash (PK), event_title, event_date, event_location, image_url, image_type, timestamps
- `ImageCache`: cache_key (PK), image_data, content_type, expires_at
- `SubmittedEvent`: id (PK), title, start_datetime, location, categories, cost, description, status, timestamps

## Client-Side JavaScript (`static/js/main.js`)

**No API Calls** - All filtering happens client-side:
- Events embedded in HTML as data attributes
- JavaScript reads DOM, filters in-memory
- Search, category filters, date filters all client-side
- Modal popups for event details
- Dark mode toggle (localStorage)
- Favorite events (localStorage)

## Development vs Production

### Local Development
- SQLite database (`data/oxford_events.db`)
- Flask development server (`python app.py`)
- No persistent disk (uses `static/images/cache/`)
- Environment variables from `.env` or system

### Production (Render)
- PostgreSQL database
- Gunicorn WSGI server
- Persistent disk for images
- Environment variables in Render dashboard
- Auto-deploy on Git push to `main` branch

## File Structure

```
OxfordEvents/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── Procfile                  # Render deployment config
├── runtime.txt               # Python version
├── lib/                      # Core business logic
│   ├── event_scraper.py      # Event collection from sources
│   ├── aggregator.py         # Event deduplication/filtering
│   ├── categorizer.py        # AI categorization
│   ├── database.py           # SQLAlchemy models
│   └── olemiss_athletics_scraper.py  # Special athletics scraper
├── utils/                    # Utility functions
│   ├── image_processing.py   # Sports matchup image generation
│   ├── image_database.py     # Image fetching/caching
│   ├── sports_helpers.py     # Sports event helpers
│   └── storage.py           # Persistent disk helpers
├── templates/                # Jinja2 HTML templates
│   ├── index.html            # Main events page
│   ├── submit_event.html     # Event submission form
│   └── admin_*.html          # Admin dashboard pages
├── static/                   # Static assets
│   ├── css/style.css         # Main stylesheet
│   ├── js/main.js            # Client-side JavaScript
│   └── images/               # Static images
├── data/                     # Data files
│   ├── sources.yaml          # Event source configuration
│   └── oxford_events.db      # SQLite database (local)
├── frontend/                 # React frontend (not deployed)
│   └── src/                  # React components
└── backend/                  # Node.js backend (not deployed)
    └── server.js              # Express image enrichment API
```

## Key Design Decisions

1. **Server-Side Rendering**: Faster initial load, SEO-friendly, simpler deployment
2. **In-Memory Caching**: Fast response times, cleared on admin actions
3. **Client-Side Filtering**: No API calls needed, instant filtering
4. **SQLAlchemy ORM**: Database-agnostic (PostgreSQL/SQLite)
5. **Persistent Disk**: Images survive deployments on Render
6. **Modular Scrapers**: Easy to add new event sources via YAML config
7. **Image Priority**: Sports > Source-provided > Venue > Category placeholder

## Security Features

- CSRF protection on all forms
- Rate limiting on admin endpoints
- Password hashing (scrypt)
- Session-based authentication
- Security headers (CSP, XSS protection)
- SQL injection protection (SQLAlchemy parameterized queries)
- Input validation on user submissions

