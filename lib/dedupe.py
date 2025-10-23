from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timedelta
from rapidfuzz import fuzz, process
from dateutil import parser as dtp

def same_day(a: str, b: str) -> bool:
    try:
        da = dtp.parse(a).date()
        db = dtp.parse(b).date()
        return da == db
    except Exception:
        return False

def dedupe(events: List[Dict[str, Any]], threshold: int = 85) -> List[Dict[str, Any]]:
    # Group by date; within each date, fuzzy match titles
    by_date = {}
    for ev in events:
        d = None
        if ev.get("start_iso"):
            try:
                d = dtp.parse(ev["start_iso"]).date().isoformat()
            except Exception:
                d = "unknown"
        else:
            d = "unknown"
        by_date.setdefault(d, []).append(ev)

    out = []
    for d, group in by_date.items():
        kept = []
        used = set()
        titles = [g["title"] for g in group]
        for i, ev in enumerate(group):
            if i in used:
                continue
            cluster = [i]
            for j in range(i+1, len(group)):
                if j in used:
                    continue
                score = fuzz.token_set_ratio(group[i]["title"], group[j]["title"])
                if score >= threshold:
                    cluster.append(j)
            # merge cluster: prefer event with link / location
            merged = ev.copy()
            for idx in cluster[1:]:
                cand = group[idx]
                if not merged.get("link") and cand.get("link"):
                    merged["link"] = cand["link"]
                if not merged.get("location") and cand.get("location"):
                    merged["location"] = cand["location"]
                if not merged.get("cost") and cand.get("cost"):
                    merged["cost"] = cand["cost"]
                used.add(idx)
            kept.append(merged)
        out.extend(kept)
    return out