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


def fetch_google_image(query: str, num_results: int = 5) -> Optional[str]:
    """
    Fetch image using DuckDuckGo (simple, no API key needed)
    Returns local file path if successful, None otherwise
    """
    try:
        # Use duckduckgo-search library (simple, no API key)
        try:
            from duckduckgo_search import DDGS
            
            search_query = f"{query} oxford MS"
            
            # Search for images
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    keywords=search_query,
                    max_results=num_results,
                    safe_search='moderate'
                ))
            
            for result in results:
                img_url = result.get('image', '') or result.get('url', '')
                if not img_url:
                    continue
                
                # Validate it's an image URL
                if not any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', 'image']):
                    continue
                
                # Try to download
                filename = get_filename_from_url(img_url, query.replace(' ', '_'))
                local_path = os.path.join(IMAGES_DIR, filename)
                
                if download_image(img_url, local_path):
                    print(f"[image_database] Successfully downloaded image from DuckDuckGo: {img_url[:80]}...")
                    return f"/static/images/cache/{filename}"
        
        except ImportError:
            # Library not installed, try simple Bing search as fallback
            print(f"[image_database] duckduckgo-search not installed, trying Bing Image Search")
            search_query = f"{query} oxford MS"
            
            # Simple Bing Image Search (no API key needed for basic use)
            bing_url = f"https://www.bing.com/images/search?q={quote(search_query)}&form=HDRSC2&first=1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(bing_url, timeout=15, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for image links in Bing results
                img_links = soup.find_all('a', class_='iusc', limit=num_results)
                
                for link in img_links:
                    # Bing stores image URL in m attribute as JSON
                    m_attr = link.get('m', '{}')
                    try:
                        import json
                        data = json.loads(m_attr)
                        img_url = data.get('murl', '')
                        
                        if img_url:
                            filename = get_filename_from_url(img_url, query.replace(' ', '_'))
                            local_path = os.path.join(IMAGES_DIR, filename)
                            
                            if download_image(img_url, local_path):
                                return f"/static/images/cache/{filename}"
                    except:
                        continue
        
        return None
    except Exception as e:
        print(f"[image_database] Error fetching image for '{query}': {e}")
        return None


def get_team_logo(team_name: str) -> Optional[List[str]]:
    """
    Get team logo URLs from PostgreSQL database (or JSON fallback), or fetch from Wikipedia if not found
    Returns list of logo URLs (local paths or remote URLs)
    """
    team_key = team_name.lower().strip()
    
    # Try PostgreSQL first
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
        # PostgreSQL not available, fall back to JSON
        print(f"[image_database] PostgreSQL not available, using JSON fallback: {e}")
        db = load_database(TEAM_LOGOS_DB)
        
        if team_key in db:
            logos = db[team_key].get('logos', [])
            if logos:
                return logos
    
    # Not in database, try to fetch from Wikipedia
    print(f"[image_database] Fetching Wikipedia logo for: {team_name}")
    logo_path = fetch_wikipedia_team_logo(team_name)
    
    if logo_path:
        # Save to database (PostgreSQL or JSON)
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


def get_venue_image(venue_name: str) -> Optional[str]:
    """
    Get venue image from PostgreSQL database (or JSON fallback), or fetch from Wikipedia/Google if not found
    Returns image URL (local path or remote URL)
    """
    if not venue_name or venue_name.lower() in ['', 'tbd', 'tba', 'venue tbd']:
        return None
    
    venue_key = venue_name.lower().strip()
    
    # Try PostgreSQL first
    try:
        from lib.database import get_session, VenueImage
        session = get_session()
        venue_image = session.query(VenueImage).filter_by(venue_name=venue_key).first()
        
        if venue_image and venue_image.image_url:
            image_url = venue_image.image_url
            session.close()
            return image_url
        session.close()
    except Exception as e:
        # PostgreSQL not available, fall back to JSON
        print(f"[image_database] PostgreSQL not available, using JSON fallback: {e}")
        db = load_database(VENUE_IMAGES_DB)
        
        if venue_key in db:
            image_url = db[venue_key].get('image_url')
            if image_url:
                return image_url
    
    # Not in database, try Wikipedia first
    print(f"[image_database] Fetching Wikipedia image for venue: {venue_name}")
    image_path = fetch_wikipedia_venue_image(venue_name)
    
    if not image_path:
        # Try Google Image Search as fallback
        print(f"[image_database] Trying DuckDuckGo image search for: {venue_name}")
        image_path = fetch_google_image(venue_name)
    
    if image_path:
        # Save to database (PostgreSQL or JSON)
        source = 'wikipedia' if 'wikipedia' in image_path.lower() else 'duckduckgo'
        try:
            from lib.database import get_session, VenueImage
            session = get_session()
            
            venue_image = VenueImage(
                venue_name=venue_key,
                image_url=image_path,
                source=source
            )
            session.merge(venue_image)  # Use merge to handle existing records
            session.commit()
            session.close()
        except Exception:
            # Fall back to JSON
            db = load_database(VENUE_IMAGES_DB)
            db[venue_key] = {
                'venue_name': venue_name,
                'image_url': image_path,
                'source': source,
                'fetched_at': time.time()
            }
            save_database(VENUE_IMAGES_DB, db)
        
        return image_path
    
    return None

