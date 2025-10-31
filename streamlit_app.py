import streamlit as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
from dateutil import parser as dtp, tz
from components.blocks import hero, event_card, unique_key
from lib.aggregator import collect_with_progress, window, load_sources
from lib.calendar_links import google_link, build_ics
import re
import urllib.parse
import csv
import io
import plotly.express as px
import plotly.graph_objects as go

VERSION = "v5.0.0"

st.set_page_config(page_title="Upcoming in Oxford", page_icon="📅", layout="wide", initial_sidebar_state="expanded")
hero("What's happening, Oxford?")

# Source verification function
def verify_all_sources_processed():
    """Verify that all sources from YAML are being processed"""
    sources = load_sources()
    return len(sources), [s.get("name") for s in sources]

# Load events with caching
@st.cache_data(ttl=7200, show_spinner=False)
def fetch_events_cached_pack():
    events, health = collect_with_progress(None)
    return {"events": events, "health": health, "fetched_at": datetime.now(tz.tzlocal()).isoformat()}

with st.spinner("Loading events…"):
    out = fetch_events_cached_pack()
events = out.get("events", [])
health = out.get("health", {})
fetched_at = out.get("fetched_at")

# Verify all sources are being processed
total_sources, source_names = verify_all_sources_processed()
processed_sources = list(health.get("per_source", {}).keys())
missing_sources = [s for s in source_names if s not in processed_sources]
if missing_sources:
    st.warning(f"⚠️ Some sources may not be loading: {', '.join(missing_sources)}")

# Read URL parameters early (before filters are set)
today = datetime.now(tz.tzlocal()).date()
groups = {"University", "Community"}
events3 = window(events, days=180)
all_categories = sorted({(e.get("category") or "Uncategorized") for e in events3})

try:
    query_params = st.query_params
    url_params_loaded = st.session_state.get("url_params_loaded", False)
    if not url_params_loaded and query_params:
        if "categories" in query_params and query_params["categories"]:
            cats = query_params["categories"].split(",")
            valid_cats = [c for c in cats if c in all_categories]
            if valid_cats:
                st.session_state["categories_selected"] = valid_cats
        if "groups" in query_params and query_params["groups"]:
            grps = query_params["groups"].split(",")
            valid_grps = [g for g in grps if g in groups]
            if valid_grps:
                st.session_state["groups_selected"] = valid_grps
        if "date_min" in query_params:
            try:
                st.session_state["date_min"] = dtp.parse(query_params["date_min"]).date()
            except:
                pass
        if "date_max" in query_params:
            try:
                st.session_state["date_max"] = dtp.parse(query_params["date_max"]).date()
            except:
                pass
        if "q" in query_params:
            st.session_state["q"] = query_params["q"]
        st.session_state["url_params_loaded"] = True
except:
    pass

# Helper functions
def set_quick_date_filter(days_offset=0, days_span=1):
    """Set date filter to a quick range"""
    today = date.today()
    start = today + timedelta(days=days_offset)
    end = start + timedelta(days=days_span - 1)
    st.session_state["date_min"] = start
    st.session_state["date_max"] = end
    st.rerun()

def set_weekend(offset_weeks: int = 0):
    today = date.today()
    friday = today + timedelta(days=(4 - today.weekday()) % 7 + 7*offset_weeks)
    sunday = friday + timedelta(days=2)
    st.session_state["date_min"] = friday
    st.session_state["date_max"] = sunday

