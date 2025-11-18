"""
Flask application for Oxford Events
"""

from flask import (
    Flask,
    render_template,
    jsonify,
    url_for,
    request,
    redirect,
    flash,
    session,
)
from flask_caching import Cache
from datetime import datetime, timedelta, date
import os
from typing import Optional, Tuple
from werkzeug.security import check_password_hash, generate_password_hash
import pytz
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from urllib.parse import urlparse, urljoin
import threading

from lib.event_scraper import collect_all_events
from lib.database import (
    init_database,
    migrate_json_to_db,
    get_session as db_get_session,
    SubmittedEvent,
)
from utils.image_processing import detect_sports_teams, create_team_matchup_image

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "change-me")
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
_allow_insecure_cookies = os.environ.get("ALLOW_INSECURE_COOKIES")
app.config['SESSION_COOKIE_SECURE'] = _allow_insecure_cookies not in {"1", "true", "True"}
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['WTF_CSRF_TIME_LIMIT'] = 60 * 60 * 8  # 8 hours

csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=os.environ.get("RATE_LIMIT_STORAGE_URI", "memory://"),
    default_limits=[],
)

@app.context_processor
def inject_csrf_token():
    """Expose CSRF token helper to Jinja templates."""
    return {'csrf_token': generate_csrf}

DEFAULT_ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME") or "CmSCMU"
_env_admin_password_hash = os.environ.get("ADMIN_PASSWORD_HASH")
_env_admin_password = os.environ.get("ADMIN_PASSWORD")
_default_admin_password_hash = (
    "scrypt:32768:8:1$Oay9OOwF6doIKTvD$"
    "f51cbbe1f4e1255867cfc9ec52eff455c9886ef87f8e0994baa9b8f81b598024"
    "e56322155f9a09e6c992716506b5786e3048b8d11defbda9187b39183284c2af"
)

if _env_admin_password_hash:
    ADMIN_PASSWORD_HASH = _env_admin_password_hash
    app.logger.info("Using ADMIN_PASSWORD_HASH from environment for admin authentication.")
elif _env_admin_password:
    ADMIN_PASSWORD_HASH = generate_password_hash(_env_admin_password)
    app.logger.warning(
        "ADMIN_PASSWORD provided; hashed at startup. Prefer supplying ADMIN_PASSWORD_HASH directly."
    )
else:
    ADMIN_PASSWORD_HASH = _default_admin_password_hash
    app.logger.info(
        "Using built-in fallback admin hash. Set ADMIN_PASSWORD_HASH to override this default."
    )

app.config['ADMIN_USERNAME'] = DEFAULT_ADMIN_USERNAME
app.config['ADMIN_PASSWORD_HASH'] = ADMIN_PASSWORD_HASH

# Timezone helpers
CENTRAL_TZ = pytz.timezone("America/Chicago")
UTC = pytz.UTC

# Category options (public + admin)
CATEGORY_CHOICES = [
    "Community",
    "Arts & Culture",
    "Music",
    "Performance",
    "Sports",
    "Ole Miss Athletics",
    "Turner Center",
    "Education",
    "University",
    "Ticketmaster",
    "SeatGeek",
    "Bandsintown",
    "Religious",
]

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# Initialize database on startup (using flag to run only once)
_db_initialized = False

_cache_warm_lock = threading.Lock()
_cache_warm_active = False


def warm_events_cache_async(force: bool = False):
    """Warm the cached events list in a background thread to reduce perceived latency."""
    global _cache_warm_active
    if not force and cache.get('all_events'):
        return

    with _cache_warm_lock:
        if _cache_warm_active:
            return
        _cache_warm_active = True

    def _warm():
        try:
            load_events()
        except Exception as exc:
            app.logger.warning("Background cache warm failed: %s", exc)
        finally:
            global _cache_warm_active
            with _cache_warm_lock:
                _cache_warm_active = False

    threading.Thread(target=_warm, daemon=True).start()

@app.before_request
def init_app():
    """Initialize database on first request"""
    global _db_initialized
    if not _db_initialized:
        try:
            # Log storage setup
            try:
                from utils.storage import log_storage_setup
                log_storage_setup()
            except Exception:
                pass

            init_database()

            # Try to migrate JSON data once (if any exists)
            try:
                migrate_json_to_db()
            except Exception as e:
                print(f"[Database] Migration skipped or failed: {e}")

            _db_initialized = True
        except Exception as e:
            print(f"[Database] Database initialization skipped (using JSON fallback): {e}")
            _db_initialized = True  # Mark as initialized even if failed


@app.after_request
def add_security_headers(response):
    """Inject HTTP security headers on every response."""
    response.headers.setdefault(
        'Strict-Transport-Security',
        'max-age=63072000; includeSubDomains; preload',
    )
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', "geolocation=(), microphone=(), camera=()")

    csp = os.environ.get("CONTENT_SECURITY_POLICY")
    if not csp:
        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'"
        )
    response.headers.setdefault('Content-Security-Policy', csp)
    return response


# Custom Jinja2 filters
@app.template_filter('format_datetime')
def format_datetime(value):
    """Format ISO datetime to readable format like 'Nov 3, 2025 7pm'"""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        # Format: "Nov 3, 2025 7:00 PM" - Windows compatible
        formatted = dt.strftime("%b %d, %Y %I:%M %p").replace(" 0", " ").replace(":00", "")
        return formatted
    except:
        try:
            # Try parsing with dateutil if ISO fails
            from dateutil import parser as dtp
            dt = dtp.parse(value)
            formatted = dt.strftime("%b %d, %Y %I:%M %p").replace(" 0", " ").replace(":00", "")
            return formatted
        except:
            return value

