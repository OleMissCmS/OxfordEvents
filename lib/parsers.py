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

def eventbrite_oxford(url: str) -> List[Dict[str, Any]]:
    soup=get_soup(url); out=[]
    for a in soup.select("a[href*='eventbrite.com/e/']"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href: out.append({"title":txt,"link":href,"source":"Eventbrite Oxford"})
    if not out: out.append({"title":"Eventbrite — Oxford (open to browse)", "link": url, "source": "Eventbrite Oxford"})
    return out

def football_schedule(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url)
    out: List[Dict[str, Any]] = []
    games = soup.select("li[class*='schedule'], li[class*='game'], li[class*='sidearm'], div[class*='game'], tr")
    for g in games:
        txt = " ".join(g.get_text(" ", strip=True).split())
        if not re.search(r"\b(vs\.?|at)\b", txt, re.I) and "ole miss" not in txt.lower():
            continue
        if not re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)", txt, re.I):
            continue
        dt = None
        try: dt = dtp.parse(txt, fuzzy=True)
        except Exception: pass
        m = re.search(r"(vs\.?|at)\s+([A-Za-z .&'-]+)", txt, re.I)
        opponent = m.group(2).strip() if m else "Opponent"
        opponent = re.sub(r"\s+(\d{1,2}:\d{2}[ap]m).*", "", opponent, flags=re.I)
        home = bool(re.search(r"\bvs\b", txt, re.I))
        location = "Vaught-Hemingway Stadium" if home else "Away"
        title = f"Ole Miss Football {'vs' if home else 'at'} {opponent}"
        out.append({"title":title,"start":dt.isoformat() if dt else None,"location":location,"category":"Sports","link":url,"description":txt})
    if not out:
        out.append({"title":"Ole Miss Football — Schedule", "link": url, "source":"Ole Miss Athletics"})
    else:
        for it in out: it["source"] = "Ole Miss Athletics (HTML)"
    return out