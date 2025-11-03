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
    from lib.categorizer import categorize_event
    
    events = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            cal = Calendar.from_ical(response.content)
            for component in cal.walk():
                if component.name == "VEVENT":
                    title = str(component.get('summary', ''))
                    description = str(component.get('description', ''))
                    
                    # Smart categorization
                    category = categorize_event(title, description, source_name)
                    
                    event = {
                        "title": title,
                        "start_iso": component.get('dtstart').dt.isoformat() if component.get('dtstart') else None,
                        "location": str(component.get('location', '')),
                        "description": description,
                        "category": category,
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
    from lib.categorizer import categorize_event
    
    events = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:50]:  # Limit to 50 events
            # Extract location from title (format: "Event Name at Location")
            location = ''
            if ' at ' in entry.title:
                location = entry.title.split(' at ', 1)[1].strip()
            
            # Get raw description (may contain HTML)
            raw_desc = entry.get('summary', entry.get('description', ''))
            
            # Parse HTML to clean description
            if raw_desc:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(raw_desc, 'html.parser')
                clean_desc = soup.get_text(separator=' ', strip=True)
            else:
                clean_desc = ''
            
            # Remove unwanted phrases
            clean_desc = clean_desc.replace('View on site', '').replace('Email this event', '').strip()
            
            # Smart categorization
            category = categorize_event(entry.title, clean_desc, source_name)
            
            event = {
                "title": entry.title,
                "start_iso": None,
                "location": location,
                "description": clean_desc,
                "category": category,
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


def fetch_espn_schedule(url: str, source_name: str, sport_type: str = "football") -> List[Dict[str, Any]]:
    """
    Fetch events from ESPN schedule page using Selenium
    Filters out away games (@ prefix) and only includes home games
    Always selects the most recent year automatically
    """
    from lib.categorizer import categorize_event
    from dateutil import parser as dtp
    from datetime import datetime
    import time
    import re
    
    events = []
    
    try:
        # Import Selenium components
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Configure Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize driver
        # Use webdriver-manager to automatically handle driver downloads
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            # Fallback: try without webdriver-manager (for systems with ChromeDriver in PATH)
            print(f"Warning: Could not use webdriver-manager: {e}")
            driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to ESPN schedule page
            print(f"Loading ESPN schedule: {url}")
            driver.get(url)
            
            # Wait for page to load (ESPN uses JavaScript rendering)
            wait = WebDriverWait(driver, 15)
            
            # Wait for schedule table or content to appear
            # ESPN schedules are typically in tables or specific containers
            try:
                # Try to find schedule container
                schedule_loaded = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table, [class*='Schedule'], [class*='schedule'], [data-testid*='schedule']"))
                )
            except:
                # If specific selector fails, just wait a bit for JS to render
                time.sleep(3)
            
            # Check if we need to select the most recent year
            # ESPN often has a year selector dropdown
            try:
                # Look for year selector buttons or dropdowns
                year_selectors = driver.find_elements(By.CSS_SELECTOR, 
                    "button[data-name*='year'], button[class*='year'], select[name*='year'], [class*='YearSelector']")
                
                if year_selectors:
                    # Find the most recent year (usually the first or last option)
                    # Click the most recent year option
                    current_year = datetime.now().year
                    for selector in year_selectors:
                        try:
                            if selector.tag_name == 'button':
                                text = selector.text
                                if str(current_year) in text or str(current_year + 1) in text:
                                    selector.click()
                                    time.sleep(2)  # Wait for page to update
                                    break
                        except:
                            continue
            except Exception as year_error:
                print(f"Could not select year (may already be on latest): {year_error}")
            
            # Parse the schedule
            # ESPN schedule tables typically have rows with date, opponent, result columns
            schedule_tables = driver.find_elements(By.CSS_SELECTOR, 
                "table[class*='Schedule'], table[class*='Table'], table[class*='schedule']")
            
            # If no tables found, try finding schedule rows directly
            if not schedule_tables:
                schedule_rows = driver.find_elements(By.CSS_SELECTOR, 
                    "tr[class*='Schedule'], tr[class*='Row'], [data-testid*='schedule-row']")
            else:
                schedule_rows = []
                for table in schedule_tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    schedule_rows.extend(rows)
            
            for row in schedule_rows:
                try:
                    # Skip header rows
                    if row.find_elements(By.TAG_NAME, "th"):
                        continue
                    
                    # Get all cells in the row
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 2:
                        continue
                    
                    # Extract date from first cell (or data attribute)
                    date_text = ""
                    try:
                        date_cell = cells[0]
                        date_text = date_cell.text.strip()
                        
                        # Also try data-date attribute
                        if not date_text:
                            date_text = date_cell.get_attribute('data-date') or ""
                    except:
                        continue
                    
                    if not date_text:
                        continue
                    
                    # Extract opponent from second cell (or nearby cell)
                    opponent_text = ""
                    opponent_cell = None
                    
                    # Try different cell positions for opponent
                    for i in range(1, min(4, len(cells))):
                        try:
                            cell_text = cells[i].text.strip()
                            # Look for opponent name (skip result columns like "W", "L", scores)
                            if cell_text and not cell_text.startswith(('W', 'L', 'T', 'Final', 'Cancelled')):
                                # Check if it's an away game (@ prefix)
                                if cell_text.startswith('@') or cell_text.startswith('at '):
                                    # Skip away games
                                    opponent_text = None
                                    break
                                opponent_text = cell_text
                                opponent_cell = cells[i]
                                break
                        except:
                            continue
                    
                    # Skip if no opponent found or it's an away game
                    if not opponent_text or opponent_text.startswith('@'):
                        continue
                    
                    # Clean opponent name (remove vs, @, etc.)
                    opponent_clean = re.sub(r'^\s*(vs|VS|v\.|versus|@|at)\s*', '', opponent_text).strip()
                    
                    # Skip placeholder text
                    if opponent_clean in ['OPPONENT', 'TBD', 'TBA', ''] or len(opponent_clean) < 2:
                        continue
                    
                    # Parse date
                    try:
                        # ESPN date formats vary: "Sep 2", "9/2", "September 2, 2024", etc.
                        current_year = datetime.now().year
                        
                        # Try to parse the date
                        if '/' in date_text:
                            # Format like "9/2" or "09/02"
                            parts = date_text.split('/')
                            if len(parts) == 2:
                                month = int(parts[0])
                                day = int(parts[1])
                                parsed_date = datetime(current_year, month, day, 19, 0)
                                
                                # If date has passed this year, assume next year
                                if parsed_date < datetime.now():
                                    parsed_date = datetime(current_year + 1, month, day, 19, 0)
                            else:
                                parsed_date = dtp.parse(date_text, fuzzy=True)
                                if parsed_date.hour == 0:
                                    parsed_date = parsed_date.replace(hour=19, minute=0)
                        else:
                            # Try fuzzy parsing for formats like "Sep 2" or "September 2, 2024"
                            parsed_date = dtp.parse(date_text, fuzzy=True)
                            # Default to 7 PM if no time specified
                            if parsed_date.hour == 0 and parsed_date.minute == 0:
                                parsed_date = parsed_date.replace(hour=19, minute=0)
                        
                        # Determine location based on sport
                        if sport_type == "football":
                            location = "Vaught-Hemingway Stadium"
                        elif "basketball" in sport_type.lower():
                            location = "The Pavilion"
                        else:
                            location = "TBD"
                        
                        # Build title
                        title = f"Ole Miss vs {opponent_clean}"
                        
                        event = {
                            "title": title,
                            "start_iso": parsed_date.isoformat(),
                            "location": location,
                            "description": f"{sport_type.title()} game: {title}",
                            "category": "Ole Miss Athletics",
                            "source": source_name,
                            "link": url,
                            "cost": "Varies"
                        }
                        events.append(event)
                        
                    except Exception as date_error:
                        print(f"Error parsing date '{date_text}': {date_error}")
                        continue
                        
                except Exception as row_error:
                    print(f"Error processing schedule row: {row_error}")
                    continue
            
            # If no events found, try alternative parsing approach
            if not events:
                # Look for schedule items in different structure
                try:
                    schedule_items = driver.find_elements(By.CSS_SELECTOR, 
                        "[class*='ScheduleRow'], [class*='GameRow'], [data-testid*='game']")
                    
                    for item in schedule_items:
                        try:
                            # Extract date
                            date_elem = item.find_element(By.CSS_SELECTOR, 
                                "[class*='date'], [data-date], [datetime]")
                            date_text = date_elem.text or date_elem.get_attribute('data-date') or date_elem.get_attribute('datetime') or ""
                            
                            # Extract opponent
                            opponent_elem = item.find_element(By.CSS_SELECTOR, 
                                "[class*='opponent'], [class*='team'], [class*='name']")
                            opponent_text = opponent_elem.text.strip()
                            
                            # Skip away games
                            if opponent_text.startswith('@') or opponent_text.startswith('at '):
                                continue
                            
                            if date_text and opponent_text:
                                try:
                                    parsed_date = dtp.parse(date_text, fuzzy=True)
                                    if parsed_date.hour == 0:
                                        parsed_date = parsed_date.replace(hour=19, minute=0)
                                    
                                    opponent_clean = re.sub(r'^\s*(vs|VS|v\.|versus|@|at)\s*', '', opponent_text).strip()
                                    
                                    if sport_type == "football":
                                        location = "Vaught-Hemingway Stadium"
                                    elif "basketball" in sport_type.lower():
                                        location = "The Pavilion"
                                    else:
                                        location = "TBD"
                                    
                                    title = f"Ole Miss vs {opponent_clean}"
                                    
                                    event = {
                                        "title": title,
                                        "start_iso": parsed_date.isoformat(),
                                        "location": location,
                                        "description": f"{sport_type.title()} game: {title}",
                                        "category": "Ole Miss Athletics",
                                        "source": source_name,
                                        "link": url,
                                        "cost": "Varies"
                                    }
                                    events.append(event)
                                except:
                                    continue
                        except:
                            continue
                except:
                    pass
            
        finally:
            # Always close the driver
            driver.quit()
            
    except ImportError:
        print(f"Selenium not available. Install with: pip install selenium webdriver-manager")
        # Return empty list if Selenium isn't installed
    except Exception as e:
        print(f"Error fetching ESPN schedule from {url}: {e}")
        import traceback
        traceback.print_exc()
    
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
        
        elif source_type == 'espn':
            url = source.get('url')
            sport_type = source.get('sport_type', 'football')
            if url:
                events = fetch_espn_schedule(url, source_name, sport_type=sport_type)
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

