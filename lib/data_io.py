
from __future__ import annotations
import requests, feedparser
from bs4 import BeautifulSoup
from icalendar import Calendar
from dateutil import parser as dtp

UA = "Mozilla/5.0 OxfordEvents/4.6"
HEADERS = {"User-Agent": UA}

def fetch(url: str, timeout: int = 15) -> bytes:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code >= 400: return b""
        return r.content or b""
    except requests.RequestException:
        return b""

def get_soup(url: str) -> BeautifulSoup:
    html = fetch(url)
    return BeautifulSoup(html or b"<html></html>", "lxml")

def parse_rss(url: str):
    fp = feedparser.parse(url)
    items=[]
    for e in fp.entries:
        title = e.get("title","").strip()
        link = e.get("link")
        summary = (e.get("summary") or e.get("description") or "").strip()
        dt = e.get("published") or e.get("updated") or e.get("date")
        start = None
        if dt:
            try: start = dtp.parse(dt)
            except Exception: start = None
        items.append({"title": title, "link": link, "description": summary, "start": start})
    return items

def parse_ics(url: str):
    data = fetch(url)
    if not data: return []
    try: cal = Calendar.from_ical(data)
    except Exception: return []
    out=[]
    for comp in cal.walk():
        if comp.name == "VEVENT":
            out.append({
                "title": str(comp.get("summary","")),
                "description": str(comp.get("description","")),
                "link": str(comp.get("url","")) or None,
                "location": str(comp.get("location","")) or None,
                "start": comp.get("dtstart").dt if comp.get("dtstart") else None,
                "end": comp.get("dtend").dt if comp.get("dtend") else None
            })
    return out
