from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from dateutil import parser as dtp
import re, html
from bs4 import BeautifulSoup

CATEGORY_RULES = [
    (re.compile(r"\b(football|baseball|softball|basketball|soccer|volleyball|golf|tennis|track|athletics|game)\b", re.I), "Sports"),
    (re.compile(r"\b(concert|live music|recital|orchestra|band|choir|jazz|music|show)\b", re.I), "Music"),
    (re.compile(r"\b(theatre|theater|play|performance|ballet|dance|opera|stage)\b", re.I), "Performing Arts"),
    (re.compile(r"\b(lecture|talk|seminar|colloquium|symposium|panel|reading)\b", re.I), "Talks & Lectures"),
    (re.compile(r"\b(workshop|training|bootcamp|certificate|faculty|academic|research|class|course|tutorial|clinic|session)\b", re.I), "Academic & Training"),
    (re.compile(r"\b(book|author|signing|poetry|literary|library|writers?)\b", re.I), "Books & Literary"),
    (re.compile(r"\b(film|movie|screening)\b", re.I), "Film"),
    (re.compile(r"\b(festival|parade|fair|celebration|holiday)\b", re.I), "Festivals"),
    (re.compile(r"\b(market|farmer'?s market|flea|bazaar)\b", re.I), "Markets & Fairs"),
    (re.compile(r"\b(kids?|family|youth|teen)\b", re.I), "Family & Kids"),
    (re.compile(r"\b(campus|student|alumni|greek|residence hall)\b", re.I), "Campus"),
    (re.compile(r"\b(community|service|volunteer|charity|fundraiser|meetup)\b", re.I), "Community"),
    (re.compile(r"\b(art|gallery|museum|exhibit|radio)\b", re.I), "Arts & Culture"),
]

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
    rrule: Optional[str]=None
    group: Optional[str]=None
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
