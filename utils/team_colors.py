"""
Team color utilities - loads team colors from logos.csv
"""

import csv
import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from functools import lru_cache
import re

# Path to logos.csv
LOGOS_CSV_PATH = Path("backend/assets/logos.csv")

# In-memory cache for team colors
_team_colors_cache: Optional[Dict[str, Tuple[str, str]]] = None


@lru_cache(maxsize=1)
def load_team_colors() -> Dict[str, Tuple[str, str]]:
    """
    Load team colors from logos.csv
    Returns dict mapping team names (normalized) to (primary_color, alt_color)
    """
    global _team_colors_cache
    if _team_colors_cache is not None:
        return _team_colors_cache
    
    colors = {}
    
    if not LOGOS_CSV_PATH.exists():
        print(f"[team_colors] Warning: logos.csv not found at {LOGOS_CSV_PATH}")
        return colors
    
    try:
        # Try UTF-8 first, fall back to latin-1 if there are encoding issues
        try:
            with open(LOGOS_CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except UnicodeDecodeError:
            # Fall back to latin-1 encoding
            with open(LOGOS_CSV_PATH, 'r', encoding='latin-1') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        
        for row in rows:
            school = row.get('school', '').strip()
            primary_color = row.get('color', '').strip()
            alt_color = row.get('alt_color', '').strip()
            
            if not school:
                continue
            
            # Normalize color - ensure it starts with #
            if primary_color and not primary_color.startswith('#'):
                primary_color = f"#{primary_color}"
            if alt_color and not alt_color.startswith('#'):
                alt_color = f"#{alt_color}"
            
            # Default to black if no color provided
            if not primary_color:
                primary_color = "#000000"
            if not alt_color:
                alt_color = "#FFFFFF"
            
            # Create multiple name variations for lookup
            school_lower = school.lower()
            colors[school_lower] = (primary_color, alt_color)
            
            # Add variations without "University of"
            if "university of" in school_lower:
                short_name = re.sub(r'university of\s+', '', school_lower).strip()
                colors[short_name] = (primary_color, alt_color)
            
            # Add variations with "University of"
            if "university of" not in school_lower and not school_lower.startswith("u "):
                long_name = f"university of {school_lower}"
                colors[long_name] = (primary_color, alt_color)
            
            # Add abbreviation if available
            abbrev = row.get('abbreviation', '').strip().lower()
            if abbrev:
                colors[abbrev] = (primary_color, alt_color)
            
            # Add alt names
            for alt_field in ['alt_name1', 'alt_name2', 'alt_name3']:
                alt_name = row.get(alt_field, '').strip().lower()
                if alt_name:
                    colors[alt_name] = (primary_color, alt_color)
        
        _team_colors_cache = colors
        print(f"[team_colors] Loaded colors for {len(colors)} team name variations")
        return colors
    except Exception as e:
        print(f"[team_colors] Error loading team colors: {e}")
        return {}


def normalize_team_name_for_color(name: str) -> str:
    """
    Normalize team name for color lookup
    """
    if not name:
        return ""
    
    # Remove common prefixes
    name = re.sub(r'^(university of|univ\.? of|u\.? of)\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^(the\s+)', '', name, flags=re.IGNORECASE)
    
    # Remove common suffixes
    name = re.sub(r'\s+(university|univ\.?)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+\([^)]+\)$', '', name)  # Remove parenthetical info
    name = re.sub(r'\s+(club|team)$', '', name, flags=re.IGNORECASE)
    
    # Clean up whitespace
    name = ' '.join(name.split())
    
    return name.strip().lower()


def get_team_color(team_name: str) -> Optional[str]:
    """
    Get primary color for a team
    Returns hex color string (e.g., "#C8122E") or None if not found
    """
    colors = load_team_colors()
    if not colors:
        return None
    
    # Try exact match
    team_lower = team_name.lower().strip()
    if team_lower in colors:
        return colors[team_lower][0]
    
    # Try normalized name
    normalized = normalize_team_name_for_color(team_name)
    if normalized in colors:
        return colors[normalized][0]
    
    # Try partial matches (e.g., "Alabama Crimson Tide" -> "Alabama")
    words = normalized.split()
    if len(words) > 1:
        # Try first word
        first_word = words[0].lower()
        if first_word in colors:
            return colors[first_word][0]
    
    return None


def get_team_colors(team_name: str) -> Optional[Tuple[str, str]]:
    """
    Get both primary and alternate colors for a team
    Returns (primary_color, alt_color) or None if not found
    """
    colors = load_team_colors()
    if not colors:
        return None
    
    # Try exact match
    team_lower = team_name.lower().strip()
    if team_lower in colors:
        return colors[team_lower]
    
    # Try normalized name
    normalized = normalize_team_name_for_color(team_name)
    if normalized in colors:
        return colors[normalized]
    
    # Try partial matches
    words = normalized.split()
    if len(words) > 1:
        first_word = words[0].lower()
        if first_word in colors:
            return colors[first_word]
    
    return None

