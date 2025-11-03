"""
Process and store location images
Crops images to event image size (400x150px) centered, and stores them locally
"""

import os
from PIL import Image
from typing import Dict, Optional
import re

# Event image dimensions
EVENT_IMAGE_WIDTH = 400
EVENT_IMAGE_HEIGHT = 150

# Use persistent disk storage if available
try:
    from utils.storage import get_images_dir, get_database_dir
    IMAGES_DIR = get_images_dir()
    DB_DIR = get_database_dir()
except Exception:
    DB_DIR = "data"
    IMAGES_DIR = os.path.join("static", "images", "cache")
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)


def normalize_location_name(filename: str) -> str:
    """
    Convert filename to normalized location name for matching
    Examples:
    - "Bryant_Hall.jpg" -> "bryant hall"
    - "Robert_C_Khayat_Law_Center.png" -> "robert c khayat law center"
    """
    # Remove extension
    name = os.path.splitext(filename)[0]
    # Replace underscores and hyphens with spaces
    name = re.sub(r'[_\-\+]', ' ', name)
    # Normalize whitespace
    name = ' '.join(name.split())
    return name.lower().strip()


def crop_and_center_image(input_path: str, output_path: str, 
                         width: int = EVENT_IMAGE_WIDTH, 
                         height: int = EVENT_IMAGE_HEIGHT) -> bool:
    """
    Crop and center an image to the specified dimensions
    
    Args:
        input_path: Path to source image
        output_path: Path to save cropped image
        width: Target width (default 400px)
        height: Target height (default 150px)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open image
        img = Image.open(input_path)
        
        # Convert to RGB if necessary (handles RGBA, P, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get original dimensions
        orig_width, orig_height = img.size
        
        # Calculate aspect ratios
        target_aspect = width / height
        orig_aspect = orig_width / orig_height
        
        # Calculate crop box (centered)
        if orig_aspect > target_aspect:
            # Image is wider - crop width
            new_width = int(orig_height * target_aspect)
            left = (orig_width - new_width) // 2
            top = 0
            right = left + new_width
            bottom = orig_height
        else:
            # Image is taller - crop height
            new_height = int(orig_width / target_aspect)
            left = 0
            top = (orig_height - new_height) // 2
            right = orig_width
            bottom = top + new_height
        
        # Crop to center
        img_cropped = img.crop((left, top, right, bottom))
        
        # Resize to target dimensions
        img_resized = img_cropped.resize((width, height), Image.Resampling.LANCZOS)
        
        # Save
        img_resized.save(output_path, 'JPEG', quality=85, optimize=True)
        print(f"[process_location_images] Processed: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"[process_location_images] Error processing {input_path}: {e}")
        return False


def process_images_from_directory(source_dir: str = "location_images") -> Dict[str, str]:
    """
    Process all images from a source directory
    
    Args:
        source_dir: Directory containing location images (relative to project root)
    
    Returns:
        Dictionary mapping normalized location names to processed image paths
    """
    processed = {}
    
    if not os.path.exists(source_dir):
        print(f"[process_location_images] Source directory not found: {source_dir}")
        print(f"[process_location_images] Please create '{source_dir}' directory and add your location images there")
        return processed
    
    # Supported image extensions
    extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Find all image files
    image_files = []
    for filename in os.listdir(source_dir):
        if any(filename.lower().endswith(ext) for ext in extensions):
            image_files.append(filename)
    
    if not image_files:
        print(f"[process_location_images] No image files found in {source_dir}")
        return processed
    
    print(f"[process_location_images] Found {len(image_files)} image files")
    
    # Process each image
    for filename in image_files:
        input_path = os.path.join(source_dir, filename)
        
        # Normalize location name from filename
        location_name = normalize_location_name(filename)
        
        # Create output filename (normalized)
        output_filename = location_name.replace(' ', '_') + '.jpg'
        output_path = os.path.join(IMAGES_DIR, output_filename)
        
        # Crop and save
        if crop_and_center_image(input_path, output_path):
            # Store path relative to static/images/cache for web serving
            web_path = f"/static/images/cache/{output_filename}"
            processed[location_name] = web_path
            print(f"[process_location_images] Mapped '{location_name}' -> {web_path}")
    
    return processed


def store_processed_images_in_database(processed_images: Dict[str, str]) -> None:
    """
    Store processed images in the database
    
    Args:
        processed_images: Dictionary mapping location names to image paths
    """
    if not processed_images:
        print("[process_location_images] No images to store in database")
        return
    
    try:
        from lib.database import get_session, VenueImage
        session = get_session()
        
        stored_count = 0
        for location_name, image_path in processed_images.items():
            try:
                venue_image = VenueImage(
                    venue_name=location_name,
                    image_url=image_path,
                    source='uploaded'
                )
                session.merge(venue_image)  # Use merge to update if exists
                stored_count += 1
            except Exception as e:
                print(f"[process_location_images] Error storing {location_name}: {e}")
        
        session.commit()
        session.close()
        print(f"[process_location_images] Stored {stored_count} images in database")
    except Exception as e:
        print(f"[process_location_images] Database error: {e}")
        # Fallback to JSON
        try:
            import json
            from utils.image_database import load_database, save_database, VENUE_IMAGES_DB
            db = load_database(VENUE_IMAGES_DB)
            for location_name, image_path in processed_images.items():
                db[location_name] = {
                    'image_url': image_path,
                    'source': 'uploaded'
                }
            save_database(VENUE_IMAGES_DB, db)
            print(f"[process_location_images] Stored {len(processed_images)} images in JSON fallback")
        except Exception as e2:
            print(f"[process_location_images] JSON fallback error: {e2}")


def process_all_location_images(source_dir: str = "location_images") -> None:
    """
    Main function to process all location images from a directory
    
    Args:
        source_dir: Directory containing location images (relative to project root)
    """
    print(f"[process_location_images] Starting image processing from '{source_dir}'...")
    
    # Process images
    processed = process_images_from_directory(source_dir)
    
    if processed:
        # Store in database
        store_processed_images_in_database(processed)
        print(f"[process_location_images] ✅ Successfully processed {len(processed)} location images")
    else:
        print(f"[process_location_images] ⚠️ No images were processed")


if __name__ == "__main__":
    # Run if called directly
    import sys
    source_dir = sys.argv[1] if len(sys.argv) > 1 else "location_images"
    process_all_location_images(source_dir)

