"""
Filter UI components
"""

import json
import streamlit as st
from typing import List


# Category color mapping with gradient order (light to darker)
CATEGORY_COLORS = {
    "All": {"bg": "#e3f2fd", "text": "#1976d2", "border": "#90caf9"},
    "Music": {"bg": "#f3e5f5", "text": "#7b1fa2", "border": "#ce93d8"},
    "Arts & Culture": {"bg": "#fff3e0", "text": "#e65100", "border": "#ffb74d"},
    "Community": {"bg": "#e8f5e9", "text": "#388e3c", "border": "#81c784"},
    "Sports": {"bg": "#fce4ec", "text": "#c2185b", "border": "#f48fb1"},
    "Arts": {"bg": "#fff3e0", "text": "#e65100", "border": "#ffb74d"},
}


def render_filter_chips(
    category_options: List[str],
    current_cat_filter: str
) -> None:
    """Render category filter chips as pill-shaped buttons with pastel colors."""
    
    st.markdown('<div class="filter-chips filter-chips-container">', unsafe_allow_html=True)
    
    # Category filter chips
    for cat in category_options:
        st.button(cat, key=f"cat_{cat}", on_click=_set_category_filter, args=(cat,))
    
    # Search
    search = st.text_input("Search", placeholder="Search events...", key="search", label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # JavaScript to set active state and apply colors
    # Temporarily disabled for debugging
    # _render_filter_active_states(category_options, current_cat_filter)


def _set_category_filter(value):
    """Callback for category filter."""
    st.session_state["category_filter"] = value
    st.rerun()


def _render_filter_active_states(
    category_options: List[str],
    current_cat_filter: str
) -> None:
    """Render JavaScript to set active filter states and apply colors."""
    # Create color map for JavaScript
    color_map = json.dumps({cat: CATEGORY_COLORS.get(cat, {"bg": "#f5f5f5", "text": "#666666", "border": "#dddddd"}) for cat in category_options})
    
    st.markdown(f"""
    <script>
    (function() {{
        setTimeout(function() {{
            const filterContainer = document.querySelector('.filter-chips-container');
            if (!filterContainer) return;
            
            const buttons = filterContainer.querySelectorAll('.stButton button');
            const colorMap = {color_map};
            
            buttons.forEach(btn => {{
                const btnText = btn.textContent.trim();
                
                // Check if this is a category filter button
                if ({json.dumps(category_options)}.includes(btnText)) {{
                    const colors = colorMap[btnText] || {json.dumps({"bg": "#f5f5f5", "text": "#666666", "border": "#dddddd"})};
                    
                    if (btnText === '{current_cat_filter}') {{
                        // Active state: filled background
                        btn.style.setProperty('background-color', colors.bg, 'important');
                        btn.style.setProperty('color', colors.text, 'important');
                        btn.style.setProperty('border-color', colors.border, 'important');
                    }} else {{
                        // Inactive state: transparent with border
                        btn.style.setProperty('background-color', 'transparent', 'important');
                        btn.style.setProperty('color', colors.text, 'important');
                        btn.style.setProperty('border-color', colors.border, 'important');
                    }}
                }}
            }});
        }}, 1000);
    }})();
    </script>
    """, unsafe_allow_html=True)
