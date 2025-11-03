# Location Images Setup Guide

## Overview

This guide explains how to add and process location images for the Oxford Events site.

## Step 1: Add Your Images

1. Create a `location_images` directory in the project root (already created if you see this)
2. Place your location images in that directory
3. Name them to match the location names (spaces, underscores, or hyphens are OK)

### Example filenames:
- `Bryant Hall.jpg`
- `Robert_C_Khayat_Law_Center.png`
- `Ole Miss Student Union.jpg`
- `Turner Center.jpeg`
- `Gertrude_C_Ford_Center.jpg`
- `Coulter Hall.png`
- `David_H_Nutt_Auditorium.jpg`
- `Cat Fish Row Museum.jpg`
- `Proud Larry's.jpg`
- etc.

## Step 2: Process the Images

Run the image processing script:

```bash
python utils/process_location_images.py
```

Or specify a custom directory:

```bash
python utils/process_location_images.py "my_images"
```

## What the Script Does

1. **Normalizes location names** from filenames
   - Removes file extensions
   - Converts underscores/hyphens to spaces
   - Lowercases the name
   - Example: `Robert_C_Khayat_Law_Center.png` → `"robert c khayat law center"`

2. **Crops and centers** each image
   - Resizes to 400x150px (event image size)
   - Maintains aspect ratio while cropping
   - Centers the crop on the original image
   - Saves as JPEG with 85% quality

3. **Stores processed images**
   - Saves to `static/images/cache/` (or persistent disk if available)
   - Updates the `VenueImage` database table
   - Creates web-accessible paths like `/static/images/cache/bryant_hall.jpg`

4. **Maps locations** to images
   - Associates normalized location names with image paths
   - When an event has a matching location, the image will be used automatically

## Example Usage

```python
from utils.process_location_images import process_all_location_images

# Process images from default 'location_images' directory
process_all_location_images()

# Or from a custom directory
process_all_location_images("my_custom_folder")
```

## Location Name Matching

The system matches locations using normalized names. Examples:

- Event location: `"Bryant Hall"` → matches image: `bryant_hall.jpg` or `Bryant Hall.png`
- Event location: `"Robert C. Khayat Law Center"` → matches: `robert_c_khayat_law_center.jpg`
- Event location: `"Ole Miss Student Union"` → matches: `ole_miss_student_union.jpg`

The matching is case-insensitive and ignores punctuation.

## Troubleshooting

- **Images not showing?** Check that:
  1. Images were processed successfully
  2. Location names in events match the normalized image names
  3. Database was updated (check with `lib.database` tools)

- **Wrong crop?** The script crops to center. If you need a different crop, edit the source image before processing.

- **Multiple images for same location?** The database uses merge, so the last processed image will be used.

