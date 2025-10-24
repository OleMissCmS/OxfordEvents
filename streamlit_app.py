import streamlit as st
import pandas as pd
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from dateutil import parser as dtp, tz
from components.blocks import hero, event_card, unique_key
from lib.aggregator import collect_with_progress, window, load_sources
from lib.calendar_links import google_link, build_ics
from lib.parsers import __dict__ as parser_ns
from lib.data_io import parse_rss, parse_ics
import yaml, io, re

VERSION = "v4.8.1"

st.set_page_config(page_title="Upcoming in Oxford", page_icon="📅", layout="wide", initial_sidebar_state="expanded")
hero("What's happening, Oxford?")

@st.cache_data(ttl=7200, show_spinner=False)
def fetch_events_cached_pack():
    events, health = collect_with_progress(None)
    return {"events": events, "health": health, "fetched_at": datetime.now(tz.tzlocal()).isoformat()}

with st.spinner("Loading events…"):
    out = fetch_events_cached_pack()
events = out.get("events", [])
health = out.get("health", {})
fetched_at = out.get("fetched_at")

with st.sidebar:
    with st.expander("Filters", expanded=True):
        groups = {"University", "Community"}
        chosen_groups = st.multiselect("Source groups", options=sorted(groups), default=sorted(groups))
        show_sources = st.toggle("Show sources panel", value=False)
        source_filter_selected = None
        if show_sources:
            src_defs = load_sources()
            counts = Counter([e.get("source") for e in events if e.get("source")])
            with st.expander("Sources health", expanded=True):
                for s in src_defs:
                    name, url, typ, grp = s.get("name"), s.get("url"), s.get("type",""), s.get("group","")
                    c = counts.get(name, 0)
                    status = health.get("per_source",{}).get(name,{})
                    ok = status.get("ok", True)
                    icon = "✅" if ok else "⚠️"
                    st.markdown(f"- {icon} [{name}]({url}) — `{typ}` — **{c}** events — _{grp}_")
            opts = sorted([k for k,v in counts.items() if v>0] or [s.get("name") for s in src_defs])
            source_filter_selected = st.multiselect("Filter by source(s)", options=opts, default=opts)
        today = datetime.now(tz.tzlocal()).date()
        date_min = st.date_input("From date", today)
        date_max = st.date_input("To date", today + timedelta(days=21))
        if st.button("🔄 Refresh events"):
            fetch_events_cached_pack.clear()
            st.experimental_rerun()

def _within(ev):
    if not ev.get("start_iso"): return False
    d = dtp.parse(ev["start_iso"]).date()
    return date_min <= d <= date_max

events3 = window(events, days=120)
sel = [e for e in events3 if _within(e) and (e.get("group") in chosen_groups if e.get("group") else True)]
if source_filter_selected:
    sel = [e for e in sel if (e.get("source") in source_filter_selected)]

def norm_title(s:str)->str:
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\b\d{1,2}:\d{2}\s*(am|pm)\b","", s)
    s = re.sub(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?\s*\d{1,2}\b","", s)
    return s.strip()

series = defaultdict(list)
for e in sel:
    key = (norm_title(e.get("title","")), (e.get("location") or "").lower())
    series[key].append(e)

collapsed = []
for key, items in series.items():
    items = sorted(items, key=lambda x: x.get("start_iso"))
    collapsed.append(items[0])  # keep simple collapse for patch

PAGE_SIZE = 50
page = st.session_state.get("page", 1)
total = len(collapsed)
end_idx = min(page*PAGE_SIZE, total)
view = collapsed[:end_idx]

st.caption(f"Last updated: {fetched_at}")
st.markdown("### Upcoming events")
st.caption(f"Showing {len(view)} of {total} events")

for i, ev in enumerate(view):
    event_card(ev, i)
    colA, colB, colC = st.columns([1,1,5])
    start_iso = ev.get("start_iso"); end_iso = ev.get("end_iso") or start_iso
    title = ev.get("title"); details = (ev.get("description") or "")[:333]; loc = ev.get("location") or ""
    if start_iso:
        g_url = google_link(title, start_iso, end_iso, details, loc)
        with colA:
            if g_url:
                st.link_button("Add to Google Calendar", g_url, use_container_width=True, key=unique_key("gcal", title or "", start_iso or "", str(i)))
        ics_payload = build_ics(title, start_iso, end_iso, details, loc)
        with colB:
            if ics_payload:
                st.download_button("Download .ics (Apple/Outlook)",
                                   data=ics_payload.encode("utf-8"),
                                   file_name=f"{title}.ics",
                                   mime="text/calendar",
                                   use_container_width=True,
                                   key=unique_key("ics", title or "", start_iso or "", str(i)))

if end_idx < total:
    if st.button("Load more", use_container_width=True):
        st.session_state["page"] = page + 1
        st.experimental_rerun()

with st.expander("Map of known venues", expanded=False):
    import folium
    venues = pd.DataFrame([{"name":"Vaught-Hemingway Stadium","lat":34.36157,"lon":-89.53663}])
    m = folium.Map(location=[34.366, -89.519], zoom_start=13, control_scale=True, zoom_control=True, prefer_canvas=True)
    m.options['scrollWheelZoom'] = False
    m.options['tap'] = False
    for _, row in venues.iterrows():
        folium.Marker([row["lat"], row["lon"]], popup=row["name"]).add_to(m)
    from streamlit.components.v1 import html as html_component
    html_component(m._repr_html_(), height=420)
