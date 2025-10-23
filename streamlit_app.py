import streamlit as st
import pandas as pd
from collections import Counter
from datetime import datetime, timedelta
from dateutil import parser as dtp, tz
from components.blocks import hero, event_card
from lib.aggregator import collect, window, load_sources
from lib.calendar_links import google_link, build_ics

st.set_page_config(page_title="Upcoming in Oxford", page_icon="📅", layout="wide", initial_sidebar_state="expanded")

hero("What's happening, Oxford?")

@st.cache_data(ttl=7200, show_spinner=False)
def fetch_events_cached_pack():
    events = collect()
    return {"events": events, "fetched_at": datetime.now(tz.tzlocal()).isoformat()}

with st.spinner("Loading events…"):
    out = fetch_events_cached_pack()
events = out.get("events", [])
fetched_at = out.get("fetched_at")

st.sidebar.header("Filters")
if st.sidebar.button("🔄 Refresh events", help="Clear cache and re-collect"):
    fetch_events_cached_pack.clear()
    st.experimental_rerun()

# Toggle & panel
show_sources = st.sidebar.toggle("Show sources panel", value=False, help="Toggle to display the complete list of sources used by the app.")
source_filter_selected = None
if show_sources:
    src_defs = load_sources()
    counts = Counter([e.get("source") for e in events if e.get("source")])
    with st.sidebar.expander(f"Sources ({len(src_defs)})", expanded=True):
        for s in src_defs:
            name = s.get("name"); url = s.get("url"); typ = s.get("type","")
            c = counts.get(name, 0)
            st.markdown(f"- [{name}]({url}) — `{typ}` — **{c}** events")
    # NEW multi-select (defaults to all sources observed in dataset)
    opts = sorted([k for k,v in counts.items() if v>0] or [s.get("name") for s in src_defs])
    source_filter_selected = st.sidebar.multiselect("Filter by source(s)", options=opts, default=opts, help="Only show events from the selected sources.")

today = datetime.now(tz.tzlocal()).date()
date_min = st.sidebar.date_input("From date", today)
date_max = st.sidebar.date_input("To date", today + timedelta(days=21))

events3 = window(events, days=90)

def _within(ev):
    if not ev.get("start_iso"): return False
    d = dtp.parse(ev["start_iso"]).date()
    return date_min <= d <= date_max

events_sel = [e for e in events3 if _within(e)]

# Apply source filter if the panel is shown
if source_filter_selected is not None and len(source_filter_selected) > 0:
    events_sel = [e for e in events_sel if (e.get("source") in source_filter_selected)]

cats = sorted({e.get("category") or "Uncategorized" for e in events_sel})
cat_choice = st.sidebar.multiselect("Category", options=cats, default=cats)
events_sel = [e for e in events_sel if (e.get("category") or "Uncategorized") in cat_choice]

st.caption(f"Last updated: {fetched_at}")
st.markdown("### Upcoming events")
st.caption(f"{len(events_sel)} events from public calendars & sites")

for ev in events_sel[:150]:
    event_card(ev)
    colA, colB, colC = st.columns([1,1,5])
    start_iso = ev.get("start_iso"); end_iso = ev.get("end_iso") or start_iso
    title = ev.get("title"); details = (ev.get("description") or "")[:996]; loc = ev.get("location") or ""
    if start_iso:
        with colA: st.link_button("Add to Google Calendar", google_link(title, start_iso, end_iso, details, loc), use_container_width=True)
        with colB: st.download_button("Download .ics (Apple/Outlook)", data=build_ics(title, start_iso, end_iso, details, loc).encode("utf-8"), file_name=f"{title}.ics", mime="text/calendar", use_container_width=True)

with st.expander("Map of known venues"):
    import folium
    venues = pd.read_csv("data/venues.csv")
    if not venues.empty:
        m = folium.Map(location=[34.366, -89.519], zoom_start=13)
        for _, row in venues.iterrows():
            folium.Marker([row["lat"], row["lon"]], popup=row["name"]).add_to(m)
        from streamlit.components.v1 import html as html_component
        html_component(m._repr_html_(), height=420)
    else:
        st.caption("No venues available.")