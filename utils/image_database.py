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

# Database file paths
DB_DIR = "data"
TEAM_LOGOS_DB = os.path.join(DB_DIR, "team_logos.json")
VENUE_IMAGES_DB = os.path.join(DB_DIR, "venue_images.json")
IMAGES_DIR = os.path.join("static", "images", "cache")

# Ensure directories exist
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


def load_database(db_path: str) -> Dict:
    """Load JSON database file, return empty dict if doesn't exist"""
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_database(db_path: str, data: Dict):
    """Save JSON database file"""
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
    Fetch image from Google Image Search using Custom Search API
    Returns local file path if successful, None otherwise
    Falls back to scraping if API key is not configured
    """
    import os
    
    # Try Google Custom Search API first (more reliable)
    api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
    search_engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
    
    if api_key and search_engine_id:
        try:
            search_query = f"{query} oxford MS"
            api_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': search_query,
                'searchType': 'image',
                'num': min(num_results, 10),  # API allows max 10 results per request
                'safe': 'active',
            }
            
            response = requests.get(api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'items' in data and len(data['items']) > 0:
                    # Try each image result
                    for item in data['items'][:num_results]:
                        img_url = item.get('link', '')
                        if not img_url:
                            continue
                        
                        # Validate it's an image URL
                        if not any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                            continue
                        
                        filename = get_filename_from_url(img_url, query.replace(' ', '_'))
                        local_path = os.path.join(IMAGES_DIR, filename)
                        
                        if download_image(img_url, local_path):
                            print(f"[image_database] Successfully downloaded image from Google API: {img_url[:80]}...")
                            return f"/static/images/cache/{filename}"
            
            elif response.status_code == 403:
                print(f"[image_database] Google Custom Search API quota exceeded or invalid key")
            else:
                print(f"[image_database] Google Custom Search API error: {response.status_code}")
        
        except Exception as e:
            print(f"[image_database] Error using Google Custom Search API: {e}")
            # Fall through to scraping fallback
    
    # Fallback to scraping if API not configured or fails
    try:
        print(f"[image_database] Falling back to scraping Google Images (consider using API key)")
        search_query = f"{query} oxford MS"
        search_url = f"https://www.google.com/search?tbm=isch&q={quote(search_query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(search_url, timeout=15, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Google Image Search structure (may change)
            # Look for img tags in search results
            img_tags = soup.find_all('img', limit=20)
            
            for img_tag in img_tags:
                src = img_tag.get('src', '') or img_tag.get('data-src', '')
                if not src or src.startswith('data:'):
                    continue
                
                # Skip Google's own images
                if 'google' in src.lower() or 'gstatic' in src.lower():
                    continue
                
                # Convert to absolute URL if needed
                if src.startswith('//'):
                    img_url = 'https:' + src
                elif not src.startswith('http'):
                    continue
                else:
                    img_url = src
                
                # Try to download
                filename = get_filename_from_url(img_url, query.replace(' ', '_'))
                local_path = os.path.join(IMAGES_DIR, filename)
                
                if download_image(img_url, local_path):
                    return f"/static/images/cache/{filename}"
                
                # Limit attempts
                num_results -= 1
                if num_results <= 0:
                    break
        
        return None
    except Exception as e:
        print(f"[image_database] Error fetching Google image for '{query}': {e}")
        return None


def get_team_logo(team_name: str) -> Optional[List[str]]:
    """
    Get team logo URLs from database, or fetch from Wikipedia if not found
    Returns list of logo URLs (local paths or remote URLs)
    """
    db = load_database(TEAM_LOGOS_DB)
    team_key = team_name.lower().strip()
    
    # Check database first
    if team_key in db:
        logos = db[team_key].get('logos', [])
        if logos:
            return logos
    
    # Not in database, try to fetch from Wikipedia
    print(f"[image_database] Fetching Wikipedia logo for: {team_name}")
    logo_path = fetch_wikipedia_team_logo(team_name)
    
    if logo_path:
        # Save to database
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
    Get venue image from database, or fetch from Wikipedia/Google if not found
    Returns image URL (local path or remote URL)
    """
    if not venue_name or venue_name.lower() in ['', 'tbd', 'tba', 'venue tbd']:
        return None
    
    db = load_database(VENUE_IMAGES_DB)
    venue_key = venue_name.lower().strip()
    
    # Check database first
    if venue_key in db:
        image_url = db[venue_key].get('image_url')
        if image_url:
            return image_url
    
    # Not in database, try Wikipedia first
    print(f"[image_database] Fetching Wikipedia image for venue: {venue_name}")
    image_path = fetch_wikipedia_venue_image(venue_name)
    
    if not image_path:
        # Try Google Image Search as fallback
        print(f"[image_database] Trying Google Image Search for: {venue_name}")
        image_path = fetch_google_image(venue_name)
    
    if image_path:
        # Save to database
        db[venue_key] = {
            'venue_name': venue_name,
            'image_url': image_path,
            'source': 'wikipedia' if 'wikipedia' in image_path.lower() else 'google',
            'fetched_at': time.time()
        }
        save_database(VENUE_IMAGES_DB, db)
        return image_path
    
    return None

