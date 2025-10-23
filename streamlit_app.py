import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser as dtp, tz
from components.blocks import hero, event_card
from lib.aggregator import collect, window
from lib.calendar_links import google_link, build_ics
import json, io, base64, os

st.set_page_config(page_title="Upcoming in Oxford", page_icon="📅", layout="wide")
hero()

st.sidebar.header("Filters")
today = datetime.now(tz.tzlocal()).date()
date_min = st.sidebar.date_input("From date", today)
date_max = st.sidebar.date_input("To date", today + timedelta(days=21))

st.sidebar.caption("Tip: open the page to refresh data.")

# Load data
@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_events():
    try:
        events = collect()
        return events
    except Exception:
        # graceful fallback to sample
        with open("data/sample_events.json","r",encoding="utf-8") as f:
            return json.load(f)

events = _fetch_events()

# Filter to window and date range
events3 = window(events, days=60)  # broaden first, then date filter
def _within(ev):
    if not ev.get("start_iso"): 
        return False
    d = dtp.parse(ev["start_iso"]).date()
    return date_min <= d <= date_max

events_sel = [e for e in events3 if _within(e)]

# Category filter
cats = sorted({e.get("category") or "Uncategorized" for e in events_sel})
cat_choice = st.sidebar.multiselect("Category", options=cats, default=cats)
events_sel = [e for e in events_sel if (e.get("category") or "Uncategorized") in cat_choice]

# Top metrics
st.markdown("### Upcoming events")
st.caption(f"{len(events_sel)} events from public calendars & sites")

# Table
if events_sel:
    df = pd.DataFrame(events_sel)
    df_show = df[["title","start_iso","location","cost","category","source","link"]].rename(columns={
        "start_iso":"start"
    })
    st.dataframe(df_show, hide_index=True, use_container_width=True)
else:
    st.info("No events in this range (yet). Try expanding the date window.")

# Cards
for ev in events_sel[:40]:
    event_card(ev)
    # Calendar buttons
    colA, colB, colC = st.columns([1,1,5])
    start_iso = ev.get("start_iso")
    end_iso = ev.get("end_iso") or start_iso
    title = ev.get("title")
    details = (ev.get("description") or "")[:996]
    loc = ev.get("location") or ""
    if start_iso:
        g_url = google_link(title, start_iso, end_iso, details, loc)
        with colA:
            st.link_button("Add to Google Calendar", g_url, use_container_width=True)
        ics_text = build_ics(title, start_iso, end_iso, details, loc)
        ics_bytes = ics_text.encode("utf-8")
        with colB:
            st.download_button("Download .ics (Apple/Outlook)", data=ics_bytes, file_name=f"{title}.ics", mime="text/calendar", use_container_width=True)

# Venue map (best effort)
with st.expander("Map of known venues"):
    import folium
    import pandas as pd
    venues = pd.read_csv("data/venues.csv")
    if not venues.empty:
        # Center roughly on Oxford
        m = folium.Map(location=[34.366, -89.519], zoom_start=13)
        for _, row in venues.iterrows():
            folium.Marker([row["lat"], row["lon"]], popup=row["name"]).add_to(m)
        from streamlit.components.v1 import html as html_component
        html_component(m._repr_html_(), height=420)
    else:
        st.caption("No venues available.")