@app.template_filter('truncate_description')
def truncate_description(value, max_words=50):
    """Truncate description to max_words (default 50)"""
    if not value:
        return ""
    words = value.split()
    if len(words) <= max_words:
        return value
    return " ".join(words[:max_words]) + "..."


@app.context_processor
def inject_sports_helpers():
    """Inject sports helper functions into all templates"""
    from utils.sports_helpers import (
        is_sports_event,
        get_opponent_from_event,
        get_team_logo_url,
        get_matchup_data
    )
    return {
        'is_sports_event': is_sports_event,
        'get_opponent_from_event': get_opponent_from_event,
        'get_team_logo_url': get_team_logo_url,
        'get_matchup_data': get_matchup_data,
    }

def clean_calendar_title(title):
    """Remove date patterns from event title for calendar invites"""
    import re
    # Remove common date patterns that might be in titles
    # Patterns like "Nov 3 - ", "11/3 - ", "2025-11-03 - ", etc.
    title = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*[-–—]\s*', '', title)  # Date - prefix
    title = re.sub(r'\d{4}-\d{2}-\d{2}\s*[-–—]\s*', '', title)  # ISO date - prefix
    title = re.sub(r'[A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4}\s*[-–—]\s*', '', title)  # "Nov 3, 2025 - " prefix
    title = re.sub(r'[A-Z][a-z]{2}\s+\d{1,2}\s*[-–—]\s*', '', title)  # "Nov 3 - " prefix
    title = re.sub(r'\s*[-–—]\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', '', title)  # - Date suffix
    title = re.sub(r'\s*[-–—]\s*\d{4}-\d{2}-\d{2}$', '', title)  # - ISO date suffix
    title = re.sub(r'\s*[-–—]\s*[A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4}$', '', title)  # - "Nov 3, 2025" suffix
    # Clean up any double spaces or leading/trailing dashes
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'^\s*[-–—]\s*', '', title).strip()
    return title

@app.template_filter('google_calendar_link')
def google_calendar_link(event):
    """Generate Google Calendar link for event"""
    try:
        dt = datetime.fromisoformat(event['start_iso'].replace('Z', '+00:00'))
    except:
        try:
            from dateutil import parser as dtp
            dt = dtp.parse(event['start_iso'])
        except:
            return "#"
    
    # Google Calendar format
    start_str = dt.strftime('%Y%m%dT%H%M%S')
    end_dt = dt + timedelta(hours=2)  # Default 2 hour event
    end_str = end_dt.strftime('%Y%m%dT%H%M%S')
    
    # Use clean title (without dates)
    calendar_title = clean_calendar_title(event['title'])
    
    params = {
        'action': 'TEMPLATE',
        'text': calendar_title,
        'dates': f"{start_str}/{end_str}",
        'details': event.get('description', ''),
        'location': event.get('location', '')
    }
    
    base_url = "https://calendar.google.com/calendar/render"
    query_string = "&".join([f"{k}={v.replace(' ', '+')}" for k, v in params.items()])
    return f"{base_url}?{query_string}"

@app.template_filter('ics_calendar_link')
def ics_calendar_link(event):
    """Generate .ics calendar download link for event"""
    return url_for('generate_ics', title=event['title'])

@app.template_filter('get_event_image_url')
def get_event_image_url(event):
    """Get event image URL - simplified to avoid expensive operations during template rendering"""
    # Ensure event is a dict
    if not isinstance(event, dict):
        return "https://via.placeholder.com/400x250/f8f9fa/6C757D?text=Event"
    
    try:
        # First priority: Use event's existing image field if available
        if event.get('image'):
            img_url = str(event.get('image', '')).strip()
            if img_url and (img_url.startswith('http') or img_url.startswith('/')):
                return img_url
        
        # Second priority: For sports/Ole Miss Athletics, use sports-image endpoint
        category = event.get('category', '')
        if 'Ole Miss Athletics' in category or category == 'Sports':
            title = event.get('title', '')
            if title:
                try:
                    image_url = url_for('sports_image', title=title)
                    params = []
                    if event.get('hash'):
                        params.append(f'hash={event.get("hash")}')
                    if event.get('start_iso'):
                        from urllib.parse import quote
                        params.append(f"date={quote(str(event['start_iso']))}")
                    if event.get('location'):
                        from urllib.parse import quote
                        params.append(f"location={quote(str(event['location']))}")
                    if params:
                        image_url += '?' + '&'.join(params)
                    return image_url
                except Exception:
                    pass
        
        # Third priority: Use placeholder based on category
        category = category or 'Event'
        return f"https://via.placeholder.com/400x250/f8f9fa/6C757D?text={category.replace(' ', '+')}"
    except Exception as e:
        app.logger.error(f"Error in get_event_image_url: {e}")
        return "https://via.placeholder.com/400x250/f8f9fa/6C757D?text=Event"


def normalize_event_dict(event: dict) -> dict:
    """Ensure event dictionaries have consistent keys used by templates."""
    normalized = dict(event)
    link = normalized.get("link") or normalized.get("info_url") or ""
    normalized.setdefault("info_url", link)
    normalized.setdefault("tickets_url", normalized.get("tickets_url", ""))
    normalized.setdefault("cost", normalized.get("cost", "Free") or "Free")
    normalized.setdefault("source", normalized.get("source", ""))
    normalized.setdefault("category", normalized.get("category", "Community"))
    return normalized


