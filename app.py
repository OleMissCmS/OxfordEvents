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
def truncate_description(value, max_words=100):
    """Truncate description to max_words"""
    if not value:
        return ""
    words = value.split()
    if len(words) <= max_words:
        return value
    return " ".join(words[:max_words]) + "..."

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
    
    params = {
        'action': 'TEMPLATE',
        'text': event['title'],
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
    # Ole Miss Athletics
    {"name": "Ole Miss Football", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=football", "group": "University"},
    {"name": "Ole Miss MBB", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=mbball", "group": "University"},
    {"name": "Ole Miss WBB", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=wbball", "group": "University"},
    {"name": "Ole Miss Baseball", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=baseball", "group": "University"},
    {"name": "Ole Miss Softball", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=softball", "group": "University"},
    {"name": "Ole Miss Track", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=track", "group": "University"},
    {"name": "Ole Miss Soccer", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=soccer", "group": "University"},
    {"name": "Ole Miss Volleyball", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=volleyball", "group": "University"},
    {"name": "Ole Miss Tennis", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=tennis", "group": "University"},
    # ESPN Ole Miss Athletics (Selenium-based with HTML fallback, always most recent year)
    {"name": "ESPN Ole Miss Football", "type": "espn", "url": "https://www.espn.com/college-football/team/schedule/_/id/145/ole-miss-rebels", "sport_type": "football", "group": "University"},
    {"name": "ESPN Ole Miss MBB", "type": "espn", "url": "https://www.espn.com/mens-college-basketball/team/schedule/_/id/145", "sport_type": "basketball", "group": "University"},
    {"name": "ESPN Ole Miss WBB", "type": "espn", "url": "https://www.espn.com/womens-college-basketball/team/schedule/_/id/145/ole-miss-rebels", "sport_type": "basketball", "group": "University"},
    # Ole Miss Events
    {"name": "Ole Miss Events", "type": "rss", "url": "https://eventcalendar.olemiss.edu/calendar.xml", "group": "University"},
    # Community
    {"name": "Visit Oxford", "type": "html", "url": "https://visitoxfordms.com/events/", "parser": "visit_oxford", "group": "Community"},
    {"name": "Bandsintown", "type": "html", "url": "https://www.bandsintown.com/c/oxford-ms", "parser": "bandsintown", "group": "Community"},
    {"name": "SeatGeek", "type": "api", "parser": "seatgeek", "city": "Oxford", "state": "MS", "group": "Community"},
    {"name": "Ticketmaster", "type": "api", "parser": "ticketmaster", "city": "Oxford", "stateCode": "MS", "group": "Community"},
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
    events = load_events()
    
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
    """Generate sports matchup image"""
    try:
        teams = detect_sports_teams(title)
        if teams:
            away, home = teams
            matchup_img, error = create_team_matchup_image(away, home)
            if matchup_img:
                from flask import send_file
                return send_file(matchup_img, mimetype='image/png')
    except:
        pass
    
    # Return placeholder if no matchup image
    from flask import send_from_directory
    return send_from_directory('static/images', 'placeholder.svg')


@app.route('/api/category-image/<category>/<path:title>')
def category_image(category, title):
    """Generate smart category placeholder image"""
    from utils.smart_image_generator import generate_category_image
    from utils.image_processing import search_location_image
    from flask import send_file, request
    
    # Try to get location image first
    location = request.args.get('location', '')
    if location:
        location_img = search_location_image(location)
        if location_img:
            # Redirect to location image
            from flask import redirect
            return redirect(location_img)
    
    # Try to generate category-specific image
    try:
        img_buffer, error = generate_category_image(category, title)
        if img_buffer:
            return send_file(img_buffer, mimetype='image/png')
    except:
        pass
    
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
    
    # Generate ICS content
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Oxford Events//Event Calendar//EN
BEGIN:VEVENT
DTSTART:{dt.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{event['title']}
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

