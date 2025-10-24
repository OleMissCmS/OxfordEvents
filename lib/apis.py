from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
from .data_io import fetch_json
from dateutil import parser as dtp

def _secret(name: str) -> Optional[str]:
    try:
        import streamlit as st
        val = st.secrets.get(name)
        if val: return str(val)
    except Exception:
        pass
    return os.environ.get(name)

def _to_iso(s: str | None) -> Optional[str]:
    if not s: return None
    try: return dtp.parse(s).isoformat()
    except Exception: return None

def seatgeek_events(city="Oxford", state="MS"):
    cid = _secret("SEATGEEK_CLIENT_ID")
    if not cid:
        return []
    url = f"https://api.seatgeek.com/2/events?venue.city={city}&venue.state={state}&per_page=50&client_id={cid}"
    data = fetch_json(url)
    if not data or "events" not in data: return []
    out=[]
    for e in data.get("events", []):
        title = e.get("title") or e.get("short_title")
        start = _to_iso(e.get("datetime_local") or e.get("datetime_utc"))
        venue = e.get("venue") or {}
        loc = ", ".join([x for x in [venue.get("name"), venue.get("address"), venue.get("extended_address")] if x])
        link = e.get("url")
        price = e.get("stats",{}).get("lowest_price")
        cost = "Free" if (price is None or price == 0) else f"From ${price}"
        out.append({
            "title": title, "start": start, "end": None, "location": loc or None,
            "link": link, "cost": cost, "description": e.get("description") or "", "category": "Music" if e.get("type")=="concert" else "Sports" if e.get("type")=="sports" else None
        })
    return out

def ticketmaster_events(city="Oxford", stateCode="MS"):
    key = _secret("TICKETMASTER_API_KEY")
    if not key:
        return []
    url = f"https://app.ticketmaster.com/discovery/v2/events.json?apikey={key}&city={city}&stateCode={stateCode}&countryCode=US&size=50"
    data = fetch_json(url)
    if not data: return []
    embed = data.get("_embedded",{})
    if "events" not in embed: return []
    out=[]
    for e in embed.get("events", []):
        name = e.get("name")
        dates = e.get("dates",{}).get("start",{})
        start = _to_iso(dates.get("dateTime") or dates.get("localDate"))
        venues = (e.get("_embedded",{}) or {}).get("venues",[{}])
        v = venues[0] if venues else {}
        loc = ", ".join([x for x in [v.get("name"), v.get("address",{}).get("line1"), v.get("city",{}).get("name")] if x])
        link = e.get("url")
        priceRanges = e.get("priceRanges",[{}])
        min_price = priceRanges[0].get("min")
        cost = "Free" if (min_price is None or min_price == 0) else f"From ${int(min_price)}"
        segs = (e.get("classifications") or [{}])
        cat = None
        if segs and segs[0].get("segment",{}).get("name"):
            seg = segs[0]["segment"]["name"].lower()
            if "music" in seg: cat="Music"
            elif "sports" in seg: cat="Sports"
            elif "arts" in seg or "theatre" in seg or "theater" in seg: cat="Performing Arts"
        out.append({"title":name,"start":start,"end":None,"location":loc or None,"link":link,"cost":cost,"description":"","category":cat})
    return out