def submission_to_event(submission: SubmittedEvent) -> dict:
    """Convert a SubmittedEvent ORM object into the event dict used by templates."""
    start_dt = submission.start_datetime
    if start_dt.tzinfo is None:
        start_dt = UTC.localize(start_dt)
    event = {
        "title": submission.title,
        "start_iso": start_dt.isoformat(),
        "location": submission.location,
        "description": submission.description or "",
        "category": submission.categories,
        "source": "Community Submission",
        "link": submission.info_url or submission.tickets_url or "",
        "info_url": submission.info_url or submission.tickets_url or "",
        "tickets_url": submission.tickets_url or "",
        "cost": submission.cost or "Free",
        "submitted_event_id": submission.id,
    }
    return normalize_event_dict(event)


def is_admin_authenticated() -> bool:
    """Check if the current session is authenticated for admin access."""
    return session.get("admin_logged_in") is True


def _is_safe_redirect_target(target: Optional[str]) -> bool:
    """Ensure redirects stay on the same host to prevent open redirects."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ('http', 'https')
        and ref_url.netloc == test_url.netloc
    )


def _safe_redirect_target(target: Optional[str], fallback_endpoint: str) -> str:
    """Return a safe redirect target or fallback to a known endpoint."""
    if target and _is_safe_redirect_target(target):
        return target
    return url_for(fallback_endpoint)


def refresh_events_cache():
    """Clear the cached events after admin updates."""
    try:
        cache.delete("all_events")
    except Exception:
        pass
    warm_events_cache_async(force=True)


def parse_local_datetime(date_str: Optional[str], time_str: Optional[str], default_time: str = "00:00") -> Optional[datetime]:
    """Parse date/time strings assuming America/Chicago timezone and return UTC datetime."""
    if not date_str:
        return None
    time_component = (time_str or default_time).strip()
    try:
        naive = datetime.strptime(f"{date_str} {time_component}", "%Y-%m-%d %H:%M")
    except ValueError as err:
        raise ValueError("Invalid date or time. Please use the provided pickers.") from err
    local_dt = CENTRAL_TZ.localize(naive)
    return local_dt.astimezone(UTC)


def local_date_time_parts(dt: Optional[datetime]) -> Tuple[str, str]:
    """Return date/time strings (local) for form fields."""
    if not dt:
        return "", ""
    dt_aware = dt if dt.tzinfo else UTC.localize(dt)
    local_dt = dt_aware.astimezone(CENTRAL_TZ)
    return local_dt.strftime("%Y-%m-%d"), local_dt.strftime("%H:%M")


def prepare_submission_for_admin(submission: SubmittedEvent) -> dict:
    """Prepare a submitted event for admin template rendering."""
    start_date, start_time = local_date_time_parts(submission.start_datetime)
    end_date, end_time = local_date_time_parts(submission.end_datetime)
    categories_list = [
        cat.strip() for cat in (submission.categories or "").split(",") if cat.strip()
    ]
    created_date, created_time = local_date_time_parts(submission.created_at)
    return {
        "id": submission.id,
        "title": submission.title,
        "description": submission.description or "",
        "location": submission.location,
        "categories": submission.categories or "",
        "categories_list": categories_list,
        "cost": submission.cost or "Free",
        "info_url": submission.info_url or "",
        "tickets_url": submission.tickets_url or "",
        "contact_email": submission.contact_email or "",
        "status": submission.status,
        "admin_notes": submission.admin_notes or "",
        "start_date": start_date,
        "start_time": start_time,
        "end_date": end_date,
        "end_time": end_time,
        "created_date": created_date,
        "created_time": created_time,
    }


def get_submission_summary() -> dict:
    """Return counts of submissions by status."""
    session = db_get_session()
    try:
        pending = session.query(SubmittedEvent).filter(SubmittedEvent.status == "pending").count()
        approved = session.query(SubmittedEvent).filter(SubmittedEvent.status == "approved").count()
        rejected = session.query(SubmittedEvent).filter(SubmittedEvent.status == "rejected").count()
    finally:
        session.close()
    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "total": pending + approved + rejected,
    }


def get_scraper_health_summary() -> dict:
    """Fetch the latest scraper/source metrics."""
    try:
        from lib.event_scraper import get_last_source_metrics

        metrics = get_last_source_metrics()
    except Exception as exc:
        app.logger.warning("Could not load scraper metrics: %s", exc)
        metrics = {}

    sources = []
    for name, data in sorted(metrics.get("sources", {}).items(), key=lambda item: item[0].lower()):
        sources.append({
            "name": name,
            "status": data.get("status", "unknown"),
            "events_total": data.get("events_total", 0),
            "events_last_week": data.get("events_last_week", 0),
            "duration_ms": data.get("duration_ms", 0.0),
            "last_error": data.get("error"),
            "url": data.get("url"),
        })

    return {
        "generated_at": metrics.get("generated_at"),
        "total_events": metrics.get("total_events", 0),
        "sources": sources,
    }


def update_submission_from_form(submission: SubmittedEvent, form, *, include_admin_fields: bool = True):
    """Update a SubmittedEvent instance from form data."""
    title = (form.get("title") or "").strip()
    if not title:
        raise ValueError("Event title is required.")
    submission.title = title

    location = (form.get("location") or "").strip()
    if not location:
        raise ValueError("Event location is required.")
    submission.location = location

    if hasattr(form, "getlist"):
        selected_categories = form.getlist("categories")
    else:
        selected_categories = None

    if selected_categories:
        categories = []
        for cat in selected_categories:
            categories.extend([c.strip() for c in cat.split(',') if c.strip()])
    else:
        categories_raw = form.get("categories", "")
        categories = [cat.strip() for cat in categories_raw.split(",") if cat.strip()]

    if not categories:
        raise ValueError("Select at least one category.")
    submission.categories = ", ".join(dict.fromkeys(categories))  # Preserve order, remove duplicates

    start_dt = parse_local_datetime(form.get("start_date"), form.get("start_time"))
    if not start_dt:
        raise ValueError("Start date is required.")
    submission.start_datetime = start_dt

    end_date_value = form.get("end_date")
    end_time_value = form.get("end_time")
    if end_date_value or end_time_value:
        end_dt = parse_local_datetime(
            end_date_value or form.get("start_date"),
            end_time_value or form.get("start_time") or "00:00",
        )
        submission.end_datetime = end_dt
    else:
        submission.end_datetime = None

    cost = (form.get("cost") or "").strip()
    submission.cost = cost or "Free"

    submission.description = (form.get("description") or "").strip()
    info_url = (form.get("info_url") or "").strip()
    tickets_url = (form.get("tickets_url") or "").strip()
    if info_url and not info_url.lower().startswith(("http://", "https://")):
        raise ValueError("Event details URL must start with http:// or https://.")
    if tickets_url and not tickets_url.lower().startswith(("http://", "https://")):
        raise ValueError("Ticket URL must start with http:// or https://.")
    submission.info_url = info_url or None
    submission.tickets_url = tickets_url or None

    contact_email = (form.get("contact_email") or "").strip()
    if contact_email and "@" not in contact_email:
        raise ValueError("Provide a valid email address.")
    submission.contact_email = contact_email or None

    if include_admin_fields:
        admin_notes = (form.get("admin_notes") or "").strip()
        submission.admin_notes = admin_notes or None


# Event sources
EVENT_SOURCES = [
    # Ole Miss Events
    {"name": "Ole Miss Events", "type": "rss", "url": "https://eventcalendar.olemiss.edu/calendar.xml", "group": "University"},
    # Community
        {"name": "Visit Oxford", "type": "html", "url": "https://visitoxfordms.com/events/", "parser": "visit_oxford", "group": "Community"},
        {"name": "Bandsintown", "type": "html", "url": "https://www.bandsintown.com/c/oxford-ms", "parser": "bandsintown", "group": "Community"},
        {"name": "Ticketmaster", "type": "api", "parser": "ticketmaster", "city": "Oxford", "stateCode": "MS", "group": "Community"},
        {"name": "SeatGeek", "type": "api", "parser": "seatgeek", "lat": 34.3665, "lon": -89.5192, "radius": "25mi", "group": "Community"},
    ]


@cache.cached(timeout=600, key_prefix='all_events')
def load_events():
    """Load events from all sources"""
    normalized_events = []
    try:
        # Try to fetch real events
        events = collect_all_events(EVENT_SOURCES)
        normalized_events = [normalize_event_dict(event) for event in events]
    except Exception as e:
        print(f"Error loading events: {e}")
        normalized_events = []

    # Add approved submitted events
    db_session = None
    try:
        db_session = db_get_session()
        now_utc = datetime.now(UTC)
        cutoff = now_utc + timedelta(days=90)
        submissions = (
            db_session.query(SubmittedEvent)
            .filter(SubmittedEvent.status == "approved")
            .filter(SubmittedEvent.start_datetime >= now_utc - timedelta(days=1))
            .filter(SubmittedEvent.start_datetime <= cutoff)
            .order_by(SubmittedEvent.start_datetime.asc())
            .all()
        )
        for submission in submissions:
            normalized_events.append(submission_to_event(submission))
    except Exception as db_error:
        print(f"[Database] Error loading submitted events: {db_error}")
    finally:
        if db_session is not None:
            db_session.close()

    # Fallback if no events available at all
    if not normalized_events:
        today = date.today()
        fallback_events = [
            {
                "title": "Ole Miss Football vs Alabama",
                "start_iso": (today + timedelta(days=7)).isoformat(),
                "location": "Vaught-Hemingway Stadium",
                "cost": "Free",
                "category": "Sports",
                "source": "Ole Miss Athletics",
                "link": "https://olemisssports.com",
                "description": "Rebels take on the Crimson Tide in a SEC matchup.",
            },
            {
                "title": "Square Books Author Reading",
                "start_iso": (today + timedelta(days=3)).isoformat(),
                "location": "Square Books",
                "cost": "Free",
                "category": "Arts & Culture",
                "source": "Visit Oxford",
                "link": "https://squarebooks.com",
                "description": "Join us for an evening with bestselling author discussing their latest work.",
            },
            {
                "title": "Proud Larry's Live Music",
                "start_iso": (today + timedelta(days=5)).isoformat(),
                "location": "Proud Larry's",
                "cost": "$10",
                "category": "Music",
                "source": "SeatGeek",
                "link": "https://proudlarrys.com",
                "description": "Local band performing original songs and covers.",
            },
            {
                "title": "Oxford Farmers Market",
                "start_iso": (today + timedelta(days=1)).isoformat(),
                "location": "Oxford Square",
                "cost": "Free",
                "category": "Community",
                "source": "Visit Oxford",
                "link": "https://visitoxfordms.com",
                "description": "Weekly farmers market with local produce, crafts, and food.",
            },
        ]
        normalized_events = [normalize_event_dict(event) for event in fallback_events]

    # Ensure events are sorted by start time
    normalized_events.sort(key=lambda e: e.get("start_iso") or "")
    
    return normalized_events


@app.route('/')
def index():
    """Main page"""
    # Start status tracking for page load
    try:
        from lib.status_tracker import set_status
        set_status(0, 1, "Loading events page...", "")
    except Exception:
        pass
    
    events = load_events()
    
    # Clear status after events loaded (but before template render)
    try:
        from lib.status_tracker import clear_status
        clear_status()
    except Exception:
        pass
    
    # Get unique categories - handle comma-separated categories
    all_categories = {"Religious"}  # Ensure Religious pill appears even if no events yet
    for event in events:
        category = event.get('category', 'Other')
        # Split comma-separated categories
        for cat in category.split(','):
            all_categories.add(cat.strip())
    
    # Arrange categories in gradient order (similar colors together)
    # Order: Blues → Teals → Greens → Pinks → Reds/Oranges → Others
    category_order = [
        'University', 'Education',  # Typically blue-ish
        'Ticketmaster',  # Blue #008CFF
        'Bandsintown',  # Teal #00CEC8
        'Community', 'Religious', 'Arts & Culture',  # Typically green-ish
        'Music', 'Performance',  # Typically pink/purple
        'SeatGeek',  # Orange #FF5B49
        'Ole Miss Athletics',  # Red (athletics)
        'Sports',  # Typically red/pink
    ]
    
    # Sort categories: first by predefined order, then alphabetically for others
    ordered_categories = []
    remaining_categories = sorted(all_categories)
    
    for cat in category_order:
        if cat in remaining_categories:
            ordered_categories.append(cat)
            remaining_categories.remove(cat)
    
    # Add any remaining categories alphabetically
    categories = ordered_categories + sorted(remaining_categories)
    
    today_str = date.today().isoformat()
    
    return render_template('index.html', 
                         events=events,
                         categories=categories,
                         total_events=len(events),
                         num_sources=len(EVENT_SOURCES),
                         today=today_str)


@app.route('/submit-event', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def submit_event():
    """Public form for submitting local events."""
    errors = []
    selected_categories = []
    form_defaults = {}

    if request.method == 'GET':
        warm_events_cache_async()

    if request.method == 'POST':
        app.logger.info(
            "Submission attempt from %s for title '%s'",
            request.remote_addr,
            (request.form.get("title") or "").strip(),
        )
        categories_raw = request.form.get('categories', '')
        selected_categories = [cat.strip() for cat in categories_raw.split(',') if cat.strip()]
        form_defaults = request.form.to_dict()
        form_defaults['categories'] = ", ".join(selected_categories)

        db_session = None
        try:
            new_submission = SubmittedEvent(status="pending")
            # Populate fields (without admin-only notes)
            update_submission_from_form(new_submission, request.form, include_admin_fields=False)
            new_submission.submitted_by = (request.form.get("contact_email") or "").strip()

            db_session = db_get_session()
            db_session.add(new_submission)
            db_session.commit()

            app.logger.info(
                "Submission stored with ID %s from %s",
                new_submission.id,
                request.remote_addr,
            )
            flash("Thanks! Your event was submitted for review.", "success")
            warm_events_cache_async()
            return redirect(url_for('submit_event'))
        except ValueError as ve:
            errors.append(str(ve))
        except Exception as exc:
            errors.append("We couldn't save your event. Please try again.")
            app.logger.exception("[submit_event] Error saving submission")
        finally:
            if db_session is not None:
                db_session.close()

    return render_template(
        'submit_event.html',
        categories=CATEGORY_CHOICES,
        errors=errors,
        selected_categories=selected_categories,
        form_defaults=form_defaults,
    )


@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin landing page with scraper health overview."""
    if not is_admin_authenticated():
        return redirect(url_for('admin_login', next=request.path))

    warm_events_cache_async()

    scraper_summary = get_scraper_health_summary()
    submission_summary = get_submission_summary()
    cached_events = cache.get('all_events') or []

    return render_template(
        'admin_dashboard.html',
        scraper_summary=scraper_summary,
        submission_summary=submission_summary,
        cached_events=len(cached_events),
    )


