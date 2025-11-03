"""
Alternative scraper for Ole Miss Athletics schedules
Uses simple HTML parsing instead of Selenium (works without Chrome)
"""

import re
from typing import List, Dict, Any
from datetime import datetime
from dateutil import parser as dtp
import requests
from bs4 import BeautifulSoup


def fetch_olemiss_schedule(url: str, source_name: str, sport_type: str = "football") -> List[Dict[str, Any]]:
    """
    Fetch events from Ole Miss Athletics schedule page using simple HTML parsing
    Filters out away games (@ prefix) and only includes home games
    Works without Selenium/Chrome
    """
    events = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        print(f"[Ole Miss Athletics] Fetching schedule from: {url}")
        response = requests.get(url, timeout=15, headers=headers)
        
        if response.status_code != 200:
            print(f"[Ole Miss Athletics] Error: Got status code {response.status_code}")
            return events
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find schedule table
        # Ole Miss Athletics typically uses tables or list items for schedules
        schedule_tables = soup.find_all('table', class_=lambda x: x and ('schedule' in str(x).lower() if x else False))
        
        if not schedule_tables:
            # Try finding any table
            schedule_tables = soup.find_all('table')
        
        if not schedule_tables:
            # Try finding schedule in list items
            schedule_lists = soup.find_all(['ul', 'ol'], class_=lambda x: x and ('schedule' in str(x).lower() if x else False))
            if schedule_lists:
                # Process list items
                for list_elem in schedule_lists:
                    items = list_elem.find_all('li')
                    for item in items:
                        event = _parse_schedule_item(item, source_name, sport_type, url)
                        if event:
                            events.append(event)
                return events
        
        # Parse table rows
        for table in schedule_tables:
            rows = table.find_all('tr')
            for row in rows:
                # Skip header rows
                if row.find('th'):
                    continue
                
                event = _parse_table_row(row, source_name, sport_type, url)
                if event:
                    events.append(event)
        
        print(f"[Ole Miss Athletics] Found {len(events)} home games")
        
    except Exception as e:
        print(f"[Ole Miss Athletics] Error fetching schedule from {url}: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def _parse_table_row(row, source_name: str, sport_type: str, base_url: str) -> Dict[str, Any]:
    """Parse a table row to extract game information"""
    try:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            return None
        
        # Extract date from first cell
        date_text = cells[0].get_text(strip=True)
        if not date_text:
            return None
        
        # Extract opponent from second cell (usually)
        opponent_text = ""
        for i in range(1, min(4, len(cells))):
            cell_text = cells[i].get_text(strip=True)
            # Skip result columns (W, L, scores, etc.)
            if cell_text and not cell_text.startswith(('W', 'L', 'T', 'Final', 'Cancelled', 'Postponed')):
                opponent_text = cell_text
                break
        
        if not opponent_text:
            return None
        
        # Skip away games (those with @ or "at")
        if opponent_text.startswith('@') or opponent_text.startswith('at '):
            return None
        
        # Clean opponent name
        opponent_clean = re.sub(r'^\s*(vs|VS|v\.|versus|@|at)\s*', '', opponent_text).strip()
        
        # Skip placeholder text
        if opponent_clean in ['OPPONENT', 'TBD', 'TBA', ''] or len(opponent_clean) < 2:
            return None
        
        # Parse date
        try:
            current_year = datetime.now().year
            parsed_date = dtp.parse(date_text, fuzzy=True)
            
            # Default to 7 PM if no time
            if parsed_date.hour == 0 and parsed_date.minute == 0:
                parsed_date = parsed_date.replace(hour=19, minute=0)
        except:
            # Try manual parsing for formats like "Sep 2"
            try:
                # Look for month name and day
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                parts = date_text.lower().strip().split()
                if len(parts) >= 2:
                    month_str = parts[0][:3]
                    day = int(re.search(r'\d+', parts[1]).group())
                    month = month_map.get(month_str, datetime.now().month)
                    parsed_date = datetime(current_year, month, day, 19, 0)
                else:
                    return None
            except:
                return None
        
        # Determine location
        if sport_type == "football":
            location = "Vaught-Hemingway Stadium"
        elif "basketball" in sport_type.lower():
            location = "The Pavilion"
        else:
            location = "TBD"
        
        # Build title
        title = f"Ole Miss vs {opponent_clean}"
        
        return {
            "title": title,
            "start_iso": parsed_date.isoformat(),
            "location": location,
            "description": f"{sport_type.title()} game: {title}",
            "category": "Ole Miss Athletics",
            "source": source_name,
            "link": base_url,
            "cost": "Varies"
        }
    except Exception as e:
        print(f"[Ole Miss Athletics] Error parsing table row: {e}")
        return None


def _parse_schedule_item(item, source_name: str, sport_type: str, base_url: str) -> Dict[str, Any]:
    """Parse a list item to extract game information"""
    try:
        text = item.get_text(strip=True)
        if not text:
            return None
        
        # Look for date pattern
        date_match = re.search(r'(\w+\s+\d+|\d+/\d+)', text)
        if not date_match:
            return None
        
        date_text = date_match.group(1)
        
        # Look for opponent (usually after date, skip @ or "at")
        opponent_match = re.search(r'(?:vs|@|at)\s+([A-Z][^,\n]+)', text, re.IGNORECASE)
        if not opponent_match:
            return None
        
        opponent_text = opponent_match.group(1).strip()
        
        # Skip away games
        if text.lower().startswith('@') or ' at ' in text.lower():
            return None
        
        # Parse date
        try:
            current_year = datetime.now().year
            parsed_date = dtp.parse(date_text, fuzzy=True)
            if parsed_date.hour == 0:
                parsed_date = parsed_date.replace(hour=19, minute=0)
        except:
            return None
        
        # Determine location
        if sport_type == "football":
            location = "Vaught-Hemingway Stadium"
        elif "basketball" in sport_type.lower():
            location = "The Pavilion"
        else:
            location = "TBD"
        
        title = f"Ole Miss vs {opponent_text}"
        
        return {
            "title": title,
            "start_iso": parsed_date.isoformat(),
            "location": location,
            "description": f"{sport_type.title()} game: {title}",
            "category": "Ole Miss Athletics",
            "source": source_name,
            "link": base_url,
            "cost": "Varies"
        }
    except:
        return None

