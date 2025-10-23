from __future__ import annotations
from typing import List, Dict, Any, Callable, Optional
import yaml
from datetime import datetime, timedelta
from dateutil import tz
from .data_io import parse_rss, parse_ics
from .parsers import visit_oxford, chambermaster, eventbrite_oxford
from .normalize import Event, infer_category, to_iso, strip_html

PARSER_MAP={"visit_oxford":visit_oxford,"chambermaster":chambermaster,"eventbrite_oxford":eventbrite_oxford}

def load_sources(path: str = "data/sources.yaml")->List[Dict[str, Any]]:
    with open(path,"r",encoding="utf-8") as f: return yaml.safe_load(f)

def normalize_records(records: List[Dict[str, Any]], source_name: str)->List[Dict[str, Any]]:
    out=[]
    for r in records:
        title=r.get("title") or "Untitled"
        start=r.get("start"); end=r.get("end")
        ev=Event(title=title,start_iso=to_iso(start),end_iso=to_iso(end) if end else to_iso(start),
                 location=r.get("location"),cost=r.get("cost"),link=r.get("link"),
                 source=source_name,category=(r.get("category")),description=strip_html(r.get("description")))
        out.append(ev.to_dict())
    return out

def collect_with_progress(notify: Optional[Callable[[str,int,int],None]]=None)->List[Dict[str,Any]]:
    sources=load_sources(); all_events=[]; total=len(sources)
    for i,s in enumerate(sources, start=1):
        if notify: notify(s["name"], i, total)
        t=s["type"]; url=s["url"]
        if t=="rss": recs=parse_rss(url)
        elif t=="ics": recs=parse_ics(url)
        elif t=="html": recs=PARSER_MAP.get(s.get("parser"), lambda u: [])(url)
        else: recs=[]
        all_events.extend(normalize_records(recs, source_name=s["name"]))
    return all_events

def window(events: List[Dict[str, Any]], days:int=21)->List[Dict[str,Any]]:
    now=datetime.now(tz.tzlocal()); end=now+timedelta(days=days); sel=[]
    for ev in events:
        if not ev.get("start_iso"): continue
        try:
            dt=datetime.fromisoformat(ev["start_iso"].replace("Z",""))
            if now<=dt<=end: sel.append(ev)
        except Exception: continue
    return sorted(sel, key=lambda e:e["start_iso"])