@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def admin_login():
    """Admin login for moderating submissions."""
    if is_admin_authenticated():
        return redirect(url_for('admin_events'))

    if request.method == 'POST':
        username = (request.form.get('username') or "").strip()
        password = request.form.get('password') or ""
        requested_next = request.form.get('next')
        next_url = _safe_redirect_target(requested_next, 'admin_dashboard')

        app.logger.info(
            "Admin login attempt for username=%s from %s",
            username,
            request.remote_addr,
        )

        if username.lower() == app.config['ADMIN_USERNAME'].lower() and check_password_hash(app.config['ADMIN_PASSWORD_HASH'], password):
            session.permanent = True
            session['admin_logged_in'] = True
            app.logger.info(
                "Admin login successful for username=%s from %s",
                username,
                request.remote_addr,
            )
            flash("Signed in successfully.", "success")
            warm_events_cache_async()
            return redirect(next_url)
        else:
            app.logger.warning(
                "Admin login failed for username=%s from %s",
                username,
                request.remote_addr,
            )
            flash("Invalid username or password.", "error")

    next_param = request.args.get('next')
    safe_next = _safe_redirect_target(next_param, 'admin_dashboard')
    return render_template('admin_login.html', next_url=safe_next)


@app.route('/admin/logout')
def admin_logout():
    """Clear admin session."""
    if is_admin_authenticated():
        app.logger.info("Admin logout from %s", request.remote_addr)
    session.pop('admin_logged_in', None)
    flash("Signed out.", "success")
    return redirect(url_for('admin_login'))


