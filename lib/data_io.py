from __future__ import annotations
import requests
import feedparser
from bs4 import BeautifulSoup
from icalendar import Calendar
from dateutil import parser as dtp

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36 OxfordEvents/4.3"
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.7",
    "Connection": "close"
}

def fetch(url: str, timeout: int = 15) -> bytes:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code >= 400:
            return b""
        return r.content or b""
    except requests.RequestException:
        return b""

def get_soup(url: str) -> BeautifulSoup:
    html = fetch(url)
    if not html:
        return BeautifulSoup("<html></html>", "lxml")
    return BeautifulSoup(html, "lxml")

def parse_rss(url: str):
    fp = feedparser.parse(url)
    items = []
    for e in fp.entries:
        title = e.get("title", "").strip()
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
    if not data:
        return []
    try:
        cal = Calendar.from_ical(data)
    except Exception:
        return []
    out = []
    for comp in cal.walk():
        if comp.name == "VEVENT":
            title = str(comp.get("summary", ""))
            desc = str(comp.get("description", ""))
            link = str(comp.get("url", "")) or None
            loc = str(comp.get("location", "")) or None
            dtstart = comp.get("dtstart").dt if comp.get("dtstart") else None
            dtend = comp.get("dtend").dt if comp.get("dtend") else None
            out.append({"title": title, "link": link, "description": desc, "location": loc, "start": dtstart, "end": dtend})
    return out