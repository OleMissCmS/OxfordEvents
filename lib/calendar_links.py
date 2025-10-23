from __future__ import annotations
from urllib.parse import urlencode, quote
from datetime import datetime
from dateutil import parser as dtp

def _fmt_google_dt(iso: str) -> str:
    # Google requires YYYYMMDDTHHMMSSZ or local without Z; keep naive if no tz
    dt = dtp.parse(iso)
    return dt.strftime("%Y%m%dT%H%M%S")

def google_link(title: str, start_iso: str, end_iso: str, details: str, location: str) -> str:
    params = {
        "action": "TEMPLATE",
        "text": title or "Event",
        "dates": f"{_fmt_google_dt(start_iso)}/{_fmt_google_dt(end_iso or start_iso)}",
        "details": details or "",
        "location": location or "",
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(params)

def build_ics(title: str, start_iso: str, end_iso: str, details: str, location: str) -> str:
    # Minimal ICS content
    dtstart = dtp.parse(start_iso).strftime("%Y%m%dT%H%M%S")
    dtend = dtp.parse(end_iso or start_iso).strftime("%Y%m%dT%H%M%S")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//OxfordEvents//EN",
        "BEGIN:VEVENT",
        f"SUMMARY:{title}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"LOCATION:{location or ''}",
        f"DESCRIPTION:{details or ''}",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    return "\r\n".join(lines)