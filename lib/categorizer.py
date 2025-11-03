"""
Smart categorization for events based on title and description
"""

import re


def categorize_event(title: str, description: str = "", source: str = "") -> str:
    """
    Intelligently categorize an event based on its title, description, and source.
    Returns a category string.
    """
    # Combine all text for analysis
    text = f"{title} {description}".lower()  # Don't include source in keyword matching
    
    # Check if source indicates Ole Miss Athletics
    if "ole miss" in source.lower() and any(sport in source.lower() for sport in ['football', 'basketball', 'baseball', 'softball', 'soccer', 'tennis', 'volleyball', 'track', 'mbb', 'wbb']):
        return "Ole Miss Athletics"
    
    # Sports keywords - be specific
    sports_keywords = [
        'football', 'basketball', 'baseball', 'softball', 'soccer', 'tennis', 
        'volleyball', 'track', 'swimming', 'golf', 'cross country', 'gymnastics',
        ' vs ', ' @ ', ' vs. ', 'game', 'match', 'tournament', 'championship',
        'tailgate', 'athletics', 'pickleball', 'fitness', 'hockey', 'ice hockey'
    ]
    
    # Music keywords
    music_keywords = [
        'concert', 'music', 'band', 'dj', 'album', 'song', 'performer', 'artist',
        'proud larry', 'lyric oxford', 'live music', 'acoustic', 'jazz', 'rock',
        'folk', 'country', 'blues', 'hip hop', 'rap', 'orchestra', 'symphony',
        'percussion', 'ensembles', 'singers', 'choral', 'guitar', 'piano', 'drum',
        'bass', 'violin', 'singer', 'fleetwood', 'tribute'
    ]
    
    # Arts & Culture keywords
    arts_keywords = [
        'art program', 'theatre', 'theater', 'play', 'drama', 'exhibition',
        'gallery', 'museum', 'poetry', 'reading', 'author', 'book', 'literary',
        'film', 'movie', 'documentary', 'cinema', 'screening', 'visual art',
        'sculpture', 'painting', 'imagination station', 'discovery'
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
    if any(keyword in text for keyword in music_keywords):
        return "Music"
    elif any(keyword in text for keyword in arts_keywords):
        return "Arts & Culture"
    elif any(keyword in text for keyword in sports_keywords):
        return "Sports"
    elif any(keyword in text for keyword in education_keywords):
        return "Education"
    elif any(keyword in text for keyword in community_keywords):
        return "Community"
    else:
        return "University"

