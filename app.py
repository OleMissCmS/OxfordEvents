"""
Flask application for Oxford Events
"""

from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta, date
import json
import os
from lib.event_scraper import collect_all_events
from utils.image_processing import detect_sports_teams, create_team_matchup_image

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

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
    # Ole Miss Events
    {"name": "Ole Miss Events", "type": "rss", "url": "https://eventcalendar.olemiss.edu/calendar.xml", "group": "University"},
    # Community
    {"name": "Visit Oxford", "type": "html", "url": "https://visitoxfordms.com/events/", "parser": "simple_list", "group": "Community"},
    {"name": "SeatGeek", "type": "api", "parser": "seatgeek", "city": "Oxford", "state": "MS", "group": "Community"},
    {"name": "Ticketmaster", "type": "api", "parser": "ticketmaster", "city": "Oxford", "stateCode": "MS", "group": "Community"},
]


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

