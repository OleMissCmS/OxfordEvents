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
            
            # Smart categorization (after processing description)
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
    """Parse Bandsintown HTML - uses data-test attributes"""
    events = []
    try:
        # Bandsintown uses React with data-test attributes
        # Look for event containers with data-test="popularEvent"
        event_containers = soup.find_all('div', {'data-test': 'popularEvent'})
        
        for container in event_containers:
            try:
                # Extract event link
                link_elem = container.find('a', {'data-test': 'popularEvent__link'})
                if not link_elem:
                    link_elem = container.find('a', href=lambda x: x and '/e/' in str(x) if x else False)
                
                link = link_elem.get('href', '') if link_elem else base_url
                if link.startswith('/'):
                    link = 'https://www.bandsintown.com' + link
                elif not link.startswith('http'):
                    link = base_url
                
                # Extract artist name
                artist_elem = container.find('div', {'data-test': 'popularEvent__info__artistName'})
                artist = artist_elem.get_text(strip=True) if artist_elem else ''
                
                # Extract venue name
                venue_elem = container.find('p', {'data-test': 'popularEvent__info__venueName'})
                if not venue_elem:
                    venue_elem = container.find('div', {'data-test': 'popularEvent__info__venueName'})
                venue = venue_elem.get_text(strip=True) if venue_elem else 'Oxford, MS'
                
                # Extract date
                date_str = None
                date_elem = container.find('div', {'data-test': 'popularEvent__date'})
                if date_elem:
                    # First try to find time element with datetime attribute
                    time_elem = date_elem.find('time')
                    if time_elem:
                        date_str = time_elem.get('datetime', '')
                    
                    # If no datetime attribute, parse the text (format: "Nov 7 - 7:00 pm")
                    if not date_str:
                        date_text = date_elem.get_text(strip=True)
                        if date_text:
                            # Parse format like "Nov 7 - 7:00 pm" or "Nov 7" or "Nov 7, 2025"
                            import re
                            from datetime import datetime
                            
                            # Try to extract month, day, and time
                            # Pattern: "Nov 7" or "Nov 7 - 7:00 pm" or "Nov 7, 2025"
                            date_match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})(?:\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm))?', date_text, re.IGNORECASE)
                            if date_match:
                                month_str = date_match.group(1)
                                day = int(date_match.group(2))
                                
                                # Get current year and month
                                now = datetime.now()
                                current_year = now.year
                                current_month = now.month
                                
                                # Convert month string to number
                                month_map = {
                                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                                }
                                month = month_map.get(month_str.lower()[:3])
                                
                                # If the event month is earlier in the year than current month,
                                # assume it's next year (e.g., if it's Nov 2025 and event is Jan, it's Jan 2026)
                                if month and month < current_month:
                                    current_year = current_year + 1
                                
                                if month:
                                    # Extract time if available
                                    hour = None
                                    minute = None
                                    if date_match.group(3):
                                        hour = int(date_match.group(3))
                                        minute = int(date_match.group(4)) if date_match.group(4) else 0
                                        ampm = date_match.group(5).lower() if date_match.group(5) else 'pm'
                                        
                                        # Convert to 24-hour format
                                        if ampm == 'pm' and hour != 12:
                                            hour += 12
                                        elif ampm == 'am' and hour == 12:
                                            hour = 0
                                    
                                    # Create datetime object
                                    if hour is not None:
                                        try:
                                            parsed_date = datetime(current_year, month, day, hour, minute or 0)
                                            date_str = parsed_date.strftime('%Y-%m-%dT%H:%M:%S')
                                        except ValueError:
                                            # Invalid date (e.g., Feb 30), try without time
                                            parsed_date = datetime(current_year, month, day, 19, 0)
                                            date_str = parsed_date.strftime('%Y-%m-%dT%H:%M:%S')
                                    else:
                                        # No time specified, default to 7pm
                                        parsed_date = datetime(current_year, month, day, 19, 0)
                                        date_str = parsed_date.strftime('%Y-%m-%dT%H:%M:%S')
                            else:
                                # Fallback: try standard dateutil parsing
                                date_str = date_text
                
                # Also check link for date information
                if not date_str and link:
                    # Try to extract date from URL pattern
                    import re
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', link)
                    if date_match:
                        date_str = date_match.group(1)
                
                # Create title from artist name
                title = artist if artist else f"Concert at {venue}"
                
                if title and (date_str or link):
                    # Try to parse date
                    start_iso = None
                    if date_str:
                        try:
                            # If date_str is already in ISO format, use it directly
                            if 'T' in date_str:
                                start_iso = date_str
                            else:
                                parsed_date = dtp.parse(date_str)
                                start_iso = parsed_date.isoformat()
                        except:
                            # Try extracting from link or other sources
                            pass
                    
                    # If we have a valid date or at least a title and venue, create event
                    if start_iso or (title and venue):
                        event = {
                            "title": title,
                            "start_iso": start_iso or None,
                            "location": venue,
                            "description": "",
                            "category": "Bandsintown",
                            "source": source_name,
                            "link": link,
                            "cost": "Varies"
                        }
                        if start_iso:  # Only add if we have a valid date
                            events.append(event)
            except Exception as e:
                print(f"[Bandsintown] Error parsing event container: {e}")
                continue
        
        # Also try to extract from JavaScript data if available
        if not events:
            # Look for window.__data which contains event data
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'window.__data' in script.string:
                    try:
                        import json
                        import re
                        # Extract JSON data from script
                        match = re.search(r'window\.__data\s*=\s*({.*?});', script.string, re.DOTALL)
                        if match:
                            data = json.loads(match.group(1))
                            # Navigate through data structure to find events
                            # This structure varies, so we'll try common paths
                            print("[Bandsintown] Found JavaScript data, but parsing structure varies")
                    except:
                        pass
    except Exception as e:
        print(f"[Bandsintown] Error parsing: {e}")
    
    print(f"[Bandsintown] Parsed {len(events)} events")
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
            print("[Ticketmaster] WARNING: No TICKETMASTER_API_KEY found in environment variables")
            print("[Ticketmaster] Make sure the secret file is named 'TICKETMASTER_API_KEY' in Render")
            return events
        
        print(f"[Ticketmaster] API key found (first 8 chars: {api_key[:8]}...)")
        
        params = {
            'apikey': api_key,
            'city': city,
            'stateCode': state_code,
            'size': 100
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            events_list = data.get('_embedded', {}).get('events', [])
            print(f"[Ticketmaster] API returned {len(events_list)} events")
            
            for item in events_list:
                # Try multiple date field options
                dates = item.get('dates', {}).get('start', {})
                start_iso = dates.get('localDateTime') or dates.get('dateTime') or dates.get('localDate')
                
                # If we only have a date, add a default time
                if start_iso and 'T' not in start_iso:
                    start_iso = f"{start_iso}T19:00:00"
                
                # Extract venue name safely
                venues = item.get('_embedded', {}).get('venues', [])
                venue_name = venues[0].get('name', 'Unknown Venue') if venues else 'Unknown Venue'
                
                event = {
                    "title": item.get('name', ''),
                    "start_iso": start_iso,
                    "location": f"{venue_name}, {city}",
                    "description": item.get('info', '') or item.get('description', ''),
                    "category": "Ticketmaster",  # Use dedicated Ticketmaster category
                    "source": "Ticketmaster",
                    "link": item.get('url', ''),
                    "cost": f"${item.get('priceRanges', [{}])[0].get('min', 0)}" if item.get('priceRanges') else "Varies"
                }
                
                if event['start_iso']:
                    events.append(event)
                else:
                    print(f"[Ticketmaster] Skipping event '{event['title'][:50]}' - no valid date")
        elif response.status_code == 401:
            print(f"[Ticketmaster] ERROR: Unauthorized (401) - API key may be invalid or expired")
            try:
                error_data = response.json()
                print(f"[Ticketmaster] API Error: {error_data}")
            except:
                print(f"[Ticketmaster] Response: {response.text[:200]}")
        elif response.status_code == 403:
            print(f"[Ticketmaster] ERROR: Forbidden (403) - API key may not have permission for this endpoint")
        else:
            print(f"[Ticketmaster] ERROR: Got status code {response.status_code}")
            try:
                error_data = response.json()
                print(f"[Ticketmaster] API Error: {error_data}")
            except:
                print(f"[Ticketmaster] Response: {response.text[:200]}")
                
    except requests.exceptions.RequestException as e:
        print(f"[Ticketmaster] Network error: {e}")
    except Exception as e:
        print(f"[Ticketmaster] Error fetching events: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"[Ticketmaster] Successfully processed {len(events)} events")
    if len(events_list) > 0 and len(events) == 0:
        print(f"[Ticketmaster] WARNING: API returned {len(events_list)} events but 0 were processed")
        print(f"[Ticketmaster] This usually means events are missing dates. Sample event structure:")
        if events_list:
            sample = events_list[0]
            dates = sample.get('dates', {})
            print(f"[Ticketmaster] Sample dates structure: {dates}")
            if dates:
                start = dates.get('start', {})
                print(f"[Ticketmaster] Sample start structure: {start}")
                print(f"[Ticketmaster] Available date fields: localDateTime={start.get('localDateTime')}, dateTime={start.get('dateTime')}, localDate={start.get('localDate')}")
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
        # Quick check: Is Chrome available? (Fail fast if not)
        import os
        chrome_binary = None
        chrome_paths = ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome', '/usr/bin/chrome']
        for possible_path in chrome_paths:
            if os.path.exists(possible_path):
                chrome_binary = possible_path
                break
        
        # If Chrome not found, fail immediately to avoid 30+ second timeout
        if not chrome_binary:
            print(f"[ESPN] Chrome/Chromium not found. Skipping ESPN scraping.")
            print(f"[ESPN] Chrome is required for ESPN scraping. Install Chrome or use a different approach.")
            return events  # Return empty list immediately
        
        # Import Selenium components (only if Chrome is available)
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Configure Chrome options for headless mode (Render-compatible)
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Set Chrome binary location
        chrome_options.binary_location = chrome_binary
        print(f"[ESPN] Using Chrome binary at: {chrome_binary}")
        
        # Initialize driver with timeout
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f"[ESPN] Chrome driver initialized successfully")
        except Exception as e:
            # Fallback: try without webdriver-manager (for systems with ChromeDriver in PATH)
            print(f"[ESPN] Warning: Could not use webdriver-manager: {e}")
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                print(f"[ESPN] Error: Failed to initialize Chrome driver: {e2}")
                return events  # Return empty list instead of raising
        
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
        print(f"[ESPN] Selenium not available. Install with: pip install selenium webdriver-manager")
        # Return empty list if Selenium isn't installed
    except Exception as e:
        print(f"[ESPN] Error fetching ESPN schedule from {url}: {e}")
        import traceback
        print(f"[ESPN] Full traceback:")
        traceback.print_exc()
    
    if not events:
        print(f"[ESPN] No events found for {source_name} - this may be normal if scraping failed or no upcoming games")
    
    return events


def _convert_espn_to_olemiss_url(espn_url: str, sport_type: str) -> str:
    """Convert ESPN URL to Ole Miss Athletics schedule URL"""
    base_url = "https://olemisssports.com/sports"
    
    if sport_type == "football":
        return f"{base_url}/football/schedule"
    elif "basketball" in sport_type.lower():
        if "women" in espn_url.lower() or "wbb" in espn_url.lower():
            return f"{base_url}/womens-basketball/schedule"
        else:
            return f"{base_url}/mens-basketball/schedule"
    
    return None


def collect_all_events(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collect events from all sources"""
    # Initialize status tracking
    try:
        from lib.status_tracker import set_status, clear_status
        total_steps = len(sources) + 2  # Each source + filtering + finalizing
        set_status(0, total_steps, "Starting to load events...", "")
    except Exception:
        pass
    
    all_events = []
    
    for idx, source in enumerate(sources):
        source_type = source.get('type')
        source_name = source.get('name', 'Unknown')
        
        # Update status for this source
        try:
            from lib.status_tracker import set_status
            source_type_name = {
                'ics': 'calendar',
                'rss': 'RSS feed',
                'html': 'website',
                'api': 'API',
                'olemiss': 'sports schedule'
            }.get(source_type, 'source')
            set_status(idx + 1, len(sources) + 2, f"Checking {source_name}...", f"Loading from {source_type_name}")
        except Exception:
            pass
        
        # Wrap each source fetch in try/except to prevent one failure from blocking others
        try:
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
                    # Use enhanced scraper for Visit Oxford (follows links)
                    if parser == 'visit_oxford':
                        try:
                            from lib.visit_oxford_scraper import fetch_visit_oxford_events
                            events = fetch_visit_oxford_events(url, source_name)
                            print(f"[collect_all_events] {source_name} (Enhanced): {len(events)} events found")
                        except Exception as e:
                            print(f"[collect_all_events] Visit Oxford scraper failed/timed out: {str(e)[:100]}")
                            # Skip Visit Oxford if it fails to prevent worker timeout
                            events = []
                    else:
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
            
            elif source_type == 'olemiss':
                url = source.get('url')
                sport_type = source.get('sport_type', 'football')
                if url:
                    from lib.olemiss_athletics_scraper import fetch_olemiss_schedule
                    print(f"[collect_all_events] Fetching Ole Miss schedule: {source_name}")
                    events = fetch_olemiss_schedule(url, source_name, sport_type=sport_type)
                    print(f"[collect_all_events] {source_name}: {len(events)} events found")
                    all_events.extend(events)
        except Exception as e:
            # Log error but continue processing other sources
            print(f"[collect_all_events] ERROR fetching {source_name}: {str(e)[:100]}")
            # Continue to next source
            continue
    
    # Filter out duplicates (especially Ole Miss Athletic events from Visit Oxford)
    print(f"[collect_all_events] Removing duplicates from {len(all_events)} total events")
    
    seen_events = {}
    deduplicated_events = []
    
    for event in all_events:
        # Create a key based on title, date, and location for duplicate detection
        title = event.get('title', '').lower().strip()
        date = event.get('start_iso', '')
        location = event.get('location', '').lower().strip()
        
        # Skip Ole Miss Athletic events from Visit Oxford (they're duplicates)
        source_lower = event.get('source', '').lower()
        if 'visit oxford' in source_lower:
            title_lower = title.lower()
            # Check if it's an athletic event
            if any(keyword in title_lower for keyword in ['ole miss', 'rebels']) and \
               any(sport in title_lower for sport in [' vs ', ' vs. ', ' game', 'football', 'basketball', 'baseball']):
                print(f"[collect_all_events] Filtering duplicate athletic event from Visit Oxford: {event.get('title')}")
                continue
        
        # Create deduplication key
        key = f"{title}_{date}_{location}"
        
        # Skip if we've seen this exact event before
        if key in seen_events:
            print(f"[collect_all_events] Filtering duplicate: {event.get('title')}")
            continue
        
        seen_events[key] = True
        deduplicated_events.append(event)
    
    print(f"[collect_all_events] After deduplication: {len(deduplicated_events)} events")
    
    # Filter to next 3 weeks
    now = datetime.now(tz.tzlocal())
    cutoff = now + timedelta(days=21)
    filtered_events = []
    
    print(f"[collect_all_events] Filtering {len(deduplicated_events)} events to next 3 weeks (now={now.isoformat()}, cutoff={cutoff.isoformat()})")
    
    athletics_count = 0
    athletics_filtered = 0
    
    for event in deduplicated_events:
        if event.get("start_iso"):
            try:
                event_date = dtp.parse(event["start_iso"])
                # Ensure event_date is timezone-aware for comparison
                if event_date.tzinfo is None:
                    event_date = event_date.replace(tzinfo=tz.tzlocal())
                
                is_athletics = event.get("category") == "Ole Miss Athletics"
                if is_athletics:
                    athletics_count += 1
                
                if now <= event_date <= cutoff:
                    filtered_events.append(event)
                    if is_athletics:
                        athletics_filtered += 1
                elif is_athletics:
                    # Log athletics events that are filtered out for debugging
                    days_diff = (event_date - now).days
                    if days_diff < 0:
                        print(f"[collect_all_events] Athletics event filtered (past): {event.get('title')} - {event_date.isoformat()}")
                    else:
                        print(f"[collect_all_events] Athletics event filtered (too far): {event.get('title')} - {event_date.isoformat()} ({days_diff} days away)")
            except Exception as e:
                print(f"[collect_all_events] Error parsing date for event {event.get('title', 'unknown')}: {e}")
                continue
    
    print(f"[collect_all_events] Filtered result: {len(filtered_events)} total events ({athletics_filtered} athletics)")
    
    # Filter out training events
    original_count = len(filtered_events)
    filtered_events = [
        event for event in filtered_events
        if "training" not in event.get("title", "").lower() and 
           "training" not in event.get("description", "").lower()
    ]
    if len(filtered_events) < original_count:
        print(f"[collect_all_events] Filtered out {original_count - len(filtered_events)} training events")
    
    # Filter out LGBTQ+ related events
    original_count = len(filtered_events)
    lgbtq_keywords = [
        'lgbtq', 'lgbt', 'lgbtq+', 'pride', 'gay', 'lesbian', 'bisexual', 
        'transgender', 'trans', 'queer', 'lgbtqia', 'lgbtqia+', 'pride month',
        'pride parade', 'rainbow', 'coming out', 'drag', 'drag show'
    ]
    
    filtered_events = [
        event for event in filtered_events
        if not any(
            keyword in event.get("title", "").lower() or 
            keyword in event.get("description", "").lower() or
            keyword in event.get("category", "").lower()
            for keyword in lgbtq_keywords
        )
    ]
    if len(filtered_events) < original_count:
        print(f"[collect_all_events] Filtered out {original_count - len(filtered_events)} LGBTQ+ related events")
    
    # Update status - filtering complete
    try:
        from lib.status_tracker import set_status
        set_status(len(sources) + 1, len(sources) + 2, "Sorting events by date...", f"Found {len(filtered_events)} events")
    except Exception:
        pass
    
    # Sort by date
    result = sorted(filtered_events, key=lambda x: x.get("start_iso", ""))
    
    # Add image URLs to events (pre-generate and cache)
    try:
        result = _add_image_urls_to_events(result)
    except Exception as e:
        print(f"[collect_all_events] Warning: Could not add image URLs: {e}")
    
    # Clear status when complete
    try:
        from lib.status_tracker import clear_status
        clear_status()
    except Exception:
        pass
    
    return result


def _add_image_urls_to_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add image URLs to events by checking database cache or generating new images.
    This creates persistent links between events and their images.
    """
    import hashlib
    try:
        from lib.database import get_session, EventImage
        
        session = get_session()
        
        for event in events:
            # Create unique hash for this event
            event_key = f"{event.get('title', '')}_{event.get('start_iso', '')}_{event.get('location', '')}"
            event_hash = hashlib.sha256(event_key.encode()).hexdigest()[:16]
            
            # Check if image exists in database
            event_image = session.query(EventImage).filter_by(event_hash=event_hash).first()
            
            if event_image and event_image.image_url:
                # Use cached image URL
                event['image_url'] = event_image.image_url
                event['image_type'] = event_image.image_type
            else:
                # Store event info in database (image will be generated on first request)
                category = event.get('category', '')
                title = event.get('title', '')
                location = event.get('location', '')
                
                # Determine image type
                if category in ['Sports', 'Ole Miss Athletics']:
                    image_type = 'sports'
                else:
                    image_type = 'category'
                
                # Store placeholder (will be populated after first image generation)
                event_image = EventImage(
                    event_hash=event_hash,
                    event_title=title,
                    event_date=event.get('start_iso', ''),
                    event_location=location,
                    image_url=None,  # Will be populated after first generation
                    image_type=image_type
                )
                session.merge(event_image)
                event['image_type'] = image_type
                event['image_hash'] = event_hash  # Store hash for later use
            
        session.commit()
        session.close()
    except Exception as e:
        print(f"[_add_image_urls_to_events] Error: {e}")
        # Continue without image URLs if database fails
    
    return events


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

