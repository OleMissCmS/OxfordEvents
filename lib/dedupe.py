from __future__ import annotations
from typing import List, Dict, Any, Tuple
from rapidfuzz import fuzz
from dateutil import parser as dtp

def _norm_loc(l: str | None) -> str:
    return (l or "").strip().lower()

def _start_key(iso: str | None) -> str | None:
    if not iso: return None
    try:
        # minute precision
        dt = dtp.parse(iso)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return None

def dedupe(events: List[Dict[str, Any]], threshold: int = 88) -> List[Dict[str, Any]]:
    if not events:
        return []

    # Stage A: strict same (start minute + location) -> keep longer title
    keyed: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for ev in events:
        k_time = _start_key(ev.get("start_iso"))
        k_loc = _norm_loc(ev.get("location"))
        if k_time and k_loc:
            key = (k_time, k_loc)
            current = keyed.get(key)
            if not current or len((ev.get("title") or "")) > len((current.get("title") or "")):
                keyed[key] = ev
        else:
            keyed[(id(ev), str(id(ev)))] = ev  # unique key to keep items without both fields

    stageA = list(keyed.values())

    # Stage B: fuzzy within same date (original behavior)
    by_date: Dict[str, List[Dict[str, Any]]] = {}
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