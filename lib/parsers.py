from __future__ import annotations
from typing import List, Dict, Any, Optional
from .data_io import get_soup

def _clean(t: Optional[str]): 
    return None if not t else " ".join(t.split())

def visit_oxford(url: str):
    soup=get_soup(url); out=[]
    for a in soup.select("a"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href and "/events/" in href: out.append({"title":txt,"link":href,"source":"Visit Oxford"})
    return out or [{"title":"Visit Oxford events","link":url,"source":"Visit Oxford"}]

def chambermaster(url: str):
    soup=get_soup(url); out=[]
    for a in soup.select("a"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href and "event" in (href.lower()+txt.lower()): out.append({"title":txt,"link":href,"source":"Oxford Chamber"})
    return out or [{"title":"Chamber events","link":url,"source":"Oxford Chamber"}]

def eventbrite_oxford(url: str):
    soup=get_soup(url); out=[]
    for a in soup.select("a[href*='eventbrite.com/e/']"):
        txt=_clean(a.get_text()); href=a.get("href")
        if txt and href: out.append({"title":txt,"link":href,"source":"Eventbrite Oxford"})
    return out or [{"title":"See more on Eventbrite","link":url,"source":"Eventbrite Oxford"}]