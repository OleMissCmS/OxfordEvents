"""
Helper functions for sports event detection and opponent extraction in Flask templates
"""
import re
from typing import Optional, Tuple

# ESPN CDN base URL for team logos
ESPN_LOGO_BASE = "https://a.espncdn.com/i/teamlogos/ncaa/500"

# Team name to ESPN ID mapping (same as frontend but simplified for Flask)
TEAM_LOGO_MAP = {
    'ole miss': 145,
    'alabama': 333,
    'arkansas': 8,
    'auburn': 2,
    'florida': 57,
    'georgia': 61,
    'kentucky': 96,
    'lsu': 99,
    'mississippi state': 344,
    'missouri': 142,
    'south carolina': 2579,
    'tennessee': 2633,
    'texas a&m': 245,
    'vanderbilt': 238,
    'texas': 251,
    'oklahoma': 201,
    'baylor': 239,
    'tcu': 2628,
    'houston': 248,
    'texas tech': 2641,
    'oklahoma state': 197,
    'kansas': 2305,
    'kansas state': 2306,
    'iowa state': 66,
    'cincinnati': 2132,
    'ucf': 2116,
    'byu': 252,
    'arizona': 12,
    'arizona state': 9,
    'colorado': 38,
    'utah': 254,
    'washington': 264,
    'washington state': 265,
    'ucla': 26,
    'southern california': 30,
    'oregon state': 204,
    'oregon': 2483,
    'michigan': 130,
    'michigan state': 127,
    'ohio state': 194,
    'penn state': 213,
    'wisconsin': 275,
    'illinois': 356,
    'indiana': 84,
    'iowa': 2294,
    'minnesota': 135,
    'nebraska': 158,
    'northwestern': 77,
    'purdue': 2509,
    'rutgers': 164,
    'maryland': 120,
    'notre dame': 87,
    'clemson': 228,
    'florida state': 52,
    'miami': 2390,
    'north carolina': 153,
    'nc state': 152,
    'duke': 150,
    'virginia': 258,
    'virginia tech': 259,
    'pitt': 221,
    'georgia tech': 59,
    'louisville': 97,
    'syracuse': 183,
    'boston college': 103,
    'wake forest': 154,
    'memphis': 235,
    'tulane': 2653,
    'southern miss': 2572,
    'uab': 5,
    'liberty': 2335,
    'boise state': 68,
    'fresno': 278,
    'san diego state': 21,
    'smu': 2567,
    'texas state': 326,
    'utsa': 2636,
    'louisiana tech': 2348,
    'louisiana lafayette': 309,
    'troy': 2652,
    'georgia southern': 290,
    'coastal carolina': 324,
    'army': 349,
    'navy': 2426,
    'air force': 2005,
    'stanford': 24,
    'cal': 25,
    'west virginia': 277,
    'jackson state': 55,
}

# Team name aliases
TEAM_ALIASES = {
    'rebels': 'ole miss',
    'ole miss rebels': 'ole miss',
    'mississippi rebels': 'ole miss',
    'crimson tide': 'alabama',
    'razorbacks': 'arkansas',
    'war eagle': 'auburn',
    'gators': 'florida',
    'dawgs': 'georgia',
    'bulldogs': 'mississippi state',
    'aggies': 'texas a&m',
    'commodores': 'vanderbilt',
    'longhorns': 'texas',
    'sooners': 'oklahoma',
    'bears': 'baylor',
    'horned frogs': 'tcu',
    'texas christian': 'tcu',
    'cougars': 'houston',
    'jayhawks': 'kansas',
    'wildcats': 'kentucky',
    'cyclones': 'iowa state',
    'bearcats': 'cincinnati',
    'knights': 'ucf',
    'broncos': 'boise state',
    'tigers': 'lsu',
    'seminoles': 'florida state',
    'hurricanes': 'miami',
    'wolfpack': 'nc state',
    'tarheels': 'north carolina',
    'bluedevils': 'duke',
    'cavaliers': 'virginia',
    'hokies': 'virginia tech',
    'panthers': 'pitt',
    'jackets': 'georgia tech',
    'cardinals': 'louisville',
    'orange': 'syracuse',
    'deacons': 'wake forest',
    'volunteers': 'tennessee',
    'usc': 'southern california',
    'southern cal': 'southern california',
}


