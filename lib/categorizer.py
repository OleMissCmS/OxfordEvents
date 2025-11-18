"""
Smart categorization for events based on title and description
"""

import re


def categorize_event(title: str, description: str = "", source: str = "", location: str = "") -> str:
    """
    Intelligently categorize an event based on its title, description, source, and location.
    Returns a category string (can be comma-separated for multiple categories).
    """
    # Combine all text for analysis
    text = f"{title} {description}".lower()
    location_lower = location.lower() if location else ""
    source_lower = source.lower()
    
    # Check for Turner Center FIRST (special case: always add Sports category, regardless of source)
    # This takes priority over source-specific categories
    if "turner center" in location_lower or "turner center" in text:
        # Turner Center events get both "Turner Center" and "Sports" categories
        # If it's from a source API, we'll add that too
        if source_lower in ["ticketmaster", "bandsintown", "seatgeek"]:
            return f"Turner Center, Sports, {source_lower.capitalize()}"
        return "Turner Center, Sports"
    
    # Check source-specific categories (these take priority for non-Turner Center events)
    if source_lower == "ticketmaster":
        return "Ticketmaster"
    
    if source_lower == "bandsintown":
        return "Bandsintown"
    
    if source_lower == "seatgeek":
        return "SeatGeek"
    
    # Check if source indicates Ole Miss Athletics
    # Check for ESPN Ole Miss sources or Ole Miss sports sources
    if ("espn" in source_lower and "ole miss" in source_lower) or \
       ("ole miss" in source_lower and any(sport in source_lower for sport in ['football', 'basketball', 'baseball', 'softball', 'soccer', 'tennis', 'volleyball', 'track', 'mbb', 'wbb'])):
        return "Ole Miss Athletics"
    
    # Also check if title/description indicates Ole Miss Athletics game
    if "ole miss" in text and (" vs " in text or " vs. " in text) and any(sport in text for sport in ['football', 'basketball', 'game']):
        return "Ole Miss Athletics"
    
    # Check for Performance category (Proud Larry's or The Lyric)
    if "proud larry" in text or "the lyric" in text.lower() or "lyric oxford" in text:
        return "Performance"
    
    # Sports keywords - be specific
    sports_keywords = [
        'football', 'basketball', 'baseball', 'softball', 'soccer', 'tennis', 
        'volleyball', 'track', 'swimming', 'golf', 'cross country', 'gymnastics',
        ' vs ', ' @ ', ' vs. ', 'game', 'match', 'tournament', 'championship',
        'tailgate', 'athletics', 'pickleball', 'fitness', 'hockey', 'ice hockey'
    ]
    
    # Music keywords (but not Performance venues)
    music_keywords = [
        'concert', 'music', 'band', 'dj', 'album', 'song', 'performer', 'artist',
        'live music', 'acoustic', 'jazz', 'rock', 'folk', 'country', 'blues', 
        'hip hop', 'rap', 'orchestra', 'symphony', 'percussion', 'ensembles', 
        'singers', 'choral', 'guitar', 'piano', 'drum', 'bass', 'violin', 
        'singer', 'fleetwood', 'tribute'
    ]
    
    # Performance keywords (Proud Larry's, The Lyric)
    performance_keywords = [
        'proud larry', 'the lyric', 'lyric oxford'
    ]
    
    # Arts & Culture keywords
    arts_keywords = [
        'art program', 'theatre', 'theater', 'play', 'drama', 'exhibition',
        'gallery', 'museum', 'poetry', 'reading', 'author', 'book', 'literary',
        'film', 'movie', 'documentary', 'cinema', 'screening', 'visual art',
        'sculpture', 'painting', 'imagination station', 'discovery'
    ]
    
    # Religious keywords
    religious_keywords = [
        'worship', 'church', 'mass', 'prayer', 'faith', 'bible', 'ministry',
        'revival', 'service', 'gospel', 'fellowship', 'sermon', 'youth group',
        'church choir', 'vacation bible school', 'vbs', 'easter', 'christmas cantata'
    ]

    # Community keywords
    community_keywords = [
        'farmers market', 'festival', 'fair', 'recycling', 'community', 'local',
        'vendor', 'craft', 'pop up shop', 'meet up', 'meeting'
    ]
    
    # Education keywords
    education_keywords = [
        'seminar', 'workshop', 'lecture', 'presentation', 'training',
        'conference', 'symposium', 'forum', 'panel', 'discussion',
        'colloquium', 'speaker', 'series', 'bootcamp', 'teaching'
    ]
    
    # Check in priority order (most specific first)
    if any(keyword in text for keyword in performance_keywords):
        return "Performance"
    elif any(keyword in text for keyword in music_keywords):
        return "Music"
    elif any(keyword in text for keyword in arts_keywords):
        return "Arts & Culture"
    elif any(keyword in text for keyword in sports_keywords):
        return "Sports"
    elif any(keyword in text for keyword in education_keywords):
        return "Education"
    elif any(keyword in text for keyword in religious_keywords):
        return "Religious"
    elif any(keyword in text for keyword in community_keywords):
        return "Community"
    else:
        return "University"

