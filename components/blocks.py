from __future__ import annotations
import streamlit as st
from typing import Dict, Any, Optional
from dateutil import parser as dtp
import hashlib, base64
from pathlib import Path

RED = "#CE1126"
NAVY = "#0C2340"
VERSION = "v5.1.0"

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
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None

def hero(subtitle: str | None = None):
    ox = _img_data_uri("assets/oxford_logo.png")
    ms = _img_data_uri("assets/ms_flag.png")
    om = _img_data_uri("assets/olemiss_logo.png")
    def _slot(data_uri: Optional[str], alt: str) -> str:
        if data_uri:
            return f'<img src="{data_uri}" alt="{alt}" style="height:48px; width:auto; object-fit:contain;" />'
        return f'<span style="padding:6px 12px;border-radius:8px;background:{NAVY};color:white;opacity:.85;font-size:12px;font-weight:500;">{alt}</span>'
    imgs_html = _slot(ox,"Oxford, MS") + _slot(ms,"Mississippi") + _slot(om,"Ole Miss")

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}

.stApp {{
    background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
}}

.main .block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
}}

.top-gradient {{
    position: fixed; 
    top: 0; 
    left: 0; 
    right: 0; 
    height: 4px; 
    z-index: 9999;
    background: linear-gradient(90deg, {RED} 0%, {RED} 50%, {NAVY} 50%, {NAVY} 100%);
    background-size: 200% 100%;
    animation: gradient-slide 3s ease infinite;
}}

@keyframes gradient-slide {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

.hero-container {{
    background: linear-gradient(135deg, {NAVY} 0%, #1a3a5c 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 40px rgba(12, 35, 64, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.1);
}}

.brandbar {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}}

.hero-title {{
    font-size: 2.5rem;
    font-weight: 700;
    margin: 0.5rem 0;
    color: white;
    text-align: center;
    letter-spacing: -0.5px;
}}

.hero-subtitle {{
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.9);
    text-align: center;
    margin: 0.5rem 0;
    font-weight: 400;
}}

.version-badge {{
    position: absolute;
    bottom: 12px;
    right: 20px;
    font-size: 0.75rem;
    opacity: 0.7;
    color: white;
    font-weight: 500;
}}

.quick-filter-container {{
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(0, 0, 0, 0.05);
}}

.filter-chip {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}}

.filter-chip:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}}

.event-card {{
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
}}

.event-card:hover {{
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
}}

@media (max-width: 768px) {{
    .hero-title {{
        font-size: 2rem;
    }}
    .brandbar img {{
        height: 36px !important;
    }}
}}

/* Sidebar styling */
[data-testid="stSidebar"] {{
    background: white;
}}

.css-1d391kg {{
    background: white;
}}
</style>

<div class="top-gradient"></div>

<div class="hero-container">
  <div class="brandbar">
    {imgs_html}
  </div>
  <h1 class="hero-title">Upcoming in Oxford</h1>
  <p class="hero-subtitle">{subtitle or "What's happening, Oxford?"}</p>
  <div class="version-badge">{VERSION}</div>
</div>
""", unsafe_allow_html=True)

def _badge(text: str, bg: str, fg: str = "white"):
    st.markdown(f'<span style="background:{bg};color:{fg};padding:0.25rem 0.65rem;border-radius:20px;font-size:0.75rem;font-weight:600;margin-right:0.5rem;display:inline-block;box-shadow:0 2px 4px rgba(0,0,0,0.1);">{text}</span>', unsafe_allow_html=True)

def event_badges(ev: Dict[str, Any]):
    cost = (ev.get("cost") or "").lower()
    if "free" in cost or cost == "—" or cost == "":
        _badge("FREE", "#0E9F6E")
    elif cost:
        _badge("PAID", "#EF4444")
    descr = (ev.get("description") or "").lower()
    title = (ev.get("title") or "").lower()
    if any(k in (title + " " + descr) for k in ["family", "kids", "children", "story time", "storytime"]):
        _badge("Family", "#F59E0B")
    src = ev.get("source") or ""
    if src:
        _badge(src, "#6B7280", "white")

def event_card(ev: Dict[str, Any], idx: int) -> None:
    when = None
    try:
        when = dtp.parse(ev.get("start_iso","")).strftime("%a %b %d, %I:%M %p")
    except Exception:
        pass
    category = ev.get("category") or "Uncategorized"
    desc = _clamp(ev.get("description"))
    
    # Modern card design
    st.markdown('<div class="event-card">', unsafe_allow_html=True)
    
    # Title with better styling
    st.markdown(f'<h2 style="margin-top:0;margin-bottom:0.75rem;color:{NAVY};font-size:1.5rem;font-weight:700;">{ev.get("title","Event")}</h2>', unsafe_allow_html=True)
    
    # Badges
    event_badges(ev)
    
    # Info grid
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**📅 When:** {when or 'TBA'}")
        st.markdown(f"**📍 Where:** {ev.get('location') or 'TBA'}")
    with col2:
        st.markdown(f"**💰 Cost:** {ev.get('cost') or '—'}")
        st.markdown(f"**🏷️ Category:** {category}")
    
    if desc:
        st.markdown(f"<p style='margin-top:1rem;color:#4B5563;line-height:1.6;'>{desc}</p>", unsafe_allow_html=True)
    
    link = ev.get("link")
    if link:
        st.markdown(f'<a href="{link}" target="_blank" style="color:{RED};text-decoration:none;font-weight:600;margin-top:0.5rem;display:inline-block;">🔗 View Event Details →</a>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def unique_key(label: str, *parts: str) -> str:
    h = hashlib.sha1(("||".join([label] + [p or "" for p in parts])).encode("utf-8")).hexdigest()[:10]
    return f"{label}-{h}"
