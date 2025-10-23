import streamlit as st, pandas as pd, json, random
from datetime import datetime, timedelta
from dateutil import parser as dtp, tz
from components.blocks import hero, event_card
from lib.aggregator import collect_with_progress, window
from lib.calendar_links import google_link, build_ics

st.set_page_config(page_title="Upcoming in Oxford", page_icon="📅", layout="wide", initial_sidebar_state="expanded")

OLE_MISS_LINES=["🔴🔵 Hotty Toddy! Rallying the calendars…","🏈 Checking the Rebels’ schedule…","📣 Hitting the Chamber board…","🎟️ Peeking at Eventbrite…","🎨 Scouting Visit Oxford’s arts & festivals…","📚 Cruising campus events…"]
hero("Gathering events around Oxford & Ole Miss…")

status = st.status("Starting up…", expanded=True)
def _notify(name, i, total):
    status.update(label=f"{random.choice(OLE_MISS_LINES)} ({i}/{total}) — {name}", state="running")

events = collect_with_progress(_notify)
status.update(label=f"All set — {len(events)} items!", state="complete")

st.sidebar.header("Filters")
today = datetime.now(tz.tzlocal()).date()
date_min = st.sidebar.date_input("From date", today)
date_max = st.sidebar.date_input("To date", today + timedelta(days=21))

events3 = window(events, days=60)

def _within(ev):
    if not ev.get("start_iso"): return False
    d = dtp.parse(ev["start_iso"]).date()
    return date_min <= d <= date_max

events_sel = [e for e in events3 if _within(e)]
cats = sorted({e.get("category") or "Uncategorized" for e in events_sel})
cat_choice = st.sidebar.multiselect("Category", options=cats, default=cats)
events_sel = [e for e in events_sel if (e.get("category") or "Uncategorized") in cat_choice]

st.markdown("### Upcoming events")
st.caption(f"{len(events_sel)} events from public calendars & sites")

for ev in events_sel[:120]:
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