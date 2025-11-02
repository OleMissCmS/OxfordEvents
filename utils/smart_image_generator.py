"""
Smart image generation for events without images
"""

import io
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont


def generate_category_image(category: str, title: str = "") -> Tuple[Optional[io.BytesIO], Optional[str]]:
    """
    Generate a smart placeholder image based on event category.
    Returns (BytesIO buffer or None, error_message or None).
    """
    try:
        # Image dimensions
        width, height = 400, 150
        
        # Create base image with category-specific color
        colors = {
            "Music": {"bg": "#6f42c1", "text": "#ffffff"},
            "Sports": {"bg": "#dc3545", "text": "#ffffff"},
            "Arts & Culture": {"bg": "#ffc107", "text": "#000000"},
            "Community": {"bg": "#28a745", "text": "#ffffff"},
            "Education": {"bg": "#17a2b8", "text": "#ffffff"},
            "University": {"bg": "#0056b3", "text": "#ffffff"},
        }
        
        category_colors = colors.get(category, {"bg": "#6C757D", "text": "#ffffff"})
        
        # Create image
        img = Image.new("RGB", (width, height), color=category_colors["bg"])
        draw = ImageDraw.Draw(img)
        
        # Get emoji or icon based on category
        icons = {
            "Music": "🎵",
            "Sports": "⚽",
            "Arts & Culture": "🎭",
            "Community": "🏠",
            "Education": "📚",
            "University": "🎓",
        }
        
        icon = icons.get(category, "📅")
        
        # Try to draw emoji (requires font that supports emoji)
        try:
            # Attempt to use a system font
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 80)
                except:
                    font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), icon, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the icon
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            draw.text((x, y), icon, fill=category_colors["text"], font=font)
        except:
            # Fallback: draw circle
            circle_size = min(width, height) // 3
            x = width // 2 - circle_size // 2
            y = height // 2 - circle_size // 2
            draw.ellipse([x, y, x + circle_size, y + circle_size], 
                        fill=category_colors["text"], outline="none")
        
        # Save to BytesIO
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer, None
        
    except Exception as e:
        return None, f"Exception generating category image: {str(e)}"

