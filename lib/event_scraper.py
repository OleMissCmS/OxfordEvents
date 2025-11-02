"""
Event scraping utilities for fetching from multiple sources
"""

import io
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dateutil import parser as dtp, tz
import requests
from icalendar import Calendar
import feedparser
from bs4 import BeautifulSoup


def fetch_ics_events(url: str, source_name: str) -> List[Dict[str, Any]]:
    """Fetch events from an ICS calendar URL"""
    events = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            cal = Calendar.from_ical(response.content)
            for component in cal.walk():
                if component.name == "VEVENT":
                    event = {
                        "title": str(component.get('summary', '')),
                        "start_iso": component.get('dtstart').dt.isoformat() if component.get('dtstart') else None,
                        "location": str(component.get('location', '')),
                        "description": str(component.get('description', '')),
                        "category": "Sports" if "sport" in source_name.lower() or "athletic" in source_name.lower() else "University",
                        "source": source_name,
                        "link": str(component.get('url', '')),
                        "cost": "Free"  # Default
                    }
                    if event['start_iso']:
                        events.append(event)
    except Exception as e:
        print(f"Error fetching ICS from {url}: {e}")
    
    return events


def fetch_rss_events(url: str, source_name: str) -> List[Dict[str, Any]]:
    """Fetch events from an RSS feed"""
    events = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:50]:  # Limit to 50 events
            event = {
                "title": entry.title,
                "start_iso": None,
                "location": entry.get('location', ''),
                "description": entry.get('summary', entry.get('description', '')),
                "category": "University",
                "source": source_name,
                "link": entry.link,
                "cost": "Free"
            }
            
            # Try to parse date
            if hasattr(entry, 'published'):
                try:
                    event['start_iso'] = dtp.parse(entry.published).isoformat()
                except:
                    pass
            
            events.append(event)
    except Exception as e:
        print(f"Error fetching RSS from {url}: {e}")
    
    return events


def fetch_html_events(url: str, source_name: str) -> List[Dict[str, Any]]:
    """
    Fetch events from HTML pages (basic parser)
    Currently returns empty list - would need site-specific parsing
    """
    # TODO: Implement HTML parsing for each specific site
    # For now, return empty
    return []


def fetch_seatgeek_events(city: str, state: str) -> List[Dict[str, Any]]:
    """Fetch events from SeatGeek API"""
    events = []
    try:
        # SeatGeek API endpoint
        url = f"https://api.seatgeek.com/2/events"
        params = {
            'venue.city': city,
            'venue.state': state,
            'per_page': 100
        }
        # TODO: Add API key if needed
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('events', []):
                event = {
                    "title": item.get('title', ''),
                    "start_iso": item.get('datetime_local'),
                    "location": f"{item.get('venue', {}).get('name', '')}, {city}, {state}",
                    "description": "",
                    "category": "Music",  # Default
                    "source": "SeatGeek",
                    "link": item.get('url', ''),
                    "cost": f"${item.get('stats', {}).get('lowest_price', 0)}" if item.get('stats', {}).get('lowest_price') else "Varies"
                }
                if event['start_iso']:
                    events.append(event)
    except Exception as e:
        print(f"Error fetching SeatGeek events: {e}")
    
    return events


def fetch_ticketmaster_events(city: str, state_code: str) -> List[Dict[str, Any]]:
    """Fetch events from Ticketmaster API"""
    events = []
    try:
        # Ticketmaster Discovery API endpoint
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {
            'apikey': '',  # TODO: Add API key
            'city': city,
            'stateCode': state_code,
            'size': 100
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('_embedded', {}).get('events', []):
                event = {
                    "title": item.get('name', ''),
                    "start_iso": item.get('dates', {}).get('start', {}).get('localDateTime'),
                    "location": f"{item.get('_embedded', {}).get('venues', [{}])[0].get('name', '')}, {city}",
                    "description": item.get('info', ''),
                    "category": item.get('classifications', [{}])[0].get('segment', {}).get('name', 'Music'),
                    "source": "Ticketmaster",
                    "link": item.get('url', ''),
                    "cost": f"${item.get('priceRanges', [{}])[0].get('min', 0)}" if item.get('priceRanges') else "Varies"
                }
                if event['start_iso']:
                    events.append(event)
    except Exception as e:
        print(f"Error fetching Ticketmaster events: {e}")
    
    return events


def collect_all_events(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collect events from all sources"""
    all_events = []
    
    for source in sources:
        source_type = source.get('type')
        source_name = source.get('name', 'Unknown')
        
        if source_type == 'ics':
            url = source.get('url')
            if url:
                events = fetch_ics_events(url, source_name)
                all_events.extend(events)
        
        elif source_type == 'rss':
            url = source.get('url')
            if url:
                events = fetch_rss_events(url, source_name)
                all_events.extend(events)
        
        elif source_type == 'html':
            url = source.get('url')
            if url:
                events = fetch_html_events(url, source_name)
                all_events.extend(events)
        
        elif source_type == 'api':
            parser = source.get('parser')
            if parser == 'seatgeek':
                city = source.get('city')
                state = source.get('state')
                if city and state:
                    events = fetch_seatgeek_events(city, state)
                    all_events.extend(events)
            elif parser == 'ticketmaster':
                city = source.get('city')
                state_code = source.get('stateCode')
                if city and state_code:
                    events = fetch_ticketmaster_events(city, state_code)
                    all_events.extend(events)
    
    # Filter to next 3 weeks
    cutoff = datetime.now(tz.tzlocal()) + timedelta(days=21)
    filtered_events = []
    for event in all_events:
        if event.get("start_iso"):
            try:
                event_date = dtp.parse(event["start_iso"])
                if event_date <= cutoff and event_date >= datetime.now(tz.tzlocal()):
                    filtered_events.append(event)
            except:
                continue
    
    # Sort by date
    return sorted(filtered_events, key=lambda x: x.get("start_iso", ""))


def detect_sports_teams(title: str) -> Optional[Tuple[Tuple[str, str], Tuple[str, str]]]:
    """Detect two teams from event title (for sports logo generation)"""
    # Import team mappings
    from utils.image_processing import TEAM_NAMES
    
    title_lower = title.lower()
    vs_pattern = r'(.+?)\s+(?:vs|@|v\.|versus)\s+(.+?)(?:\s+(?:in|at)|$)'
    match = re.search(vs_pattern, title_lower)
    if not match:
        return None
    
    team1_text, team2_text = match.groups()
    
    def find_team(text):
        text_lower = text.lower().strip()
        sorted_teams = sorted(TEAM_NAMES.items(), key=lambda x: len(x[0]), reverse=True)
        for key, (name, logo_urls) in sorted_teams:
            if key in text_lower:
                return name, logo_urls
        return None, None
    
    team1_result = find_team(team1_text)
    team2_result = find_team(team2_text)
    
    if team1_result[0] and team2_result[0]:
        return team1_result, team2_result
    
    return None