@app.route('/admin/events', methods=['GET', 'POST'])
def admin_events():
    """Admin dashboard for reviewing submitted events."""
    if not is_admin_authenticated():
        app.logger.warning(
            "Blocked unauthorized access to admin dashboard from %s",
            request.remote_addr,
        )
        return redirect(url_for('admin_login', next=request.path))

    warm_events_cache_async()

    if request.method == 'POST':
        action = request.form.get('action')
        event_id = request.form.get('event_id')

        if not event_id:
            flash("Missing event identifier.", "error")
            return redirect(url_for('admin_events'))

        try:
            submission_id = int(event_id)
        except ValueError:
            flash("Invalid event identifier.", "error")
            return redirect(url_for('admin_events'))

        db_session = db_get_session()
        submission = db_session.get(SubmittedEvent, submission_id)

        if not submission:
            db_session.close()
            flash("Event submission not found.", "error")
            return redirect(url_for('admin_events'))

        try:
            if action in ('approve', 'update'):
                update_submission_from_form(submission, request.form)
                if action == 'approve':
                    submission.status = 'approved'
                db_session.add(submission)
                message = "Event approved." if action == 'approve' else "Event updated."
            elif action == 'reject':
                submission.status = 'rejected'
                message = "Event rejected."
            elif action == 'delete':
                db_session.delete(submission)
                message = "Submission deleted."
            else:
                message = "No changes applied."

            db_session.commit()

            if action in ('approve', 'update', 'delete'):
                refresh_events_cache()

            app.logger.info(
                "Admin action '%s' applied to submission %s from %s",
                action,
                submission_id,
                request.remote_addr,
            )
            flash(message, "success")
        except ValueError as ve:
            db_session.rollback()
            flash(str(ve), "error")
        except Exception as exc:
            db_session.rollback()
            flash("Unexpected error updating submission.", "error")
            app.logger.exception("Error handling submission %s", event_id)
        finally:
            db_session.close()

        return redirect(url_for('admin_events'))

    # GET request - show submissions
    db_session = db_get_session()
    pending_submissions = (
        db_session.query(SubmittedEvent)
        .filter(SubmittedEvent.status == "pending")
        .order_by(SubmittedEvent.created_at.asc())
        .all()
    )
    approved_submissions = (
        db_session.query(SubmittedEvent)
        .filter(SubmittedEvent.status == "approved")
        .order_by(SubmittedEvent.start_datetime.asc())
        .all()
    )
    rejected_submissions = (
        db_session.query(SubmittedEvent)
        .filter(SubmittedEvent.status == "rejected")
        .order_by(SubmittedEvent.updated_at.desc())
        .limit(10)
        .all()
    )
    db_session.close()

    pending_events = [prepare_submission_for_admin(event) for event in pending_submissions]
    approved_events = [prepare_submission_for_admin(event) for event in approved_submissions]
    rejected_events = [prepare_submission_for_admin(event) for event in rejected_submissions]

    return render_template(
        'admin_events.html',
        pending_events=pending_events,
        approved_events=approved_events,
        rejected_events=rejected_events,
        categories=CATEGORY_CHOICES,
    )


