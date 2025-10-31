"""
Event card rendering components
"""

import io
import streamlit as st
from dateutil import parser as dtp
from typing import Dict, Any
from utils.image_processing import get_event_image


def render_event_card(event: Dict[str, Any], debug_mode: bool = False) -> None:
    """Render a single event card in Bandsintown style."""
    with st.container():
        st.markdown('<div class="event-card">', unsafe_allow_html=True)
        
        # Event image
        _img, error = get_event_image(event)
        if error:
            if debug_mode:
                st.warning(f"Image error: {error}")
            # Use placeholder if image generation failed
            _img = "https://placehold.co/400x250/f8f9fa/6C757D?text=Event"
        
        # Render image (handle both URL strings and BytesIO buffers)
        if _img:
            try:
                if isinstance(_img, io.BytesIO):
                    _img.seek(0)
                    st.image(_img, use_container_width=True)
                else:
                    st.image(_img, use_container_width=True)
            except Exception as e:
                if debug_mode:
                    st.error(f"Failed to load image: {e}")
                # Fallback to HTML img tag
                if isinstance(_img, str):
                    st.markdown(f'<img src="{_img}" class="event-image" alt="Event image" />', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="event-image"></div>', unsafe_allow_html=True)
        else:
            # No image available
            st.markdown('<div class="event-image"></div>', unsafe_allow_html=True)
        
        # Card content
        st.markdown('<div style="padding: 1rem;">', unsafe_allow_html=True)
        
        # Format date
        try:
            event_date = dtp.parse(event["start_iso"]).strftime("%a, %b %d")
            event_time = dtp.parse(event["start_iso"]).strftime("%I:%M %p")
        except:
            event_date = "TBA"
            event_time = ""
        
        # Date with calendar icon
        date_display = event_date.upper() if event_date != "TBA" else "TBA"
        calendar_svg = '<svg class="calendar-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
        st.markdown(f'<div class="event-date-pill">{calendar_svg} {date_display} {event_time}</div>', unsafe_allow_html=True)
        
        # Title as link
        title = event.get("title") or "Event"
        link = event.get("link")
        if link:
            st.markdown(f'<a href="{link}" style="text-decoration: none; color: inherit;"><h3 class="event-title">{title}</h3></a>', unsafe_allow_html=True)
        else:
            st.markdown(f'<h3 class="event-title">{title}</h3>', unsafe_allow_html=True)
        
        # Venue
        location = event.get("location", "")
        if location:
            st.markdown(f'<div class="event-venue">{location}</div>', unsafe_allow_html=True)
        
        # Meta info (time, cost, category)
        meta_parts = []
        if event_time:
            meta_parts.append(event_time)
        cost = event.get("cost", "")
        if cost and cost != "Free":
            meta_parts.append(cost)
        category = event.get("category", "")
        if category:
            meta_parts.append(category)
        
        if meta_parts:
            meta_text = " • ".join(meta_parts)
            st.markdown(f'<div class="event-meta">{meta_text}</div>', unsafe_allow_html=True)
        
        # Tickets/Details button
        if link:
            st.link_button("Tickets", link, use_container_width=True)
        else:
            st.button("Details", key=f"event_{event.get('title', '')}", use_container_width=True, disabled=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close padding
        st.markdown('</div>', unsafe_allow_html=True)  # Close event-card

