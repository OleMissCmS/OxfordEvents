from __future__ import annotations
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from dateutil import parser as dtp
from datetime import datetime
import re
from .data_io import get_soup

def _clean(t: Optional[str]) -> Optional[str]:
    if not t: return None
    return " ".join(t.split())

def visit_oxford(url: str) -> List[Dict[str, Any]]:
    # WordPress events; fallback to simple card parse
    soup = get_soup(url)
    items = []
    for card in soup.select("[class*='event'] a"):
        title = _clean(card.get_text())
        link = card.get("href")
        if title and link and "/events/" in link:
            items.append({"title": title, "link": link, "source": "Visit Oxford"})
    return items

def chambermaster(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    items = []
    for row in soup.select("div#calendarmodule, .event, .event-listing"):
        title_el = row.select_one("a")
        date_el = row.find(["time","span"], string=re.compile(r"\b\d{4}|\b[A-Za-z]{3}"))
        title = _clean(title_el.get_text()) if title_el else None
        link = title_el.get("href") if title_el else None
        items.append({"title": title or "Chamber Event", "link": link, "source": "Oxford Chamber"})
    return items

def simple_list(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for a in soup.select("a"):
        txt = _clean(a.get_text())
        href = a.get("href")
        if txt and href and ("event" in href or "events" in href):
            out.append({"title": txt, "link": href, "source": url.split('/')[2]})
    return out

def lyric(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for ev in soup.select("article, .event, .tribe-events-calendar-list__event-row"):
        a = ev.find("a")
        title = _clean(a.get_text()) if a else None
        href = a.get("href") if a else None
        meta = ev.get_text(" ", strip=True)
        out.append({"title": title or "Lyric Event", "link": href, "description": meta, "source": "The Lyric Oxford"})
    return out

def proud_larrys(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    # the site often lists "Upcoming Shows" links
    for a in soup.select("a"):
        txt = _clean(a.get_text())
        href = a.get("href")
        if txt and href and ("show" in href or "event" in href or "p=" in href):
            out.append({"title": txt, "link": href, "source": "Proud Larry's"})
    return out

def square_books(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for ev in soup.select("div.view-content a"):
        txt = _clean(ev.get_text())
        href = ev.get("href")
        if txt and href and "/event" in href:
            out.append({"title": txt, "link": href if href.startswith("http") else "https://squarebooks.com"+href, "source": "Square Books"})
    return out

def thacker(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for post in soup.select("article"):
        a = post.find("a")
        if not a: continue
        out.append({"title": _clean(a.get_text()), "link": a.get("href"), "source": "Thacker Mountain Radio Hour"})
    return out

def yac_powerhouse(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for card in soup.select("article, .product, .product-inner"):
        a = card.find("a")
        title = _clean(a.get_text()) if a else None
        href = a.get("href") if a else None
        price = None
        price_el = card.select_one(".price, .amount")
        if price_el:
            price = _clean(price_el.get_text())
        out.append({"title": title or "YAC Event", "link": href, "cost": price, "source": "YAC / Powerhouse"})
    return out

def oxcm(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    hdr = soup.find(text=re.compile("Every Tuesday", re.I))
    out.append({"title": "Oxford Community Market (OXCM)", "description": _clean(hdr) if hdr else None, "link": url, "source": "OXCM"})
    return out

def ford_center(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for ev in soup.select("article, .tribe-events-calendar-list__event"):
        a = ev.find("a")
        title = _clean(a.get_text()) if a else "Ford Center Event"
        href = a.get("href") if a else url
        meta = ev.get_text(" ", strip=True)
        out.append({"title": title, "link": href, "description": meta, "source": "Ford Center"})
    return out

def alumni(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for card in soup.select("article, .event, .tribe-events-calendar-list__event"):
        a = card.find("a")
        if not a: continue
        out.append({"title": _clean(a.get_text()), "link": a.get("href"), "source": "Ole Miss Alumni Association"})
    return out

def athletics(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for a in soup.select("a[href*='schedule'] , a[href*='calendar'] , a[href*='composite']"):
        txt = _clean(a.get_text())
        href = a.get("href")
        if txt and href and "olemisssports.com" in href:
            out.append({"title": txt, "link": href, "source": "Ole Miss Athletics"})
    return out

def engage_campus(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for a in soup.select("a"):
        txt = _clean(a.get_text())
        href = a.get("href")
        if txt and href and "/event/" in href:
            out.append({"title": txt, "link": href, "source": "Ole Miss Engage"})
    # Even if none, keep a placeholder link
    if not out:
        out.append({"title": "Campus events on The ForUM", "link": url, "source": "Ole Miss Engage"})
    return out

def city_meetings(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for li in soup.select("li"):
        txt = _clean(li.get_text())
        if txt and any(k in txt.lower() for k in ["meeting", "commission", "board of aldermen"]):
            out.append({"title": txt, "link": url, "source": "City of Oxford"})
    if not out:
        out.append({"title": "City of Oxford — Meetings", "link": url, "source": "City of Oxford"})
    return out

def occ_lite(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = []
    for a in soup.select("a"):
        txt = _clean(a.get_text())
        href = a.get("href")
        if txt and href and "event" in txt.lower():
            out.append({"title": txt, "link": href, "source": "Oxford Conference Center"})
    if not out:
        out.append({"title": "Oxford Conference Center — homepage", "link": url, "source": "Oxford Conference Center"})
    return out

def library_portal(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out = [{"title": "First Regional Library — Calendars", "link": url, "source": "Oxford Public Library (FRL)"}]
    return out