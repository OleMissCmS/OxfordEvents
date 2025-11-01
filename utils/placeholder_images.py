"""
Generic placeholder images for events by category
"""

CATEGORY_PLACEHOLDERS = {
    "Music": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=250&fit=crop",
    "Sports": "https://images.unsplash.com/photo-1551958219-acbc608c6377?w=400&h=250&fit=crop",
    "Arts & Culture": "https://images.unsplash.com/photo-1511578314322-379afb476865?w=400&h=250&fit=crop",
    "Community": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=400&h=250&fit=crop",
    "Arts": "https://images.unsplash.com/photo-1511578314322-379afb476865?w=400&h=250&fit=crop",
    "default": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=400&h=250&fit=crop"
}


def get_placeholder_image(category: str) -> str:
    """Get a placeholder image URL based on category."""
    return CATEGORY_PLACEHOLDERS.get(category, CATEGORY_PLACEHOLDERS["default"])

