import streamlit as st
import pandas as pd
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from dateutil import parser as dtp, tz
from components.blocks import hero, event_card, unique_key
from lib.aggregator import collect_with_progress, window, load_sources
from lib.calendar_links import google_link, build_ics
import re

VERSION = "v4.9.0"

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

# Sidebar Filters
with st.sidebar:
    with st.expander("Filters", expanded=True):
        groups = {"University", "Community"}
        chosen_groups = st.multiselect("Source groups", options=sorted(groups), default=sorted(groups), help="Quick filter by source grouping.", key="groups_selected")
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
            source_filter_selected = st.multiselect("Filter by source(s)", options=opts, default=opts, key="sources_selected")
        today = datetime.now(tz.tzlocal()).date()
        if "date_min" not in st.session_state: st.session_state["date_min"] = today
        if "date_max" not in st.session_state: st.session_state["date_max"] = today + timedelta(days=21)
        date_min = st.date_input("From date", st.session_state["date_min"], key="date_min")
        date_max = st.date_input("To date", st.session_state["date_max"], key="date_max")
        colW1, colW2, colW3 = st.columns(3)
        with colW1:
            if st.button("This weekend"):
                now = datetime.now(tz.tzlocal()).date()
                friday = now + timedelta(days=(4 - now.weekday()) % 7)
                sunday = friday + timedelta(days=2)
                st.session_state["date_min"] = friday
                st.session_state["date_max"] = sunday
                st.experimental_rerun()
        with colW2:
            if st.button("Next weekend"):
                now = datetime.now(tz.tzlocal()).date()
                friday = now + timedelta(days=(4 - now.weekday()) % 7 + 7)
                sunday = friday + timedelta(days=2)
                st.session_state["date_min"] = friday
                st.session_state["date_max"] = sunday
                st.experimental_rerun()
        with colW3:
            if st.button("Clear"):
                st.session_state["date_min"] = today
                st.session_state["date_max"] = today + timedelta(days=21)
                st.experimental_rerun()
        if st.button("🔄 Refresh events", help="Clear cache and re-collect"):
            fetch_events_cached_pack.clear()
            st.experimental_rerun()

def _within(ev):
    if not ev.get("start_iso"): return False
    try:
        d = dtp.parse(ev["start_iso"]).date()
    except Exception:
        return False
    return st.session_state["date_min"] <= d <= st.session_state["date_max"]

events3 = window(events, days=180)
sel0 = [e for e in events3 if _within(e) and (e.get("group") in st.session_state["groups_selected"] if e.get("group") else True)]
if st.session_state.get("sources_selected"):
    sel0 = [e for e in sel0 if (e.get("source") in st.session_state["sources_selected"])]

categories_all = sorted({(e.get("category") or "Uncategorized") for e in sel0} - {None}) or ["Uncategorized"]
if "categories_selected" not in st.session_state: st.session_state["categories_selected"] = categories_all

st.markdown("#### Quick filters")
chip_cols = st.columns(min(len(categories_all), 6) or 1)
for idx, cat in enumerate(categories_all):
    count = sum(1 for e in sel0 if (e.get("category") or "Uncategorized")==cat)
    label = f"{cat} ({count})"
    col = chip_cols[idx % len(chip_cols)]
    with col:
        if st.button(label, key=f"chip_{idx}"):
            sel = set(st.session_state["categories_selected"])
            if cat in sel: sel.remove(cat)
            else: sel.add(cat)
            st.session_state["categories_selected"] = sorted(sel)
            st.experimental_rerun()

sel1 = [e for e in sel0 if ((e.get("category") or "Uncategorized") in st.session_state["categories_selected"])]

q = st.text_input("Search titles & descriptions", value=st.session_state.get("q",""), key="q", placeholder="e.g., music, parade, lecture, 'Proud Larry'")
def _match(ev, q):
    if not q: return True
    hay = f"{ev.get('title','')} {ev.get('description','')}"
    for token in q.split():
        if token.lower() not in hay.lower(): return False
    return True
sel = [e for e in sel1 if _match(e, q)]

def norm_title(s:str)->str:
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\b\d{1,2}:\d{2}\s*(am|pm)\b","", s)
    s = re.sub(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\.?\s*\d{1,2}\b","", s)
    return s.strip()

from collections import defaultdict
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

with st.expander("Map of filtered events", expanded=False):
    import folium
    from folium.plugins import MarkerCluster
    import csv
    venue_map = {}
    try:
        with open("data/venues.csv","r",encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    venue_map[row["name"].lower()] = (float(row.get("lat")), float(row.get("lon")))
                except Exception:
                    pass
    except Exception:
        pass
    pts = []
    for e in sel:
        loc = (e.get("location") or "").lower()
        for name,(lat,lon) in venue_map.items():
            if name in loc:
                pts.append((lat,lon,e.get("title")))
                break
    center = [34.366, -89.519]
    if pts:
        lats = [p[0] for p in pts]; lons=[p[1] for p in pts]
        center = [sum(lats)/len(lats), sum(lons)/len(lons)]
    m = folium.Map(location=center, zoom_start=13, control_scale=True, zoom_control=True, prefer_canvas=True)
    m.options['scrollWheelZoom'] = False
    m.options['tap'] = False
    cluster = MarkerCluster().add_to(m)
    for lat,lon,title in pts[:200]:
        folium.Marker([lat,lon], popup=title).add_to(cluster)
    from streamlit.components.v1 import html as html_component
    html_component(m._repr_html_(), height=420)
