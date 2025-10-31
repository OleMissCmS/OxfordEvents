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

/* Filter section */
.filter-section {
    background: white;
    padding: 1.25rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* Quick filter buttons */
.quick-filter-btn {
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    margin: 0.25rem;
    transition: all 0.2s ease;
    cursor: pointer;
}

.quick-filter-btn:hover {
    background: #e2e8f0;
    border-color: #94a3b8;
}

.quick-filter-btn.active {
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
}

/* Event cards */
.event-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.event-card {
    background: white;
    border-radius: 8px;
    padding: 1.25rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
}

.event-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-color: #cbd5e1;
}

.event-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1e293b;
    margin: 0 0 0.75rem 0;
    line-height: 1.3;
}

.event-meta {
    font-size: 0.875rem;
    color: #64748b;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.event-description {
    font-size: 0.875rem;
    color: #475569;
    margin-bottom: 1rem;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* Action buttons */
.action-buttons {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

.btn-primary {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary:hover {
    background: #2563eb;
}

.btn-secondary {
    background: white;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-secondary:hover {
    background: #f8fafc;
    border-color: #94a3b8;
}

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

/* Search bar */
.search-container {
    background: white;
    padding: 1.25rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    border: 1px solid #e2e8f0;
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

# Quick filters
st.markdown('<div class="filter-section">', unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("Today", key="today", use_container_width=True):
        st.session_state["date_filter"] = "today"

with col2:
    if st.button("This Week", key="week", use_container_width=True):
        st.session_state["date_filter"] = "week"

with col3:
    if st.button("This Month", key="month", use_container_width=True):
        st.session_state["date_filter"] = "month"

with col4:
    if st.button("All", key="all", use_container_width=True):
        st.session_state["date_filter"] = "all"

with col5:
    category = st.selectbox("Category", ["All", "Sports", "Music", "Arts", "Community"], key="category_filter")

st.markdown('</div>', unsafe_allow_html=True)

# Search
st.markdown('<div class="search-container">', unsafe_allow_html=True)
search = st.text_input("Search events", placeholder="Search by event name, venue, or description", key="search")
st.markdown('</div>', unsafe_allow_html=True)

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

# Event grid
st.markdown('<div class="event-grid">', unsafe_allow_html=True)

for event in events:
    # Format date
    try:
        event_date = dtp.parse(event["start_iso"]).strftime("%a, %b %d")
        event_time = dtp.parse(event["start_iso"]).strftime("%I:%M %p")
    except:
        event_date = "TBA"
        event_time = ""

    st.markdown(f"""
    <div class="event-card">
        <h3 class="event-title">{event["title"]}</h3>

        <div class="event-meta">
            <span>📅 {event_date}</span>
            <span>🕐 {event_time}</span>
            <span>📍 {event["location"]}</span>
        </div>

        <div class="event-meta">
            <span>💰 {event["cost"]}</span>
            <span>🏷️ {event["category"]}</span>
        </div>

        <p class="event-description">{event["description"]}</p>

        <div class="action-buttons">
            <button class="btn-primary">📅 Add to Calendar</button>
            <button class="btn-secondary">🔗 Details</button>
            <button class="btn-secondary">📍 Map</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(EVENT_SOURCES)} sources")
