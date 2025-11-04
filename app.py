"""
Flask application for Oxford Events
"""

from flask import Flask, render_template, jsonify, url_for
from flask_caching import Cache
from datetime import datetime, timedelta, date
import json
import os
from lib.event_scraper import collect_all_events
from utils.image_processing import detect_sports_teams, create_team_matchup_image

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# Initialize database on startup (using flag to run only once)
_db_initialized = False

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
            
            # Initialize database (SQLite - always free, no PostgreSQL)
            from lib.database import init_database, migrate_json_to_db
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

# Event sources
EVENT_SOURCES = [
    # Ole Miss Athletics Direct Schedule Sources (HTML-based scraper, no Selenium needed)
    {"name": "Ole Miss Football Schedule", "type": "olemiss", "url": "https://olemisssports.com/sports/football/schedule", "sport_type": "football", "group": "University"},
    {"name": "Ole Miss Men's Basketball Schedule", "type": "olemiss", "url": "https://olemisssports.com/sports/mens-basketball/schedule", "sport_type": "basketball", "group": "University"},
    {"name": "Ole Miss Women's Basketball Schedule", "type": "olemiss", "url": "https://olemisssports.com/sports/womens-basketball/schedule", "sport_type": "basketball", "group": "University"},
    {"name": "Ole Miss Baseball Schedule", "type": "olemiss", "url": "https://olemisssports.com/sports/baseball/schedule", "sport_type": "baseball", "group": "University"},
    {"name": "Ole Miss Softball Schedule", "type": "olemiss", "url": "https://olemisssports.com/sports/softball/schedule", "sport_type": "softball", "group": "University"},
    {"name": "Ole Miss Women's Volleyball Schedule", "type": "olemiss", "url": "https://olemisssports.com/sports/womens-volleyball/schedule", "sport_type": "volleyball", "group": "University"},
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
    try:
        # Try to fetch real events
        events = collect_all_events(EVENT_SOURCES)
        
        # If no events found, return mock data
        if not events:
            today = date.today()
            events = [
                {
                    "title": "Ole Miss Football vs Alabama",
                    "start_iso": (today + timedelta(days=7)).isoformat(),
                    "location": "Vaught-Hemingway Stadium",
                    "cost": "Free",
                    "category": "Sports",
                    "source": "Ole Miss Athletics",
                    "link": "https://olemisssports.com",
                    "description": "Rebels take on the Crimson Tide in a SEC matchup."
                },
                {
                    "title": "Square Books Author Reading",
                    "start_iso": (today + timedelta(days=3)).isoformat(),
                    "location": "Square Books",
                    "cost": "Free",
                    "category": "Arts & Culture",
                    "source": "Visit Oxford",
                    "link": "https://squarebooks.com",
                    "description": "Join us for an evening with bestselling author discussing their latest work."
                },
                {
                    "title": "Proud Larry's Live Music",
                    "start_iso": (today + timedelta(days=5)).isoformat(),
                    "location": "Proud Larry's",
                    "cost": "$10",
                    "category": "Music",
                    "source": "SeatGeek",
                    "link": "https://proudlarrys.com",
                    "description": "Local band performing original songs and covers."
                },
                {
                    "title": "Ole Miss Basketball vs Arkansas",
                    "start_iso": (today + timedelta(days=2)).isoformat(),
                    "location": "The Pavilion",
                    "cost": "$15",
                    "category": "Sports",
                    "source": "Ole Miss Athletics",
                    "link": "https://olemisssports.com",
                    "description": "Men's basketball game against Arkansas."
                },
                {
                    "title": "Oxford Farmers Market",
                    "start_iso": (today + timedelta(days=1)).isoformat(),
                    "location": "Oxford Square",
                    "cost": "Free",
                    "category": "Community",
                    "source": "Visit Oxford",
                    "link": "https://visitoxfordms.com",
                    "description": "Weekly farmers market with local produce, crafts, and food."
                },
                {
                    "title": "The Lyric Oxford - Concert",
                    "start_iso": (today + timedelta(days=10)).isoformat(),
                    "location": "The Lyric Oxford",
                    "cost": "$25",
                    "category": "Music",
                    "source": "Ticketmaster",
                    "link": "https://www.thelyricoxford.com",
                    "description": "Live concert featuring local and touring artists."
                }
            ]
    except Exception as e:
        print(f"Error loading events: {e}")
        # Fallback to mock data
        today = date.today()
        events = [{
            "title": "Error Loading Events",
            "start_iso": today.isoformat(),
            "location": "Oxford, MS",
            "cost": "Free",
            "category": "Community",
            "source": "System",
            "link": "#",
            "description": "Unable to load events at this time."
        }]
    
    return events


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
    
    # Get unique categories
    categories = sorted(set(event['category'] for event in events))
    
    return render_template('index.html', 
                         events=events,
                         categories=categories,
                         total_events=len(events),
                         num_sources=len(EVENT_SOURCES))


@app.route('/api/events')
def api_events():
    """API endpoint for events"""
    events = load_events()
    return jsonify(events)


@app.route('/api/status')
def api_status():
    """API endpoint for loading status"""
    try:
        from lib.status_tracker import get_status
        status = get_status()
        return jsonify(status)
    except Exception:
        return jsonify({"status": "unknown", "step": 0, "total_steps": 0, "message": "Status unavailable", "details": ""})


@app.route('/api/clear-cache')
def clear_cache():
    """Clear the events cache - useful for testing"""
    try:
        cache.clear()
        return jsonify({"status": "success", "message": "Cache cleared successfully"})
    except Exception as e:
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
                matchup_img, error = create_team_matchup_image(away, home)
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

