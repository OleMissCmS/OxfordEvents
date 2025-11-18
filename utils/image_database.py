"""
Image database and fetching utilities
Stores team logos and venue images, with automatic fetching from Wikipedia and Google
"""

import json
import os
import re
import hashlib
from typing import Optional, Dict, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
import time
from collections import defaultdict
from threading import Lock

# Use persistent disk storage if available
try:
    from utils.storage import (
        get_images_dir, get_database_dir, 
        get_json_db_path, log_storage_setup
    )
    IMAGES_DIR = get_images_dir()
    DB_DIR = get_database_dir()
    TEAM_LOGOS_DB = get_json_db_path("team_logos.json")
    VENUE_IMAGES_DB = get_json_db_path("venue_images.json")
    
    # Log storage setup on first import
    try:
        _storage_logged = getattr(__import__('utils.image_database', fromlist=['']), '_storage_logged', False)
        if not _storage_logged:
            log_storage_setup()
            setattr(__import__('utils.image_database', fromlist=['']), '_storage_logged', True)
    except:
        pass
except Exception as e:
    # Fallback to default paths
    DB_DIR = "data"
    IMAGES_DIR = os.path.join("static", "images", "cache")
    TEAM_LOGOS_DB = os.path.join(DB_DIR, "team_logos.json")
    VENUE_IMAGES_DB = os.path.join(DB_DIR, "venue_images.json")
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

# Ensure directories exist (in case storage.py fails)
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Rate limiting for DuckDuckGo requests
_rate_limit_lock = Lock()
_last_request_time = defaultdict(float)
_min_request_interval = 2.0  # Minimum 2 seconds between DuckDuckGo requests
_rate_limit_errors = defaultdict(int)  # Track rate limit errors per endpoint
_max_rate_limit_errors = 5  # Stop trying after 5 rate limit errors


def load_database(db_path: str) -> Dict:
    """Load JSON database file (fallback only)"""
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_database(db_path: str, data: Dict):
    """Save JSON database file (fallback only)"""
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_filename_from_url(url: str, team_name: str = "") -> str:
    """Generate a safe filename from URL or team name"""
    if team_name:
        # Use team name for filename
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', team_name.lower())
        ext = urlparse(url).path.split('.')[-1].lower()
        if ext not in ['png', 'jpg', 'jpeg', 'svg', 'gif', 'webp']:
            ext = 'png'
        return f"{safe_name}.{ext}"
    else:
        # Use URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = urlparse(url).path.split('.')[-1].lower()
        if ext not in ['png', 'jpg', 'jpeg', 'svg', 'gif', 'webp']:
            ext = 'png'
        return f"{url_hash}.{ext}"