# Sidebar with enhanced filters
with st.sidebar:
    with st.expander("Filters", expanded=True):
        groups_selected = st.multiselect("Source groups", options=sorted(groups), 
                       default=st.session_state.get("groups_selected", sorted(groups)),
                       help="Quick filter by source grouping.", key="groups_selected")
        
        # Quick date filter buttons
        st.markdown("**Quick date filters**")
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        with col1:
            if st.button("📅 Today", use_container_width=True, help="Show events today"):
                set_quick_date_filter(0, 1)
        with col2:
            if st.button("📆 This Week", use_container_width=True, help="Show events this week"):
                set_quick_date_filter(0, 7)
        with col3:
            if st.button("🗓️ This Month", use_container_width=True, help="Show events this month"):
                set_quick_date_filter(0, 30)
        with col4:
            if st.button("⏭️ Next 7 Days", use_container_width=True, help="Show next 7 days"):
                set_quick_date_filter(0, 7)

        st.session_state.setdefault("date_min", today)
        st.session_state.setdefault("date_max", today + timedelta(days=21))
        st.date_input("From date", st.session_state["date_min"], key="date_min")
        st.date_input("To date", st.session_state["date_max"], key="date_max")

        # Weekend buttons
        c1, c2, c3 = st.columns(3)
        with c1: 
            st.button("This weekend", on_click=set_weekend, kwargs={"offset_weeks": 0}, use_container_width=True)
        with c2: 
            st.button("Next weekend", on_click=set_weekend, kwargs={"offset_weeks": 1}, use_container_width=True)
        with c3:
            def _clear():
                st.session_state["date_min"] = today
                st.session_state["date_max"] = today + timedelta(days=21)
            st.button("Clear", on_click=_clear, use_container_width=True)

        st.checkbox("Show sources panel", value=False, key="show_sources_panel")

        st.markdown("---")
        st.markdown("**Suggest a new source**")
        sug_url = st.text_input("Source URL", key="suggest_url", placeholder="https://…")
        sug_type = st.selectbox("Type", ["rss","ics","html","api"], key="suggest_type")
        sug_group = st.selectbox("Group", ["Community","University"], key="suggest_group")
        sug_notes = st.text_area("Notes (optional)", key="suggest_notes", height=60)
        yaml_snippet = f"""- name: Your Source Name
  type: {sug_type}
  url: {sug_url or 'https://example.com'}
  parser: simple_list
  group: {sug_group}
  # notes: {sug_notes or ''}
"""
        st.download_button("Download YAML entry", data=yaml_snippet.encode("utf-8"),
                           file_name="source_suggestion.yml", use_container_width=True)

# Sources panel
if st.session_state.get("show_sources_panel"):
    with st.sidebar.expander("Sources & diagnostics", expanded=True):
        src_defs = load_sources()
        counts = Counter([e.get("source") for e in events if e.get("source")])
        
        # Show source verification
        st.markdown(f"**Total sources configured:** {len(src_defs)}")
        st.markdown(f"**Sources processed:** {len(processed_sources)}")
        
        for s in src_defs:
            name, url, typ, grp = s.get("name"), s.get("url"), s.get("type",""), s.get("group","")
            c = counts.get(name, 0)
            status = health.get("per_source",{}).get(name,{})
            ok = status.get("ok", True)
            icon = "✅" if ok else "⚠️"
            error_msg = status.get("error", "")
            error_text = f" — {error_msg[:50]}…" if error_msg else ""
            st.markdown(f"- {icon} [{name}]({url}) — `{typ}` — **{c}** events — _{grp}_{error_text}")

# Filter events
def _within(ev):
    if not ev.get("start_iso"): return False
    try:
        d = dtp.parse(ev["start_iso"]).date()
    except Exception:
        return False
    return st.session_state["date_min"] <= d <= st.session_state["date_max"]

if "categories_selected" not in st.session_state:
    st.session_state["categories_selected"] = all_categories

sel0 = [e for e in events3 if _within(e) and (e.get("group") in st.session_state["groups_selected"] if e.get("group") else True)]

# Source filter
if st.session_state.get("show_sources_panel"):
    srcs = sorted({e.get("source") for e in events3 if e.get("source")})
    source_counts = Counter([e.get("source") for e in sel0 if e.get("source")])
    srcs_with_counts = [f"{s} ({source_counts.get(s, 0)})" for s in srcs]
    selected_srcs_display = st.sidebar.multiselect("Filter by source(s)", options=srcs_with_counts, default=srcs_with_counts, key="sources_selected_display")
    # Parse back source names from display format
    selected_srcs = [s.split(" (")[0] for s in selected_srcs_display]
    st.session_state["sources_selected"] = selected_srcs

if st.session_state.get("sources_selected"):
    sel0 = [e for e in sel0 if (e.get("source") in st.session_state["sources_selected"])]

# Category filter with counts
category_counts = Counter([(e.get("category") or "Uncategorized") for e in sel0])
categories_with_counts = [f"{cat} ({category_counts.get(cat, 0)})" for cat in all_categories]
selected_cats_display = st.sidebar.multiselect("Categories", options=categories_with_counts,
                   default=[f"{cat} ({category_counts.get(cat, 0)})" for cat in st.session_state["categories_selected"]],
                   key="categories_selected_display")
