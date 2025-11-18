# Fallback Images Directory

This directory contains fallback images used when events don't have images from APIs.

## Required Images

### Category Images

- `music.jpg` - For Music events
- `sports.jpg` - For Sports events (non-Ole Miss Athletics)
- `arts-culture.jpg` - For Arts & Culture and Arts events
- `Community1.webp` - For Community events (alternates with Community2)
- `Community2.jpg` - For Community events (alternates with Community1)
- `performance.jpg` - For Performance events
- `education.jpg` - For Education events
- `university.jpg` - For University events
- `default.jpg` - Default fallback for any category not listed above

### Venue-Specific Images

- `Proud_Larrys.jpg` - For events at Proud Larry's venue
- `Pavilion.webp` - Background for Ole Miss Basketball games (used with logo overlay)
- `Swayze.jpg` - Background for Ole Miss Baseball games (used with logo overlay)
- `Vaught.jpg` - Background for Ole Miss Football games (used with logo overlay)

## Image Specifications

- **Format**: JPG, JPEG, PNG, or WEBP
- **Recommended size**: 400x250 pixels (or similar 16:10 aspect ratio)
- **File size**: Keep under 5MB for fast loading (webp files are typically smaller)

## How It Works

### Priority Order

1. **API Images** - Images from SeatGeek, Ticketmaster, or Bandsintown APIs (highest priority)
2. **Sports Matchup Images** - For sports events:
   - **Ole Miss Athletics**: Venue background image (Pavilion/Swayze/Vaught) with team logos overlaid at 60% opacity
   - **Other Sports**: Standard matchup image with team logos
3. **Venue-Specific Images** - Proud Larry's events use `Proud_Larrys.jpg`
4. **Category Images** - Fallback based on event category:
   - **Community**: Alternates between `Community1.jpg` and `Community2.jpg` (deterministic based on event title)
   - **University**: Uses `university.jpg`
   - **Other categories**: Use their respective category images

### Special Features

- **Community Events**: Automatically alternates between Community1 and Community2 images based on event title hash (same event always gets same image)
- **Ole Miss Athletics**: Venue images are used as semi-transparent backgrounds (60% opacity) with team logos overlaid on top

