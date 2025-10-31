import streamlit as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
from dateutil import parser as dtp, tz
import re
import urllib.parse
import csv
import io
import json
import requests
from typing import Optional, Dict, Any, Tuple
from PIL import Image, ImageDraw
import base64

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

/* Event cards - Bandsintown style */
.event-card {
    background: white;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
    transition: box-shadow 0.2s;
}
.event-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.event-image {
    width: 100%;
    height: 180px;
    object-fit: cover;
    background: #f3f4f6;
}

.event-date-pill {
    font-size: 0.75rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin-top: 0.5rem;
}

.event-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
    margin: 0.5rem 0 0.25rem 0;
    line-height: 1.4;
}

.event-venue {
    font-size: 0.875rem;
    color: #6b7280;
    margin: 0.25rem 0;
}

.event-meta {
    font-size: 0.75rem;
    color: #9ca3af;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.calendar-icon {
    display: inline-block;
    width: 14px;
    height: 14px;
    vertical-align: middle;
    margin-right: 4px;
    opacity: 0.6;
}

/* Filter chips (Bandsintown style) */
.filter-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    padding: 0.75rem 0;
    align-items: center;
}

.filter-chip {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid #e5e7eb;
    background: white;
    color: #374151;
    text-decoration: none;
    white-space: nowrap;
}

.filter-chip:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
    transform: translateY(-1px);
}

.filter-chip.active {
    background: #1f2937;
    color: white;
    border-color: #1f2937;
}

.filter-chip.active:hover {
    background: #374151;
    border-color: #374151;
}

.filter-search-wrapper {
    flex: 1;
    min-width: 200px;
}

/* Style Streamlit buttons as chips */
.filter-chips-container button.stButton {
    margin: 0;
    padding: 0;
    flex-shrink: 0;
}

.filter-chips-container button.stButton > button {
    padding: 0.5rem 1rem !important;
    border-radius: 20px !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    border: 1px solid #e5e7eb !important;
    background: white !important;
    color: #374151 !important;
    transition: all 0.2s !important;
    white-space: nowrap !important;
    width: auto !important;
}

.filter-chips-container button.stButton > button:hover {
    background: #f3f4f6 !important;
    border-color: #d1d5db !important;
    transform: translateY(-1px);
}

/* Active state via data attribute (set via JavaScript) */
.filter-chips-container button.stButton[data-active="true"] > button {
    background: #1f2937 !important;
    color: white !important;
    border-color: #1f2937 !important;
}

.filter-chips-container button.stButton[data-active="true"] > button:hover {
    background: #374151 !important;
    border-color: #374151 !important;
}

/* Style search input within filter chips */
.filter-chips-container .stTextInput {
    flex: 1;
    min-width: 200px;
    margin-left: 0.5rem;
}

