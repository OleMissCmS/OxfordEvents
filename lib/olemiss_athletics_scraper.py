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
        # Reduced timeout to 10s - fail faster to avoid worker timeouts
        try:
            response = requests.get(url, timeout=10, headers=headers)
        except requests.exceptions.Timeout:
            print(f"[Ole Miss Athletics] Timeout fetching schedule from {url} (10s)")
            return events
        except requests.exceptions.RequestException as e:
            print(f"[Ole Miss Athletics] Error fetching schedule from {url}: {e}")
            return events
        
        if response.status_code != 200:
            print(f"[Ole Miss Athletics] Error: Got status code {response.status_code}")
            return events
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"[Ole Miss Athletics] Error parsing HTML from {url}: {e}")
            return events
        
        # Ole Miss Athletics pages use divs with game information
        # Look for schedule items - they contain date, opponent, and game info
        # Common patterns: divs with dates, "vs" indicators, game centers
        
        # Try finding game entries by looking for "vs" and "at" patterns
        # Games are often in divs or sections with dates and team names
        all_text = soup.get_text()
        
        # Look for date patterns followed by opponent info
        # Pattern: Date (like "Nov 8", "Sep 13") followed by "vs" or "at"
        
        # Method 1: Find schedule container and parse games
        schedule_container = soup.find(['div', 'section'], class_=lambda x: x and ('schedule' in str(x).lower() if x else False))
        
        # Method 2: Look for game entries by finding "vs" and "at" patterns with dates
        # Find all text that contains date patterns and game indicators
        game_pattern = re.compile(r'([A-Z][a-z]{2})\s+(\d{1,2}).*?(vs|at)\s+([A-Z][^,\n]+)', re.IGNORECASE | re.DOTALL)
        matches = game_pattern.findall(all_text)
        
        # Method 3: Find divs containing game information
        # Look for elements that contain both date and opponent info
        game_elements = soup.find_all(['div', 'li', 'tr'], string=re.compile(r'(vs|at)\s+[A-Z]'))
        
        # Also try finding by looking for game links or calendar entries
        calendar_items = soup.find_all(['div', 'article'], class_=lambda x: x and (
            'game' in str(x).lower() or 
            'schedule' in str(x).lower() or
            'event' in str(x).lower()
        ) if x else False)
        
        # Try to extract games from various structures
        seen_games = set()  # Avoid duplicates
        
        # Process calendar items first
        for item in calendar_items:
            event = _parse_game_element(item, source_name, sport_type, url, seen_games)
            if event:
                events.append(event)
        
        # If no events from calendar items, try parsing text patterns
        if not events:
            for match in matches:
                month_abbr, day, game_type, opponent = match
                # Skip away games
                if game_type.lower() == 'at':
                    continue
                
                # Parse date
                try:
                    month_map = {
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                    }
                    month = month_map.get(month_abbr.lower()[:3])
                    day_int = int(day)
                    current_year = datetime.now().year
                    
                    # Create date string for deduplication
                    game_key = f"{month_abbr} {day} vs {opponent.strip()}"
                    if game_key in seen_games:
                        continue
                    seen_games.add(game_key)
                    
                    # Determine year (if month has passed, assume next year)
                    parsed_date = datetime(current_year, month, day_int, 19, 0)
                    if parsed_date < datetime.now():
                        parsed_date = datetime(current_year + 1, month, day_int, 19, 0)
                    
                    # Parse time from context if available (would need more sophisticated parsing)
                    # For now, default to 7 PM
                    
                    opponent_clean = opponent.strip()
                    # Clean opponent name - remove date/time patterns
                    opponent_clean = opponent_clean.strip()
                    # Remove date patterns like "Nov 08 / Noon" or "Nov 8 / 12 PM"
                    opponent_clean = re.sub(r'\s*[A-Z][a-z]{2}\s+\d{1,2}\s*/\s*(Noon|\d{1,2}\s*[AP]M)', '', opponent_clean, flags=re.IGNORECASE)
                    opponent_clean = re.sub(r'\s*/\s*(Noon|\d{1,2}\s*[AP]M)', '', opponent_clean, flags=re.IGNORECASE)
                    opponent_clean = re.sub(r'\s*\d{1,2}/\d{1,2}\s*/\s*(Noon|\d{1,2}\s*[AP]M)', '', opponent_clean, flags=re.IGNORECASE)
                    opponent_clean = re.sub(r'\s+Oxford.*$', '', opponent_clean, flags=re.IGNORECASE)
                    opponent_clean = re.sub(r'\s+Miss\..*$', '', opponent_clean, flags=re.IGNORECASE)
                    opponent_clean = opponent_clean.strip()
                    
                    if not opponent_clean or len(opponent_clean) < 2:
                        continue
                    
                    # Determine location and title based on sport
                    if sport_type == "football":
                        location = "Vaught-Hemingway Stadium"
                        title = f"Ole Miss vs {opponent_clean}"
                        sport_desc = "Football"
                    elif "basketball" in sport_type.lower():
                        location = "The Pavilion"
                        # Determine if men's or women's basketball based on sport_type or source
                        sport_type_lower = sport_type.lower()
                        source_lower = source_name.lower()
                        if "women" in sport_type_lower or "wbb" in sport_type_lower or "women" in source_lower:
                            title = f"Ole Miss Women's Basketball vs {opponent_clean}"
                            sport_desc = "Women's Basketball"
                        elif "men" in sport_type_lower or "mbb" in sport_type_lower or "men" in source_lower:
                            title = f"Ole Miss Men's Basketball vs {opponent_clean}"
                            sport_desc = "Men's Basketball"
                        else:
                            # Default based on URL
                            if "womens" in url.lower() or "women" in url.lower():
                                title = f"Ole Miss Women's Basketball vs {opponent_clean}"
                                sport_desc = "Women's Basketball"
                            else:
                                title = f"Ole Miss Men's Basketball vs {opponent_clean}"
                                sport_desc = "Men's Basketball"
                    else:
                        location = "TBD"
                        title = f"Ole Miss vs {opponent_clean}"
                        sport_desc = sport_type.title()
                    
                    events.append({
                        "title": title,
                        "start_iso": parsed_date.isoformat(),
                        "location": location,
                        "description": f"{sport_desc} game: {title}",
                        "category": "Ole Miss Athletics",
                        "source": source_name,
                        "link": url,
                        "cost": "Varies"
                    })
                except Exception as e:
                    print(f"[Ole Miss Athletics] Error parsing match {match}: {e}")
                    continue
        
        # If still no events, try table parsing as fallback
        if not events:
            schedule_tables = soup.find_all('table')
            for table in schedule_tables:
                rows = table.find_all('tr')
                for row in rows:
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
        
        # Clean opponent name - remove vs/@ prefixes and date/time patterns
        opponent_clean = re.sub(r'^\s*(vs|VS|v\.|versus|@|at)\s*', '', opponent_text).strip()
        # Remove date patterns like "Nov 08 / Noon" or "Nov 8 / 12 PM"
        opponent_clean = re.sub(r'\s*[A-Z][a-z]{2}\s+\d{1,2}\s*/\s*(Noon|\d{1,2}\s*[AP]M)', '', opponent_clean, flags=re.IGNORECASE)
        opponent_clean = re.sub(r'\s*/\s*(Noon|\d{1,2}\s*[AP]M)', '', opponent_clean, flags=re.IGNORECASE)
        opponent_clean = re.sub(r'\s*\d{1,2}/\d{1,2}\s*/\s*(Noon|\d{1,2}\s*[AP]M)', '', opponent_clean, flags=re.IGNORECASE)
        
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
        
        # Determine location and title based on sport
        if sport_type == "football":
            location = "Vaught-Hemingway Stadium"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = "Football"
        elif "basketball" in sport_type.lower():
            location = "The Pavilion"
            # Determine if men's or women's basketball based on sport_type or source
            sport_type_lower = sport_type.lower()
            source_lower = source_name.lower()
            if "women" in sport_type_lower or "wbb" in sport_type_lower or "women" in source_lower:
                title = f"Ole Miss Women's Basketball vs {opponent_clean}"
                sport_desc = "Women's Basketball"
            elif "men" in sport_type_lower or "mbb" in sport_type_lower or "men" in source_lower:
                title = f"Ole Miss Men's Basketball vs {opponent_clean}"
                sport_desc = "Men's Basketball"
            else:
                # Default based on URL
                if "womens" in base_url.lower() or "women" in base_url.lower():
                    title = f"Ole Miss Women's Basketball vs {opponent_clean}"
                    sport_desc = "Women's Basketball"
                else:
                    title = f"Ole Miss Men's Basketball vs {opponent_clean}"
                    sport_desc = "Men's Basketball"
        elif sport_type == "baseball":
            location = "Swayze Field"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = "Baseball"
        elif sport_type == "softball":
            location = "Ole Miss Softball Complex"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = "Softball"
        elif sport_type == "volleyball":
            location = "The Pavilion"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = "Volleyball"
        else:
            location = "TBD"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = sport_type.title()
        
        return {
            "title": title,
            "start_iso": parsed_date.isoformat(),
            "location": location,
            "description": f"{sport_desc} game: {title}",
            "category": "Ole Miss Athletics",
            "source": source_name,
            "link": base_url,
            "cost": "Varies"
        }
    except Exception as e:
        print(f"[Ole Miss Athletics] Error parsing table row: {e}")
        return None


