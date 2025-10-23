from __future__ import annotations
import requests, feedparser
from bs4 import BeautifulSoup
from icalendar import Calendar
from dateutil import parser as dtp

HEADERS = {"User-Agent":"OxfordEvents/1.0","Accept":"*/*"}

def fetch(url: str, timeout: int = 20) -> bytes:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.content

def get_soup(url: str) -> BeautifulSoup:
    return BeautifulSoup(fetch(url), "lxml")

def parse_rss(url: str):
    fp = feedparser.parse(url)
    items=[]
    for e in fp.entries:
        items.append({"title":e.get("title","").strip(),"link":e.get("link"),"description":(e.get("summary") or e.get("description") or "").strip(),"start": e.get("published")})
    return items

def parse_ics(url: str):
    data = fetch(url); cal = Calendar.from_ical(data); out=[]
    for comp in cal.walk():
        if comp.name=="VEVENT":
            out.append({"title":str(comp.get("summary","")), "description":str(comp.get("description","")), "link":str(comp.get("url","")) or None, "location":str(comp.get("location","")) or None, "start": comp.get("dtstart").dt if comp.get("dtstart") else None, "end": comp.get("dtend").dt if comp.get("dtend") else None})
    return out