@app.route('/api/events')
def api_events():
    """API endpoint for events"""
    events = load_events()
    return jsonify(events)


@app.route('/api/status')
@limiter.limit("120 per minute")
def api_status():
    """API endpoint for loading status"""
    try:
        from lib.status_tracker import get_status
        status = get_status()
        return jsonify(status)
    except Exception:
        return jsonify({"status": "unknown", "step": 0, "total_steps": 0, "message": "Status unavailable", "details": ""})


@app.route('/api/clear-cache')
@limiter.limit("5 per minute")
def clear_cache():
    """Clear the events cache - useful for testing"""
    try:
        cache.clear()
        return jsonify({"status": "success", "message": "Cache cleared successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@csrf.exempt
@app.route('/api/admin/reset-images', methods=['POST'])
@limiter.limit("10 per hour")
def admin_reset_images():
    """Admin-only endpoint to reset all cached event images"""
    if not is_admin_authenticated():
        app.logger.warning(
            "Blocked unauthorized access to reset-images from %s",
            request.remote_addr,
        )
        return jsonify({"status": "error", "message": "Authentication required"}), 401
    
    try:
        # Import reset function from script
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from scripts.reset_event_images import reset_event_images
        
        deleted_rows, removed_files, images_dir = reset_event_images()
        
        # Also clear the Flask cache to force fresh image generation
        cache.clear()
        
        app.logger.info(
            "Image reset completed: %d rows deleted, %d files removed from %s (admin: %s)",
            deleted_rows,
            removed_files,
            images_dir,
            request.remote_addr,
        )
        
        return jsonify({
            "status": "success",
            "message": "Event images reset successfully",
            "deleted_rows": deleted_rows,
            "removed_files": removed_files,
            "images_dir": images_dir,
        })
    except Exception as e:
        app.logger.error("Error resetting images: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/sports-image/<path:title>')
def sports_image(title):
    """Generate sports matchup image with caching and database storage"""
    import hashlib
    from flask import request
    from lib.database import get_session, EventImage

    # Try to get event hash from query param (for database lookup)
    event_hash = request.args.get('hash')
    date_str = request.args.get('date', '')
    location_str = request.args.get('location', '')

    # Create unique cache key
    cache_key = f'sports_image_{title}'
    cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()

    # Check database first (if event_hash provided)
    if event_hash:
        try:
            session = get_session()
            event_image = session.query(EventImage).filter_by(event_hash=event_hash).first()
            if event_image and event_image.image_url:
                session.close()
                # Redirect to cached image URL
                from flask import redirect
                return redirect(event_image.image_url)
            session.close()
        except Exception:
            pass

    # Check Flask cache
    cached_response = cache.get(cache_key_hash)
    if cached_response:
        from flask import Response
        response = Response(cached_response, mimetype='image/png')
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response

    # Add timeout protection - don't let image generation hang
    import threading
    import queue
    
    def generate_image_with_timeout():
        """Generate image in a thread with timeout protection"""
        try:
            teams = detect_sports_teams(title)
            if teams:
                away, home = teams
                
                # Determine background image for Ole Miss Athletics
                background_image_path = None
                location_lower = (location_str or '').lower()
                title_lower = title.lower()
                
                print(f"[sports-image] Checking venue for: title='{title}', location='{location_str}'")
                
                # Check if this is Ole Miss Athletics and determine venue
                # More flexible matching for venue names
                if "pavilion" in location_lower or "basketball" in title_lower or "mbb" in title_lower or "wbb" in title_lower:
                    background_image_path = os.path.join("static", "images", "fallbacks", "Pavilion.webp")
                    print(f"[sports-image] Detected Pavilion venue, using: {background_image_path}")
                elif "swayze" in location_lower or "baseball" in title_lower:
                    background_image_path = os.path.join("static", "images", "fallbacks", "Swayze.jpg")
                    print(f"[sports-image] Detected Swayze venue, using: {background_image_path}")
                elif "vaught" in location_lower or "hemingway" in location_lower or "football" in title_lower:
                    background_image_path = os.path.join("static", "images", "fallbacks", "Vaught.jpg")
                    print(f"[sports-image] Detected Vaught venue, using: {background_image_path}")
                
                # Try multiple path variations
                if background_image_path:
                    # Try relative path first
                    if not os.path.exists(background_image_path):
                        # Try absolute path from app root
                        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        abs_path = os.path.join(app_root, background_image_path)
                        if os.path.exists(abs_path):
                            background_image_path = abs_path
                            print(f"[sports-image] Found background at absolute path: {abs_path}")
                        else:
                            print(f"[sports-image] WARNING: Background image not found at {background_image_path} or {abs_path}")
                    else:
                        print(f"[sports-image] Found background at relative path: {background_image_path}")
                
                matchup_img, error = create_team_matchup_image(
                    away, 
                    home, 
                    background_image_path=background_image_path,
                    background_opacity=0.6
                )
                result_queue.put(('success', matchup_img, error))
            else:
                result_queue.put(('no_teams', None, None))
        except Exception as e:
            result_queue.put(('error', None, str(e)))
    
    result_queue = queue.Queue()
    timeout_seconds = 8  # Max 8 seconds for image generation
    
    try:
        # Start image generation in thread
        img_thread = threading.Thread(target=generate_image_with_timeout, daemon=True)
        img_thread.start()
        img_thread.join(timeout=timeout_seconds)
        
        # Check if result is available
        try:
            result = result_queue.get_nowait()
            result_type, matchup_img, error = result
            
            if result_type == 'success' and matchup_img:
                # Store in cache
                img_data = matchup_img.getvalue()
                cache.set(cache_key_hash, img_data, timeout=3600)
                
                # Save to database if event_hash provided
                if event_hash:
                    try:
                        session = get_session()
                        event_image = EventImage(
                            event_hash=event_hash,
                            event_title=title,
                            event_date=date_str,
                            event_location=location_str,
                            image_url=f"/api/sports-image/{title}?hash={event_hash}",
                            image_type='sports'
                        )
                        session.merge(event_image)
                        session.commit()
                        session.close()
                    except Exception:
                        pass

                from flask import send_file
                response = send_file(matchup_img, mimetype='image/png')
                response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
                return response
            elif result_type == 'error':
                print(f"Error generating sports image: {error}")
            elif result_type == 'no_teams':
                print(f"No teams detected in title: {title}")
        except queue.Empty:
            # Timeout - image generation took too long
            print(f"Timeout generating sports image for: {title} (>{timeout_seconds}s)")
    except Exception as e:
        print(f"Error in sports image generation: {e}")
    
    # Return placeholder if no matchup image
    from flask import send_from_directory
    return send_from_directory('static/images', 'placeholder.svg')


@app.route('/static/images/cache/<path:filename>')
def serve_cached_image(filename):
    """Serve cached images from persistent disk or static directory"""
    try:
        # Try persistent disk first
        from utils.storage import get_images_dir, is_persistent_disk
        images_dir = get_images_dir()
        
        # Check if file exists
        file_path = os.path.join(images_dir, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            from flask import send_file
            return send_file(file_path)
    except Exception:
        pass
    
    # Fallback to static/images/cache
    try:
        from flask import send_from_directory
        return send_from_directory('static/images/cache', filename)
    except Exception:
        # Ultimate fallback to placeholder
        from flask import send_from_directory
        return send_from_directory('static/images', 'placeholder.svg')


@app.route('/api/category-image/<category>/<path:title>')
def category_image(category, title):
    """Generate smart category placeholder image with caching"""
    from utils.smart_image_generator import generate_category_image
    from utils.image_processing import search_location_image
    from flask import send_file, request
    import hashlib
    
    # Get location for cache key uniqueness
    location = request.args.get('location', '')
    
    # Create unique cache key including location and title
    cache_key = f'category_image_{category}_{title}_{location}'
    cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
    
    # Check cache first
    cached_response = cache.get(cache_key_hash)
    if cached_response:
        from flask import Response
        response = Response(cached_response, mimetype='image/png')
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
    
    # Get event_hash if provided (for event-specific storage)
    event_hash = request.args.get('hash', '')
    
    # Check EventImage database first (fast path - no searching)
    if event_hash:
        try:
            from lib.database import get_session, EventImage
            session = get_session()
            event_image = session.query(EventImage).filter_by(event_hash=event_hash).first()
            if event_image and event_image.image_url:
                image_url = event_image.image_url
                session.close()
                if image_url and image_url.startswith('/'):
                    from flask import redirect
                    return redirect(image_url)
            session.close()
        except Exception:
            pass
    
    # Try to get location image with timeout (don't block page load)
    if location:
        # Quick check: try event-specific storage without expensive searches
        try:
            from utils.image_database import get_event_venue_image
            if event_hash:
                quick_img = get_event_venue_image(event_hash, location)
                if quick_img:
                    from flask import redirect
                    return redirect(quick_img)
        except Exception:
            pass
        
        # Only do expensive search with timeout - limit to 3 seconds max
        try:
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def search_with_timeout():
                try:
                    img = search_location_image(location, event_hash=event_hash)
                    result_queue.put(img)
                except Exception:
                    result_queue.put(None)
            
            # Start search in thread with 3 second timeout
            search_thread = threading.Thread(target=search_with_timeout, daemon=True)
            search_thread.start()
            search_thread.join(timeout=3.0)
            
            # Get result if available, otherwise timeout
            try:
                location_img = result_queue.get_nowait()
            except queue.Empty:
                location_img = None
                print(f"[category_image] Timeout searching for venue image: {location}")
            
            if location_img:
                # Store in EventImage if event_hash provided
                if event_hash:
                    try:
                        from lib.database import get_session, EventImage
                        session = get_session()
                        event_image = session.query(EventImage).filter_by(event_hash=event_hash).first()
                        if event_image:
                            event_image.image_url = location_img
                            event_image.image_type = 'venue'
                            session.merge(event_image)
                            session.commit()
                        session.close()
                    except Exception:
                        pass
                
                # Redirect to location image (these are external, no need to cache)
                from flask import redirect
                return redirect(location_img)
        except Exception as e:
            print(f"[category_image] Error searching for venue image: {e}")
            pass
    
    # Try to generate category-specific image
    try:
        img_buffer, error = generate_category_image(category, title)
        if img_buffer:
            # Store in cache
            img_data = img_buffer.getvalue()
            cache.set(cache_key_hash, img_data, timeout=3600)
            
            response = send_file(img_buffer, mimetype='image/png')
            response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
            return response
    except Exception as e:
        print(f"Error generating category image: {e}")
    
    # Return plain placeholder if category image fails
    from flask import send_from_directory
    return send_from_directory('static/images', 'placeholder.svg')


@app.route('/calendar/<path:title>.ics')
def generate_ics(title):
    """Generate .ics calendar file for an event"""
    from flask import Response
    
    # Find the event
    events = load_events()
    event = next((e for e in events if e['title'] == title), None)
    
    if not event or not event.get('start_iso'):
        return "Event not found", 404
    
    try:
        from dateutil import parser as dtp
        dt = dtp.parse(event['start_iso'])
        end_dt = dt + timedelta(hours=2)  # Default 2 hour duration
    except:
        return "Invalid date", 400
    
    # Clean title for calendar (remove dates)
    calendar_title = clean_calendar_title(event['title'])
    
    # Generate ICS content
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Oxford Events//Event Calendar//EN
BEGIN:VEVENT
DTSTART:{dt.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{calendar_title}
DESCRIPTION:{event.get('description', '')[:100]}
LOCATION:{event.get('location', '')}
URL:{event.get('link', '')}
END:VEVENT
END:VCALENDAR"""
    
    from flask import make_response
    response = make_response(ics_content)
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{title[:50]}.ics"'
    return response


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    """Provide a user-friendly error response for CSRF failures."""
    app.logger.warning(
        "CSRF validation failed on %s from %s: %s",
        request.path,
        request.remote_addr,
        error.description,
    )
    if request.path.startswith('/api/'):
        return jsonify({"status": "error", "message": "CSRF validation failed."}), 400
    flash("Your session expired. Please try submitting the form again.", "error")
    return redirect(request.referrer or url_for('index')), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

