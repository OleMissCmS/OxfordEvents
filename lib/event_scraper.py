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
            # Get raw description (may contain HTML)
            raw_desc = entry.get('summary', entry.get('description', ''))
            
            # Strip HTML tags for cleaner display
            if raw_desc:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(raw_desc, 'html.parser')
                clean_desc = soup.get_text(separator=' ', strip=True)
            else:
                clean_desc = ''
            
            event = {
                "title": entry.title,
                "start_iso": None,
                "location": entry.get('location', ''),
                "description": clean_desc,
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


def fetch_html_events(url: str, source_name: str, parser: str = None) -> List[Dict[str, Any]]:
    """
    Fetch events from HTML pages using site-specific parsers
    """
    events = []
    try:
        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Use parser-specific logic
            if parser == 'bandsintown':
                events = _parse_bandsintown(soup, source_name, url)
            elif parser == 'visit_oxford':
                events = _parse_visit_oxford(soup, source_name, url)
            elif parser == 'simple_list':
                # Generic parser - try to extract basic event info
                events = _parse_generic(soup, source_name, url)
    except Exception as e:
        print(f"Error fetching HTML from {url}: {e}")
    
    return events


def _parse_bandsintown(soup, source_name: str, base_url: str) -> List[Dict[str, Any]]:
    """Parse Bandsintown HTML"""
    events = []
    try:
        # Bandsintown uses specific event containers
        # Look for event cards or listings
        event_elements = soup.find_all(['div', 'article'], class_=lambda x: x and ('event' in x.lower() or 'concert' in x.lower()))
        
        for elem in event_elements:
            try:
                # Try to extract title
                title_elem = elem.find(['h2', 'h3', 'h4'], class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower()))
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                if not title:
                    # Try finding any heading
                    title_elem = elem.find(['h1', 'h2', 'h3', 'h4'])
                    title = title_elem.get_text(strip=True) if title_elem else ''
                
                # Try to extract date
                date_elem = elem.find(class_=lambda x: x and 'date' in x.lower())
                date_str = date_elem.get_text(strip=True) if date_elem else ''
                
                # Try to extract venue
                venue_elem = elem.find(class_=lambda x: x and 'venue' in x.lower())
                venue = venue_elem.get_text(strip=True) if venue_elem else 'Oxford, MS'
                
                # Try to extract link
                link_elem = elem.find('a', href=True)
                link = link_elem['href'] if link_elem else base_url
                if link.startswith('/'):
                    link = 'https://www.bandsintown.com' + link
                
                if title and date_str:
                    # Try to parse date
                    try:
                        parsed_date = dtp.parse(date_str)
                        event = {
                            "title": title,
                            "start_iso": parsed_date.isoformat(),
                            "location": venue,
                            "description": "",
                            "category": "Music",
                            "source": source_name,
                            "link": link,
                            "cost": "Varies"
                        }
                        events.append(event)
                    except:
                        # Skip if we can't parse the date
                        pass
            except:
                continue
    except Exception as e:
        print(f"Error parsing Bandsintown: {e}")
    
    return events


def _parse_visit_oxford(soup, source_name: str, base_url: str) -> List[Dict[str, Any]]:
    """Parse Visit Oxford HTML"""
    events = []
    try:
        # Visit Oxford specific parsing
        event_elements = soup.find_all(['article', 'div', 'li'], class_=lambda x: x and 'event' in x.lower() if x else False)
        
        for elem in event_elements:
            try:
                # Extract title
                title_elem = elem.find(['h2', 'h3', 'a'], class_=lambda x: x and 'title' in x.lower() if x else False)
                if not title_elem:
                    title_elem = elem.find(['h2', 'h3', 'h4'])
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                # Extract date
                date_elem = elem.find(class_=lambda x: x and 'date' in x.lower())
                date_str = date_elem.get_text(strip=True) if date_elem else ''
                
                # Extract location
                location_elem = elem.find(class_=lambda x: x and ('location' in x.lower() or 'venue' in x.lower()))
                location = location_elem.get_text(strip=True) if location_elem else 'Oxford, MS'
                
                # Extract link
                link_elem = elem.find('a', href=True)
                link = link_elem['href'] if link_elem else base_url
                if link.startswith('/'):
                    link = base_url.rstrip('/') + link
                
                if title and date_str:
                    try:
                        parsed_date = dtp.parse(date_str)
                        event = {
                            "title": title,
                            "start_iso": parsed_date.isoformat(),
                            "location": location,
                            "description": "",
                            "category": "Community",
                            "source": source_name,
                            "link": link,
                            "cost": "Free"  # Default for community events
                        }
                        events.append(event)
                    except:
                        pass
            except:
                continue
    except Exception as e:
        print(f"Error parsing Visit Oxford: {e}")
    
    return events


def _parse_generic(soup, source_name: str, base_url: str) -> List[Dict[str, Any]]:
    """Generic HTML parser for events"""
    events = []
    try:
        # Look for common event patterns
        event_elements = soup.find_all(['article', 'div'], class_=lambda x: x and ('event' in x.lower() if x else False))
        
        for elem in event_elements:
            try:
                title_elem = elem.find(['h1', 'h2', 'h3', 'h4'])
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                if title:
                    event = {
                        "title": title,
                        "start_iso": None,
                        "location": "Oxford, MS",
                        "description": "",
                        "category": "Community",
                        "source": source_name,
                        "link": base_url,
                        "cost": "Free"
                    }
                    events.append(event)
            except:
                continue
    except:
        pass
    
    return events


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
    import os
    events = []
    try:
        # Ticketmaster Discovery API endpoint
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        
        # Get API key from environment variable
        api_key = os.environ.get('TICKETMASTER_API_KEY', '')
        if not api_key:
            print("No TICKETMASTER_API_KEY found in environment variables")
            return events
        
        params = {
            'apikey': api_key,
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
            parser = source.get('parser')
            if url:
                events = fetch_html_events(url, source_name, parser=parser)
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