# Parse back category names
selected_cats = [cat.split(" (")[0] for cat in selected_cats_display]
st.session_state["categories_selected"] = selected_cats

# Quick category filter chips
st.markdown("#### Quick filters")
import math
chip_cols = st.columns(min(len(all_categories), 6) or 1)
for idx, cat in enumerate(all_categories):
    count = category_counts.get(cat, 0)
    label = f"{cat} ({count})"
    col = chip_cols[idx % len(chip_cols)]
    with col:
        if st.button(label, key=f"chip_{idx}", use_container_width=True):
            cur = set(st.session_state["categories_selected"])
            if cat in cur: 
                cur.remove(cat)
            else: 
                cur.add(cat)
            st.session_state["categories_selected"] = sorted(cur)
            st.rerun()

sel1 = [e for e in sel0 if ((e.get("category") or "Uncategorized") in st.session_state["categories_selected"])]

# Search
q = st.text_input("🔍 Search titles & descriptions", value=st.session_state.get("q",""), key="q", placeholder="e.g., music, parade, lecture, 'Proud Larry'")
def _match(ev, q):
    if not q: return True
    hay = f"{ev.get('title','')} {ev.get('description','')}"
    return all(t.lower() in hay.lower() for t in q.split())
sel = [e for e in sel1 if _match(e, q)]

# Deduplicate similar events
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

# Statistics Dashboard
with st.expander("📊 Event Statistics", expanded=False):
    col1, col2, col3, col4 = st.columns(4)
    
    total_filtered = len(sel)
    today_events = len([e for e in sel if e.get("start_iso") and dtp.parse(e["start_iso"]).date() == date.today()])
    free_events = len([e for e in sel if "free" in (e.get("cost") or "").lower() or (e.get("cost") or "").strip() == ""])
    
    top_category_data = Counter([e.get("category") or "Uncategorized" for e in sel])
    top_category = top_category_data.most_common(1)[0][0] if top_category_data else "N/A"
    
    with col1:
        st.metric("Total Events", total_filtered)
    with col2:
        st.metric("Today", today_events)
    with col3:
        st.metric("Free Events", free_events)
    with col4:
        st.metric("Top Category", top_category)
    
    # Charts
    if sel:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Category distribution
            cat_counts_dict = dict(top_category_data)
            if cat_counts_dict:
                fig_pie = px.pie(
                    values=list(cat_counts_dict.values()), 
                    names=list(cat_counts_dict.keys()), 
                    title="Events by Category"
                )
                fig_pie.update_layout(showlegend=True, height=300)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with chart_col2:
            # Events by day
            day_counts = Counter()
            for e in sel:
                if e.get("start_iso"):
                    try:
                        day = dtp.parse(e["start_iso"]).date()
                        day_counts[day] += 1
                    except:
                        pass
            
            if day_counts:
                sorted_days = sorted(day_counts.items())[:14]  # Next 14 days
                dates = [str(d[0]) for d in sorted_days]
                counts = [d[1] for d in sorted_days]
                
                fig_bar = px.bar(
                    x=dates, 
                    y=counts, 
                    title="Events by Day (Next 2 Weeks)",
                    labels={"x": "Date", "y": "Event Count"}
                )
                fig_bar.update_layout(height=300, xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)

# Export functionality
def export_all_events_ics(events_list):
    """Export all filtered events as .ics file"""
    ics_lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//OxfordEvents//EN"]
    
    for ev in events_list:
        title = (ev.get("title") or "Event").replace("\n", " ").replace("\r", "")
        start_iso = ev.get("start_iso")
        end_iso = ev.get("end_iso") or start_iso
        location = (ev.get("location") or "").replace("\n", " ").replace("\r", "")
        description = (ev.get("description") or "").replace("\n", " ").replace("\r", "")[:500]
        link = ev.get("link") or ""
        
        if start_iso:
            try:
                start_dt = dtp.parse(start_iso)
                end_dt = dtp.parse(end_iso) if end_iso else start_dt
                start_str = start_dt.strftime("%Y%m%dT%H%M%S")
                end_str = end_dt.strftime("%Y%m%dT%H%M%S")
                
                ics_lines.append("BEGIN:VEVENT")
                ics_lines.append(f"SUMMARY:{title}")
                ics_lines.append(f"DTSTART;TZID=America/Chicago:{start_str}")
                ics_lines.append(f"DTEND;TZID=America/Chicago:{end_str}")
                if location:
                    ics_lines.append(f"LOCATION:{location}")
                if description:
                    ics_lines.append(f"DESCRIPTION:{description}")
                if link:
                    ics_lines.append(f"URL:{link}")
                ics_lines.append("END:VEVENT")
            except:
                pass
    
    ics_lines.append("END:VCALENDAR")
    return "\r\n".join(ics_lines)

