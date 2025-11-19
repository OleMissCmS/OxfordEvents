"""
Generic placeholder images for events by category or location.
Uses local images from static/images/fallbacks/ and static/images/buildings/.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Optional

# Base path for fallback images
FALLBACK_IMAGES_DIR = Path("static/images/fallbacks")
BUILDING_IMAGES_DIR = Path("static/images/buildings")

# Category to filename mapping
# Users should place their images in static/images/fallbacks/ with these filenames
CATEGORY_FILENAMES = {
    "Music": "music.jpg",
    "Sports": "sports.jpg",
    "Arts & Culture": "arts-culture.jpg",
    "Arts": "arts-culture.jpg",  # Alias for Arts & Culture
    "Performance": "performance.jpg",
    "Education": "education.jpg",
    "University": "University.jpg",
    "Ole Miss Athletics": "sports.jpg",  # Use sports image for athletics (overridden by venue-specific logic)
    "default": "default.jpg"
}


def _build_static_url(path: Path) -> str:
    """Convert a file path to a web-accessible /static/... URL."""
    return f"/{path.as_posix()}"


def _normalize_key(value: str) -> str:
    """Normalize text to alphanumeric lowercase for loose matching."""
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _load_building_images() -> Dict[str, str]:
    """Build a lookup of sanitized building names to static URLs."""
    mapping: Dict[str, str] = {}
    if not BUILDING_IMAGES_DIR.exists():
        return mapping

    for file_path in BUILDING_IMAGES_DIR.iterdir():
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        key = _normalize_key(file_path.stem)
        if key:
            mapping[key] = _build_static_url(file_path)
    return mapping


BUILDING_IMAGE_MAP = _load_building_images()


def _building_image_from_location(location: str) -> Optional[str]:
    """Return the best matching building image for a location string."""
    if not location:
        return None

    normalized = _normalize_key(location)
    if not normalized:
        return None

    # Exact match first
    if normalized in BUILDING_IMAGE_MAP:
        return BUILDING_IMAGE_MAP[normalized]

    # Fuzzy contains match (longest keys first for specificity)
    for key, image_url in sorted(BUILDING_IMAGE_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if key and key in normalized:
            return image_url

    return None


def get_university_default_image() -> str:
    """Return the default University fallback image URL."""
    fallback = FALLBACK_IMAGES_DIR / "University.jpg"
    if fallback.exists():
        return _build_static_url(fallback)
    return "https://via.placeholder.com/400x250/f8f9fa/6C757D?text=University"


def get_location_image(location: str) -> Optional[str]:
    """Return a location-specific image (building, Pavilion, etc.) if available."""
    if not location:
        return None

    building_image = _building_image_from_location(location)
    if building_image:
        return building_image

    location_lower = location.lower()

    # If it's clearly a University/Hall building without a dedicated image, fallback to University default
    if "university of mississippi" in location_lower or "hall" in location_lower:
        return get_university_default_image()

    return None


def get_placeholder_image(category: str, event_title: str = "") -> str:
    """
    Get a placeholder image URL based on category.
    For Community events, alternates between Community1.jpg and Community2.jpg.
    Returns local path to image in static/images/fallbacks/ directory.
    Falls back to default.jpg if category-specific image not found.
    """
    # Special handling for Community events - alternate between Community1 and Community2
    if category == "Community":
        if event_title:
            hash_val = int(hashlib.md5(event_title.encode()).hexdigest(), 16)
            filename = "Community1.webp" if hash_val % 2 == 0 else "Community2.jpg"
        else:
            filename = "Community1.webp"
    else:
        filename = CATEGORY_FILENAMES.get(category, CATEGORY_FILENAMES["default"])

    image_path = FALLBACK_IMAGES_DIR / filename

    if not image_path.exists():
        default_path = FALLBACK_IMAGES_DIR / CATEGORY_FILENAMES["default"]
        if default_path.exists():
            image_path = default_path
        else:
            return f"https://via.placeholder.com/400x250/f8f9fa/6C757D?text={category or 'Event'}"

    return _build_static_url(image_path)