def normalize_team_name(name: str) -> str:
    """Normalize team name for lookup"""
    if not name:
        return ''
    normalized = name.lower().strip()
    normalized = re.sub(r'[^a-z0-9& ]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def get_team_logo_url(team_name: str) -> Optional[str]:
    """Get ESPN logo URL for a team name"""
    if not team_name:
        return None
    
    normalized = normalize_team_name(team_name)
    if not normalized:
        return None
    
    # Check direct match
    if normalized in TEAM_LOGO_MAP:
        espn_id = TEAM_LOGO_MAP[normalized]
        return f"{ESPN_LOGO_BASE}/{espn_id}.png"
    
    # Check aliases
    if normalized in TEAM_ALIASES:
        alias_key = TEAM_ALIASES[normalized]
        if alias_key in TEAM_LOGO_MAP:
            espn_id = TEAM_LOGO_MAP[alias_key]
            return f"{ESPN_LOGO_BASE}/{espn_id}.png"
    
    # Fuzzy match - check if any key contains the normalized name or vice versa
    for key, espn_id in TEAM_LOGO_MAP.items():
        if normalized in key or key in normalized:
            return f"{ESPN_LOGO_BASE}/{espn_id}.png"
    
    return None


def is_sports_event(event: dict) -> bool:
    """Check if event is a sports event"""
    category = (event.get('category', '') or '').lower()
    sports_keywords = ['sports', 'athletics', 'football', 'basketball', 'baseball', 'softball']
    
    if any(keyword in category for keyword in sports_keywords):
        return True
    
    title_desc = f"{event.get('title', '')} {event.get('description', '')}".lower()
    return 'ole miss' in title_desc and (' vs' in title_desc or ' at ' in title_desc or ' versus' in title_desc)


def get_opponent_from_event(event: dict) -> Optional[str]:
    """Extract opponent name from event title/description for Ole Miss home games"""
    title = event.get('title', '')
    description = event.get('description', '')
    haystack = f"{title} {description}"
    
    # Patterns to match: "Team vs Ole Miss", "Team at Ole Miss", "Ole Miss vs Team", etc.
    patterns = [
        r'(?:^|\s)([A-Za-z0-9&.\'\-\s]+?)\s+(?:vs\.?|vs|versus)\s+(?:Ole Miss|University of Mississippi|Rebels)',
        r'(?:Ole Miss|University of Mississippi|Rebels)\s+(?:vs\.?|vs|versus)\s+([A-Za-z0-9&.\'\-\s]+?)(?:\s|$)',
        r'([A-Za-z0-9&.\'\-\s]+?)\s+at\s+(?:Ole Miss|University of Mississippi|The Pavilion|Vaught[- ]Hemingway)',
        r'host(?:ing)?\s+(?:the\s+)?([A-Za-z0-9&.\'\-\s]+?)(?:\s|$)',
        r'welcomes?\s+(?:the\s+)?([A-Za-z0-9&.\'\-\s]+?)(?:\s|$)',
    ]
    
    blacklisted = ['ole miss', 'rebels', 'university of mississippi', 'mississippi', 'the', 'at', 'vs', 'versus']
    
    for pattern in patterns:
        match = re.search(pattern, haystack, re.IGNORECASE)
        if match and match.group(1):
            opponent = match.group(1).strip()
            # Clean up
            opponent = re.sub(r'\s+(?:vs\.?|vs|versus|at)\s+.*$', '', opponent, flags=re.IGNORECASE)
            opponent = re.sub(r'^(?:the\s+)?', '', opponent, flags=re.IGNORECASE)
            opponent = opponent.strip()
            
            # Title case
            opponent = ' '.join(word.capitalize() for word in opponent.split())
            
            # Check if valid (not blacklisted)
            if opponent and opponent.lower() not in blacklisted and len(opponent) > 2:
                return opponent
    
    return None


def get_matchup_data(event: dict) -> Optional[dict]:
    """Get matchup data for a sports event (opponent name and logo URLs)"""
    if not is_sports_event(event):
        return None
    
    opponent = get_opponent_from_event(event)
    if not opponent:
        return None
    
    away_logo = get_team_logo_url(opponent)
    home_logo = get_team_logo_url('Ole Miss')
    
    return {
        'opponent': opponent,
        'away_logo': away_logo,
        'home_logo': home_logo,
        'has_logos': bool(away_logo and home_logo)
    }


