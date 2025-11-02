"""
Simplified event aggregator for Oxford Events
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from dateutil import parser as dtp, tz

def collect_events() -> List[Dict[str, Any]]:
    """
    Simplified event collection - returns mock data for now
    Replace with real data collection later
    """
    today = datetime.now(tz.tzlocal()).date()
    events = [
        {
            "title": "Ole Miss Football vs Alabama",
            "start_iso": (today + timedelta(days=7)).isoformat(),
            "location": "Vaught-Hemingway Stadium",
            "cost": "Free",
            "category": "Sports",
            "source": "Ole Miss Athletics",
            "link": "https://olemisssports.com",
            "description": "Rebels take on the Crimson Tide in a SEC matchup."
        },
        {
            "title": "Square Books Author Reading",
            "start_iso": (today + timedelta(days=3)).isoformat(),
            "location": "Square Books",
            "cost": "Free",
            "category": "Arts & Culture",
            "source": "Visit Oxford",
            "link": "https://squarebooks.com",
            "description": "Join us for an evening with bestselling author discussing their latest work."
        },
        {
            "title": "Proud Larry's Live Music",
            "start_iso": (today + timedelta(days=5)).isoformat(),
            "location": "Proud Larry's",
            "cost": "$10",
            "category": "Music",
            "source": "SeatGeek",
            "link": "https://proudlarrys.com",
            "description": "Local band performing original songs and covers."
        },
        {
            "title": "Ole Miss Basketball vs Arkansas",
            "start_iso": (today + timedelta(days=2)).isoformat(),
            "location": "The Pavilion",
            "cost": "$15",
            "category": "Sports",
            "source": "Ole Miss Athletics",
            "link": "https://olemisssports.com",
            "description": "Men's basketball game against Arkansas."
        },
        {
            "title": "Oxford Farmers Market",
            "start_iso": (today + timedelta(days=1)).isoformat(),
            "location": "Oxford Square",
            "cost": "Free",
            "category": "Community",
            "source": "Visit Oxford",
            "link": "https://visitoxfordms.com",
            "description": "Weekly farmers market with local produce, crafts, and food."
        },
        {
            "title": "The Lyric Oxford - Concert",
            "start_iso": (today + timedelta(days=10)).isoformat(),
            "location": "The Lyric Oxford",
            "cost": "$25",
            "category": "Music",
            "source": "Ticketmaster",
            "link": "https://www.thelyricoxford.com",
            "description": "Live concert featuring local and touring artists."
        }
    ]

    # Filter to next 3 weeks
    cutoff = datetime.now(tz.tzlocal()) + timedelta(days=21)
    filtered_events = []
    for event in events:
        if event.get("start_iso"):
            try:
                event_date = dtp.parse(event["start_iso"])
                if event_date <= cutoff:
                    filtered_events.append(event)
            except:
                continue
        else:
            filtered_events.append(event)

    return sorted(filtered_events, key=lambda x: x.get("start_iso", ""))

def get_event_stats(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get basic statistics about events"""
    return {
        "total": len(events),
        "free": len([e for e in events if "Free" in e.get("cost", "")]),
        "categories": len(set([e.get("category", "") for e in events])),
        "sources": len(set([e.get("source", "") for e in events]))
    }
