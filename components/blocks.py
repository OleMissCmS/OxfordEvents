from __future__ import annotations
import streamlit as st
from typing import Dict, Any, Optional
from dateutil import parser as dtp
import hashlib, base64
from pathlib import Path

# Fresh new color scheme - Teal & Coral
PRIMARY = "#14B8A6"  # Teal
SECONDARY = "#F97316"  # Coral/Orange
ACCENT = "#8B5CF6"  # Purple
SUCCESS = "#10B981"  # Green
NAVY = "#1E293B"  # Dark slate
LIGHT_BG = "#F8FAFC"  # Very light gray
DARK_TEXT = "#0F172A"  # Dark slate
MEDIUM_TEXT = "#64748B"  # Medium gray
VERSION = "v5.2.0"

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
    """Clean, simple hero section"""
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

* {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    color: {DARK_TEXT};
}}

.stApp {{
    background: {LIGHT_BG};
}}

.main .block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}}

/* Simple top accent bar */
.stApp > header {{
    background: linear-gradient(90deg, {PRIMARY} 0%, {SECONDARY} 100%);
    height: 4px;
}}

/* Clean header style */
.hero-header {{
    margin-bottom: 2rem;
    padding: 0;
}}

.hero-title {{
    font-size: 2.25rem;
    font-weight: 700;
    color: {DARK_TEXT};
    margin: 0.5rem 0 0.25rem 0;
    line-height: 1.2;
}}

.hero-subtitle {{
    font-size: 1rem;
    color: {MEDIUM_TEXT};
    margin: 0 0 1.5rem 0;
    font-weight: 400;
}}

.version-badge {{
    display: inline-block;
    font-size: 0.75rem;
    color: {MEDIUM_TEXT};
    margin-left: 0.5rem;
}}

/* Event cards */
.event-card-container {{
    background: white;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
}}

.event-card-container:hover {{
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    border-color: {PRIMARY};
}}

.event-title {{
    font-size: 1.35rem;
    font-weight: 600;
    color: {DARK_TEXT};
    margin: 0 0 0.75rem 0;
    line-height: 1.3;
}}

/* Buttons styling */
.stButton > button {{
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}}

/* Quick filter container */
.quick-filter-box {{
    background: white;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    border: 1px solid #E2E8F0;
}}

/* Mobile responsive */
@media (max-width: 768px) {{
    .hero-title {{
        font-size: 1.75rem;
    }}
    
    .main .block-container {{
        padding-left: 1rem;
        padding-right: 1rem;
    }}
    
    .event-card-container {{
        padding: 1rem;
    }}
}}

/* Sidebar styling */
[data-testid="stSidebar"] {{
    background: white;
}}

.css-1d391kg {{
    background: white;
}}

/* Badge improvements */
.badge {{
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
}}
</style>

<div class="hero-header">
  <h1 class="hero-title">Upcoming in Oxford <span class="version-badge">{VERSION}</span></h1>
  <p class="hero-subtitle">{subtitle or "What's happening in Oxford?"}</p>
</div>
""", unsafe_allow_html=True)

def _badge(text: str, bg: str, fg: str = "white"):
    st.markdown(f'<span class="badge" style="background:{bg};color:{fg};">{text}</span>', unsafe_allow_html=True)

def event_badges(ev: Dict[str, Any]):
    cost = (ev.get("cost") or "").lower()
    if "free" in cost or cost == "—" or cost == "":
        _badge("FREE", SUCCESS)
    elif cost:
        _badge("PAID", SECONDARY)
    descr = (ev.get("description") or "").lower()
    title = (ev.get("title") or "").lower()
    if any(k in (title + " " + descr) for k in ["family", "kids", "children", "story time", "storytime"]):
        _badge("Family", ACCENT)
    src = ev.get("source") or ""
    if src:
        _badge(src, "#CBD5E1", NAVY)

def event_card(ev: Dict[str, Any], idx: int) -> None:
    when = None
    try:
        when = dtp.parse(ev.get("start_iso","")).strftime("%a %b %d, %I:%M %p")
    except Exception:
        pass
    category = ev.get("category") or "Uncategorized"
    desc = _clamp(ev.get("description"))
    
    # Clean card design
    st.markdown('<div class="event-card-container">', unsafe_allow_html=True)
    
    # Title
    st.markdown(f'<h3 class="event-title">{ev.get("title","Event")}</h3>', unsafe_allow_html=True)
    
    # Badges
    event_badges(ev)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Info in clean layout
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**📅 When:** {when or 'TBA'}")
        st.markdown(f"**📍 Where:** {ev.get('location') or 'TBA'}")
    with col2:
        st.markdown(f"**💰 Cost:** {ev.get('cost') or '—'}")
        st.markdown(f"**🏷️ Category:** {category}")
    
    if desc:
        st.markdown(f"<p style='margin-top:1rem;color:{MEDIUM_TEXT};line-height:1.6;'>{desc}</p>", unsafe_allow_html=True)
    
    link = ev.get("link")
    if link:
        st.markdown(f'<a href="{link}" target="_blank" style="color:{PRIMARY};text-decoration:none;font-weight:600;margin-top:0.75rem;display:inline-block;">🔗 View Event Details →</a>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def unique_key(label: str, *parts: str) -> str:
    h = hashlib.sha1(("||".join([label] + [p or "" for p in parts])).encode("utf-8")).hexdigest()[:10]
    return f"{label}-{h}"
