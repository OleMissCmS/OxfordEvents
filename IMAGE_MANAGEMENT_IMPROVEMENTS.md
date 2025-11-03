# Image Management Improvements

## Current Image System

### How It Works Now:
1. **Sports Images**: Generated on-the-fly using team logos (matchup images)
2. **Category Images**: Generated using category/title/location (smart placeholders)
3. **Venue Images**: Fetched from Wikipedia/DuckDuckGo, cached locally
4. **Team Logos**: Fetched from Wikipedia, cached in SQLite/JSON

### Current Issues:
- ❌ Images regenerated on every request (even with cache, still slow)
- ❌ No persistent link between events and their images
- ❌ Same location = same image (not unique per event)
- ❌ No way to store event-specific images
- ❌ Image URLs not stored with events

## Proposed Improvements

### Option 1: Store Image URLs in Event Database (Recommended)

**Create an `event_images` table in SQLite:**

```python
class EventImage(Base):
    __tablename__ = 'event_images'
    
    event_hash = Column(String(64), primary_key=True)  # Hash of title+date+location
    image_url = Column(String(500))  # Cached image URL
    image_type = Column(String(50))  # 'sports', 'venue', 'category', 'custom'
    created_at = Column(DateTime)
```

**Benefits:**
- ✅ One image lookup per event (fast)
- ✅ Persistently links images to events
- ✅ Can pre-generate images and store URLs
- ✅ Easy to update/replace images
- ✅ Works with SQLite (free)

**Implementation:**
1. Generate image when event is first seen
2. Store URL in database with event hash
3. Use stored URL on subsequent loads
4. Regenerate if event changes

### Option 2: Store Image Data in Event Objects

**Add `image_url` field to events:**

```python
event = {
    "title": "...",
    "image_url": "/static/images/cache/football_vs_alabama_2025-11-15.png",
    ...
}
```

**Benefits:**
- ✅ Simple - just add one field
- ✅ Images travel with events
- ✅ No separate database table needed

**Implementation:**
1. Generate image during event collection
2. Save to static/images/cache/
3. Add image_url to event dict
4. Template uses event.image_url directly

### Option 3: Pre-generate and Cache All Images

**Generate images during event collection:**

```python
def collect_all_events(sources):
    events = [...]
    
    # Pre-generate images for all events
    for event in events:
        event['image_url'] = generate_and_cache_event_image(event)
    
    return events
```

**Benefits:**
- ✅ All images ready before page load
- ✅ Fast page rendering
- ✅ Can batch process

### Option 4: Event-Image Hash Mapping

**Create unique hash for each event-image pair:**

```python
import hashlib

def get_event_image_hash(event):
    """Create unique hash for event-image mapping"""
    key = f"{event['title']}_{event['start_iso']}_{event['location']}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]

# Store: hash -> image_path
event_images[hash] = "/static/images/cache/abc123.png"
```

**Benefits:**
- ✅ Unique images per event
- ✅ Fast lookup
- ✅ Prevents image reuse issues

## Recommended Approach: Hybrid

**Combine Option 1 + Option 2:**

1. **Store image URLs in SQLite** (`event_images` table)
2. **Add `image_url` to event objects** during collection
3. **Use event hash** for unique identification
4. **Pre-generate on first load**, cache forever

### Implementation Plan:

```python
# 1. Create EventImage model
class EventImage(Base):
    event_hash = Column(String(64), primary_key=True)
    image_url = Column(String(500))
    image_type = Column(String(50))
    
# 2. Generate and store during collection
def collect_all_events(sources):
    events = [...]
    for event in events:
        event_hash = get_event_hash(event)
        # Check if image exists in DB
        cached_image = get_event_image_from_db(event_hash)
        if cached_image:
            event['image_url'] = cached_image
        else:
            # Generate new image
            image_url = generate_event_image(event)
            store_event_image_in_db(event_hash, image_url)
            event['image_url'] = image_url
    return events

# 3. Use in template
<img src="{{ event.image_url }}" alt="{{ event.title }}">
```

## Additional Improvements

### Better Image Matching:

1. **Venue Normalization**: Map "Turner Center" = "Turner Center at Ole Miss" = same image
2. **Location Aliases**: "Vaught-Hemingway Stadium" = "Vaught Hemingway" = "VHS"
3. **Team Name Variations**: "Ole Miss" = "Mississippi" = "Rebels"

### Image Priority System:

1. **Custom event image** (if provided in source)
2. **Sports matchup image** (if sports event with teams)
3. **Venue image** (if location found)
4. **Category placeholder** (fallback)

### Image Refresh Strategy:

- **Never refresh** once generated (unless event changes)
- **Hash-based caching** prevents duplicates
- **Database lookup** before generation

## Implementation Priority

1. ✅ **Filter training events** (DONE)
2. **Add EventImage database model**
3. **Store image URLs in events**
4. **Pre-generate during collection**
5. **Use stored URLs in template**

