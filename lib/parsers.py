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
    soup = get_soup(url); items = []
    for a in soup.select("[class*='event'] a"):
        title = _clean(a.get_text()); link = a.get("href")
        if title and link and "/events/" in link:
            items.append({"title": title, "link": link})
    if not items: items.append({"title":"Visit Oxford events", "link": url})
    return items

def chambermaster(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); items=[]
    for a in soup.select("a"):
        txt = _clean(a.get_text()); href = a.get("href") or ""
        if txt and ("event" in (txt.lower() + " " + href.lower())):
            items.append({"title": txt, "link": href if href.startswith("http") else "https://business.oxfordms.com"+href})
    if not items: items.append({"title":"Chamber events", "link": url})
    return items

def simple_list(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); out=[]
    for a in soup.select("a"):
        txt=_clean(a.get_text()); href=a.get("href") or ""
        if not txt or not href: continue
        if any(k in (href.lower()+" "+txt.lower()) for k in ["event","calendar","show"]):
            if not href.startswith("http"):
                base = url.split("//")[0]+"//"+url.split("//")[1].split("/")[0]
                href = base + href
            out.append({"title":txt,"link":href})
    if not out: out.append({"title":"Events listing","link":url})
    return out

def lyric(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); out=[]
    for ev in soup.select("article, .event, .tribe-events-calendar-list__event-row"):
        a = ev.find("a"); title=_clean(a.get_text()) if a else None; href=a.get("href") if a else None
        if title:
            out.append({"title": title, "link": href or url, "description": ev.get_text(' ', strip=True)})
    if not out: out.append({"title":"Lyric calendar","link":url})
    return out

def proud_larrys(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for a in soup.select("a"):
        txt=_clean(a.get_text()); href=a.get("href") or ""
        if txt and href and any(k in href.lower() for k in ["show","event","p="]):
            out.append({"title":txt,"link":href})
    if not out: out.append({"title":"Proud Larry's — shows","link":url})
    return out

def square_books(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for ev in soup.select("div.view-content a"):
        txt=_clean(ev.get_text()); href=ev.get("href") or ""
        if txt and "/event" in href:
            if not href.startswith("http"): href="https://squarebooks.com"+href
            out.append({"title":txt,"link":href})
    if not out: out.append({"title":"Square Books events","link":url})
    return out

def thacker(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for post in soup.select("article"):
        a=post.find("a")
        if a: out.append({"title":_clean(a.get_text()),"link":a.get("href")})
    if not out: out.append({"title":"Thacker Mountain — site","link":url})
    return out

def yac_powerhouse(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for card in soup.select("article, .product, .product-inner"):
        a=card.find("a")
        title=_clean(a.get_text()) if a else None
        href=a.get("href") if a else None
        price=None; price_el = card.select_one(".price, .amount")
        if price_el: price=_clean(price_el.get_text())
        out.append({"title": title or "YAC Event", "link": href or url, "cost": price})
    if not out: out.append({"title":"Powerhouse events","link":url})
    return out

def ford_center(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for ev in soup.select("article, .tribe-events-calendar-list__event"):
        a=ev.find("a")
        title=_clean(a.get_text()) if a else "Ford Center Event"
        href=a.get("href") if a else url
        out.append({"title":title,"link":href,"description":ev.get_text(' ', strip=True)})
    if not out: out.append({"title":"Ford Center — events","link":url})
    return out

def occ_lite(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for a in soup.select("a"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href and "event" in (txt.lower() or ""):
            out.append({"title":txt,"link":href})
    if not out: out.append({"title":"Oxford Conference Center — site","link":url})
    return out

def library_portal(url: str) -> List[Dict[str, Any]]:
    return [{"title":"First Regional Library — Calendars","link":url}]

def eventbrite_oxford(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for a in soup.select("a[href*='eventbrite.com/e/']"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href: out.append({"title":txt,"link":href})
    if not out: out.append({"title":"Eventbrite — Oxford (open to browse)", "link": url})
    return out

def football_schedule(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); out=[]
    games = soup.select("li[class*='schedule'], li[class*='game'], li[class*='sidearm'], div[class*='game'], tr")
    for g in games:
        txt = " ".join(g.get_text(" ", strip=True).split())
        if not re.search(r"\b(vs\.?|at)\b", txt, re.I) and "ole miss" not in txt.lower():
            continue
        if not re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)", txt, re.I): continue
        try: dt = dtp.parse(txt, fuzzy=True)
        except Exception: dt = None
        m = re.search(r"(vs\.?|at)\s+([A-Za-z .&'-]+)", txt, re.I); opponent = m.group(2).strip() if m else "Opponent"
        opponent = re.sub(r"\s+(\d{1,2}:\d{2}[ap]m).*", "", opponent, flags=re.I)
        home = bool(re.search(r"\bvs\b", txt, re.I)); location = "Vaught-Hemingway Stadium" if home else "Away"
        title = f"Ole Miss Football {'vs' if home else 'at'} {opponent}"
        out.append({"title":title,"start":dt.isoformat() if dt else None,"location":location,"category":"Sports","link":url,"description":txt})
    if not out: out.append({"title":"Ole Miss Football — Schedule", "link": url})
    return out

def social_stub(url: str) -> List[Dict[str, Any]]:
    return [{"title":"Social feed (open to browse)", "link": url}]
