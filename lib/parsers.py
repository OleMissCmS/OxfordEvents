from __future__ import annotations
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from dateutil import parser as dtp
import re
from .data_io import get_soup

def _clean(t: Optional[str]) -> Optional[str]:
    if not t: return None
    return " ".join(t.split())

def visit_oxford(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    items = []
    for card in soup.select("[class*='event'] a"):
        title = _clean(card.get_text())
        link = card.get("href")
        if title and link and "/events/" in link:
            items.append({"title": title, "link": link, "source": "Visit Oxford"})
    if not items:
        items.append({"title":"Visit Oxford events", "link": url, "source":"Visit Oxford"})
    return items

def chambermaster(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); items=[]
    for a in soup.select("a"):
        txt = _clean(a.get_text()); href=a.get("href")
        if txt and href and "event" in (href.lower() + " " + txt.lower()):
            items.append({"title": txt, "link": href, "source":"Oxford Chamber"})
    if not items: items.append({"title":"Chamber events","link":url,"source":"Oxford Chamber"})
    return items

def simple_list(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); out=[]
    for a in soup.select("a"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href and ("event" in href.lower() or "events" in href.lower()):
            out.append({"title":txt,"link":href,"source":url.split('/')[2]})
    if not out: out.append({"title":"Events listing","link":url,"source":url.split('/')[2]})
    return out

def lyric(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); out=[]
    for ev in soup.select("article, .event, .tribe-events-calendar-list__event-row"):
        a = ev.find("a")
        title = _clean(a.get_text()) if a else None
        href = a.get("href") if a else None
        meta = ev.get_text(" ", strip=True) if ev else None
        out.append({"title": title or "Lyric Event", "link": href or url, "description": meta, "source": "The Lyric Oxford"})
    if not out: out.append({"title":"Lyric calendar","link":url,"source":"The Lyric Oxford"})
    return out

def proud_larrys(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); out=[]
    for a in soup.select("a"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href and any(k in (href.lower()) for k in ["show","event","p="]):
            out.append({"title":txt,"link":href,"source":"Proud Larry's"})
    if not out: out.append({"title":"Proud Larry's — shows","link":url,"source":"Proud Larry's"})
    return out

def square_books(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); out=[]
    for ev in soup.select("div.view-content a"):
        txt=_clean(ev.get_text()); href=ev.get("href")
        if txt and href and "/event" in href:
            if not href.startswith("http"):
                href="https://squarebooks.com"+href
            out.append({"title":txt,"link":href,"source":"Square Books"})
    if not out: out.append({"title":"Square Books events","link":url,"source":"Square Books"})
    return out

def thacker(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for post in soup.select("article"):
        a=post.find("a")
        if a: out.append({"title":_clean(a.get_text()),"link":a.get("href"),"source":"Thacker Mountain Radio Hour"})
    if not out: out.append({"title":"Thacker Mountain — site","link":url,"source":"Thacker Mountain Radio Hour"})
    return out

def yac_powerhouse(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for card in soup.select("article, .product, .product-inner"):
        a = card.find("a")
        title=_clean(a.get_text()) if a else None
        href=a.get("href") if a else None
        price=None
        price_el = card.select_one(".price, .amount")
        if price_el: price=_clean(price_el.get_text())
        out.append({"title": title or "YAC Event", "link": href or url, "cost": price, "source": "YAC / Powerhouse"})
    if not out: out.append({"title":"Powerhouse events","link":url,"source":"YAC / Powerhouse"})
    return out

def oxcm(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    hdr = soup.find(string=re.compile("Market", re.I))
    out.append({"title":"Oxford Community Market (OXCM)","description":_clean(hdr) if hdr else None,"link":url,"source":"OXCM"})
    return out

def ford_center(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for ev in soup.select("article, .tribe-events-calendar-list__event"):
        a=ev.find("a")
        title=_clean(a.get_text()) if a else "Ford Center Event"
        href=a.get("href") if a else url
        meta=ev.get_text(" ", strip=True)
        out.append({"title":title,"link":href,"description":meta,"source":"Ford Center"})
    if not out: out.append({"title":"Ford Center — events","link":url,"source":"Ford Center"})
    return out

def alumni(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for card in soup.select("article, .event, .tribe-events-calendar-list__event"):
        a=card.find("a")
        if a: out.append({"title":_clean(a.get_text()),"link":a.get("href"),"source":"Ole Miss Alumni Association"})
    if not out: out.append({"title":"Alumni events","link":url,"source":"Ole Miss Alumni Association"})
    return out

def athletics(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for a in soup.select("a[href*='calendar']"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href: out.append({"title":txt,"link":href,"source":"Ole Miss Athletics"})
    if not out: out.append({"title":"Ole Miss Athletics — calendar","link":url,"source":"Ole Miss Athletics"})
    return out

def engage_campus(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for a in soup.select("a[href*='/event/']"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href: out.append({"title":txt,"link":href,"source":"Ole Miss Engage"})
    if not out: out.append({"title":"Campus events portal","link":url,"source":"Ole Miss Engage"})
    return out

def city_meetings(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for li in soup.select("li"):
        txt=_clean(li.get_text() or "")
        if txt and any(k in txt.lower() for k in ["meeting","commission","board of aldermen","planning"]):
            out.append({"title":txt,"link":url,"source":"City of Oxford"})
    if not out: out.append({"title":"City of Oxford — meetings","link":url,"source":"City of Oxford"})
    return out

def occ_lite(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for a in soup.select("a"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href and "event" in txt.lower():
            out.append({"title":txt,"link":href,"source":"Oxford Conference Center"})
    if not out: out.append({"title":"Oxford Conference Center — site","link":url,"source":"Oxford Conference Center"})
    return out

def library_portal(url: str) -> List[Dict[str, Any]]:
    return [{"title":"First Regional Library — Calendars","link":url,"source":"Oxford Public Library (FRL)"}]

def eventbrite_oxford(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for a in soup.select("a[href*='eventbrite.com/e/']"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href: out.append({"title":txt,"link":href,"source":"Eventbrite Oxford"})
    if not out: out.append({"title":"See more on Eventbrite","link":url,"source":"Eventbrite Oxford"})
    return out

def social_stub(url: str) -> List[Dict[str, Any]]:
    # Placeholder indicating social feeds to monitor; APIs are needed for live ingest.
    return [{"title":"Social feed (monitor for updates)","link":url,"source":"Social"}]
