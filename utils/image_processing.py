"""
Image processing utilities for event images, including sports team logos
"""

import io
import os
import re
import base64
from functools import lru_cache
from pathlib import Path
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
    "texas a&m": ("Texas A&M", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/245.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Texas-A-M-Aggies-Logo.png",
    ]),
    "aggies": ("Texas A&M", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/245.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Texas-A-M-Aggies-Logo.png",
    ]),
    "kentucky": ("Kentucky", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/96.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Kentucky-Wildcats-Logo.png",
    ]),
    "wildcats": ("Kentucky", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/96.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Kentucky-Wildcats-Logo.png",
    ]),
    "missouri": ("Missouri", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/142.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Missouri-Tigers-Logo.png",
    ]),
    "vanderbilt": ("Vanderbilt", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/238.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Vanderbilt-Commodores-Logo.png",
    ]),
    "commodores": ("Vanderbilt", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/238.png",
        "https://logos-world.net/wp-content/uploads/2020/06/Vanderbilt-Commodores-Logo.png",
    ]),
    "south carolina": ("South Carolina", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/2579.png",
        "https://logos-world.net/wp-content/uploads/2020/06/South-Carolina-Gamecocks-Logo.png",
    ]),
    "gamecocks": ("South Carolina", [
        "https://a.espncdn.com/i/teamlogos/ncaa/500/2579.png",
        "https://logos-world.net/wp-content/uploads/2020/06/South-Carolina-Gamecocks-Logo.png",
    ]),
}

OLE_MISS_LOGO_FILE = Path("static/images/ole-miss-logo.png")


@lru_cache(maxsize=8)
def _load_ole_miss_logo(size: int) -> Optional[Image.Image]:
    if not OLE_MISS_LOGO_FILE.exists():
        return None
    try:
        img = Image.open(OLE_MISS_LOGO_FILE)
        img = img.convert("RGBA")
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        return img
    except Exception:
        return None


