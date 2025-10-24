from __future__ import annotations
from urllib.parse import urlencode
from typing import Optional
from dateutil import parser as dtp

CTZ = "America/Chicago"

def _fmt(iso: str) -> str:
    dt = dtp.parse(iso)
    return dt.strftime("%Y%m%dT%H%M%S")

def google_link(title: str, start_iso: str, end_iso: str | None, details: str | None, location: str | None) -> Optional[str]:
    try:
        s = _fmt(start_iso)
        e = _fmt(end_iso or start_iso)
    except Exception:
        return None
    params = {"action":"TEMPLATE","text":title or "Event","dates":f"{s}/{e}","details":details or "","location":location or "","ctz":CTZ}
    return "https://calendar.google.com/calendar/render?" + urlencode(params)

def build_ics(title: str, start_iso: str, end_iso: str | None, details: str | None, location: str | None) -> Optional[str]:
    try:
        s = dtp.parse(start_iso).strftime("%Y%m%dT%H%M%S")
        e = dtp.parse(end_iso or start_iso).strftime("%Y%m%dT%H%M%S")
    except Exception:
        return None
    return "\r\n".join(["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//OxfordEvents//EN","BEGIN:VEVENT",
                          f"SUMMARY:{title or 'Event'}",
                          f"DTSTART;TZID={CTZ}:{s}",
                          f"DTEND;TZID={CTZ}:{e}",
                          f"LOCATION:{(location or '').replace('\n',' ')}",
                          f"DESCRIPTION:{(details or '').replace('\n',' ')}",
                          "END:VEVENT","END:VCALENDAR",""])
