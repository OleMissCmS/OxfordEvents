"""
Image processing utilities for event images, including sports team logos
"""

import io
import re
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw
import requests
import streamlit as st

# Team name mappings to logo URLs
TEAM_NAMES = {
    # Ole Miss / SEC teams
    "ole miss": ("Ole Miss", "https://logos-world.net/wp-content/uploads/2020/06/Ole-Miss-Logo.png"),
    "rebel": ("Ole Miss", "https://logos-world.net/wp-content/uploads/2020/06/Ole-Miss-Logo.png"),
    "rebels": ("Ole Miss", "https://logos-world.net/wp-content/uploads/2020/06/Ole-Miss-Logo.png"),
    "alabama": ("Alabama", "https://logos-world.net/wp-content/uploads/2020/06/Alabama-Crimson-Tide-Logo.png"),
    "crimson tide": ("Alabama", "https://logos-world.net/wp-content/uploads/2020/06/Alabama-Crimson-Tide-Logo.png"),
    "arkansas": ("Arkansas", "https://logos-world.net/wp-content/uploads/2020/06/Arkansas-Razorbacks-Logo.png"),
    "razorbacks": ("Arkansas", "https://logos-world.net/wp-content/uploads/2020/06/Arkansas-Razorbacks-Logo.png"),
    "lsu": ("LSU", "https://logos-world.net/wp-content/uploads/2020/06/LSU-Tigers-Logo.png"),
    "tigers": ("LSU", "https://logos-world.net/wp-content/uploads/2020/06/LSU-Tigers-Logo.png"),
    "mississippi state": ("Miss State", "https://logos-world.net/wp-content/uploads/2020/06/Mississippi-State-Bulldogs-Logo.png"),
    "bulldogs": ("Miss State", "https://logos-world.net/wp-content/uploads/2020/06/Mississippi-State-Bulldogs-Logo.png"),
    "auburn": ("Auburn", "https://logos-world.net/wp-content/uploads/2020/06/Auburn-Tigers-Logo.png"),
    "georgia": ("Georgia", "https://logos-world.net/wp-content/uploads/2020/06/Georgia-Bulldogs-Logo.png"),
    "florida": ("Florida", "https://logos-world.net/wp-content/uploads/2020/06/Florida-Gators-Logo.png"),
    "tennessee": ("Tennessee", "https://logos-world.net/wp-content/uploads/2020/06/Tennessee-Volunteers-Logo.png"),
}


@st.cache_data
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
        for key, (name, logo_url) in sorted_teams:
            if key in text_lower:
                return name, logo_url
        return None, None
    
    team1_result = find_team(team1_text)
    team2_result = find_team(team2_text)
    
    if team1_result[0] and team2_result[0]:
        # First team is away, second is home
        return team1_result, team2_result
    
    return None


@st.cache_data
def get_logo_image(url: str, size: int = 120) -> Optional[Image.Image]:
    """Download and resize team logo."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img = img.convert("RGBA")
            # Resize maintaining aspect ratio
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            return img
    except Exception as e:
        # Silently fail - logo will just not show
        pass
    return None


def create_team_matchup_image(
    away_team: Tuple[str, str], 
    home_team: Tuple[str, str], 
    width: int = 400, 
    height: int = 300
) -> Optional[io.BytesIO]:
    """
    Create composite image with away team (upper left), home team (lower right), diagonal divider.
    Returns BytesIO buffer or None if logos can't be loaded.
    """
    try:
        # Download logos
        away_logo = get_logo_image(away_team[1], size=120)
        home_logo = get_logo_image(home_team[1], size=120)
        
        # If we can't get both logos, return None
        if not away_logo or not home_logo:
            return None
        
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
        return buffer
    except Exception:
        return None


def get_event_image(event: dict) -> Tuple[Any, Optional[str]]:
    """
    Get event image URL or generated sports matchup image.
    Returns (image_url_or_buffer, error_message).
    """
    title = event.get("title", "")
    category = event.get("category", "")
    
    # Check if it's a sports event with team matchup
    is_sports = category == "Sports" or "vs" in title.lower() or "@" in title.lower()
    
    if is_sports:
        teams = detect_sports_teams(title)
        if teams:
            away, home = teams
            matchup_img = create_team_matchup_image(away, home)
            if matchup_img:
                return matchup_img, None
            # If matchup image creation fails, return error for debugging
            return None, f"Failed to create matchup image for {away[0]} vs {home[0]}"
    
    # Try to get regular event image
    url = (event.get("image") or event.get("img") or "").strip()
    if url:
        return url, None
    
    # Fallback placeholder
    placeholder = "https://placehold.co/400x250/f8f9fa/6C757D?text=Event"
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

