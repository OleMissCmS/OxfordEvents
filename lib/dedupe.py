from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from rapidfuzz import fuzz
from dateutil import parser as dtp
import re

def _norm(text: str | None) -> str:
    s = (text or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _start_key(iso: str | None) -> Optional[str]:
    if not iso: return None
    try:
        dt = dtp.parse(iso); return dt.strftime("%Y-%m-%d %H:%M")
    except Exception: return None

def dedupe(events: List[Dict[str, Any]], aliases: Dict[str, str] | None = None, threshold: int = 88) -> List[Dict[str, Any]]:
    aliases = aliases or {}
    def canon_loc(l: str | None) -> str:
        norm = _norm(l)
        return aliases.get(norm, norm)
    keyed: Dict[Tuple[str, str], Dict[str, Any]] = {}
    leftovers: List[Dict[str, Any]] = []
    for ev in events:
        k_time = _start_key(ev.get("start_iso"))
        k_loc = canon_loc(ev.get("location"))
        if k_time and k_loc:
            key = (k_time, k_loc)
            cur = keyed.get(key)
            if not cur or len((ev.get("title") or "")) > len((cur.get("title") or "")):
                keyed[key] = ev
        else:
            leftovers.append(ev)
    stageA = list(keyed.values()) + leftovers
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
                title_score = fuzz.token_set_ratio(a.get("title",""), b.get("title",""))
                desc_score = fuzz.token_set_ratio(a.get("description","") or "", b.get("description","") or "")
                if title_score >= threshold or (title_score >= 75 and desc_score >= 75):
                    for k in ["link","location","cost","description","category"]:
                        if not merged.get(k) and b.get(k): merged[k] = b[k]
                    used.add(j)
            out.append(merged)
    return out
