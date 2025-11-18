"""
Test script for the admin reset-images endpoint.
This simulates what the endpoint does without requiring authentication.
"""
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.reset_event_images import reset_event_images

print("Testing reset_event_images function...")
try:
    deleted_rows, removed_files, images_dir = reset_event_images()
    print("SUCCESS!")
    print(f"   Deleted rows: {deleted_rows}")
    print(f"   Removed files: {removed_files}")
    print(f"   Images directory: {images_dir}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