def download_image(url: str, local_path: str) -> bool:
    """Download image from URL and save locally"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if response.status_code == 200 and response.content:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"[image_database] Error downloading image from {url}: {e}")
    return False


def fetch_wikipedia_team_logo(team_name: str) -> Optional[str]:
    """
    Fetch team logo from Wikipedia athletics page
    Returns local file path if successful, None otherwise
    """
    try:
        # Construct Wikipedia search URL
        # Try variations: "Team Name athletics", "Team Name (sports)", etc.
        search_queries = [
            f"{team_name} athletics",
            f"{team_name} (sports)",
            f"{team_name} football",
            f"{team_name}",
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        for query in search_queries:
            try:
                # Search Wikipedia
                search_url = f"https://en.wikipedia.org/wiki/{quote(query.replace(' ', '_'))}"
                response = requests.get(search_url, timeout=10, headers=headers, allow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for infobox logo image
                    # Wikipedia typically has logos in infobox or main article image
                    infobox = soup.find('table', class_='infobox')
                    if infobox:
                        # Look for image in infobox
                        img_tag = infobox.find('img')
                        if img_tag and img_tag.get('src'):
                            img_url = img_tag.get('src')
                            # Convert relative URLs to absolute
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            elif img_url.startswith('/'):
                                img_url = 'https://en.wikipedia.org' + img_url
                            
                            # Try to get higher resolution version
                            if 'thumb' in img_url:
                                img_url = img_url.split('/thumb/')[0] + '/' + '/'.join(img_url.split('/thumb/')[1].split('/')[2:])
                            
                            # Download and save
                            filename = get_filename_from_url(img_url, team_name)
                            local_path = os.path.join(IMAGES_DIR, filename)
                            
                            if download_image(img_url, local_path):
                                # Return relative path from static/images
                                return f"/static/images/cache/{filename}"
                    
                    # Also check for main article image
                    img_tags = soup.find_all('img', limit=10)
                    for img_tag in img_tags:
                        src = img_tag.get('src', '')
                        if any(keyword in src.lower() for keyword in ['logo', 'seal', 'emblem', 'crest']):
                            if src.startswith('//'):
                                img_url = 'https:' + src
                            elif src.startswith('/'):
                                img_url = 'https://en.wikipedia.org' + src
                            else:
                                continue
                            
                            # Remove thumb size
                            if 'thumb' in img_url:
                                img_url = img_url.split('/thumb/')[0] + '/' + '/'.join(img_url.split('/thumb/')[1].split('/')[2:])
                            
                            filename = get_filename_from_url(img_url, team_name)
                            local_path = os.path.join(IMAGES_DIR, filename)
                            
                            if download_image(img_url, local_path):
                                return f"/static/images/cache/{filename}"
                
                # Small delay to be polite
                time.sleep(0.5)
            except Exception as e:
                print(f"[image_database] Error searching Wikipedia for '{query}': {e}")
                continue
        
        return None
    except Exception as e:
        print(f"[image_database] Error fetching Wikipedia logo for {team_name}: {e}")
        return None


def fetch_wikipedia_venue_image(venue_name: str) -> Optional[str]:
    """
    Fetch venue image from Wikipedia with "Ole Miss" prefix
    Returns local file path if successful, None otherwise
    """
    try:
        # Add "Ole Miss" prefix
        queries = [
            f"Ole Miss {venue_name}",
            venue_name,
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        for query in queries:
            try:
                search_url = f"https://en.wikipedia.org/wiki/{quote(query.replace(' ', '_'))}"
                response = requests.get(search_url, timeout=10, headers=headers, allow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for main article image or infobox image
                    infobox = soup.find('table', class_='infobox')
                    if infobox:
                        img_tag = infobox.find('img')
                        if img_tag and img_tag.get('src'):
                            img_url = img_tag.get('src')
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            elif img_url.startswith('/'):
                                img_url = 'https://en.wikipedia.org' + img_url
                            
                            # Get higher resolution
                            if 'thumb' in img_url:
                                img_url = img_url.split('/thumb/')[0] + '/' + '/'.join(img_url.split('/thumb/')[1].split('/')[2:])
                            
                            filename = get_filename_from_url(img_url, venue_name)
                            local_path = os.path.join(IMAGES_DIR, filename)
                            
                            if download_image(img_url, local_path):
                                return f"/static/images/cache/{filename}"
                    
                    # Check main article images
                    img_tags = soup.find_all('img', limit=10)
                    for img_tag in img_tags:
                        src = img_tag.get('src', '')
                        # Skip common non-relevant images
                        if any(skip in src.lower() for skip in ['icon', 'stub', 'flag', 'map']):
                            continue
                        
                        if src.startswith('//'):
                            img_url = 'https:' + src
                        elif src.startswith('/'):
                            img_url = 'https://en.wikipedia.org' + src
                        else:
                            continue
                        
                        if 'thumb' in img_url:
                            img_url = img_url.split('/thumb/')[0] + '/' + '/'.join(img_url.split('/thumb/')[1].split('/')[2:])
                        
                        filename = get_filename_from_url(img_url, venue_name)
                        local_path = os.path.join(IMAGES_DIR, filename)
                        
                        if download_image(img_url, local_path):
                            return f"/static/images/cache/{filename}"
                
                time.sleep(0.5)
            except Exception as e:
                print(f"[image_database] Error searching Wikipedia for venue '{query}': {e}")
                continue
        
        return None
    except Exception as e:
        print(f"[image_database] Error fetching Wikipedia venue image for {venue_name}: {e}")
        return None


def _check_rate_limit(endpoint: str = "default") -> bool:
    """Check if we should throttle requests due to rate limiting"""
    with _rate_limit_lock:
        # If we've hit too many rate limit errors, stop trying
        if _rate_limit_errors[endpoint] >= _max_rate_limit_errors:
            return False
        
        # Check time since last request
        last_time = _last_request_time[endpoint]
        elapsed = time.time() - last_time
        
        if elapsed < _min_request_interval:
            # Wait until minimum interval has passed
            sleep_time = _min_request_interval - elapsed
            time.sleep(sleep_time)
        
        return True


def _record_rate_limit_error(endpoint: str = "default"):
    """Record a rate limit error"""
    with _rate_limit_lock:
        _rate_limit_errors[endpoint] += 1


def _record_successful_request(endpoint: str = "default"):
    """Record a successful request"""
    with _rate_limit_lock:
        _last_request_time[endpoint] = time.time()
        # Reset error count on success
        _rate_limit_errors[endpoint] = 0


def fetch_duckduckgo_image(query: str, num_results: int = 5) -> Optional[str]:
    """Fetch image using DuckDuckGo"""
    # Check rate limit first
    if not _check_rate_limit("duckduckgo"):
        return None
    
    try:
        from duckduckgo_search import DDGS
        
        search_query = f"{query} oxford MS"
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    keywords=search_query,
                    max_results=num_results,
                    safesearch='moderate'
                ))
        except Exception as e:
            error_str = str(e).lower()
            if 'ratelimit' in error_str or '403' in error_str or '202' in error_str:
                _record_rate_limit_error("duckduckgo")
                return None
            else:
                raise
        
        for result in results:
            img_url = result.get('image', '') or result.get('url', '')
            if not img_url:
                continue
            
            if not any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', 'image']):
                continue
            
            filename = get_filename_from_url(img_url, query.replace(' ', '_'))
            local_path = os.path.join(IMAGES_DIR, filename)
            
            if download_image(img_url, local_path):
                print(f"[image_database] Successfully downloaded from DuckDuckGo: {img_url[:80]}...")
                _record_successful_request("duckduckgo")
                return f"/static/images/cache/{filename}"
        
        _record_successful_request("duckduckgo")
        return None
    except ImportError:
        return None
    except Exception as e:
        print(f"[image_database] DuckDuckGo error for '{query}': {e}")
        return None


def fetch_pexels_image(query: str, num_results: int = 5) -> Optional[str]:
    """Fetch image using Pexels API"""
    api_key = os.environ.get('PEXELS_API_KEY')
    if not api_key:
        return None
    
    try:
        search_query = f"{query} oxford MS"
        headers = {
            'Authorization': api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(
            'https://api.pexels.com/v1/search',
            params={'query': search_query, 'per_page': num_results, 'orientation': 'landscape'},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            photos = data.get('photos', [])
            
            for photo in photos:
                img_url = photo.get('src', {}).get('medium') or photo.get('src', {}).get('large')
                if img_url:
                    # Return the Pexels URL directly (they allow hotlinking)
                    print(f"[image_database] Found Pexels image: {img_url[:80]}...")
                    return img_url
        
        return None
    except Exception as e:
        print(f"[image_database] Pexels error for '{query}': {e}")
        return None


def fetch_bing_image(query: str, num_results: int = 5) -> Optional[str]:
    """Fetch image using Bing Image Search"""
    try:
        search_query = f"{query} oxford MS"
        bing_url = f"https://www.bing.com/images/search?q={quote(search_query)}&form=HDRSC2&first=1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(bing_url, timeout=15, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            img_links = soup.find_all('a', class_='iusc', limit=num_results)
            
            for link in img_links:
                m_attr = link.get('m', '{}')
                try:
                    import json
                    data = json.loads(m_attr)
                    img_url = data.get('murl', '')
                    
                    if img_url:
                        filename = get_filename_from_url(img_url, query.replace(' ', '_'))
                        local_path = os.path.join(IMAGES_DIR, filename)
                        
                        if download_image(img_url, local_path):
                            print(f"[image_database] Successfully downloaded from Bing: {img_url[:80]}...")
                            return f"/static/images/cache/{filename}"
                except:
                    continue
        return None
    except Exception as e:
        print(f"[image_database] Bing error for '{query}': {e}")
        return None


def fetch_google_image_scrape(query: str, num_results: int = 5) -> Optional[str]:
    """Fetch image using Google Image Search (scraping, no API key)"""
    try:
        search_query = f"{query} oxford MS"
        google_url = f"https://www.google.com/search?tbm=isch&q={quote(search_query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(google_url, timeout=15, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Google stores images in various ways, try common patterns
            img_tags = soup.find_all('img', limit=20)
            
            for img in img_tags:
                src = img.get('src', '') or img.get('data-src', '')
                if not src or src.startswith('data:'):
                    continue
                
                # Filter out Google's own images
                if 'google.com' in src.lower() or 'googleusercontent' in src.lower():
                    continue
                
                if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    # Convert relative URLs
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        continue  # Skip relative URLs
                    
                    filename = get_filename_from_url(src, query.replace(' ', '_'))
                    local_path = os.path.join(IMAGES_DIR, filename)
                    
                    if download_image(src, local_path):
                        print(f"[image_database] Successfully downloaded from Google: {src[:80]}...")
                        return f"/static/images/cache/{filename}"
        return None
    except Exception as e:
        print(f"[image_database] Google error for '{query}': {e}")
        return None


def fetch_brave_image(query: str, num_results: int = 5) -> Optional[str]:
    """Fetch image using Brave Search (scraping)"""
    try:
        search_query = f"{query} oxford MS"
        brave_url = f"https://search.brave.com/images?q={quote(search_query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(brave_url, timeout=15, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            img_tags = soup.find_all('img', limit=20)
            
            for img in img_tags:
                src = img.get('src', '') or img.get('data-src', '')
                if not src or src.startswith('data:'):
                    continue
                
                if 'brave.com' in src.lower():
                    continue
                
                if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        continue
                    
                    filename = get_filename_from_url(src, query.replace(' ', '_'))
                    local_path = os.path.join(IMAGES_DIR, filename)
                    
                    if download_image(src, local_path):
                        print(f"[image_database] Successfully downloaded from Brave: {src[:80]}...")
                        return f"/static/images/cache/{filename}"
        return None
    except Exception as e:
        print(f"[image_database] Brave error for '{query}': {e}")
        return None


def fetch_google_image(query: str, num_results: int = 5, timeout: int = 8) -> Optional[str]:
    """
    Fetch image using multiple search engines as fallbacks.
    Tries: DuckDuckGo -> Bing -> Google -> Brave
    Returns local file path if successful, None otherwise
    Has overall timeout to prevent blocking page load
    """
    import time
    start_time = time.time()
    
    # Try each search engine in order until one succeeds or timeout
    search_engines = [
        ("DuckDuckGo", fetch_duckduckgo_image),
        ("Bing", fetch_bing_image),
        ("Google", fetch_google_image_scrape),
        ("Brave", fetch_brave_image),
    ]
    
    for engine_name, fetch_func in search_engines:
        # Check timeout
        if time.time() - start_time > timeout:
            print(f"[image_database] Timeout ({timeout}s) exceeded for '{query}', skipping remaining engines")
            break
        
        try:
            print(f"[image_database] Trying {engine_name} for '{query}'...")
            result = fetch_func(query, num_results)
            if result:
                return result
        except Exception as e:
            print(f"[image_database] {engine_name} failed for '{query}': {e}")
            continue
    
    print(f"[image_database] All search engines failed for '{query}'")
    return None


def get_team_logo(team_name: str) -> Optional[List[str]]:
    """
    Get team logo URLs from SQLite database (or JSON fallback), or fetch from Wikipedia if not found
    Returns list of logo URLs (local paths or remote URLs)
    """
    team_key = team_name.lower().strip()
    
    # Try SQLite database first
    try:
        from lib.database import get_session, TeamLogo
        session = get_session()
        team_logo = session.query(TeamLogo).filter_by(team_name=team_key).first()
        
        if team_logo and team_logo.logo_urls:
            import json
            logos = json.loads(team_logo.logo_urls)
            session.close()
            if logos:
                return logos
        session.close()
    except Exception as e:
        # SQLite not available, fall back to JSON
        print(f"[image_database] SQLite not available, using JSON fallback: {e}")
        db = load_database(TEAM_LOGOS_DB)
        
        if team_key in db:
            logos = db[team_key].get('logos', [])
            if logos:
                return logos
    
    # Not in database, try to fetch from Wikipedia
    print(f"[image_database] Fetching Wikipedia logo for: {team_name}")
    logo_path = fetch_wikipedia_team_logo(team_name)
    
    if logo_path:
        # Save to SQLite database (or JSON fallback)
        try:
            from lib.database import get_session, TeamLogo
            session = get_session()
            import json
            
            team_logo = TeamLogo(
                team_name=team_key,
                logo_urls=json.dumps([logo_path]),
                source='wikipedia'
            )
            session.merge(team_logo)  # Use merge to handle existing records
            session.commit()
            session.close()
        except Exception:
            # Fall back to JSON
            db = load_database(TEAM_LOGOS_DB)
            db[team_key] = {
                'team_name': team_name,
                'logos': [logo_path],
                'source': 'wikipedia',
                'fetched_at': time.time()
            }
            save_database(TEAM_LOGOS_DB, db)
        
        return [logo_path]
    
    return None


def get_event_venue_image(event_hash: str, venue_name: str) -> Optional[str]:
    """
    Get venue image for a specific event (by event_hash).
    Checks EventImage database first to avoid re-searching for the same event.
    Returns image URL if found, None otherwise.
    """
    if not event_hash or not venue_name:
        return None
    
    # Check EventImage database first (event-specific storage)
    try:
        from lib.database import get_session, EventImage
        session = get_session()
        event_image = session.query(EventImage).filter_by(event_hash=event_hash).first()
        
        if event_image and event_image.image_url:
            image_url = event_image.image_url
            session.close()
            # Verify file exists
            if image_url.startswith('/static/images/cache/'):
                filename = image_url.replace('/static/images/cache/', '')
                local_path = os.path.join(IMAGES_DIR, filename)
                if os.path.exists(local_path):
                    return image_url
        session.close()
    except Exception:
        pass
    
    return None


def get_venue_image(venue_name: str, event_hash: str = None) -> Optional[str]:
    """
    Get venue image from SQLite database (or JSON fallback), or fetch from Wikipedia/search engines if not found.
    If event_hash is provided, checks EventImage first to avoid re-searching for the same event.
    Returns image URL (local path or remote URL)
    """
    if not venue_name or venue_name.lower() in ['', 'tbd', 'tba', 'venue tbd']:
        return None
    
    venue_key = venue_name.lower().strip()
    
    # If event_hash provided, check event-specific storage first
    if event_hash:
        event_img = get_event_venue_image(event_hash, venue_name)
        if event_img:
            return event_img
    
    # Try venue database (general venue storage)
    try:
        from lib.database import get_session, VenueImage
        session = get_session()
        venue_image = session.query(VenueImage).filter_by(venue_name=venue_key).first()
        
        if venue_image and venue_image.image_url:
            image_url = venue_image.image_url
            session.close()
            # Verify file exists
            if image_url.startswith('/static/images/cache/'):
                filename = image_url.replace('/static/images/cache/', '')
                local_path = os.path.join(IMAGES_DIR, filename)
                if os.path.exists(local_path):
                    return image_url
        session.close()
    except Exception as e:
        # SQLite not available, fall back to JSON
        db = load_database(VENUE_IMAGES_DB)
        if venue_key in db:
            image_url = db[venue_key].get('image_url')
            if image_url:
                return image_url
    
    # Not in database, try Wikipedia first (more reliable, less rate limiting)
    print(f"[image_database] Fetching Wikipedia image for venue: {venue_name}")
    image_path = fetch_wikipedia_venue_image(venue_name)
    
    if not image_path:
        # Try Pexels API first (fast, reliable, allows hotlinking)
        print(f"[image_database] Trying Pexels API for: {venue_name}")
        image_path = fetch_pexels_image(venue_name, num_results=3)
    
    if not image_path:
        # Try multiple search engines as fallback with short timeout (don't block page load)
        print(f"[image_database] Trying multiple search engines for: {venue_name}")
        image_path = fetch_google_image(venue_name, timeout=5)  # 5 second max timeout
    
    if image_path:
        # Save to venue database
        if 'wikipedia' in image_path.lower():
            source = 'wikipedia'
        elif 'pexels' in image_path.lower():
            source = 'pexels'
        else:
            source = 'search_engine'
        try:
            from lib.database import get_session, VenueImage
            session = get_session()
            
            venue_image = VenueImage(
                venue_name=venue_key,
                image_url=image_path,
                source=source
            )
            session.merge(venue_image)
            session.commit()
            session.close()
        except Exception:
            # Fallback to JSON
            db = load_database(VENUE_IMAGES_DB)
            db[venue_key] = {
                'venue_name': venue_name,
                'image_url': image_path,
                'source': source,
                'fetched_at': time.time()
            }
            save_database(VENUE_IMAGES_DB, db)
        
        # Also save to EventImage if event_hash provided (so we don't search again for this event)
        if event_hash:
            try:
                from lib.database import get_session, EventImage
                session = get_session()
                
                event_image = session.query(EventImage).filter_by(event_hash=event_hash).first()
                if event_image:
                    event_image.image_url = image_path
                    event_image.image_type = 'venue'
                    session.merge(event_image)
                    session.commit()
                session.close()
            except Exception:
                pass
        
        return image_path
    
    return None

