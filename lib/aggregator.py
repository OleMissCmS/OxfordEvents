from __future__ import annotations
from typing import List, Dict, Any, Callable, Optional, Tuple
import yaml, csv
from datetime import datetime, timedelta
from dateutil import tz, parser as dtp
from .data_io import parse_rss, parse_ics
from .parsers import simple_list, eventbrite_oxford, football_schedule, social_stub
from .normalize import Event, infer_category, to_iso, strip_html
from .dedupe import dedupe
from .apis import seatgeek_events, ticketmaster_events

PARSER_MAP={"simple_list":simple_list,"eventbrite_oxford":eventbrite_oxford,"football_schedule":football_schedule,"social_stub":social_stub}

def load_sources(path: str = "data/sources.yaml")->List[Dict[str, Any]]:
    import os
    if not os.path.exists(path): return []
    with open(path,"r",encoding="utf-8") as f: return yaml.safe_load(f) or []

def load_alias_map(path: str = "data/venues.csv")->Dict[str,str]:
    import re, os, csv as _csv
    def norm(s:str)->str:
        s=(s or "").lower()
        s=re.sub(r"[^a-z0-9]+"," ",s); s=re.sub(r"\s+"," ",s).strip()
        return s
    out={}
    if not os.path.exists(path): return out
    with open(path,"r",encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            name=row["name"]; aliases=(row.get("aliases") or "").split("|")
            for a in [name]+[x.strip() for x in aliases if x.strip()]:
                out[norm(a)] = norm(name)
    return out

def normalize_records(records: List[Dict[str, Any]], source_name: str, group: Optional[str])->List[Dict[str, Any]]:
    out=[]
    for r in records:
        title=r.get("title") or "Untitled"
        start=r.get("start"); end=r.get("end"); loc=r.get("location"); link=r.get("link")
        desc=strip_html(r.get("description")); cost=r.get("cost"); rrule=r.get("rrule")
        cat=r.get("category") or infer_category(title, desc)
        ev=Event(title=title,start_iso=to_iso(start),end_iso=to_iso(end) if end else to_iso(start),
                 location=loc,cost=cost,link=link,source=source_name,category=cat,description=desc,rrule=rrule,group=group)
        out.append(ev.to_dict())
    return out

def collect_with_progress(notify: Optional[Callable[[str,int,int],None]]=None)->Tuple[List[Dict[str,Any]], Dict[str,Any]]:
    sources=load_sources(); all_events=[]; total=len(sources)
    health={"started_at": datetime.now(tz.tzlocal()).isoformat(), "per_source": {}}
    for i,s in enumerate(sources, start=1):
        name=s.get("name","(source)"); t=s.get("type"); url=s.get("url"); group=s.get("group"); parser=s.get("parser")
        if notify: notify(name, i, total)
        try:
            if t=="rss": recs=parse_rss(url)
            elif t=="ics": recs=parse_ics(url)
            elif t=="html":
                fn=PARSER_MAP.get(parser, social_stub if any(k in (url or "") for k in ["twitter.com","facebook.com","instagram.com"]) else simple_list)
                recs=fn(url)
            elif t=="api":
                if parser=="seatgeek":
                    recs=seatgeek_events(city=s.get("city","Oxford"), state=s.get("state","MS"))
                elif parser=="ticketmaster":
                    recs=ticketmaster_events(city=s.get("city","Oxford"), stateCode=s.get("state","MS"))
                else:
                    recs=[]
            else:
                recs=[]
            all_events.extend(normalize_records(recs, source_name=name, group=group))
            health["per_source"][name]={"count": len(recs), "ok": True}
        except Exception as e:
            all_events.append({"title": f"[{name}] (source error)", "start_iso": None, "end_iso": None, "location": None, "cost": None, "link": url, "source": name, "category": None, "description": str(e), "group": group})
            health["per_source"][name]={"count": 0, "ok": False, "error": str(e)}
    alias_map = load_alias_map()
    deduped = dedupe(all_events, aliases=alias_map, threshold=88)
    health["finished_at"] = datetime.now(tz.tzlocal()).isoformat()
    health["total_events"] = len(deduped)
    return deduped, health

def collect()->List[Dict[str,Any]]:
    return collect_with_progress(None)[0]

def window(events: List[Dict[str, Any]], days:int=90)->List[Dict[str,Any]]:
    now=datetime.now(tz.tzlocal()); end=now+timedelta(days=days); sel=[]
    for ev in events:
        if not ev.get("start_iso"): continue
        try:
            dt = dtp.parse(ev["start_iso"])
            if now<=dt<=end: sel.append(ev)
        except Exception: continue
    return sorted(sel, key=lambda e:e["start_iso"])
