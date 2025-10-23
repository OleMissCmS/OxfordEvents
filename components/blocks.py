from __future__ import annotations
import streamlit as st
from typing import Dict, Any
from dateutil import parser as dtp

def hero(subtitle: str | None = None):
    st.markdown(f"""
<div style="padding:1rem 1.2rem;border-radius:16px;background:linear-gradient(90deg,#0C2340,#163b6a);color:white">
  <h1 style="margin:0">Upcoming in Oxford</h1>
  <p style="margin-top:.5rem;opacity:.95">{subtitle or "What's happening, Oxford?"}</p>
</div>
""", unsafe_allow_html=True)

def event_card(ev: Dict[str, Any]) -> None:
    when = None
    try:
        when = dtp.parse(ev.get("start_iso","")).strftime("%a %b %d, %I:%M %p")
    except Exception:
        pass

    with st.container(border=True):
        st.subheader(ev.get("title","Event"))
        st.markdown(
            f"**When:** {when or 'TBA'}  \n"
            f"**Where:** {ev.get('location') or 'TBA'}  \n"
            f"**Cost:** {ev.get('cost') or '—'}  \n"
            f"**Source:** {ev.get('source') or ''}"
        )
        desc = ev.get("description")
        if desc:
            st.markdown(desc)
        link = ev.get("link")
        if link:
            st.markdown(f"[Event link]({link})")