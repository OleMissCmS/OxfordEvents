"""
Generic placeholder images for events by category
Uses local images from static/images/fallbacks/ directory
"""

import os
import hashlib

# Base path for fallback images
FALLBACK_IMAGES_DIR = "static/images/fallbacks"

# Category to filename mapping
# Users should place their images in static/images/fallbacks/ with these filenames
CATEGORY_FILENAMES = {
    "Music": "music.jpg",
    "Sports": "sports.jpg",
    "Arts & Culture": "arts-culture.jpg",
    "Arts": "arts-culture.jpg",  # Alias for Arts & Culture
    "Performance": "performance.jpg",
    "Education": "education.jpg",
    "University": "university.jpg",
    "Ole Miss Athletics": "sports.jpg",  # Use sports image for athletics (but will be overridden by venue-specific)
    "default": "default.jpg"
}


def get_placeholder_image(category: str, event_title: str = "") -> str:
    """
    Get a placeholder image URL based on category.
    For Community events, alternates between Community1.jpg and Community2.jpg.
    Returns local path to image in static/images/fallbacks/ directory.
    Falls back to default.jpg if category-specific image not found.
    """
    # Special handling for Community events - alternate between Community1 and Community2
    if category == "Community":
        # Use event title to deterministically alternate (same event always gets same image)
        if event_title:
            # Hash the title to get consistent result
            hash_val = int(hashlib.md5(event_title.encode()).hexdigest(), 16)
            # Community1 is webp, Community2 is jpg
            filename = "Community1.webp" if hash_val % 2 == 0 else "Community2.jpg"
        else:
            # Fallback to Community1 if no title
            filename = "Community1.webp"
    else:
        # Get filename for this category
        filename = CATEGORY_FILENAMES.get(category, CATEGORY_FILENAMES["default"])
    
    # Construct full path
    image_path = os.path.join(FALLBACK_IMAGES_DIR, filename)
    
    # Check if file exists, if not use default
    if not os.path.exists(image_path):
        default_filename = CATEGORY_FILENAMES["default"]
        image_path = os.path.join(FALLBACK_IMAGES_DIR, default_filename)
        
        # If default also doesn't exist, return placeholder URL as last resort
        if not os.path.exists(image_path):
            return f"https://via.placeholder.com/400x250/f8f9fa/6C757D?text={category or 'Event'}"
    
    # Return URL path (Flask will serve from static directory)
    return f"/{image_path.replace(os.sep, '/')}"

