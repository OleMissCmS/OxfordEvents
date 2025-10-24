import streamlit as st
import pandas as pd
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from dateutil import parser as dtp, tz
from components.blocks import hero, event_card, unique_key
from lib.aggregator import collect_with_progress, window, load_sources
from lib.calendar_links import google_link, build_ics
import re

VERSION = "v4.8.3"

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
        chosen_groups = st.multiselect("Source groups", options=sorted(groups), default=sorted(groups), help="Quick filter by source grouping.")
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
        if st.button("🔄 Refresh events", help="Clear cache and re-collect"):
            fetch_events_cached_pack.clear()
            st.experimental_rerun()

def _within(ev):
    if not ev.get("start_iso"): return False
    try:
        d = dtp.parse(ev["start_iso"]).date()
    except Exception:
        return False
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
    items = sorted(items, key=lambda x: x.get("start_iso") or "")
    rep = max(items, key=lambda x: len(x.get("title") or ""))
    collapsed.append(rep)

PAGE_SIZE = 50
page = st.session_state.get("page", 1)
total = len(collapsed)
end_idx = min(page*PAGE_SIZE, total)
view = collapsed[:end_idx]

st.caption(f"Last updated: {fetched_at}")
st.markdown("### Upcoming events")
st.caption(f"Showing {len(view)} of {total} events")

def render_calendar_buttons(ev: dict, idx: int):
    start_iso = ev.get("start_iso")
    end_iso = ev.get("end_iso") or start_iso
    title = (ev.get("title") or "Event").strip()
    details = (ev.get("description") or "")[:333]
    loc = (ev.get("location") or "").strip()
    if not start_iso:
        return
    g_url = None
    ics_payload = None
    try: g_url = google_link(title, start_iso, end_iso, details, loc)
    except Exception: g_url = None
    try: ics_payload = build_ics(title, start_iso, end_iso, details, loc)
    except Exception: ics_payload = None

    colA, colB, _ = st.columns([1,1,5])
    with colA:
        if isinstance(g_url, str) and g_url.startswith("http"):
            # link_button does NOT accept `key`; remove it to avoid TypeError
            st.link_button("Add to Google Calendar", g_url, use_container_width=True)
        else:
            st.caption("Google Calendar link unavailable.")
    with colB:
        if isinstance(ics_payload, str) and len(ics_payload) > 0:
            st.download_button("Download .ics (Apple/Outlook)",
                               data=ics_payload.encode("utf-8"),
                               file_name=f"{re.sub(r'[^A-Za-z0-9 _.-]+','',title)}.ics",
                               mime="text/calendar",
                               use_container_width=True,
                               key=unique_key("ics", title, start_iso or "", str(idx)))
        else:
            st.caption("ICS unavailable.")

for i, ev in enumerate(view):
    event_card(ev, i)
    render_calendar_buttons(ev, i)

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
