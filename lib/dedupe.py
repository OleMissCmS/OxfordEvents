from __future__ import annotations
from typing import List, Dict, Any, Tuple
from rapidfuzz import fuzz
from dateutil import parser as dtp
import re

def _norm_loc(l: str | None) -> str:
    s = (l or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _start_key(iso: str | None) -> str | None:
    if not iso: return None
    try:
        dt = dtp.parse(iso)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return None

def dedupe(events: List[Dict[str, Any]], threshold: int = 88) -> List[Dict[str, Any]]:
    if not events: return []
    keyed: Dict[Tuple[str, str], Dict[str, Any]] = {}
    leftovers: List[Dict[str, Any]] = []
    for ev in events:
        k_time = _start_key(ev.get("start_iso"))
        k_loc = _norm_loc(ev.get("location"))
        if k_time and k_loc:
            key = (k_time, k_loc)
            cur = keyed.get(key)
            if not cur or len((ev.get("title") or "")) > len((cur.get("title") or "")):
                keyed[key] = ev
        else:
            leftovers.append(ev)
    stageA = list(keyed.values()) + leftovers
    by_date = {}
    for ev in stageA:
        d = "unknown"
        if ev.get("start_iso"):
            try: d = dtp.parse(ev["start_iso"]).date().isoformat()
            except Exception: pass
        by_date.setdefault(d, []).append(ev)
    out: List[Dict[str, Any]] = []
    for group in by_date.values():
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