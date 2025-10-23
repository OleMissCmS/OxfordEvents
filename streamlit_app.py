import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser as dtp, tz
from components.blocks import hero, event_card
from lib.aggregator import collect, window
from lib.calendar_links import google_link, build_ics
import json

st.set_page_config(page_title="Upcoming in Oxford", page_icon="📅", layout="wide", initial_sidebar_state="collapsed")
hero()

st.sidebar.header("Filters")
today = datetime.now(tz.tzlocal()).date()
date_min = st.sidebar.date_input("From date", today)
date_max = st.sidebar.date_input("To date", today + timedelta(days=21))
st.sidebar.caption("Tip: open the page to refresh data.")

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_events():
    try:
        return collect()
    except Exception:
        with open("data/sample_events.json","r",encoding="utf-8") as f:
            return json.load(f)

events = _fetch_events()

# First, broaden window, then apply chosen range
events3 = window(events, days=60)
def _within(ev):
    if not ev.get("start_iso"): 
        return False
    d = dtp.parse(ev["start_iso"]).date()
    return date_min <= d <= date_max

events_sel = [e for e in events3 if _within(e)]
cats = sorted({e.get("category") or "Uncategorized" for e in events_sel})
cat_choice = st.sidebar.multiselect("Category", options=cats, default=cats)
events_sel = [e for e in events_sel if (e.get("category") or "Uncategorized") in cat_choice]

# --- Calendar view (month) ---
import plotly.graph_objects as go
from calendar import monthrange

def build_month_calendar(evts, year, month):
    from collections import defaultdict
    by_day = defaultdict(list)
    for e in evts:
        try:
            d = dtp.parse(e["start_iso"]).date()
            by_day[d].append(e)
        except Exception:
            pass

    first_wday, days_in_month = monthrange(year, month)  # Mon=0
    cells = [[None for _ in range(7)] for _ in range(6)]
    start_idx = (first_wday + 1) % 7  # convert Mon=0 to Sun=0
    r = 0; c = start_idx
    for day in range(1, days_in_month+1):
        cells[r][c] = day
        c += 1
        if c == 7:
            c = 0; r += 1

    z = [[0]*7 for _ in range(6)]
    text = [["" for _ in range(7)] for _ in range(6)]
    annotations = []
    for rr in range(6):
        for cc in range(7):
            day = cells[rr][cc]
            if day is None:
                text[rr][cc] = ""
                z[rr][cc] = None
                continue
            d = datetime(year, month, day).date()
            lst = by_day.get(d, [])
            z[rr][cc] = len(lst) if lst else 0
            titles = []
            for e in lst[:6]:
                try:
                    tstr = dtp.parse(e["start_iso"]).strftime("%I:%M %p ").lstrip("0")
                except Exception:
                    tstr = ""
                titles.append(f"{tstr}{e.get('title','')}")
            text[rr][cc] = "<br>".join(titles) if titles else "No events"
            annotations.append(dict(
                x=cc, y=rr, text=str(day), showarrow=False, xanchor="left", yanchor="top",
                xshift=5, yshift=-5, font=dict(size=12)
            ))

    fig = go.Figure(data=go.Heatmap(
        z=z, x=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"], y=[f"W{w+1}" for w in range(6)],
        text=text, hoverinfo="text", showscale=False, colorscale="Blues"
    ))
    fig.update_layout(
        title=f"{datetime(year, month, 1).strftime('%B %Y')} — events per day",
        xaxis=dict(side="top"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10,r=10,t=40,b=10),
        height=320
    )
    fig.update_layout(annotations=annotations)
    return fig

# Use selected 'From date' as the month anchor
month_anchor = date_min
cal_fig = build_month_calendar(events_sel, month_anchor.year, month_anchor.month)
st.plotly_chart(cal_fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

# --- Cards with calendar buttons ---
for ev in events_sel[:60]:
    event_card(ev)
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
        with colB:
            st.download_button("Download .ics (Apple/Outlook)", data=ics_text.encode("utf-8"),
                               file_name=f"{title}.ics", mime="text/calendar", use_container_width=True)

# --- Map ---
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