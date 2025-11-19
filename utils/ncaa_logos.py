"""
NCAA logo lookup utilities using local cache from klunn91/team-logos
Handles name variations like "Alabama" vs "University of Alabama"
"""

import os
import json
from pathlib import Path
from typing import Optional, List
import re

# Local cache directory
CACHE_DIR = Path("static/images/ncaa-logos")
MAPPING_FILE = Path("data/ncaa_team_mappings.json")

# In-memory cache for mappings
_team_mappings: Optional[dict] = None


def load_mappings() -> dict:
    """Load team name mappings from JSON file"""
    global _team_mappings
    if _team_mappings is not None:
        return _team_mappings
    
    if not MAPPING_FILE.exists():
        return {}
    
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            _team_mappings = json.load(f)
        return _team_mappings
    except Exception as e:
        print(f"[ncaa_logos] Error loading mappings: {e}")
        return {}


def normalize_team_name(name: str) -> str:
    """
    Normalize team name for lookup.
    Removes common prefixes/suffixes and standardizes format.
    """
    if not name:
        return ""
    
    # Remove common prefixes
    name = re.sub(r'^(university of|univ\.? of|u\.? of)\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^(the\s+)', '', name, flags=re.IGNORECASE)
    
    # Remove common suffixes
    name = re.sub(r'\s+(university|univ\.?)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+\([^)]+\)$', '', name)  # Remove parenthetical info like "(D2)"
    name = re.sub(r'\s+(club|team)$', '', name, flags=re.IGNORECASE)  # Remove "Club" or "Team"
    
    # Clean up whitespace
    name = ' '.join(name.split())
    
    return name.strip()


def get_ncaa_logo_path(team_name: str) -> Optional[str]:
    """
    Get local path to NCAA team logo.
    Returns relative path like "/static/images/ncaa-logos/Alabama.png" or None if not found.
    Handles name variations like:
    - "Alabama" -> "Alabama.png"
    - "University of Alabama" -> "Alabama.png"
    - "Alabama Crimson Tide" -> "Alabama.png" (if mapping exists)
    """
    if not team_name:
        return None
    
    mappings = load_mappings()
    if not mappings:
        # If mappings don't exist, try direct lookup
        normalized = normalize_team_name(team_name)
        # Try various filename formats
        possible_names = [
            normalized,
            normalized.replace(' ', ''),
            normalized.replace(' ', '_'),
            team_name.replace(' ', ''),
            team_name.replace(' ', '_'),
        ]
        
        for name in possible_names:
            # Try different extensions
            for ext in ['.png', '.jpg', '.jpeg', '.svg']:
                filename = f"{name}{ext}"
                logo_path = CACHE_DIR / filename
                if logo_path.exists():
                    return f"/static/images/ncaa-logos/{filename}"
        return None
    
    # Try exact match first (case-insensitive)
    team_lower = team_name.lower()
    if team_lower in mappings:
        filename = mappings[team_lower]
        logo_path = CACHE_DIR / filename
        if logo_path.exists():
            return f"/static/images/ncaa-logos/{filename}"
    
    # Try normalized name
    normalized = normalize_team_name(team_name)
    normalized_lower = normalized.lower()
    
    if normalized_lower in mappings:
        filename = mappings[normalized_lower]
        logo_path = CACHE_DIR / filename
        if logo_path.exists():
            return f"/static/images/ncaa-logos/{filename}"
    
    # Try partial matches (e.g., "Alabama Crimson Tide" -> "Alabama")
    words = normalized.split()
    if len(words) > 1:
        # Try first word (often the school name)
        first_word = words[0].lower()
        if first_word in mappings:
            filename = mappings[first_word]
            logo_path = CACHE_DIR / filename
            if logo_path.exists():
                return f"/static/images/ncaa-logos/{filename}"
        
        # Try first two words (e.g., "Notre Dame Fighting Irish" -> "Notre Dame")
        if len(words) >= 2:
            first_two = f"{words[0]} {words[1]}".lower()
            if first_two in mappings:
                filename = mappings[first_two]
                logo_path = CACHE_DIR / filename
                if logo_path.exists():
                    return f"/static/images/ncaa-logos/{filename}"
        
        # Try last word (sometimes the nickname)
        last_word = words[-1].lower()
        if last_word in mappings:
            filename = mappings[last_word]
            logo_path = CACHE_DIR / filename
            if logo_path.exists():
                return f"/static/images/ncaa-logos/{filename}"
    
    # Try direct filename lookup as fallback
    words = normalized.split()
    for ext in ['.png', '.jpg', '.jpeg', '.svg']:
        # Try normalized name
        filename = f"{normalized}{ext}"
        logo_path = CACHE_DIR / filename
        if logo_path.exists():
            return f"/static/images/ncaa-logos/{filename}"
        
        # Try first two words (e.g., "Notre Dame Fighting Irish" -> "Notre Dame")
        if len(words) >= 2:
            first_two = f"{words[0]} {words[1]}"
            filename = f"{first_two}{ext}"
            logo_path = CACHE_DIR / filename
            if logo_path.exists():
                return f"/static/images/ncaa-logos/{filename}"
            
            # Try camelCase of first two words (e.g., "Notre Dame" -> "notreDame")
            camel_case = words[0].lower() + ''.join(word.capitalize() for word in words[1:2])
            filename = f"{camel_case}{ext}"
            logo_path = CACHE_DIR / filename
            if logo_path.exists():
                return f"/static/images/ncaa-logos/{filename}"
        
        # Try camelCase version of full normalized name (e.g., "Notre Dame Fighting Irish" -> "notreDameFightingIrish")
        if len(words) > 1:
            camel_case = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
            filename = f"{camel_case}{ext}"
            logo_path = CACHE_DIR / filename
            if logo_path.exists():
                return f"/static/images/ncaa-logos/{filename}"
        
        # Try all lowercase, no spaces
        no_space = normalized.replace(' ', '').lower()
        filename = f"{no_space}{ext}"
        logo_path = CACHE_DIR / filename
        if logo_path.exists():
            return f"/static/images/ncaa-logos/{filename}"
        
        # Try original name
        filename = f"{team_name}{ext}"
        logo_path = CACHE_DIR / filename
        if logo_path.exists():
            return f"/static/images/ncaa-logos/{filename}"
    
    return None


def get_ncaa_logo_urls(team_name: str) -> Optional[List[str]]:
    """
    Get NCAA logo URLs for a team (for compatibility with existing code).
    Returns list with single local path, or None if not found.
    """
    logo_path = get_ncaa_logo_path(team_name)
    if logo_path:
        return [logo_path]
    return None

