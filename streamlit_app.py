"""
Main Streamlit application for Oxford Events
"""

import streamlit as st
from datetime import datetime
from components.css import BANDSINTOWN_CSS
from components.filters import render_filter_chips
from components.event_card import render_event_card
from utils.filters import apply_all_filters
from utils.image_processing import curl_test_url

# Page config
st.set_page_config(
    page_title="Oxford Events",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.set_option("client.showErrorDetails", True)

# Apply CSS
st.markdown(BANDSINTOWN_CSS, unsafe_allow_html=True)

# Event sources
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


@st.cache_data(ttl=7200)
def load_events():
    """Load and cache events"""
    try:
        from lib.aggregator import collect_events
        return collect_events()
    except Exception as e:
        st.error(f"Error loading events: {e}")
        # Fallback to mock data
        from datetime import date, timedelta
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

# Load events
events = load_events()

# Initialize filter state
if "category_filter" not in st.session_state:
    st.session_state["category_filter"] = "All"

# Read URL params for initial filter state
query_params = st.query_params
if "category_filter" in query_params:
    st.session_state["category_filter"] = query_params["category_filter"]

# Get all unique categories from events
all_categories = sorted(set([e.get("category", "Other") for e in events if e.get("category")]))
category_options = ["All"] + all_categories

# Render filter chips
render_filter_chips(
    category_options,
    st.session_state.get("category_filter", "All")
)

# Apply filters
filtered_events = apply_all_filters(
    events,
    date_filter="all",  # No date filtering
    category_filter=st.session_state.get("category_filter", "All"),
    search_term=st.session_state.get("search", "")
)

# Stats
try:
    from lib.aggregator import get_event_stats
    stats = get_event_stats(filtered_events)
except:
    stats = {
        "total": len(filtered_events), 
        "free": len([e for e in filtered_events if "Free" in e.get("cost", "")]), 
        "categories": len(set([e.get("category") for e in filtered_events if e.get("category")]))
    }

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

# Debug panel
with st.sidebar:
    with st.expander("🔧 Debug Tools", expanded=False):
        st.session_state["debug_mode"] = st.checkbox(
            "Enable Debug Mode", 
            value=st.session_state.get("debug_mode", False), 
            key="debug_toggle"
        )
        
        st.markdown("### URL Diagnostics (curl-like)")
        st.caption("Test any URL to see status code, headers, content-type (like curl -I)")
        debug_url = st.text_input("Test URL", placeholder="https://example.com/image.jpg", key="debug_url")
        if debug_url:
            with st.spinner("Testing URL..."):
                diag = curl_test_url(debug_url)
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
            "events_count": len(filtered_events),
            "sources_count": len(EVENT_SOURCES),
            "timestamp": datetime.now().isoformat(),
            "debug_mode": st.session_state.get("debug_mode", False)
        })

# Event grid
if filtered_events:
    # Create 3-column grid
    for i in range(0, len(filtered_events), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(filtered_events):
                event = filtered_events[i + j]
                with cols[j]:
                    render_event_card(event, debug_mode=st.session_state.get("debug_mode", False))
else:
    st.info("No events found matching your filters.")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(EVENT_SOURCES)} sources")
