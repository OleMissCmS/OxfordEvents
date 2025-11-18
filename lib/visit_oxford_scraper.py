"""
Enhanced scraper for Visit Oxford events page
Follows event links to get full details without Selenium
"""

from typing import List, Dict, Any, Optional, Union
from bs4 import BeautifulSoup
from dateutil import parser as dtp
import requests
import json
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
        event_links = _extract_event_links(soup, url)
        print(f"[Visit Oxford] Found {len(event_links)} candidate event links")
        
        if not event_links:
            print("[Visit Oxford] No event links found on main page.")
            return events
        
        MAX_EVENTS = 30
        processed = 0
        
        for idx, event_link in enumerate(event_links):
            if processed >= MAX_EVENTS:
                print(f"[Visit Oxford] Reached max events ({MAX_EVENTS}) to prevent timeout.")
                break
            try:
                href = event_link['href']
                print(f"[Visit Oxford] Processing event {idx + 1}/{len(event_links)}: {href}")
                
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
                
                event_payload = _parse_event_detail(detail_soup, event_link)
                
                if not event_payload:
                    print(f"[Visit Oxford] Skipping {href} - could not parse required fields.")
                    continue
                
                title = event_payload["title"]
                start_iso = event_payload["start_iso"]
                location = event_payload["location"]
                description = event_payload["description"]
                cost = event_payload.get("cost", "Free")
                
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
                    "cost": cost or "Free"
                }
                
                events.append(event)
                processed += 1
                print(f"[Visit Oxford] Successfully parsed: {title}")
                
                if processed % 5 == 0:
                    time.sleep(0.2)
                
            except Exception as e:
                print(f"[Visit Oxford] Error processing event {href}: {e}")
                continue
        
        print(f"[Visit Oxford] Successfully scraped {len(events)} events")
            
    except Exception as e:
        print(f"[Visit Oxford] Error in scraper: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def _extract_event_links(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    links = []
    seen = set()

    candidate_selectors = [
        'a.elementor-post__thumbnail__link',
        '.event-card a',
        '.tribe-events-widget-events-list__event-title a',
        '.tribe-events-calendar-list__event-title a',
        'article a',
        'a[href*="/event/"]',
        'a[href*="/events/"]',
    ]

    for selector in candidate_selectors:
        for anchor in soup.select(selector):
            href = anchor.get('href')
            if not href:
                continue

            href = _normalize_link(href, base_url)
            if not href or href in seen:
                continue

            text = anchor.get_text(strip=True)
            seen.add(href)
            links.append({'href': href, 'text': text})

    return links


def _normalize_link(href: str, base_url: str) -> Optional[str]:
    if href.startswith(('mailto:', 'tel:')):
        return None
    if href.startswith('/'):
        return base_url.rstrip('/') + href
    if href.startswith('http'):
        return href
    return base_url.rstrip('/') + '/' + href


def _parse_event_detail(detail_soup: BeautifulSoup, event_link: Dict[str, str]) -> Optional[Dict[str, Union[str, None]]]:
    payload = _parse_ld_json(detail_soup)

    if payload is None:
        payload = _parse_event_fallback(detail_soup, event_link)

    if payload and payload.get("start_iso"):
        return payload

    return None


def _parse_ld_json(detail_soup: BeautifulSoup) -> Optional[Dict[str, Union[str, None]]]:
    scripts = detail_soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue

        data_items = data if isinstance(data, list) else [data]

        for item in data_items:
            if not isinstance(item, dict):
                continue
            if item.get('@type') not in {'Event', 'MusicEvent', 'Festival'}:
                continue

            title = item.get('name')
            start = item.get('startDate') or item.get('startTime')
            location = ''

            loc = item.get('location')
            if isinstance(loc, dict):
                location = loc.get('name') or loc.get('address', '')
            elif isinstance(loc, str):
                location = loc

            description = item.get('description', '')
            offers = item.get('offers')
            cost = None
            if isinstance(offers, dict):
                price = offers.get('price')
                currency = offers.get('priceCurrency', 'USD')
                if price:
                    cost = f"{currency} {price}".strip()

            start_iso = None
            if start:
                try:
                    start_iso = dtp.parse(start).isoformat()
                except Exception:
                    start_iso = None

            if not start_iso:
                continue

            return {
                "title": title or '',
                "start_iso": start_iso,
                "location": location or 'Oxford, MS',
                "description": description or '',
                "cost": cost or None,
            }

    return None


def _parse_event_fallback(detail_soup: BeautifulSoup, event_link: Dict[str, str]) -> Optional[Dict[str, Union[str, None]]]:
    title = None
    title_selectors = ['h1', 'h2.event-title', '.event-title', '.event-name', 'title']
    for selector in title_selectors:
        title_elem = detail_soup.select_one(selector)
        if title_elem:
            title = title_elem.get_text(strip=True)
            if title and len(title) > 3:
                break

    if not title:
        title = event_link.get('text') or 'Untitled Event'

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

    description = ''
    desc_selectors = [
        '.event-description', '.description', '[class*="description"]',
        '.event-details', '.content', '.event-content'
    ]
    for selector in desc_selectors:
        desc_elem = detail_soup.select_one(selector)
        if desc_elem:
            description = desc_elem.get_text(strip=True)[:500]
            if description:
                break

    start_iso = None
    if date_str:
        try:
            parsed_date = dtp.parse(date_str)
            start_iso = parsed_date.isoformat()
        except Exception:
            start_iso = None

    if not start_iso:
        return None

    return {
        "title": title,
        "start_iso": start_iso,
        "location": location,
        "description": description,
        "cost": None,
    }
