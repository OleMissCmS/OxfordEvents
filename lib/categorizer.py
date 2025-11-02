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
    text = f"{title} {description} {source}".lower()
    
    # Sports keywords
    sports_keywords = [
        'football', 'basketball', 'baseball', 'softball', 'soccer', 'tennis', 
        'volleyball', 'track', 'swimming', 'golf', 'cross country', 'gymnastics',
        'vs', '@', 'game', 'match', 'tournament', 'championship', 'halftime',
        'tailgate', 'athletics', 'sport', 'ole miss', 'sec'
    ]
    
    # Music keywords
    music_keywords = [
        'concert', 'music', 'band', 'dj', 'album', 'song', 'performer', 'artist',
        'proud larry', 'lyric oxford', 'live music', 'acoustic', 'jazz', 'rock',
        'folk', 'country', 'blues', 'hip hop', 'rap', 'orchestra', 'symphony',
        'guitar', 'piano', 'drum', 'bass', 'violin', 'singer', 'show'
    ]
    
    # Arts & Culture keywords
    arts_keywords = [
        'art', 'theatre', 'theater', 'play', 'drama', 'show', 'exhibition',
        'gallery', 'museum', 'poetry', 'reading', 'author', 'book', 'literary',
        'film', 'movie', 'documentary', 'cinema', 'screening', 'culture',
        'square books', 'rowan oak', 'visual art', 'sculpture', 'painting'
    ]
    
    # Community keywords
    community_keywords = [
        'farmers market', 'festival', 'fair', 'market', 'community', 'town',
        'square', 'oxford', 'local', 'neighborhood', 'town hall', 'meeting',
        'food', 'vendor', 'craft', 'vendor fair'
    ]
    
    # Education keywords
    education_keywords = [
        'seminar', 'workshop', 'lecture', 'presentation', 'class', 'course',
        'training', 'conference', 'symposium', 'forum', 'panel', 'discussion',
        'colloquium', 'talk', 'speaker', 'series', 'bootcamp'
    ]
    
    # Check each category
    if any(keyword in text for keyword in sports_keywords):
        return "Sports"
    elif any(keyword in text for keyword in music_keywords):
        return "Music"
    elif any(keyword in text for keyword in arts_keywords):
        return "Arts & Culture"
    elif any(keyword in text for keyword in education_keywords):
        return "Education"
    elif any(keyword in text for keyword in community_keywords):
        return "Community"
    else:
        return "University"

