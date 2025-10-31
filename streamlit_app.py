import streamlit as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
from dateutil import parser as dtp, tz
import re
import urllib.parse
import csv
import io
import requests
from typing import Optional, Dict, Any, Tuple

# Page config
st.set_page_config(
    page_title="Oxford Events",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.set_option("client.showErrorDetails", True)

# Custom CSS for clean, professional design
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Let Streamlit manage background via theme to keep text readable in light/dark modes */

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
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.025em;
}

.header p {
    font-size: 1rem;
    margin: 0;
}

/* Top accent bar */
.accent-bar { height: 4px; background: linear-gradient(90deg, #22c1c3 0%, #3a7bd5 100%); margin-bottom: 0; }

/* Hero (Bandsintown-inspired) */
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #334155 100%);
    color: white;
    padding: 2rem 1rem;
    border-radius: 0 0 16px 16px;
    margin-bottom: 1rem;
}
.hero h1 { font-size: 2.25rem; margin: 0 0 .5rem 0; letter-spacing: -0.02em; }
.hero p { margin: 0; opacity: .9; }

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

# Header (Bandsintown style)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="hero">
  <h1>Concerts & Events in Oxford</h1>
  <p>Browse live music, community happenings, athletics, arts and more over the next 3 weeks.</p>
</div>
""", unsafe_allow_html=True)

# Combined filters and search (chip-like)
col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 3])

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

# Helper - curl-like URL diagnostics (defined early for sidebar use)
def _curl_test_url(url: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Test a URL like curl -I would: returns status, headers, content-type, size.
    """
    result = {
        "url": url,
        "status_code": None,
        "content_type": None,
        "content_length": None,
        "headers": {},
        "error": None,
        "accessible": False
    }
    
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        result["status_code"] = response.status_code
        result["content_type"] = response.headers.get("Content-Type", "unknown")
        result["content_length"] = response.headers.get("Content-Length", "unknown")
        result["headers"] = dict(response.headers)
        result["accessible"] = 200 <= response.status_code < 400
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection Error"
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"Unexpected: {type(e).__name__}: {e}"
    
    return result

# Helper - event image URL with validation
def _event_image_url(ev: dict, validate: bool = False) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Get event image URL, optionally validate it.
    Returns (url, diagnostics_dict) or (url, None).
    """
    url = (ev.get("image") or ev.get("img") or "").strip()
    if url:
        if validate:
            diag = _curl_test_url(url)
            if not diag["accessible"]:
                # Fallback to placeholder if validation fails
                url = "https://placehold.co/800x1000/1f2937/ffffff?text=Oxford+Event"
            return url, diag
        return url, None
    # poster-like placeholder (4:5)
    placeholder = "https://placehold.co/800x1000/1f2937/ffffff?text=Oxford+Event"
    return placeholder, None

# Debug panel (curl-like diagnostics) - after events are loaded
with st.sidebar:
    with st.expander("🔧 Debug Tools", expanded=False):
        # Debug mode toggle
        st.session_state["debug_mode"] = st.checkbox("Enable Debug Mode", value=st.session_state.get("debug_mode", False), key="debug_toggle")
        
        st.markdown("### URL Diagnostics (curl-like)")
        st.caption("Test any URL to see status code, headers, content-type (like curl -I)")
        debug_url = st.text_input("Test URL", placeholder="https://example.com/image.jpg", key="debug_url")
        if debug_url:
            with st.spinner("Testing URL..."):
                diag = _curl_test_url(debug_url)
                if diag["accessible"]:
                    st.success(f"✅ {diag['status_code']} - {diag['content_type']}")
                else:
                    st.error(f"❌ Status: {diag['status_code']} - {diag.get('error', 'Failed')}")
                st.json(diag)
        
        st.markdown("---")
        st.markdown("### App Diagnostics")
        if st.button("Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")
        
        st.markdown("**Current State:**")
        st.json({
            "events_count": len(events),
            "sources_count": len(EVENT_SOURCES),
            "timestamp": datetime.now().isoformat(),
            "debug_mode": st.session_state.get("debug_mode", False)
        })

# Event grid - using Streamlit components for proper rendering
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

                    # Use Streamlit components with a bordered card
                    with st.container(border=True):
                        # Image header (poster) with diagnostics & safe fallback
                        _img, _diag = _event_image_url(event, validate=False)
                        # If diagnostics available, show in debug mode
                        if _diag and st.session_state.get("debug_mode", False):
                            with st.expander(f"🔍 Image Diagnostics: {_img[:50]}..."):
                                st.json(_diag)
                        try:
                            st.image(_img, use_container_width=True)
                        except Exception as e:
                            # If image fails, validate URL and show diagnostics
                            _img_new, _diag_new = _event_image_url(event, validate=True)
                            if _diag_new:
                                st.error(f"Image failed to load: {_diag_new.get('error', 'Unknown error')}")
                                with st.expander("📋 Full Diagnostics"):
                                    st.json(_diag_new)
                            # Fallback to HTML img tag
                            st.markdown(f"<img src='{_img_new}' style='width:100%;border-radius:8px' alt='Event image' />", unsafe_allow_html=True)

                        # Date pill at top
                        st.markdown(f"**{event_date}**  · {event_time}")
                        # Title as link to details when available
                        title = event.get("title") or "Event"
                        link = event.get("link")
                        if link:
                            st.markdown(f"#### [{title}]({link})")
                        else:
                            st.markdown(f"#### {title}")

                        # Date and location
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption(f"📅 {event_date}")
                            st.caption(f"🕐 {event_time}")
                        with col2:
                            st.caption(f"📍 {event['location']}")

                        # Badges for cost and category
                        badge_cols = st.columns(2)
                        with badge_cols[0]:
                            if "Free" in event.get("cost", ""):
                                st.markdown("🟢 **FREE**")
                            else:
                                st.markdown(f"💰 **{event.get('cost','')}**")
                        with badge_cols[1]:
                            st.markdown(f"🏷️ **{event['category']}**")

                        # Description
                        if len(event["description"]) > 100:
                            st.caption(event["description"][:100] + "...")
                        else:
                            st.caption(event["description"])

                        # Action buttons - compact CTAs inspired by Bandsintown
                        btn_cols = st.columns([1,1,1])
                        with btn_cols[0]:
                            if st.button("📅 Add", key=f"cal_{i}_{j}"):
                                st.info("Calendar integration coming soon!")
                        with btn_cols[1]:
                            if link:
                                st.link_button("🎟️ Tickets", link, use_container_width=True)
                            else:
                                st.button("🔗 Details", key=f"det_{i}_{j}")
                        with btn_cols[2]:
                            if st.button("📍 Map", key=f"map_{i}_{j}"):
                                st.info(f"Location: {event['location']}")

                    st.markdown("---")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(EVENT_SOURCES)} sources")
