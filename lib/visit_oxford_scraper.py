"""
Enhanced scraper for Visit Oxford events page
Follows event links to get full details without Selenium
"""

from typing import List, Dict, Any
from bs4 import BeautifulSoup
from dateutil import parser as dtp
import requests
import time


def fetch_visit_oxford_events(url: str, source_name: str) -> List[Dict[str, Any]]:
    """
    Fetch events from Visit Oxford by finding event links and following them
    Returns list of event dictionaries
    """
    events = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        print(f"[Visit Oxford] Loading main page: {url}")
        response = requests.get(url, timeout=10, headers=headers)
        
        if response.status_code != 200:
            print(f"[Visit Oxford] Error: Got status code {response.status_code}")
            return events
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all event links
        event_links = []
        
        # Try multiple selectors for event links
        # Look for links containing /event or /events/
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if href and ('/event' in href.lower() or '/events/' in href.lower()):
                # Make absolute URL
                if href.startswith('/'):
                    href = url.rstrip('/') + href
                elif not href.startswith('http'):
                    href = url.rstrip('/') + '/' + href
                
                # Get text preview
                text = link.get_text(strip=True)
                if href not in [l['href'] for l in event_links]:
                    event_links.append({
                        'href': href,
                        'text': text
                    })
        
        print(f"[Visit Oxford] Found {len(event_links)} event links")
        
        # Limit to first 10 events to avoid timeout (Visit Oxford scraping is slow)
        # Skip if too many links to avoid worker timeout
        if len(event_links) > 20:
            print(f"[Visit Oxford] WARNING: Too many links ({len(event_links)}), skipping to avoid timeout")
            print(f"[Visit Oxford] Consider using a different approach or limiting links")
            return events
        
        for idx, event_link in enumerate(event_links[:10]):
            try:
                href = event_link['href']
                print(f"[Visit Oxford] Processing event {idx + 1}/{min(len(event_links), 10)}: {href}")
                
                # Fetch event detail page with short timeout
                try:
                    detail_response = requests.get(href, timeout=5, headers=headers)
                    if detail_response.status_code != 200:
                        print(f"[Visit Oxford] Skipping {href} - status {detail_response.status_code}")
                        continue
                except requests.exceptions.Timeout:
                    print(f"[Visit Oxford] Timeout fetching {href}, skipping")
                    continue
                except requests.exceptions.RequestException as e:
                    print(f"[Visit Oxford] Error fetching {href}: {e}")
                    continue
                
                detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                
                # Extract title
                title = None
                title_selectors = ['h1', 'h2.event-title', '.event-title', '.event-name', 'title']
                for selector in title_selectors:
                    title_elem = detail_soup.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title and len(title) > 3:
                            break
                
                if not title:
                    title = event_link['text'] or 'Untitled Event'
                
                # Extract date
                date_str = None
                date_selectors = [
                    '.event-date', '.date', '[class*="date"]', 
                    'time', '[datetime]', '.event-time', '.event-datetime'
                ]
                for selector in date_selectors:
                    date_elem = detail_soup.select_one(selector)
                    if date_elem:
                        date_str = date_elem.get('datetime') or date_elem.get('content') or date_elem.get_text(strip=True)
                        if date_str:
                            break
                
                # Extract location/venue
                location = 'Oxford, MS'
                location_selectors = [
                    '.event-location', '.venue', '.location', 
                    '[class*="location"]', '[class*="venue"]', '.event-venue'
                ]
                for selector in location_selectors:
                    loc_elem = detail_soup.select_one(selector)
                    if loc_elem:
                        location = loc_elem.get_text(strip=True)
                        if location:
                            break
                
                # Extract description
                description = ''
                desc_selectors = [
                    '.event-description', '.description', '[class*="description"]',
                    '.event-details', '.content', '.event-content'
                ]
                for selector in desc_selectors:
                    desc_elem = detail_soup.select_one(selector)
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)[:500]  # Limit to 500 chars
                        if description:
                            break
                
                # Try to parse date
                start_iso = None
                if date_str:
                    try:
                        parsed_date = dtp.parse(date_str)
                        start_iso = parsed_date.isoformat()
                    except:
                        pass
                
                # Skip if no valid date
                if not start_iso:
                    print(f"[Visit Oxford] Skipping event (no valid date): {title}")
                    continue
                
                # Check if this is an Ole Miss Athletic event (filter out duplicates)
                title_lower = title.lower()
                description_lower = description.lower()
                if any(keyword in title_lower or keyword in description_lower 
                       for keyword in ['ole miss', 'rebels', 'football', 'basketball', 'baseball']):
                    # Check if it's actually an athletic event vs just mentioning Ole Miss
                    if any(sport in title_lower for sport in [' vs ', ' vs. ', ' game', ' matchup', ' schedule']):
                        print(f"[Visit Oxford] Skipping duplicate athletic event: {title}")
                        continue
                
                event = {
                    "title": title,
                    "start_iso": start_iso,
                    "location": location,
                    "description": description,
                    "category": "Community",  # Will be recategorized by categorizer
                    "source": source_name,
                    "link": href,
                    "cost": "Free"  # Default
                }
                
                events.append(event)
                print(f"[Visit Oxford] Successfully parsed: {title}")
                
                # Skip delay to speed up (already limited to 10 events)
                # time.sleep(0.5)  # Removed to prevent timeout
                
            except Exception as e:
                print(f"[Visit Oxford] Error processing event {href}: {e}")
                continue
        
        print(f"[Visit Oxford] Successfully scraped {len(events)} events")
            
    except Exception as e:
        print(f"[Visit Oxford] Error in scraper: {e}")
        import traceback
        traceback.print_exc()
    
    return events