def export_all_events_csv(events_list):
    """Export all filtered events as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Title", "Date", "Time", "Location", "Cost", "Category", "Source", "Description", "Link"])
    
    for ev in events_list:
        title = ev.get("title", "")
        start_iso = ev.get("start_iso", "")
        location = ev.get("location", "")
        cost = ev.get("cost", "")
        category = ev.get("category", "")
        source = ev.get("source", "")
        description = (ev.get("description") or "").replace("\n", " ")[:200]
        link = ev.get("link", "")
        
        date_str = ""
        time_str = ""
        if start_iso:
            try:
                dt = dtp.parse(start_iso)
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%I:%M %p")
            except:
                date_str = start_iso
        
        writer.writerow([title, date_str, time_str, location, cost, category, source, description, link])
    
    return output.getvalue()

# Pagination
PAGE_SIZE = 50
page = st.session_state.get("page", 1)
total = len(collapsed)
end_idx = min(page*PAGE_SIZE, total)
view = collapsed[:end_idx]

# Main content area
st.caption(f"Last updated: {fetched_at} | Total sources: {total_sources}")

# Export and share buttons
export_col1, export_col2, export_col3 = st.columns([1, 1, 2])
with export_col1:
    if st.button("📥 Export All (.ics)", use_container_width=True, help="Download all filtered events as calendar file"):
        ics_data = export_all_events_ics(sel)
        st.download_button(
            "Download .ics File",
            data=ics_data.encode("utf-8"),
            file_name=f"oxford_events_{date.today().strftime('%Y%m%d')}.ics",
            mime="text/calendar",
            use_container_width=True
        )
with export_col2:
    if st.button("📊 Export CSV", use_container_width=True, help="Download all filtered events as spreadsheet"):
        csv_data = export_all_events_csv(sel)
        st.download_button(
            "Download CSV File",
            data=csv_data,
            file_name=f"oxford_events_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# Shareable URL
params = {
    "categories": ",".join(st.session_state.get("categories_selected", [])),
    "groups": ",".join(st.session_state.get("groups_selected", [])),
    "date_min": str(st.session_state.get("date_min", today)),
    "date_max": str(st.session_state.get("date_max", today + timedelta(days=21))),
    "q": st.session_state.get("q", "")
}
share_url = f"https://oxfordevents.streamlit.app?{urllib.parse.urlencode(params)}"
with export_col3:
    if st.button("🔗 Copy Shareable Link", use_container_width=True, help="Copy link with current filters"):
        st.code(share_url, language=None)
        st.success("Link copied! Share this URL to preserve your filter settings.")

st.markdown("### Upcoming events")
st.caption(f"Showing {len(view)} of {total} events")

# Empty state
if len(sel) == 0:
    st.info("🎭 No events match your filters. Try:")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- Adjusting date range")
        st.markdown("- Clearing category filters")
        st.markdown("- Checking different source groups")
    with col2:
        st.markdown("- Removing search terms")
        st.markdown("- Showing more sources")
    if st.button("🔄 Reset All Filters", use_container_width=True):
        st.session_state["categories_selected"] = all_categories
        st.session_state["groups_selected"] = sorted(groups)
        st.session_state["date_min"] = today
        st.session_state["date_max"] = today + timedelta(days=21)
        st.session_state["q"] = ""
        st.session_state["sources_selected"] = []
        st.session_state["page"] = 1
        st.rerun()

# Social sharing helper
def render_share_buttons(ev: dict):
    """Render social sharing buttons for an event"""
    title = (ev.get("title") or "Event").strip()
    link = ev.get("link") or "https://oxfordevents.streamlit.app"
    encoded_title = urllib.parse.quote(title)
    encoded_link = urllib.parse.quote(link)
    
    twitter_url = f"https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_link}"
    facebook_url = f"https://www.facebook.com/sharer/sharer.php?u={encoded_link}"
    
    share_col1, share_col2, share_col3 = st.columns(3)
    with share_col1:
        st.link_button("🐦 Twitter", twitter_url, use_container_width=True)
    with share_col2:
        st.link_button("📘 Facebook", facebook_url, use_container_width=True)
    with share_col3:
        if st.button("📋 Copy Link", key=f"copy_{ev.get('title', '')}_{ev.get('start_iso', '')}", use_container_width=True):
            st.success("Link copied!")

# Calendar buttons with enhanced functionality
def render_calendar_buttons(ev: dict, idx: int):
    start_iso = ev.get("start_iso")
    end_iso = ev.get("end_iso") or start_iso
    title = (ev.get("title") or "Event").strip()
    details = (ev.get("description") or "")[:333]
    loc = (ev.get("location") or "").strip()
    if not start_iso:
        return
    g_url = google_link(title, start_iso, end_iso, details, loc)
    ics_payload = build_ics(title, start_iso, end_iso, details, loc)

    colA, colB, colC = st.columns([1,1,1])
    with colA:
        if isinstance(g_url, str) and g_url.startswith("http"):
            st.link_button("📅 Google Calendar", g_url, use_container_width=True)
        else:
            st.caption("Calendar link unavailable.")
    with colB:
        if isinstance(ics_payload, str) and len(ics_payload) > 0:
            safe = re.sub(r'[^A-Za-z0-9 _.-]+','',title)
            st.download_button("📥 Download .ics",
                               data=ics_payload.encode("utf-8"),
                               file_name=f"{safe}.ics",
                               mime="text/calendar",
                               use_container_width=True,
                               key=unique_key("ics", title, start_iso or "", str(idx)))
        else:
            st.caption("ICS unavailable.")
    with colC:
        render_share_buttons(ev)

# Venue click-to-filter helper
def filter_by_venue(venue_name):
    """Filter events by venue when venue is clicked"""
    st.session_state["venue_filter"] = venue_name.lower()
    st.rerun()

# Apply venue filter before rendering
venue_filter = st.session_state.get("venue_filter")
if venue_filter:
    view = [e for e in view if venue_filter.lower() in (e.get("location") or "").lower()]
    if st.button("❌ Clear venue filter", use_container_width=True):
        del st.session_state["venue_filter"]
        st.rerun()

# Render events
for i, ev in enumerate(view):
    event_card(ev, i)
    
    render_calendar_buttons(ev, i)
    
    # Venue filter button
    venue = ev.get("location", "")
    if venue:
        if st.button(f"📍 Filter by venue: {venue}", key=f"venue_{i}", use_container_width=True):
            st.session_state["venue_filter"] = venue.lower()
            st.rerun()
    
    st.markdown("---")

if end_idx < total:
    if st.button("Load more", use_container_width=True):
        st.session_state["page"] = page + 1
        st.rerun()

# Enhanced map
with st.expander("🗺️ Map of filtered events", expanded=False):
    import folium
    from folium.plugins import MarkerCluster
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
                title = e.get("title", "Event")
                link = e.get("link", "")
                when = ""
                try:
                    if e.get("start_iso"):
                        when = dtp.parse(e["start_iso"]).strftime("%a %b %d, %I:%M %p")
                except:
                    pass
                popup_html = f'<b>{title}</b><br>{when}<br>{loc}<br><a href="{link}" target="_blank">More info</a>'
                pts.append((lat,lon,title,popup_html))
                break
    center = [34.366, -89.519]
    if pts:
        lats = [p[0] for p in pts]; lons=[p[1] for p in pts]
        center = [sum(lats)/len(lats), sum(lons)/len(lons)]
    m = folium.Map(location=center, zoom_start=13, control_scale=True, zoom_control=True, prefer_canvas=True)
    m.options['scrollWheelZoom'] = False
    m.options['tap'] = False
    cluster = MarkerCluster().add_to(m)
    for lat,lon,title,popup_html in pts[:200]:
        folium.Marker([lat,lon], popup=folium.Popup(popup_html, max_width=300), tooltip=title).add_to(cluster)
    from streamlit.components.v1 import html as html_component
    html_component(m._repr_html_(), height=420)