.filter-chips-container .stTextInput > div > div > input {
    padding: 0.5rem 1rem !important;
    border-radius: 20px !important;
    border: 1px solid #e5e7eb !important;
    font-size: 0.875rem !important;
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

# Load events first
events = load_events()

# Initialize filter state
if "date_filter" not in st.session_state:
    st.session_state["date_filter"] = "all"
if "category_filter" not in st.session_state:
    st.session_state["category_filter"] = "All"

# Read URL params for initial filter state (before rendering)
query_params = st.query_params
if "date_filter" in query_params:
    st.session_state["date_filter"] = query_params["date_filter"]
if "category_filter" in query_params:
    st.session_state["category_filter"] = query_params["category_filter"]

# Get all unique categories from events
all_categories = sorted(set([e.get("category", "Other") for e in events if e.get("category")]))
category_options = ["All"] + all_categories

# Callback functions for filter chips
def set_date_filter(value):
    st.session_state["date_filter"] = value
    st.rerun()

def set_category_filter(value):
    st.session_state["category_filter"] = value
    st.rerun()

# Filter chips (Bandsintown style)
st.markdown('<div class="filter-chips filter-chips-container">', unsafe_allow_html=True)

# Date filter chips
date_filters = [
    ("Today", "today"),
    ("This Week", "week"),
    ("This Month", "month"),
    ("All Dates", "all")
]

for label, value in date_filters:
    st.button(label, key=f"date_{value}", on_click=set_date_filter, args=(value,))

# Separator
st.markdown('<span style="margin: 0 0.5rem; color: #9ca3af; font-size: 0.875rem;">|</span>', unsafe_allow_html=True)

# Category filter chips
for cat in category_options:
    st.button(cat, key=f"cat_{cat}", on_click=set_category_filter, args=(cat,))

# Search
search = st.text_input("Search", placeholder="Search events...", key="search", label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True)

# JavaScript to set active state based on session state
current_date_filter = st.session_state.get("date_filter", "all")
current_cat_filter = st.session_state.get("category_filter", "All")

# Map filter values to button labels
date_label_map = {v: l for l, v in date_filters}
active_date_label = date_label_map.get(current_date_filter, "All Dates")

st.markdown(f"""
<script>
(function() {{
    setTimeout(function() {{
        const filterContainer = document.querySelector('.filter-chips-container');
        if (!filterContainer) return;
        
        const buttons = filterContainer.querySelectorAll('.stButton button');
        buttons.forEach(btn => {{
            const btnText = btn.textContent.trim();
            const stBtn = btn.closest('.stButton');
            
            // Check if this is an active date filter button
            if ({json.dumps([l for l, _ in date_filters])}.includes(btnText)) {{
                if (btnText === '{active_date_label}') {{
                    stBtn.setAttribute('data-active', 'true');
                }} else {{
                    stBtn.setAttribute('data-active', 'false');
                }}
            }}
            // Check if this is an active category filter button
            else if ({json.dumps(category_options)}.includes(btnText)) {{
                if (btnText === '{current_cat_filter}') {{
                    stBtn.setAttribute('data-active', 'true');
                }} else {{
                    stBtn.setAttribute('data-active', 'false');
                }}
            }}
        }});
    }}, 200);
}})();
</script>
""", unsafe_allow_html=True)

# Apply filters to events
filtered_events = events.copy()

# Date filter
date_filter = st.session_state.get("date_filter", "all")
if date_filter != "all":
    today = date.today()
    def parse_event_date(ev):
        try:
            return dtp.parse(ev.get("start_iso", "")).date()
        except:
            return None
    
    if date_filter == "today":
        filtered_events = [e for e in filtered_events if parse_event_date(e) == today]
    elif date_filter == "week":
        week_end = today + timedelta(days=7)
        filtered_events = [e for e in filtered_events if parse_event_date(e) and today <= parse_event_date(e) <= week_end]
    elif date_filter == "month":
        month_end = today + timedelta(days=30)
        filtered_events = [e for e in filtered_events if parse_event_date(e) and today <= parse_event_date(e) <= month_end]

# Category filter
category_filter = st.session_state.get("category_filter", "All")
if category_filter != "All":
    filtered_events = [e for e in filtered_events if e.get("category") == category_filter]

# Search filter
search_term = st.session_state.get("search", "").lower()
if search_term:
    filtered_events = [
        e for e in filtered_events
        if search_term in (e.get("title", "") + " " + e.get("location", "") + " " + e.get("description", "")).lower()
    ]

# Update events to filtered
events = filtered_events

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

# Sports team detection and logo helpers
TEAM_NAMES = {
    # Ole Miss / SEC teams
    "ole miss": ("Ole Miss", "https://logos-world.net/wp-content/uploads/2020/06/Ole-Miss-Logo.png"),
    "rebel": ("Ole Miss", "https://logos-world.net/wp-content/uploads/2020/06/Ole-Miss-Logo.png"),
    "rebels": ("Ole Miss", "https://logos-world.net/wp-content/uploads/2020/06/Ole-Miss-Logo.png"),
    "alabama": ("Alabama", "https://logos-world.net/wp-content/uploads/2020/06/Alabama-Crimson-Tide-Logo.png"),
    "crimson tide": ("Alabama", "https://logos-world.net/wp-content/uploads/2020/06/Alabama-Crimson-Tide-Logo.png"),
    "arkansas": ("Arkansas", "https://logos-world.net/wp-content/uploads/2020/06/Arkansas-Razorbacks-Logo.png"),
    "razorbacks": ("Arkansas", "https://logos-world.net/wp-content/uploads/2020/06/Arkansas-Razorbacks-Logo.png"),
    "lsu": ("LSU", "https://logos-world.net/wp-content/uploads/2020/06/LSU-Tigers-Logo.png"),
    "tigers": ("LSU", "https://logos-world.net/wp-content/uploads/2020/06/LSU-Tigers-Logo.png"),
    "mississippi state": ("Miss State", "https://logos-world.net/wp-content/uploads/2020/06/Mississippi-State-Bulldogs-Logo.png"),
    "bulldogs": ("Miss State", "https://logos-world.net/wp-content/uploads/2020/06/Mississippi-State-Bulldogs-Logo.png"),
    "auburn": ("Auburn", "https://logos-world.net/wp-content/uploads/2020/06/Auburn-Tigers-Logo.png"),
    "georgia": ("Georgia", "https://logos-world.net/wp-content/uploads/2020/06/Georgia-Bulldogs-Logo.png"),
    "florida": ("Florida", "https://logos-world.net/wp-content/uploads/2020/06/Florida-Gators-Logo.png"),
    "tennessee": ("Tennessee", "https://logos-world.net/wp-content/uploads/2020/06/Tennessee-Volunteers-Logo.png"),
}

@st.cache_data
def _detect_sports_teams(title: str) -> Optional[Tuple[Tuple[str, str], Tuple[str, str]]]:
    """Detect two teams from event title. Returns ((away_name, away_logo), (home_name, home_logo)) or None."""
    title_lower = title.lower()
    # Pattern: "Team A vs Team B" or "Team A @ Team B"
    vs_pattern = r'(.+?)\s+(?:vs|@|v\.|versus)\s+(.+?)(?:\s+in|\s+at|\s+|$)'
    match = re.search(vs_pattern, title_lower)
    if not match:
        return None
    
    team1_text, team2_text = match.groups()
    
    # Find team names
    def find_team(text):
        for key, (name, logo_url) in TEAM_NAMES.items():
            if key in text:
                return name, logo_url
        return None, None
    
    team1_result = find_team(team1_text.strip())
    team2_result = find_team(team2_text.strip())
    
    if team1_result[0] and team2_result[0]:
        # First team is away, second is home (Ole Miss is typically home when second)
        return team1_result, team2_result
    
    return None

@st.cache_data
def _get_logo_image(url: str, size: int = 120) -> Optional[Image.Image]:
    """Download and resize team logo."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img = img.convert("RGBA")
            # Resize maintaining aspect ratio
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            return img
    except Exception:
        pass
    return None

def _create_team_matchup_image(away_team: Tuple[str, str], home_team: Tuple[str, str], width: int = 400, height: int = 300) -> io.BytesIO:
    """Create composite image with away team (upper left), home team (lower right), diagonal divider."""
    img = Image.new("RGB", (width, height), color="#f8f9fa")
    draw = ImageDraw.Draw(img)
    
    # Draw diagonal line from bottom-left to top-right
    draw.line([(0, height), (width, 0)], fill="#000000", width=4)
    
    # Download and place logos
    away_logo = _get_logo_image(away_team[1], size=120)
    home_logo = _get_logo_image(home_team[1], size=120)
    
    if away_logo:
        # Upper left quadrant (center at x=width/4, y=height/4)
        paste_x = width // 4 - away_logo.width // 2
        paste_y = height // 4 - away_logo.height // 2
        img.paste(away_logo, (paste_x, paste_y), away_logo if away_logo.mode == "RGBA" else None)
    
    if home_logo:
        # Lower right quadrant (center at x=3*width/4, y=3*height/4)
        paste_x = 3 * width // 4 - home_logo.width // 2
        paste_y = 3 * height // 4 - home_logo.height // 2
        img.paste(home_logo, (paste_x, paste_y), home_logo if home_logo.mode == "RGBA" else None)
    
    # Convert to base64 for display
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

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

# Helper - event image URL with validation and sports detection
def _event_image_url(ev: dict, validate: bool = False) -> Tuple[Any, Optional[Dict[str, Any]]]:
    """
    Get event image URL or generated image, optionally validate it.
    For sports events, generates team matchup image.
    Returns (image_url_or_buffer, diagnostics_dict) or (image_url_or_buffer, None).
    """
    # Check if it's a sports event with team matchup
    title = ev.get("title", "")
    if ev.get("category") == "Sports" or "vs" in title.lower() or "@" in title.lower():
        teams = _detect_sports_teams(title)
        if teams:
            away, home = teams
            matchup_img = _create_team_matchup_image(away, home)
            return matchup_img, None
    
    url = (ev.get("image") or ev.get("img") or "").strip()
    if url:
        if validate:
            diag = _curl_test_url(url)
            if not diag["accessible"]:
                # Fallback to smaller placeholder
                url = "https://placehold.co/400x250/e5e7eb/6b7280?text=Event"
            return url, diag
        return url, None
    # Smaller placeholder (Bandsintown-style)
    placeholder = "https://placehold.co/400x250/e5e7eb/6b7280?text=Event"
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

                    # Bandsintown-style event card
                    with st.container():
                        st.markdown('<div class="event-card">', unsafe_allow_html=True)
                        
                        # Smaller image (Bandsintown style)
                        _img, _diag = _event_image_url(event, validate=False)
                        if _diag and st.session_state.get("debug_mode", False):
                            with st.expander(f"Image Diagnostics: {str(_img)[:50]}..."):
                                st.json(_diag)
                        
                        # Handle both URL strings and image buffers
                        try:
                            if isinstance(_img, io.BytesIO):
                                # Reset buffer position
                                _img.seek(0)
                                st.image(_img, use_container_width=True)
                            else:
                                st.image(_img, use_container_width=True)
                        except Exception as e:
                            # If image fails, try validation fallback
                            _img_new, _diag_new = _event_image_url(event, validate=True)
                            try:
                                if isinstance(_img_new, io.BytesIO):
                                    _img_new.seek(0)
                                    st.image(_img_new, use_container_width=True)
                                else:
                                    st.markdown(f'<img src="{_img_new}" class="event-image" alt="Event image" />', unsafe_allow_html=True)
                            except:
                                # Final fallback
                                st.markdown(f'<div class="event-image"></div>', unsafe_allow_html=True)

                        # Card content
                        st.markdown('<div style="padding: 1rem;">', unsafe_allow_html=True)
                        
                        # Date with calendar icon (Bandsintown style)
                        date_display = event_date.upper() if event_date != "TBA" else "TBA"
                        calendar_svg = '<svg class="calendar-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
                        st.markdown(f'<div class="event-date-pill">{calendar_svg} {date_display} {event_time}</div>', unsafe_allow_html=True)
                        
                        # Title as link
                        title = event.get("title") or "Event"
                        link = event.get("link")
                        if link:
                            st.markdown(f'<a href="{link}" style="text-decoration: none; color: inherit;"><h3 class="event-title">{title}</h3></a>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<h3 class="event-title">{title}</h3>', unsafe_allow_html=True)
                        
                        # Venue
                        location = event.get("location", "")
                        st.markdown(f'<div class="event-venue">{location}</div>', unsafe_allow_html=True)
                        
                        # Meta info (time, cost, category) - typography-based
                        meta_parts = []
                        if event_time:
                            meta_parts.append(event_time)
                        cost = event.get("cost", "")
                        if cost and cost != "Free":
                            meta_parts.append(cost)
                        category = event.get("category", "")
                        if category:
                            meta_parts.append(category)
                        
                        if meta_parts:
                            meta_text = " • ".join(meta_parts)
                            st.markdown(f'<div class="event-meta">{meta_text}</div>', unsafe_allow_html=True)
                        
                        # Tickets button (Bandsintown style)
                        if link:
                            st.link_button("Tickets", link, use_container_width=True)
                        else:
                            st.button("Details", key=f"det_{i}_{j}", use_container_width=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)  # Close padding
                        st.markdown('</div>', unsafe_allow_html=True)  # Close event-card

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(EVENT_SOURCES)} sources")
