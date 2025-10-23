from __future__ import annotations
import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
from dateutil import parser as dtp

def hero():
    st.markdown(
        """
        <div style="padding:1rem 1.2rem;border-radius:16px;background:linear-gradient(90deg,#0C2340, #163b6a);color:white">
          <h1 style="margin:0">Upcoming in Oxford</h1>
          <p style="margin-top:.5rem;opacity:.95">A consolidated view of events around Oxford & Ole Miss — updated when you open the page.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def event_card(ev: Dict[str, Any]):
    when = None
    try:
        when = dtp.parse(ev["start_iso"]).strftime("%a %b %d, %I:%M %p")
    except Exception:
        pass

    with st.container(border=True):
        st.subheader(ev["title"])
        cols = st.columns([1,1,1,1])
        cols[0].markdown(f"**When:** {when or 'TBA'}")
        cols[1].markdown(f"**Where:** {ev.get('location') or 'TBA'}")
        cols[2].markdown(f"**Cost:** {ev.get('cost') or '—'}")
        cols[3].markdown(f"**Source:** {ev.get('source') or ''}")
        if ev.get("link"):
            st.markdown(f"[Event link]({ev['link']})")