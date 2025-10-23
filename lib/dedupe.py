from __future__ import annotations
from typing import List, Dict, Any
from rapidfuzz import fuzz
from dateutil import parser as dtp

def dedupe(events: List[Dict[str, Any]], threshold: int = 88) -> List[Dict[str, Any]]:
    # group by date; within each date, fuzzy-match titles
    by_date = {}
    for ev in events:
        d = "unknown"
        if ev.get("start_iso"):
            try: d = dtp.parse(ev["start_iso"]).date().isoformat()
            except Exception: pass
        by_date.setdefault(d, []).append(ev)

    out = []
    for d, group in by_date.items():
        used = set()
        for i, a in enumerate(group):
            if i in used: continue
            merged = a.copy()
            for j, b in enumerate(group[i+1:], start=i+1):
                if j in used: continue
                score = fuzz.token_set_ratio(a.get("title",""), b.get("title",""))
                if score >= threshold:
                    for k in ["link","location","cost","description","category"]:
                        if not merged.get(k) and b.get(k):
                            merged[k] = b[k]
                    used.add(j)
            out.append(merged)
    return out