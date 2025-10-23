from __future__ import annotations
import requests
import feedparser
from bs4 import BeautifulSoup
from icalendar import Calendar
from dateutil import parser as dtp

USER_AGENT = "OxfordEvents/1.0 (+https://github.com/your-username/OxfordEvents)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "*/*"}

def fetch(url: str, timeout: int = 20) -> bytes:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.content

def get_soup(url: str) -> BeautifulSoup:
    html = fetch(url)
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
    cal = Calendar.from_ical(data)
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