def detect_sports_teams(title: str) -> Optional[Tuple[Tuple[str, str], Tuple[str, str]]]:
    """
    Detect two teams from event title.
    Returns ((away_name, away_logo), (home_name, home_logo)) or None.
    Uses database first, then falls back to hardcoded TEAM_NAMES.
    """
    title_lower = title.lower()
    # Pattern: "Team A vs Team B", "Team A @ Team B", or "Team A at Team B"
    # More flexible pattern - capture team names even if followed by words or parenthetical info
    # Handle patterns like:
    # - "Ice Hockey Club (D2) vs Alabama at Mid-South Ice House"
    # - "Miami Hurricanes at Ole Miss Rebels Mens Basketball"
    # - "Longwood Lancers at Ole Miss Rebels Womens Basketball"
    
    # Try "at" pattern first (common for "Team A at Team B")
    at_pattern = r'(.+?)\s+at\s+(.+?)(?:\s+(?:mens|womens|men\'s|women\'s|mbb|wbb|basketball|football|baseball|in|@)|$)'
    match = re.search(at_pattern, title_lower)
    
    if not match:
        # Try "vs" pattern
        vs_pattern = r'(.+?)\s+(?:vs|@|v\.|versus)\s+(.+?)(?:\s+(?:in|at|@)|$)'
        match = re.search(vs_pattern, title_lower)
    
    if not match:
        return None
    
    team1_text, team2_text = match.groups()
    # Clean up team text - remove trailing location info and sport names
    team1_text = re.sub(r'\s+(?:at|in|mens|womens|men\'s|women\'s|mbb|wbb|basketball|football|baseball)\s+.+$', '', team1_text).strip()
    team2_text = re.sub(r'\s+(?:at|in|mens|womens|men\'s|women\'s|mbb|wbb|basketball|football|baseball)\s+.+$', '', team2_text).strip()
    
    # Find team names - try database first, then hardcoded
    def find_team(text):
        text_lower = text.lower().strip()
        
        # Clean up team name (remove common prefixes and suffixes like "(D2)", "(D1)", etc.)
        team_name_clean = re.sub(r'^(#?\d+\s+)?', '', text_lower).strip()
        # Remove parenthetical suffixes like "(D2)", "(D1)", "(Club)", etc.
        team_name_clean = re.sub(r'\s*\([^)]+\)\s*$', '', team_name_clean).strip()
        
        # Special handling for "Ice Hockey Club" - treat as Ole Miss (home team)
        # This handles "Ice Hockey Club (D2)" or "Ole Miss Ice Hockey Club" etc.
        if "ice hockey club" in team_name_clean:
            ole_miss_entry = TEAM_NAMES.get("ole miss")
            if ole_miss_entry:
                return ("Ole Miss", ole_miss_entry[1])
        
        # Try database first
        try:
            from utils.image_database import get_team_logo
            logos = get_team_logo(team_name_clean)
            if logos:
                # Return standardized name and logos
                # Capitalize properly
                name_parts = team_name_clean.split()
                name = ' '.join(word.capitalize() for word in name_parts)
                return name, logos
        except Exception as e:
            # If database lookup fails, continue to hardcoded list
            pass
        
        # Fallback to hardcoded TEAM_NAMES
        # Sort by key length (longer first) to match "mississippi state" before "mississippi"
        sorted_teams = sorted(TEAM_NAMES.items(), key=lambda x: len(x[0]), reverse=True)
        for key, (name, logo_urls) in sorted_teams:
            # Check if key appears in the text (as whole word or part of phrase)
            if key in text_lower or key in team_name_clean:
                return name, logo_urls
            # Also check if any word in the key matches (e.g., "rebels" in "ole miss rebels")
            key_words = key.split()
            if len(key_words) == 1 and key_words[0] in text_lower:
                return name, logo_urls
        
        # If not in hardcoded list, try database with cleaned name
        if team_name_clean and team_name_clean != text_lower:
            try:
                from utils.image_database import get_team_logo
                logos = get_team_logo(team_name_clean)
                if logos:
                    name_parts = team_name_clean.split()
                    name = ' '.join(word.capitalize() for word in name_parts)
                    return name, logos
            except:
                pass
        
        return None, None
    
    team1_result = find_team(team1_text)
    team2_result = find_team(team2_text)
    
    # Debug logging
    print(f"[detect_sports_teams] Team1 '{team1_text}': {team1_result}")
    print(f"[detect_sports_teams] Team2 '{team2_text}': {team2_result}")
    
    # If both teams found, return them
    if team1_result[0] and team2_result[0]:
        # First team is away, second is home
        return team1_result, team2_result
    
    # If only one team found, try to fetch the other from database/wiki/NCAA cache
    # This handles cases like "Ole Miss vs Norfolk State" where Norfolk State isn't in hardcoded list
    if team1_result[0] and not team2_result[0]:
        # Try harder to find team2 - clean the text and try database/wiki/NCAA
        team2_clean = team2_text.strip()
        try:
            from utils.image_database import get_team_logo
            logos = get_team_logo(team2_clean)
            if logos:
                name_parts = team2_clean.split()
                name = ' '.join(word.capitalize() for word in name_parts)
                team2_result = (name, logos)
                print(f"[detect_sports_teams] Found team2 via database: {team2_result}")
                return team1_result, team2_result
        except Exception as e:
            print(f"[detect_sports_teams] Error finding team2: {e}")
    
    if team2_result[0] and not team1_result[0]:
        # Try harder to find team1 - clean the text and try database/wiki/NCAA
        team1_clean = team1_text.strip()
        try:
            from utils.image_database import get_team_logo
            logos = get_team_logo(team1_clean)
            if logos:
                name_parts = team1_clean.split()
                name = ' '.join(word.capitalize() for word in name_parts)
                team1_result = (name, logos)
                print(f"[detect_sports_teams] Found team1 via database: {team1_result}")
                return team1_result, team2_result
            # Also try just the first word (e.g., "Longwood" from "Longwood Lancers")
            first_word = team1_clean.split()[0] if team1_clean.split() else team1_clean
            if first_word != team1_clean:
                logos = get_team_logo(first_word)
                if logos:
                    name = first_word.capitalize()
                    team1_result = (name, logos)
                    print(f"[detect_sports_teams] Found team1 via first word '{first_word}': {team1_result}")
                    return team1_result, team2_result
        except Exception as e:
            print(f"[detect_sports_teams] Error finding team1: {e}")
    
    return None


