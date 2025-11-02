"""
Image processing utilities for event images, including sports team logos
"""

import io
import re
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw
import requests

# Team name mappings to logo URLs (multiple fallback sources)
TEAM_NAMES = {
    # Ole Miss / SEC teams - with fallback URLs
    "ole miss": ("Ole Miss", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/145.png",  # ESPN CDN (primary)
        "https://logos-world.net/wp-content/uploads/2020/06/Ole-Miss-Logo.png",  # Fallback
    ]),
    "rebel": ("Ole Miss", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/145.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Ole-Miss-Logo.png",
    ]),
    "rebels": ("Ole Miss", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/145.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Ole-Miss-Logo.png",
    ]),
    "alabama": ("Alabama", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/333.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Alabama-Crimson-Tide-Logo.png",
    ]),
    "crimson tide": ("Alabama", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/333.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Alabama-Crimson-Tide-Logo.png",
    ]),
    "arkansas": ("Arkansas", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/8.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Arkansas-Razorbacks-Logo.png",
    ]),
    "razorbacks": ("Arkansas", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/8.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Arkansas-Razorbacks-Logo.png",
    ]),
    "lsu": ("LSU", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/99.png",
        "https://logos-world.net/wp-content/uploads/2020/06/LSU-Tigers-Logo.png",
    ]),
    "tigers": ("LSU", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/99.png",
        "https://logos-world.net/wp-content/uploads/2020/06/LSU-Tigers-Logo.png",
    ]),
    "mississippi state": ("Miss State", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/344.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Mississippi-State-Bulldogs-Logo.png",
    ]),
    "bulldogs": ("Miss State", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/344.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Mississippi-State-Bulldogs-Logo.png",
    ]),
    "auburn": ("Auburn", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/2.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Auburn-Tigers-Logo.png",
    ]),
    "georgia": ("Georgia", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/61.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Georgia-Bulldogs-Logo.png",
    ]),
    "florida": ("Florida", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/57.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Florida-Gators-Logo.png",
    ]),
    "tennessee": ("Tennessee", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/2633.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Tennessee-Volunteers-Logo.png",
    ]),
}


def detect_sports_teams(title: str) -> Optional[Tuple[Tuple[str, str], Tuple[str, str]]]:
    """
    Detect two teams from event title.
    Returns ((away_name, away_logo), (home_name, home_logo)) or None.
    """
    title_lower = title.lower()
    # Pattern: "Team A vs Team B" or "Team A @ Team B"
    # More flexible pattern - capture team names even if followed by words
    vs_pattern = r'(.+?)\s+(?:vs|@|v\.|versus)\s+(.+?)(?:\s+(?:in|at)|$)'
    match = re.search(vs_pattern, title_lower)
    if not match:
        return None
    
    team1_text, team2_text = match.groups()
    
    # Find team names - try longer matches first
    def find_team(text):
        text_lower = text.lower().strip()
        # Sort by key length (longer first) to match "mississippi state" before "mississippi"
        sorted_teams = sorted(TEAM_NAMES.items(), key=lambda x: len(x[0]), reverse=True)
        for key, (name, logo_urls) in sorted_teams:
            if key in text_lower:
                return name, logo_urls
        return None, None
    
    team1_result = find_team(team1_text)
    team2_result = find_team(team2_text)
    
    if team1_result[0] and team2_result[0]:
        # First team is away, second is home
        return team1_result, team2_result
    
    return None


# Caching disabled to prevent infinite hangs on network failures
def get_logo_image(url_or_urls, size: int = 120) -> Optional[Image.Image]:
    """
    Download and resize team logo.
    Accepts either a single URL string or a list of URLs (for fallback).
    """
    # Normalize input to list
    if isinstance(url_or_urls, str):
        urls = [url_or_urls]
    else:
        urls = url_or_urls
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    # Try each URL until one works
    for url in urls:
        try:
            response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
            if response.status_code == 200 and response.content:
                img = Image.open(io.BytesIO(response.content))
                img = img.convert("RGBA")
                # Resize maintaining aspect ratio
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                return img
        except Exception:
            # Try next URL
            continue
    
    # All URLs failed
    return None


