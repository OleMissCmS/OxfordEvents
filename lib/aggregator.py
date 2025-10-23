from __future__ import annotations
from typing import List, Dict, Any, Callable, Optional
import yaml
from datetime import datetime, timedelta
from dateutil import tz
from .data_io import parse_rss, parse_ics
from .parsers import (
    visit_oxford, chambermaster, simple_list, lyric, proud_larrys, square_books, thacker,
    yac_powerhouse, oxcm, ford_center, alumni, athletics, engage_campus, city_meetings, occ_lite, library_portal,
    eventbrite_oxford, social_stub
)
from .normalize import Event, infer_category, to_iso, strip_html
from .dedupe import dedupe

PARSER_MAP = {
    "visit_oxford": visit_oxford,
    "chambermaster": chambermaster,
    "simple_list": simple_list,
    "lyric": lyric,
    "proud_larrys": proud_larrys,
    "square_books": square_books,
    "thacker": thacker,
    "yac_powerhouse": yac_powerhouse,
    "oxcm": oxcm,
    "ford_center": ford_center,
    "alumni": alumni,
    "athletics": athletics,
    "engage_campus": engage_campus,
    "city_meetings": city_meetings,
    "occ_lite": occ_lite,
    "library_portal": library_portal,
    "eventbrite_oxford": eventbrite_oxford,
    "social_stub": social_stub,
}

def load_sources(path: str = "data/sources.yaml") -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def normalize_records(records: List[Dict[str, Any]], source_name: str) -> List[Dict[str, Any]]:
    out = []
    for r in records:
        title = r.get("title") or "Untitled"
        start = r.get("start")
        end = r.get("end")
        loc = r.get("location")
        link = r.get("link")
        desc_raw = r.get("description")
        desc = strip_html(desc_raw)
        cost = r.get("cost")
        cat = r.get("category") or infer_category(title, desc)
        ev = Event(
            title=title,
            start_iso=to_iso(start),
            end_iso=to_iso(end) if end else to_iso(start),
            location=loc,
            cost=cost,
            link=link,
            source=source_name,
            category=cat,
            description=desc
        )
        out.append(ev.to_dict())
    return out

def collect_with_progress(notify: Optional[Callable[[str, int, int], None]] = None) -> List[Dict[str, Any]]:
    sources = load_sources()
    all_events: List[Dict[str, Any]] = []
    total = len(sources)
    for i, s in enumerate(sources, start=1):
        name = s["name"]; t = s["type"]; url = s["url"]
        if notify: notify(name, i, total)
        try:
            if t == "rss":
                recs = parse_rss(url)
            elif t == "ics":
                recs = parse_ics(url)
            elif t == "html":
                fn = PARSER_MAP.get(s.get("parser"))
                recs = fn(url) if fn else []
            else:
                recs = []
            all_events.extend(normalize_records(recs, source_name=name))
        except Exception as e:
            all_events.append({"title": f"[{name}] (source error)", "start_iso": None, "end_iso": None, "location": None, "cost": None, "link": url, "source": name, "category": None, "description": str(e)})
    return dedupe(all_events, threshold=88)

def collect() -> List[Dict[str, Any]]:
    # Simple wrapper for caching use (no notify callback requirement)
    return collect_with_progress(None)

def window(events: List[Dict[str, Any]], days: int = 21) -> List[Dict[str, Any]]:
    now = datetime.now(tz.tzlocal())
    end = now + timedelta(days=days)
    sel = []
    for ev in events:
        if not ev.get("start_iso"): continue
        try:
            # More tolerant: dateutil handles date-only strings too.
            dt = __import__("dateutil").parser.parse(ev["start_iso"])
            # If parse yields a date without time, assume 00:00 local to include it in the list
            if isinstance(dt, datetime):
                pass
            else:
                dt = datetime(dt.year, dt.month, dt.day, tzinfo=tz.tzlocal())
            if now <= dt <= end:
                sel.append(ev)
        except Exception:
            continue
    return sorted(sel, key=lambda e: e["start_iso"])