# Logo download with timeout and quick failure
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
            # Handle local file paths (from database or NCAA cache)
            if url.startswith('/static/images/cache/'):
                # Local file path
                file_path = url.replace('/static/images/cache/', 'static/images/cache/')
                if os.path.exists(file_path):
                    img = Image.open(file_path)
                    img = img.convert("RGBA")
                    img.thumbnail((size, size), Image.Resampling.LANCZOS)
                    return img
                continue
            elif url.startswith('/static/images/ncaa-logos/'):
                # NCAA logo cache path
                file_path = url.replace('/static/images/ncaa-logos/', 'static/images/ncaa-logos/')
                if os.path.exists(file_path):
                    img = Image.open(file_path)
                    img = img.convert("RGBA")
                    img.thumbnail((size, size), Image.Resampling.LANCZOS)
                    return img
                continue
            
            # Remote URL - reduced timeout for faster failure
            response = requests.get(url, timeout=5, headers=headers, allow_redirects=True)
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
    height: int = 150,  # Match display height
    background_image_path: Optional[str] = None,
    background_opacity: float = 0.6
) -> Tuple[Optional[io.BytesIO], Optional[str]]:
    """
    Create composite image with away team (upper left), home team (lower right), diagonal divider.
    Uses team colors from logos.csv for split background (Ole Miss color vs opponent color).
    Returns (BytesIO buffer or None, error_message or None).
    Image size matches display size (400x150) to prevent cropping.
    """
    try:
        # Download logos with appropriate size for 150px height display
        logo_size = 80  # Reduced to fit better in 150px height
        away_logo = get_logo_image(away_team[1], size=logo_size)
        home_logo = get_logo_image(home_team[1], size=logo_size)
        
        away_urls_str = str(away_team[1]) if isinstance(away_team[1], list) else away_team[1]
        home_urls_str = str(home_team[1]) if isinstance(home_team[1], list) else home_team[1]
        fallback_logo = _load_ole_miss_logo(logo_size)

        # Always ensure we have at least Ole Miss logo as fallback
        if not fallback_logo:
            return None, "Ole Miss fallback logo not available"
        
        # Use Ole Miss logo for missing logos
        if not away_logo:
            away_logo = fallback_logo.copy()
            print(f"[create_team_matchup_image] Using Ole Miss logo for missing away team: {away_team[0]}")
        if not home_logo:
            home_logo = fallback_logo.copy()
            print(f"[create_team_matchup_image] Using Ole Miss logo for missing home team: {home_team[0]}")
        
        # At this point, we should have both logos (at least Ole Miss)
        if not away_logo or not home_logo:
            return None, f"Failed to load logos (away: {away_team[0]}, home: {home_team[0]})"
        
        # Determine which team is Ole Miss
        away_name_lower = away_team[0].lower()
        home_name_lower = home_team[0].lower()
        is_ole_miss_away = any(keyword in away_name_lower for keyword in ['ole miss', 'rebel', 'rebels'])
        is_ole_miss_home = any(keyword in home_name_lower for keyword in ['ole miss', 'rebel', 'rebels'])
        
        # Get team colors from CSV
        from utils.team_colors import get_team_color
        
        ole_miss_color = get_team_color("Ole Miss") or "#C8122E"  # Default Ole Miss red
        away_color = get_team_color(away_team[0]) or "#FFFFFF"  # Default white
        home_color = get_team_color(home_team[0]) or "#FFFFFF"  # Default white
        
        # Determine background colors: Ole Miss side vs opponent side
        if is_ole_miss_away:
            # Away team is Ole Miss
            away_side_color = ole_miss_color
            home_side_color = home_color
        elif is_ole_miss_home:
            # Home team is Ole Miss
            away_side_color = away_color
            home_side_color = ole_miss_color
        else:
            # Neither is Ole Miss (shouldn't happen for athletics, but handle gracefully)
            away_side_color = away_color
            home_side_color = home_color
        
        # Create base image - use venue background if provided, otherwise split colors
        has_background = False
        if background_image_path:
            # Try multiple path variations
            possible_paths = [
                background_image_path,
                os.path.join(os.getcwd(), background_image_path),
                os.path.abspath(background_image_path),
            ]
            
            # Also try with app root if we can find it
            import sys
            if hasattr(sys, '_getframe'):
                try:
                    current_file = os.path.abspath(__file__)
                    project_root = os.path.dirname(os.path.dirname(current_file))
                    possible_paths.append(os.path.join(project_root, background_image_path))
                except:
                    pass
            
            bg_img = None
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        bg_img = Image.open(path)
                        print(f"[create_team_matchup_image] Successfully loaded venue background from: {path}")
                        break
                    except Exception as e:
                        print(f"[create_team_matchup_image] Failed to open {path}: {e}")
                        continue
            
            if bg_img:
                try:
                    # Resize to match display size
                    bg_img = bg_img.resize((width, height), Image.Resampling.LANCZOS)
                    # Convert to RGBA for transparency
                    if bg_img.mode != 'RGBA':
                        bg_img = bg_img.convert('RGBA')
                    
                    # Apply opacity to background - keep it more visible (85% = 0.85) so venue shows through
                    # User wants venue behind logos/colors, so make it more opaque
                    venue_opacity = 0.85  # 85% opacity for better visibility
                    alpha = bg_img.split()[3]
                    alpha = alpha.point(lambda p: int(p * venue_opacity))
                    bg_img.putalpha(alpha)
                    
                    # Create base image with venue background
                    img = Image.new("RGB", (width, height), color="#FFFFFF")
                    img.paste(bg_img, (0, 0), bg_img)
                    has_background = True
                    print(f"[create_team_matchup_image] Venue background applied with {background_opacity*100}% opacity")
                except Exception as e:
                    print(f"[create_team_matchup_image] Failed to process venue background: {e}")
                    img = Image.new("RGB", (width, height), color="#FFFFFF")
            else:
                print(f"[create_team_matchup_image] Venue background not found. Tried paths: {possible_paths}")
                img = Image.new("RGB", (width, height), color="#FFFFFF")
        else:
            # No venue background - use split team colors
            img = Image.new("RGB", (width, height), color="#FFFFFF")
        
        draw = ImageDraw.Draw(img)
        
        # Overlay split team colors on top of venue background (or create if no background)
        if not has_background:
            # Create polygon for away team side (upper left triangle)
            away_polygon = [
                (0, 0),           # Top-left
                (width, 0),       # Top-right
                (0, height),      # Bottom-left
            ]
            draw.polygon(away_polygon, fill=away_side_color)
            
            # Create polygon for home team side (lower right triangle)
            home_polygon = [
                (width, 0),       # Top-right
                (width, height),  # Bottom-right
                (0, height),      # Bottom-left
            ]
            draw.polygon(home_polygon, fill=home_side_color)
        else:
            # Overlay semi-transparent team colors on venue background
            # Reduce team color opacity to 30% so venue is more visible behind
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Away team side (upper left triangle) - 30% opacity for better venue visibility
            away_polygon = [(0, 0), (width, 0), (0, height)]
            # Convert hex color to RGB
            away_rgb = tuple(int(away_side_color[i:i+2], 16) for i in (1, 3, 5))
            overlay_draw.polygon(away_polygon, fill=(*away_rgb, 77))  # 30% opacity (77/255)
            
            # Home team side (lower right triangle) - 30% opacity
            home_polygon = [(width, 0), (width, height), (0, height)]
            home_rgb = tuple(int(home_side_color[i:i+2], 16) for i in (1, 3, 5))
            overlay_draw.polygon(home_polygon, fill=(*home_rgb, 77))  # 30% opacity
            
            # Composite overlay onto base image
            img = Image.alpha_composite(img.convert("RGBA"), overlay)
            # Keep as RGBA for logo transparency
            draw = ImageDraw.Draw(img)
        
        # Draw diagonal divider line (white with shadow for visibility)
        draw.line([(0, height), (width, 0)], fill="#FFFFFF", width=3)
        draw.line([(1, height), (width + 1, 0)], fill="#000000", width=1)
        
        # Calculate safe positioning with generous padding for 150px height
        padding = 15  # Padding from edges
        away_center_x = width // 4
        away_center_y = height // 3  # Slightly lower for better fit
        home_center_x = 3 * width // 4
        home_center_y = 2 * height // 3  # Slightly higher for better fit
        
        # Ensure logos don't get cut off - use center positioning with bounds checking
        # Apply 40% opacity to logos (102/255 ≈ 0.4)
        logo_opacity = 102  # 40% opacity
        
        # Away logo (upper left) - apply transparency
        away_logo_with_alpha = away_logo.copy()
        if away_logo_with_alpha.mode == 'RGBA':
            alpha = away_logo_with_alpha.split()[3]
            alpha = alpha.point(lambda p: int(p * (logo_opacity / 255)))
            away_logo_with_alpha.putalpha(alpha)
        else:
            away_logo_with_alpha = away_logo_with_alpha.convert('RGBA')
            alpha = Image.new('L', away_logo_with_alpha.size, logo_opacity)
            away_logo_with_alpha.putalpha(alpha)
        
        paste_x = max(padding, min(away_center_x - away_logo.width // 2, width - away_logo.width - padding))
        paste_y = max(padding, min(away_center_y - away_logo.height // 2, height - away_logo.height - padding))
        
        # Paste logo with transparency onto RGBA image
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        img.paste(away_logo_with_alpha, (paste_x, paste_y), away_logo_with_alpha)
        
        # Home logo (lower right) - apply transparency
        home_logo_with_alpha = home_logo.copy()
        if home_logo_with_alpha.mode == 'RGBA':
            alpha = home_logo_with_alpha.split()[3]
            alpha = alpha.point(lambda p: int(p * (logo_opacity / 255)))
            home_logo_with_alpha.putalpha(alpha)
        else:
            home_logo_with_alpha = home_logo_with_alpha.convert('RGBA')
            alpha = Image.new('L', home_logo_with_alpha.size, logo_opacity)
            home_logo_with_alpha.putalpha(alpha)
        
        paste_x = max(padding, min(home_center_x - home_logo.width // 2, width - home_logo.width - padding))
        paste_y = max(padding, min(home_center_y - home_logo.height // 2, height - home_logo.height - padding))
        img.paste(home_logo_with_alpha, (paste_x, paste_y), home_logo_with_alpha)
        
        # Convert back to RGB if needed (for PNG compatibility)
        if img.mode == 'RGBA':
            # Create white background and composite
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Convert to BytesIO
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        return buffer, None
    except Exception as e:
        return None, f"Exception creating matchup image: {str(e)}"


def get_event_image(event: dict) -> Tuple[Any, Optional[str]]:
    """
    Get event image URL or generated sports matchup image.
    Priority order:
    1. API-provided image (from SeatGeek, Ticketmaster, Bandsintown)
    2. Sports matchup image (for sports events)
       - For Ole Miss Athletics: venue background + logos overlay
    3. Location-specific image (Proud Larry's uses Proud_Larrys.jpg)
    4. Category-specific placeholder (user-provided fallback images)
       - Community: alternates between Community1.jpg and Community2.jpg
       - University: University.jpg
    
    Returns (image_url_or_buffer, error_message).
    """
    title = event.get("title", "")
    category = event.get("category", "")
    location = event.get("location", "")
    
    # PRIORITY 1: Check for API-provided image first (from SeatGeek, Ticketmaster, Bandsintown)
    url = (event.get("image") or event.get("img") or "").strip()
    if url:
        return url, None
    
    # PRIORITY 2: Check if this is a sports event (generate matchup image)
    is_sports = category == "Sports" or category == "Ole Miss Athletics" or "vs" in title.lower() or "@" in title.lower()
    is_olemiss_athletics = category == "Ole Miss Athletics"
    
    if is_sports:
        teams = detect_sports_teams(title)
        if teams:
            away, home = teams
            
            # For Ole Miss Athletics, try to get venue-specific background image
            background_image_path = None
            if is_olemiss_athletics:
                location_lower = location.lower()
                title_lower = title.lower()
                
                # Determine sport and venue from location or title
                if "pavilion" in location_lower or "basketball" in title_lower:
                    # Basketball at The Pavilion (webp file)
                    background_image_path = os.path.join("static", "images", "fallbacks", "Pavilion.webp")
                elif "swayze" in location_lower or "baseball" in title_lower:
                    # Baseball at Swayze Field
                    background_image_path = os.path.join("static", "images", "fallbacks", "Swayze.jpg")
                elif "vaught" in location_lower or "hemingway" in location_lower or "football" in title_lower:
                    # Football at Vaught-Hemingway Stadium
                    background_image_path = os.path.join("static", "images", "fallbacks", "Vaught.jpg")
                
                # Check if background image exists
                if background_image_path and not os.path.exists(background_image_path):
                    background_image_path = None
            
            # Create matchup image with optional background
            matchup_img, error = create_team_matchup_image(
                away, 
                home, 
                background_image_path=background_image_path,
                background_opacity=0.6  # 60% opacity for background
            )
            if matchup_img:
                return matchup_img, None
            # If matchup image creation fails, return the specific error
            return None, error or f"Failed to create matchup image for {away[0]} vs {home[0]}"
    
    # PRIORITY 3: Try to get location-specific image
    # Special case: Proud Larry's uses Proud_Larrys.jpg
    location_lower = location.lower() if location else ""
    if "proud larry" in location_lower or "proud larrys" in location_lower:
        proud_larrys_path = os.path.join("static", "images", "fallbacks", "Proud_Larrys.jpg")
        if os.path.exists(proud_larrys_path):
            return f"/{proud_larrys_path.replace(os.sep, '/')}", None
    
    # Try general location image search
    location_img = search_location_image(location)
    if location_img:
        return location_img, None
    
    # PRIORITY 4: Fallback to category-specific placeholder (user-provided images)
    from utils.placeholder_images import get_placeholder_image
    placeholder = get_placeholder_image(category or "default", event_title=title)
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


# Known venue images - can be expanded with actual image URLs
VENUE_IMAGES = {
    # Oxford venues from Bandsintown + local places
    "kennon observatory": "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=800",
    "the lyric oxford": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
    "lyric": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
    "proud larry's": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800",
    "proud larry": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800",
    "vaught-hemingway stadium": "https://images.unsplash.com/photo-1530035415911-95194de4ebcc?w=800",
    "vaught": "https://images.unsplash.com/photo-1530035415911-95194de4ebcc?w=800",
    "hemingway": "https://images.unsplash.com/photo-1530035415911-95194de4ebcc?w=800",
    "swayze field": "https://images.unsplash.com/photo-1566577134770-3d85bb3a9cc4?w=800",
    "swayze": "https://images.unsplash.com/photo-1566577134770-3d85bb3a9cc4?w=800",
    "the pavilion": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800",
    "pavilion": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800",
    "square books": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=800",
    "square": "https://images.unsplash.com/photo-1483808161634-29aa1b0e585e?w=800",
    "landers center": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800",
    "landers": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800",
    "cadence bank arena": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800",
    "cadence": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800",
    "heindl center": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
    "heindl": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
    "ford center": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
    "ford": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
    "hillcrest": "https://images.unsplash.com/photo-1474650918787-cf5ee6380121?w=800",
    "houston high school": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800",
    "houston": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800",
    "library": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800",
    "gertrude": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
    "performing arts": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
    # Ole Miss venues
    "turner center": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800",
    "turner": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800",
    "bryant hall": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800",
    "bryant": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800",
    "law center": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800",
    "khayat": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800",
    "robert c. khayat": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800",
    "catfish row museum": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800",
    "catfish row": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800",
    "south campus recreation center": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800",
    "recreation center": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800",
    "lyceum": "https://images.unsplash.com/photo-1562774053-701939374585?w=800",
}

def search_location_image(location: str, event_hash: str = None) -> Optional[str]:
    """
    Search for an image of a location.
    Uses database first, then falls back to hardcoded VENUE_IMAGES, then fetches from Wikipedia/search engines.
    If event_hash is provided, checks EventImage first to avoid re-searching for the same event.
    Returns the first image URL found or None.
    """
    if not location or location.lower() in ['', 'oxford, ms', 'oxford', 'tbd', 'tba', 'venue tbd']:
        return None
    
    try:
        # Clean location name
        location_clean = location.split(',')[0].strip()
        location_clean_lower = location_clean.lower()
        location_clean_lower = location_clean_lower.split('-')[0].strip()
        
        # Try database first (includes Wikipedia/search engine fetching, with event_hash for event-specific storage)
        try:
            from utils.image_database import get_venue_image
            db_image = get_venue_image(location_clean, event_hash=event_hash)
            if db_image:
                return db_image
        except Exception as e:
            # If database lookup fails, continue to hardcoded list
            pass
        
        # Fallback to hardcoded VENUE_IMAGES
        for venue_key, image_url in VENUE_IMAGES.items():
            if venue_key in location_clean_lower:
                return image_url
        
        # If no match found, return None to use category placeholder
        return None
    except Exception as e:
        return None

