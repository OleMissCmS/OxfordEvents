from __future__ import annotations
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from dateutil import parser as dtp
import re
from .data_io import get_soup

def _clean(t: Optional[str]) -> Optional[str]:
    if not t: return None
    return " ".join(t.split())

def simple_list(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); out=[]
    for a in soup.select("a"):
        txt=_clean(a.get_text()); href=a.get("href") or ""
        if not txt or not href: continue
        if any(k in (href.lower()+" "+txt.lower()) for k in ["event","calendar","show","game"]):
            out.append({"title":txt,"link":href})
    if not out: out.append({"title":"Events listing","link":url})
    return out

def visit_oxford(url: str)->List[Dict[str, Any]]: return simple_list(url)
def chambermaster(url: str)->List[Dict[str, Any]]: return simple_list(url)
def lyric(url: str)->List[Dict[str, Any]]: return simple_list(url)
def proud_larrys(url: str)->List[Dict[str, Any]]: return simple_list(url)
def square_books(url: str)->List[Dict[str, Any]]: return simple_list(url)
def thacker(url: str)->List[Dict[str, Any]]: return simple_list(url)
def yac_powerhouse(url: str)->List[Dict[str, Any]]: return simple_list(url)
def ford_center(url: str)->List[Dict[str, Any]]: return simple_list(url)
def occ_lite(url: str)->List[Dict[str, Any]]: return simple_list(url)
def library_portal(url: str)->List[Dict[str, Any]]: return [{"title":"Library calendars","link":url}]
def eventbrite_oxford(url: str)->List[Dict[str, Any]]: return simple_list(url)

def football_schedule(url: str)->List[Dict[str, Any]]:
    # Stubbier but safe; your real parser can be dropped back in
    soup = get_soup(url); out=[]
    text = soup.get_text(" ", strip=True)
    if "Ole Miss" in text or "Rebels" in text:
        out.append({"title":"Ole Miss Football – Game", "start":None, "location":"Vaught-Hemingway Stadium", "link":url, "category":"Sports"})
    else:
        out.append({"title":"Ole Miss Football — Schedule", "link": url})
    return out

def social_stub(url: str)->List[Dict[str, Any]]: return [{"title":"Social feed (open to browse)","link":url}]
