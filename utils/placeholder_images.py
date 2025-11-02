"""
Generic placeholder images for events by category
"""

CATEGORY_PLACEHOLDERS = {
    "Music": "https://via.placeholder.com/400x250/f8f9fa/6C757D?text=Music",
    "Sports": "https://via.placeholder.com/400x250/f8f9fa/6C757D?text=Sports",
    "Arts & Culture": "https://via.placeholder.com/400x250/f8f9fa/6C757D?text=Arts",
    "Community": "https://via.placeholder.com/400x250/f8f9fa/6C757D?text=Community",
    "Arts": "https://via.placeholder.com/400x250/f8f9fa/6C757D?text=Arts",
    "default": "https://via.placeholder.com/400x250/f8f9fa/6C757D?text=Event"
}


def get_placeholder_image(category: str) -> str:
    """Get a placeholder image URL based on category."""
    return CATEGORY_PLACEHOLDERS.get(category, CATEGORY_PLACEHOLDERS["default"])

