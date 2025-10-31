"""
Filter UI components
"""

import json
import streamlit as st
from typing import List, Tuple


def render_filter_chips(
    date_filters: List[Tuple[str, str]],
    category_options: List[str],
    current_date_filter: str,
    current_cat_filter: str
) -> None:
    """Render filter chips in Bandsintown style."""
    st.markdown('<div class="filter-chips filter-chips-container">', unsafe_allow_html=True)
    
    # Date filter chips
    for label, value in date_filters:
        st.button(label, key=f"date_{value}", on_click=_set_date_filter, args=(value,))
    
    # Separator
    st.markdown('<span style="margin: 0 0.5rem; color: #6C757D; font-size: 0.875rem;">|</span>', unsafe_allow_html=True)
    
    # Category filter chips
    for cat in category_options:
        st.button(cat, key=f"cat_{cat}", on_click=_set_category_filter, args=(cat,))
    
    # Search
    search = st.text_input("Search", placeholder="Search events...", key="search", label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # JavaScript to set active state
    _render_filter_active_states(date_filters, category_options, current_date_filter, current_cat_filter)


def _set_date_filter(value):
    """Callback for date filter."""
    st.session_state["date_filter"] = value
    st.rerun()


def _set_category_filter(value):
    """Callback for category filter."""
    st.session_state["category_filter"] = value
    st.rerun()


def _render_filter_active_states(
    date_filters: List[Tuple[str, str]],
    category_options: List[str],
    current_date_filter: str,
    current_cat_filter: str
) -> None:
    """Render JavaScript to set active filter states."""
    date_label_map = {v: l for l, v in date_filters}
    active_date_label = date_label_map.get(current_date_filter, "All Dates")
    
    st.markdown(f"""
    <script>
    (function() {{
        setTimeout(function() {{
            const filterContainer = document.querySelector('.filter-chips-container');
            if (!filterContainer) return;
            
            const buttons = filterContainer.querySelectorAll('.stButton button');
            buttons.forEach(btn => {{
                const btnText = btn.textContent.trim();
                const stBtn = btn.closest('.stButton');
                
                // Check if this is an active date filter button
                if ({json.dumps([l for l, _ in date_filters])}.includes(btnText)) {{
                    if (btnText === '{active_date_label}') {{
                        stBtn.setAttribute('data-active', 'true');
                    }} else {{
                        stBtn.setAttribute('data-active', 'false');
                    }}
                }}
                // Check if this is an active category filter button
                else if ({json.dumps(category_options)}.includes(btnText)) {{
                    if (btnText === '{current_cat_filter}') {{
                        stBtn.setAttribute('data-active', 'true');
                    }} else {{
                        stBtn.setAttribute('data-active', 'false');
                    }}
                }}
            }});
        }}, 200);
    }})();
    </script>
    """, unsafe_allow_html=True)

