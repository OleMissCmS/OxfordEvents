from __future__ import annotations
import streamlit as st
from typing import Dict, Any, Optional
from dateutil import parser as dtp
import hashlib, base64
from pathlib import Path

RED = "#CE1126"
NAVY = "#0C2340"
VERSION = "v4.8.4"

def _clamp(text: str | None, n: int = 333) -> str | None:
    if not text: return text
    text = text.strip()
    return text if len(text) <= n else text[:n-1] + "…"

def _img_data_uri(path: str) -> Optional[str]:
    try:
        p = Path(path)
        if not p.exists() or p.stat().st_size == 0:
            return None
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        # Assume PNG by default; works for PNG/SVG served as image/png here
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None

def hero(subtitle: str | None = None):
    ox = _img_data_uri("assets/oxford_logo.png")
    ms = _img_data_uri("assets/ms_flag.png")
    om = _img_data_uri("assets/olemiss_logo.png")
    def _slot(data_uri: Optional[str], alt: str) -> str:
        if data_uri:
            return f'<img src="{data_uri}" alt="{alt}" />'
        # Graceful fallback: show text badge when image missing
        return f'<span style="padding:4px 8px;border-radius:8px;background:{NAVY};color:white;opacity:.85;font-size:12px;">{alt}</span>'
    imgs_html = _slot(ox,"Oxford, MS") + _slot(ms,"Mississippi") + _slot(om,"Ole Miss")

    st.markdown(f"""
<style>
.top-gradient {{
  position: fixed; top: 0; left: 0; right: 0; height: 6px; z-index: 9999;
  background: repeating-linear-gradient(90deg, {RED} 0 48px, {NAVY} 48px 96px);
  animation: bar-slide 8s linear infinite;
  background-size: 300% 100%;
}}
@keyframes bar-slide {{ 0% {{ background-position: 0 0; }} 100% {{ background-position: 300% 0; }} }}
.filters-badge {{
  position: fixed; top: 16px; left: 8px; z-index: 9998;
  background: {NAVY}; color: white; padding: 2px 8px; border-radius: 999px;
  font-size: 12px; opacity: .9; pointer-events: none;
}}
.brandbar {{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:.25rem;flex-wrap:wrap;}}
.brandbar img {{height:44px; width:auto; object-fit:contain;}}
@media (max-width: 640px){{ .brandbar img {{height:34px;}} }}
</style>
<div class="top-gradient"></div>
<div class="filters-badge">Filters</div>

<div style="padding:0.8rem 1.2rem 0.5rem 1.2rem;border-radius:16px;margin-top:10px;background:linear-gradient(180deg, rgba(12,35,64,.98), rgba(12,35,64,.85));color:white; text-align:center; position:relative;">
  <div class="brandbar">
    {imgs_html}
  </div>
  <h1 style="margin:.1rem 0 0 0;">Upcoming in Oxford</h1>
  <p style="margin:.25rem 0 .5rem 0;opacity:.95">{subtitle or "What's happening, Oxford?"}</p>
  <div style="position:absolute; bottom:4px; left:10px; font-size:11px; opacity:.85;">{VERSION}</div>
</div>
""", unsafe_allow_html=True)

def _badge(text: str, bg: str, fg: str = "white"):
    st.markdown(f'<span style="background:{bg};color:{fg};padding:.15rem .45rem;border-radius:999px;font-size:11px;margin-right:.25rem;display:inline-block">{text}</span>', unsafe_allow_html=True)

def event_badges(ev: Dict[str, Any]):
    cost = (ev.get("cost") or "").lower()
    if "free" in cost or cost == "—" or cost == "":
        _badge("FREE", "#0E9F6E")
    elif cost:
        _badge("PAID", "#EF4444")
    title = (ev.get("title") or "").lower()
    loc = (ev.get("location") or "").lower()
    if "vaught" in loc or " vs " in title:
        _badge("HOME", "#1D4ED8")
    elif " away " in loc or " at " in title:
        _badge("AWAY", "#6B7280")
    descr = (ev.get("description") or "").lower()
    if any(k in (title + " " + descr) for k in ["family", "kids", "children", "story time", "storytime"]):
        _badge("Family", "#F59E0B")

def event_card(ev: Dict[str, Any], idx: int) -> None:
    when = None
    try:
        when = dtp.parse(ev.get("start_iso","")).strftime("%a %b %d, %I:%M %p")
    except Exception:
        pass
    category = ev.get("category") or "Uncategorized"
    desc = _clamp(ev.get("description"))
    with st.container(border=True):
        st.subheader(ev.get("title","Event"))
        event_badges(ev)
        st.markdown(
            f"**When:** {when or 'TBA'}  \n"
            f"**Where:** {ev.get('location') or 'TBA'}  \n"
            f"**Cost:** {ev.get('cost') or '—'}  \n"
            f"**Source:** {ev.get('source') or ''}  \n"
            f"**Category:** {category}"
        )
        if desc:
            st.markdown(desc)
        link = ev.get("link")
        if link:
            st.markdown(f"[Event link]({link})")

def unique_key(label: str, *parts: str) -> str:
    h = hashlib.sha1(("||".join([label] + [p or "" for p in parts])).encode("utf-8")).hexdigest()[:10]
    return f"{label}-{h}"
