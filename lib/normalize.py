from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from dateutil import parser as dtp, tz
from datetime import datetime

CATEGORY_MAP = {
    "music": "Music",
    "concert": "Music",
    "sports": "Sports",
    "athletics": "Sports",
    "lecture": "Talks & Lectures",
    "book": "Books & Literary",
    "reading": "Books & Literary",
    "signing": "Books & Literary",
    "museum": "Arts & Culture",
    "gallery": "Arts & Culture",
    "radio": "Arts & Culture",
    "festival": "Festivals",
    "market": "Markets & Fairs",
    "farmer": "Markets & Fairs",
    "kids": "Family & Kids",
    "family": "Family & Kids",
    "theatre": "Performing Arts",
    "theater": "Performing Arts",
    "dance": "Performing Arts",
    "film": "Film",
    "movie": "Film",
    "community": "Community",
    "service": "Community",
    "alumni": "Campus",
    "student": "Campus",
    "campus": "Campus",
}

@dataclass
class Event:
    title: str
    start_iso: Optional[str]
    end_iso: Optional[str]
    location: Optional[str]
    cost: Optional[str]
    link: Optional[str]
    source: str
    category: Optional[str]
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def infer_category(title: str, description: Optional[str]) -> Optional[str]:
    text = f"{title} {description or ''}".lower()
    for key, cat in CATEGORY_MAP.items():
        if key in text:
            return cat
    return None

def to_iso(dt) -> Optional[str]:
    if not dt:
        return None
    if isinstance(dt, str):
        try:
            return dtp.parse(dt).isoformat()
        except Exception:
            return None
    try:
        return dt.isoformat()
    except Exception:
        return None