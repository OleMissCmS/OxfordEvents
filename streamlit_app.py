import streamlit as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
from dateutil import parser as dtp, tz
import re
import urllib.parse
import csv
import io

# Page config
st.set_page_config(
    page_title="Oxford Events",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for clean, professional design
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: #f8fafc;
}

.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Header */
.header {
    text-align: center;
    padding: 1.5rem 0;
    margin-bottom: 2rem;
}

.header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.025em;
}

.header p {
    font-size: 1rem;
    color: #64748b;
    margin: 0;
}

/* Top accent bar */
.accent-bar {
    height: 4px;
    background: linear-gradient(90deg, #3b82f6 0%, #06b6d4 50%, #8b5cf6 100%);
    margin-bottom: 1rem;
}

/* Event cards - now using inline styles */

/* Stats section */
.stats-section {
    background: white;
    padding: 1.25rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    border: 1px solid #e2e8f0;
}

.stat-card {
    text-align: center;
    padding: 0.75rem;
}

.stat-number {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0;
}

.stat-label {
    font-size: 0.875rem;
    color: #64748b;
    margin: 0.25rem 0 0 0;
}


/* Responsive */
@media (max-width: 768px) {
    .event-grid {
        grid-template-columns: 1fr;
    }

    .header h1 {
        font-size: 1.5rem;
    }

    .action-buttons {
        flex-direction: column;
    }
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Event sources (same as before)
EVENT_SOURCES = [
    # Ole Miss Athletics
    {"name": "Ole Miss Football", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=football", "group": "University"},
    {"name": "Ole Miss MBB", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=mbball", "group": "University"},
    {"name": "Ole Miss WBB", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=wbball", "group": "University"},
    {"name": "Ole Miss Baseball", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=baseball", "group": "University"},
    {"name": "Ole Miss Softball", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=softball", "group": "University"},
    {"name": "Ole Miss Track", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=track", "group": "University"},
    {"name": "Ole Miss Soccer", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=soccer", "group": "University"},
    {"name": "Ole Miss Volleyball", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=volleyball", "group": "University"},
    {"name": "Ole Miss Tennis", "type": "ics", "url": "https://olemisssports.com/calendar.ashx/calendar.ics?path=tennis", "group": "University"},

    # Ole Miss Events
    {"name": "Ole Miss Events", "type": "rss", "url": "https://eventcalendar.olemiss.edu/calendar.xml", "group": "University"},

    # Community
    {"name": "Visit Oxford", "type": "html", "url": "https://visitoxfordms.com/events/", "parser": "simple_list", "group": "Community"},
    {"name": "SeatGeek", "type": "api", "parser": "seatgeek", "city": "Oxford", "state": "MS", "group": "Community"},
    {"name": "Ticketmaster", "type": "api", "parser": "ticketmaster", "city": "Oxford", "stateCode": "MS", "group": "Community"},
]

# Load events with caching
@st.cache_data(ttl=7200)
def load_events():
    """Load and cache events"""
    try:
        from lib.aggregator import collect_events
        return collect_events()
    except Exception as e:
        st.error(f"Error loading events: {e}")
        # Fallback to mock data
        today = date.today()
        return [
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
            }
        ]

# Header
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="header">
    <h1>Oxford Events</h1>
    <p>What's happening in Oxford, MS</p>
</div>
""", unsafe_allow_html=True)

# Combined filters and search
col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])

with col1:
    if st.button("Today", key="today"):
        st.session_state["date_filter"] = "today"

with col2:
    if st.button("This Week", key="week"):
        st.session_state["date_filter"] = "week"

with col3:
    if st.button("This Month", key="month"):
        st.session_state["date_filter"] = "month"

with col4:
    if st.button("All", key="all"):
        st.session_state["date_filter"] = "all"

with col5:
    category = st.selectbox("Category", ["All", "Sports", "Music", "Arts", "Community"], key="category_filter", label_visibility="collapsed")

with col6:
    search = st.text_input("Search", placeholder="event name, venue...", key="search", label_visibility="collapsed")

# Load events
events = load_events()

# Stats
try:
    from lib.aggregator import get_event_stats
    stats = get_event_stats(events)
except:
    stats = {"total": len(events), "free": 0, "categories": 0, "sources": len(EVENT_SOURCES)}

st.markdown('<div class="stats-section">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="stat-card">', unsafe_allow_html=True)
    st.markdown(f'<p class="stat-number">{stats["total"]}</p>', unsafe_allow_html=True)
    st.markdown('<p class="stat-label">Total Events</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="stat-card">', unsafe_allow_html=True)
    st.markdown(f'<p class="stat-number">{stats["free"]}</p>', unsafe_allow_html=True)
    st.markdown('<p class="stat-label">Free Events</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="stat-card">', unsafe_allow_html=True)
    st.markdown(f'<p class="stat-number">{stats["categories"]}</p>', unsafe_allow_html=True)
    st.markdown('<p class="stat-label">Categories</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="stat-card">', unsafe_allow_html=True)
    st.markdown(f'<p class="stat-number">{len(EVENT_SOURCES)}</p>', unsafe_allow_html=True)
    st.markdown('<p class="stat-label">Sources</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Event grid - using Streamlit columns for proper layout
if events:
    # Create 3-column grid
    for i in range(0, len(events), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(events):
                event = events[i + j]
                with cols[j]:
                    # Format date
                    try:
                        event_date = dtp.parse(event["start_iso"]).strftime("%a, %b %d")
                        event_time = dtp.parse(event["start_iso"]).strftime("%I:%M %p")
                    except:
                        event_date = "TBA"
                        event_time = ""

                    # Event card using Streamlit components
                    st.markdown(f"""
                    <div style="background: white; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);">
                        <h4 style="margin: 0 0 0.5rem 0; font-size: 1rem; font-weight: 600; color: #1e293b;">{event["title"]}</h4>

                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.25rem; font-size: 0.8rem; color: #64748b;">
                            <span>📅 {event_date}</span>
                            <span>🕐 {event_time}</span>
                        </div>

                        <div style="margin-bottom: 0.25rem; font-size: 0.8rem; color: #64748b;">
                            📍 {event["location"]}
                        </div>

                        <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem; font-size: 0.8rem;">
                            <span style="background: {'#dcfce7' if 'Free' in event['cost'] else '#fef3c7'}; color: {'#166534' if 'Free' in event['cost'] else '#92400e'}; padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-weight: 500;">{event["cost"]}</span>
                            <span style="background: #e0e7ff; color: #3730a3; padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-weight: 500;">{event["category"]}</span>
                        </div>

                        <p style="margin: 0 0 0.75rem 0; font-size: 0.8rem; color: #475569; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">{event["description"]}</p>

                        <div style="display: flex; gap: 0.25rem; flex-wrap: wrap;">
                            <button style="background: #f1f5f9; color: #1e293b; border: 1px solid #cbd5e1; border-radius: 4px; padding: 0.25rem 0.5rem; font-size: 0.75rem; font-weight: 500; cursor: pointer;">📅 Add to Calendar</button>
                            <button style="background: #f1f5f9; color: #1e293b; border: 1px solid #cbd5e1; border-radius: 4px; padding: 0.25rem 0.5rem; font-size: 0.75rem; font-weight: 500; cursor: pointer;">🔗 Details</button>
                            <button style="background: #f1f5f9; color: #1e293b; border: 1px solid #cbd5e1; border-radius: 4px; padding: 0.25rem 0.5rem; font-size: 0.75rem; font-weight: 500; cursor: pointer;">📍 Map</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(EVENT_SOURCES)} sources")
