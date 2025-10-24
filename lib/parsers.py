from __future__ import annotations
from typing import List, Dict, Any
from .data_io import get_soup

def simple_list(url: str) -> List[Dict[str, Any]]:
    soup = get_soup(url); out=[]
    for a in soup.select("a"):
        txt = (a.get_text() or "").strip()
        href = a.get("href") or ""
        if not txt or not href: continue
        if any(k in (href.lower()+" "+txt.lower()) for k in ["event","calendar","show","game"]):
            out.append({"title":txt,"link":href})
    if not out: out.append({"title":"Events listing","link":url})
    return out

def eventbrite_oxford(url: str)->List[Dict[str, Any]]: return simple_list(url)

def football_schedule(url: str)->List[Dict[str, Any]]:
    soup = get_soup(url); text = soup.get_text(" ", strip=True)
    if ("Ole Miss" in text) or ("Rebels" in text):
        return [{"title":"Ole Miss Football – Game","location":"Vaught-Hemingway Stadium","link":url,"category":"Sports"}]
    return [{"title":"Ole Miss Football — Schedule","link":url}]

def social_stub(url: str)->List[Dict[str, Any]]: return [{"title":"Social feed (open to browse)","link":url}]
