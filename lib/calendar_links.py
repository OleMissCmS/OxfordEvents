from __future__ import annotations
from urllib.parse import urlencode
from dateutil import parser as dtp

def _fmt(iso: str) -> str:
    dt = dtp.parse(iso); return dt.strftime("%Y%m%dT%H%M%S")

def google_link(title, start_iso, end_iso, details, location):
    return "https://calendar.google.com/calendar/render?" + urlencode({"action":"TEMPLATE","text":title or "Event","dates":f"{_fmt(start_iso)}/{_fmt(end_iso or start_iso)}","details":details or "","location":location or ""})

def build_ics(title, start_iso, end_iso, details, location):
    s = dtp.parse(start_iso).strftime("%Y%m%dT%H%M%S"); e = dtp.parse(end_iso or start_iso).strftime("%Y%m%dT%H%M%S")
    return "\r\n".join(["BEGIN:VCALENDAR","VERSION:2.0","BEGIN:VEVENT",f"SUMMARY:{title}",f"DTSTART:{s}",f"DTEND:{e}",f"LOCATION:{location or ''}",f"DESCRIPTION:{details or ''}","END:VEVENT","END:VCALENDAR",""])