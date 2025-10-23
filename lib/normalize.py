from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from dateutil import parser as dtp
import re, html
from bs4 import BeautifulSoup

CATEGORY_RULES=[(re.compile(r"\b(football|baseball|softball|basketball|soccer|volleyball|golf|tennis|track|athletics|game)\b", re.I),"Sports")]

def strip_html(text: Optional[str]) -> Optional[str]:
    if not text: return text
    s = BeautifulSoup(text, "lxml").get_text(" ", strip=True)
    s = html.unescape(re.sub(r"\s{2,}"," ", s)).strip()
    return s or None

@dataclass
class Event:
    title: str
    start_iso: Optional[str]
    end_iso: Optional[str]
    location: Optional[str]
    cost: Optional[str]
    link: Optional[str]
    source: str
    category: Optional[str]
    description: Optional[str]=None
    def to_dict(self)->Dict[str,Any]: return asdict(self)

def infer_category(title:str, description:Optional[str])->Optional[str]:
    text=f"{title} {description or ''}"
    for rx,cat in CATEGORY_RULES:
        if rx.search(text): return cat
    return None

def to_iso(dt)->Optional[str]:
    if not dt: return None
    if isinstance(dt,str):
        try: return dtp.parse(dt).isoformat()
        except Exception: return None
    try: return dt.isoformat()
    except Exception: return None