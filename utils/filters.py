"""
Event filtering utilities
"""

from datetime import date, timedelta
from dateutil import parser as dtp
from typing import List, Dict, Any


def parse_event_date(event: dict) -> Any:
    """Parse event date, returning date object or None if parsing fails."""
    try:
        return dtp.parse(event.get("start_iso", "")).date()
    except:
        return None


def filter_events_by_date(
    events: List[Dict[str, Any]], 
    date_filter: str
) -> List[Dict[str, Any]]:
    """Filter events by date range."""
    if date_filter == "all":
        return events
    
    today = date.today()
    filtered = []
    
    for event in events:
        event_date = parse_event_date(event)
        if event_date is None:
            continue
            
        if date_filter == "today":
            if event_date == today:
                filtered.append(event)
        elif date_filter == "week":
            week_end = today + timedelta(days=7)
            if today <= event_date <= week_end:
                filtered.append(event)
        elif date_filter == "month":
            month_end = today + timedelta(days=30)
            if today <= event_date <= month_end:
                filtered.append(event)
    
    return filtered


def filter_events_by_category(
    events: List[Dict[str, Any]], 
    category: str
) -> List[Dict[str, Any]]:
    """Filter events by category."""
    if category == "All":
        return events
    return [e for e in events if e.get("category") == category]


def filter_events_by_search(
    events: List[Dict[str, Any]], 
    search_term: str
) -> List[Dict[str, Any]]:
    """Filter events by search term."""
    if not search_term:
        return events
    
    search_lower = search_term.lower()
    filtered = []
    
    for event in events:
        title = (event.get("title", "") or "").lower()
        location = (event.get("location", "") or "").lower()
        description = (event.get("description", "") or "").lower()
        
        if search_lower in title or search_lower in location or search_lower in description:
            filtered.append(event)
    
    return filtered


def apply_all_filters(
    events: List[Dict[str, Any]],
    date_filter: str = "all",
    category_filter: str = "All",
    search_term: str = ""
) -> List[Dict[str, Any]]:
    """Apply all filters to events list."""
    filtered = events.copy()
    filtered = filter_events_by_date(filtered, date_filter)
    filtered = filter_events_by_category(filtered, category_filter)
    filtered = filter_events_by_search(filtered, search_term)
    return filtered

