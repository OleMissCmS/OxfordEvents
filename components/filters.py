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
        color_scheme = CATEGORY_COLORS.get(cat, {"bg": "#f5f5f5", "text": "#666666", "border": "#dddddd"})
        st.button(cat, key=f"cat_{cat}", on_click=_set_category_filter, args=(cat,))
    
    # Search
    search = st.text_input("Search", placeholder="Search events...", key="search", label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # JavaScript to set active state and colors
    _render_filter_active_states(category_options, current_cat_filter)


def _set_category_filter(value):
    """Callback for category filter."""
    st.session_state["category_filter"] = value
    st.rerun()


def _render_filter_active_states(
    category_options: List[str],
    current_cat_filter: str
) -> None:
    """Render JavaScript to set active filter states and apply pastel colors."""
    category_colors_json = json.dumps(CATEGORY_COLORS)
    
    st.markdown(f"""
    <script>
    (function() {{
        setTimeout(function() {{
            const filterContainer = document.querySelector('.filter-chips-container');
            if (!filterContainer) return;
            
            const colors = {category_colors_json};
            const buttons = filterContainer.querySelectorAll('.stButton button');
            
            buttons.forEach(btn => {{
                const btnText = btn.textContent.trim();
                const stBtn = btn.closest('.stButton');
                
                // Check if this is a category filter button
                if ({json.dumps(category_options)}.includes(btnText)) {{
                    const colorScheme = colors[btnText] || {{bg: "#f5f5f5", text: "#666666", border: "#dddddd"}};
                    
                    if (btnText === '{current_cat_filter}') {{
                        // Active state - filled background
                        stBtn.setAttribute('data-active', 'true');
                        btn.style.backgroundColor = colorScheme.bg + ' !important';
                        btn.style.color = colorScheme.text + ' !important';
                        btn.style.borderColor = colorScheme.border + ' !important';
                    }} else {{
                        // Inactive state - border only
                        stBtn.setAttribute('data-active', 'false');
                        btn.style.backgroundColor = 'transparent !important';
                        btn.style.color = colorScheme.text + ' !important';
                        btn.style.borderColor = colorScheme.border + ' !important';
                    }}
                }}
            }});
        }}, 200);
    }})();
    </script>
    """, unsafe_allow_html=True)