def _parse_game_element(elem, source_name: str, sport_type: str, base_url: str, seen_games: set) -> Dict[str, Any]:
    """Parse a game element (div/article) to extract game information"""
    try:
        text = elem.get_text(separator=' ', strip=True)
        if not text:
            return None
        
        # Look for date pattern (e.g., "Nov 8", "Sep 13")
        date_match = re.search(r'([A-Z][a-z]{2})\s+(\d{1,2})', text)
        if not date_match:
            return None
        
        month_abbr, day = date_match.groups()
        
        # Look for "vs" or "at" pattern - be more specific to avoid matching date patterns
        # First, try to find a clear "vs" followed by opponent name
        game_match = re.search(r'\b(vs|at)\s+([A-Z#][A-Za-z\s&]+?)(?:\s*[,\n\(]|\s*$|Logo|Oxford|Miss\.)', text, re.IGNORECASE)
        if not game_match:
            # Fallback to simpler pattern
            game_match = re.search(r'(vs|at)\s+([A-Z#][^,\n\(]+)', text, re.IGNORECASE)
        
        if not game_match:
            return None
        
        game_type, opponent_raw = game_match.groups()
        
        # Skip away games
        if game_type.lower() == 'at':
            return None
        
        # Clean opponent name (remove extra info like logos, rankings, locations, dates/times)
        opponent_clean = opponent_raw.strip()
        
        # Remove date/time patterns that got included in opponent - patterns like:
        # "Nov 15 / 2:30-3:30 or 5-7 PM vs Florida" -> should extract just "Florida"
        # "Nov 08 / Noon vs The Citadel" -> should extract just "The Citadel"
        # Strategy: Find the last "vs" after a date pattern and extract what follows
        # First, try to remove everything from date pattern up to and including the next "vs"
        opponent_clean = re.sub(r'[A-Z][a-z]{2}\s+\d{1,2}\s*/\s*[^vs]+?\s+vs\s+', '', opponent_clean, flags=re.IGNORECASE)
        opponent_clean = re.sub(r'\s*[A-Z][a-z]{2}\s+\d{1,2}\s*/\s*[^A-Z]+?vs\s+', '', opponent_clean, flags=re.IGNORECASE)
        # Remove standalone date patterns
        opponent_clean = re.sub(r'\s*[A-Z][a-z]{2}\s+\d{1,2}\s*/\s*(Noon|\d{1,2}\s*[AP]M|\d{1,2}:\d{2}[^\s]*?)', '', opponent_clean, flags=re.IGNORECASE)
        opponent_clean = re.sub(r'\s*/\s*(Noon|\d{1,2}\s*[AP]M|\d{1,2}:\d{2}[^\s]*?\s*(or|PM|AM|pm|am))', '', opponent_clean, flags=re.IGNORECASE)
        opponent_clean = re.sub(r'\s*\d{1,2}/\d{1,2}\s*/\s*(Noon|\d{1,2}\s*[AP]M)', '', opponent_clean, flags=re.IGNORECASE)
        # Remove "vs" if it appears at the start (duplicate)
        opponent_clean = re.sub(r'^\s*(vs|VS)\s+', '', opponent_clean, flags=re.IGNORECASE)
        # Remove other patterns
        opponent_clean = re.sub(r'^(#?\d+\s+)?', '', opponent_clean)
        opponent_clean = re.sub(r'\s+Logo.*$', '', opponent_clean, flags=re.IGNORECASE)
        opponent_clean = re.sub(r'\s+Oxford.*$', '', opponent_clean, flags=re.IGNORECASE)
        opponent_clean = re.sub(r'\s+Miss\..*$', '', opponent_clean, flags=re.IGNORECASE)
        opponent_clean = opponent_clean.strip()
        
        if not opponent_clean or len(opponent_clean) < 2:
            return None
        
        # Create deduplication key
        game_key = f"{month_abbr} {day} vs {opponent_clean}"
        if game_key in seen_games:
            return None
        seen_games.add(game_key)
        
        # Parse date
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        month = month_map.get(month_abbr.lower()[:3])
        if not month:
            return None
        
        day_int = int(day)
        current_year = datetime.now().year
        
        # Parse time if available (look for patterns like "Noon", "7 p.m.", "2:30-3:30 or 5-7 PM")
        time_match = re.search(r'(Noon|12\s*[Pp][Mm]|(\d{1,2}):?(\d{2})?\s*([AaPp][Mm])|(\d{1,2})\s*([Pp][Mm]))', text, re.IGNORECASE)
        hour = 19  # Default 7 PM
        minute = 0
        
        if time_match:
            time_str = time_match.group(0).lower()
            if 'noon' in time_str or '12' in time_str:
                hour = 12
                minute = 0
            else:
                # Try to extract hour
                hour_match = re.search(r'(\d{1,2})', time_str)
                if hour_match:
                    hour = int(hour_match.group(1))
                    if 'pm' in time_str and hour < 12:
                        hour += 12
                    elif 'am' in time_str and hour == 12:
                        hour = 0
        
        parsed_date = datetime(current_year, month, day_int, hour, minute)
        
        # If date has passed this year, assume next year
        if parsed_date < datetime.now():
            parsed_date = datetime(current_year + 1, month, day_int, hour, minute)
        
        # Determine location and build title with sport description
        if sport_type == "football":
            location = "Vaught-Hemingway Stadium"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = "Football"
        elif "basketball" in sport_type.lower():
            location = "The Pavilion"
            # Determine if men's or women's basketball based on sport_type or source
            sport_type_lower = sport_type.lower()
            source_lower = source_name.lower()
            if "women" in sport_type_lower or "wbb" in sport_type_lower or "women" in source_lower:
                title = f"Ole Miss Women's Basketball vs {opponent_clean}"
                sport_desc = "Women's Basketball"
            elif "men" in sport_type_lower or "mbb" in sport_type_lower or "men" in source_lower:
                title = f"Ole Miss Men's Basketball vs {opponent_clean}"
                sport_desc = "Men's Basketball"
            else:
                # Default based on URL
                if "womens" in base_url.lower() or "women" in base_url.lower():
                    title = f"Ole Miss Women's Basketball vs {opponent_clean}"
                    sport_desc = "Women's Basketball"
                else:
                    title = f"Ole Miss Men's Basketball vs {opponent_clean}"
                    sport_desc = "Men's Basketball"
        elif sport_type == "baseball":
            location = "Swayze Field"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = "Baseball"
        elif sport_type == "softball":
            location = "Ole Miss Softball Complex"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = "Softball"
        elif sport_type == "volleyball":
            location = "The Pavilion"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = "Volleyball"
        else:
            location = "TBD"
            title = f"Ole Miss vs {opponent_clean}"
            sport_desc = sport_type.title()
        
        return {
            "title": title,
            "start_iso": parsed_date.isoformat(),
            "location": location,
            "description": f"{sport_desc} game: {title}",
            "category": "Ole Miss Athletics",
            "source": source_name,
            "link": base_url,
            "cost": "Varies"
        }
    except Exception as e:
        print(f"[Ole Miss Athletics] Error parsing game element: {e}")
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
        elif sport_type == "baseball":
            location = "Swayze Field"
        elif sport_type == "softball":
            location = "Ole Miss Softball Complex"
        elif sport_type == "volleyball":
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