def create_team_matchup_image(
    away_team: Tuple[str, str], 
    home_team: Tuple[str, str], 
    width: int = 400, 
    height: int = 300
) -> Tuple[Optional[io.BytesIO], Optional[str]]:
    """
    Create composite image with away team (upper left), home team (lower right), diagonal divider.
    Returns (BytesIO buffer or None, error_message or None).
    """
    try:
        # Download logos
        away_logo = get_logo_image(away_team[1], size=120)
        home_logo = get_logo_image(home_team[1], size=120)
        
        # Check which logos failed
        away_urls_str = str(away_team[1]) if isinstance(away_team[1], list) else away_team[1]
        home_urls_str = str(home_team[1]) if isinstance(home_team[1], list) else home_team[1]
        
        if not away_logo and not home_logo:
            return None, f"Failed to download both logos: {away_team[0]} and {home_team[0]}"
        if not away_logo:
            return None, f"Failed to download away team logo: {away_team[0]} (tried: {away_urls_str})"
        if not home_logo:
            return None, f"Failed to download home team logo: {home_team[0]} (tried: {home_urls_str})"
        
        # Create base image
        img = Image.new("RGB", (width, height), color="#f8f9fa")
        draw = ImageDraw.Draw(img)
        
        # Draw diagonal line from bottom-left to top-right
        draw.line([(0, height), (width, 0)], fill="#000000", width=4)
        
        # Place away logo in upper left quadrant
        paste_x = width // 4 - away_logo.width // 2
        paste_y = height // 4 - away_logo.height // 2
        img.paste(away_logo, (paste_x, paste_y), away_logo)
        
        # Place home logo in lower right quadrant
        paste_x = 3 * width // 4 - home_logo.width // 2
        paste_y = 3 * height // 4 - home_logo.height // 2
        img.paste(home_logo, (paste_x, paste_y), home_logo)
        
        # Convert to BytesIO
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer, None
    except Exception as e:
        return None, f"Exception creating matchup image: {str(e)}"


def get_event_image(event: dict) -> Tuple[Any, Optional[str]]:
    """
    Get event image URL or generated sports matchup image.
    Returns (image_url_or_buffer, error_message).
    """
    title = event.get("title", "")
    category = event.get("category", "")
    
    # Check if this is a sports event
    is_sports = category == "Sports" or "vs" in title.lower() or "@" in title.lower()
    
    if is_sports:
        teams = detect_sports_teams(title)
        if teams:
            away, home = teams
            matchup_img, error = create_team_matchup_image(away, home)
            if matchup_img:
                return matchup_img, None
            # If matchup image creation fails, return the specific error
            return None, error or f"Failed to create matchup image for {away[0]} vs {home[0]}"
    
    # Try to get regular event image
    url = (event.get("image") or event.get("img") or "").strip()
    if url:
        return url, None
    
    # Fallback to category-specific placeholder
    from utils.placeholder_images import get_placeholder_image
    placeholder = get_placeholder_image(category or "default")
    return placeholder, None


def curl_test_url(url: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Test a URL like curl -I would: returns status, headers, content-type, size.
    """
    result = {
        "url": url,
        "status_code": None,
        "content_type": None,
        "content_length": None,
        "headers": {},
        "error": None,
        "accessible": False
    }
    
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        result["status_code"] = response.status_code
        result["content_type"] = response.headers.get("Content-Type", "unknown")
        result["content_length"] = response.headers.get("Content-Length", "unknown")
        result["headers"] = dict(response.headers)
        result["accessible"] = 200 <= response.status_code < 400
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection Error"
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"Unexpected: {type(e).__name__}: {e}"
    
    return result

