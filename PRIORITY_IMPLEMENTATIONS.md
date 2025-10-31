# Priority Implementation Plan

## Phase 1: Quick Wins (High Impact, Low Effort)

### 1. Quick Date Filter Chips ⚡
**Impact**: High - Users frequently want "today" or "this week"
**Effort**: Low - Add buttons to sidebar

```python
# Add to sidebar after date inputs
st.markdown("**Quick filters**")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Today", use_container_width=True):
        today = date.today()
        st.session_state["date_min"] = today
        st.session_state["date_max"] = today
        st.rerun()
with col2:
    if st.button("This Week", use_container_width=True):
        today = date.today()
        st.session_state["date_min"] = today
        st.session_state["date_max"] = today + timedelta(days=6)
        st.rerun()
with col3:
    if st.button("This Month", use_container_width=True):
        today = date.today()
        st.session_state["date_min"] = today
        st.session_state["date_max"] = today + timedelta(days=30)
        st.rerun()
with col4:
    if st.button("Next 7 Days", use_container_width=True):
        today = date.today()
        st.session_state["date_min"] = today
        st.session_state["date_max"] = today + timedelta(days=7)
        st.rerun()
```

### 2. Event Count Badges 📊
**Impact**: Medium - Helps users understand filter results
**Effort**: Low - Add counts to filter labels

```python
# Update category multiselect
category_counts = Counter((e.get("category") or "Uncategorized") for e in sel0)
options_with_counts = [f"{cat} ({category_counts.get(cat, 0)})" for cat in all_categories]
# Parse back the category name when filtering
```

### 3. Export All Filtered Events 📥
**Impact**: High - Users want to export their filtered view
**Effort**: Medium - Add export button

```python
# Add after event list
if st.button("📥 Export All Filtered Events (.ics)", use_container_width=True):
    ics_content = []
    ics_content.append("BEGIN:VCALENDAR")
    ics_content.append("VERSION:2.0")
    ics_content.append("PRODID:-//OxfordEvents//EN")
    
    for ev in sel:
        ics_content.append("BEGIN:VEVENT")
        ics_content.append(f"SUMMARY:{ev.get('title', 'Event')}")
        # ... build full .ics
        ics_content.append("END:VEVENT")
    
    ics_content.append("END:VCALENDAR")
    st.download_button(
        "Download All Events",
        data="\r\n".join(ics_content),
        file_name=f"oxford_events_{date.today().strftime('%Y%m%d')}.ics",
        mime="text/calendar"
    )
```

### 4. Better Empty States 💬
**Impact**: Medium - Better UX when no results
**Effort**: Low - Add conditional message

```python
if len(sel) == 0:
    st.info("🎭 No events match your filters. Try:")
    st.markdown("- Adjusting date range")
    st.markdown("- Clearing category filters")
    st.markdown("- Checking different source groups")
    if st.button("Reset All Filters"):
        st.session_state["categories_selected"] = all_categories
        st.session_state["groups_selected"] = sorted(groups)
        st.session_state["date_min"] = today
        st.session_state["date_max"] = today + timedelta(days=21)
        st.rerun()
```

### 5. Shareable URLs 🔗
**Impact**: High - Users want to share filtered views
**Effort**: Medium - Use Streamlit query params

```python
# At top of app
import urllib.parse

# Read from URL params
params = st.query_params
if "categories" in params:
    st.session_state["categories_selected"] = params["categories"].split(",")

# Generate shareable URL
share_url = f"{st.get_option('server.headless')}/?categories={','.join(st.session_state['categories_selected'])}"
if st.button("🔗 Copy Shareable Link"):
    st.code(share_url)
```

## Phase 2: Enhanced Features (Medium Effort)

### 6. Statistics Dashboard 📈
**Impact**: High - Users love insights
**Effort**: Medium - Add statistics section

```python
with st.expander("📊 Event Statistics", expanded=False):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Events", len(sel))
    with col2:
        st.metric("This Week", len([e for e in sel if _is_this_week(e)]))
    with col3:
        st.metric("Free Events", len([e for e in sel if "free" in (e.get("cost") or "").lower()]))
    with col4:
        st.metric("Top Category", max(Counter([e.get("category") for e in sel]).items(), key=lambda x: x[1])[0] if sel else "N/A")
    
    # Category distribution chart
    import plotly.express as px
    cat_counts = Counter([e.get("category") or "Uncategorized" for e in sel])
    fig = px.pie(values=list(cat_counts.values()), names=list(cat_counts.keys()), 
                 title="Events by Category")
    st.plotly_chart(fig, use_container_width=True)
```

### 7. Calendar View 📅
**Impact**: High - Visual calendar is intuitive
**Effort**: High - Requires custom component or complex layout

### 8. Social Sharing Buttons 📱
**Impact**: Medium - Helps with discovery
**Effort**: Low - Add share buttons

```python
def share_buttons(event_title, event_link):
    encoded_title = urllib.parse.quote(event_title)
    encoded_link = urllib.parse.quote(event_link or "")
    
    twitter_url = f"https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_link}"
    facebook_url = f"https://www.facebook.com/sharer/sharer.php?u={encoded_link}"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button("🐦 Twitter", twitter_url)
    with col2:
        st.link_button("📘 Facebook", facebook_url)
    with col3:
        if st.button("📋 Copy Link", use_container_width=True):
            st.session_state["copied"] = True
            st.success("Link copied!")
```

## Phase 3: Advanced Features (Higher Effort)

### 9. Event Details Modal
Requires Streamlit components or custom HTML/CSS

### 10. Favorites/Bookmarks
Requires persistent storage (database or file)

### 11. Email Notifications
Requires backend service or third-party integration

## Recommended Order of Implementation

1. ✅ Quick Date Filter Chips (15 min)
2. ✅ Better Empty States (10 min)
3. ✅ Export All Filtered Events (30 min)
4. ✅ Event Count Badges (20 min)
5. ✅ Statistics Dashboard (1 hour)
6. ✅ Shareable URLs (45 min)
7. ✅ Social Sharing Buttons (30 min)
8. ⏳ Calendar View (4-6 hours)
9. ⏳ Event Details Modal (2-3 hours)
10. ⏳ Favorites System (3-4 hours)

