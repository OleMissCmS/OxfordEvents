"""
Storage utilities for persistent disk on Render
Automatically detects and uses persistent disk if available
"""

import os
import shutil


def get_storage_base_path():
    """
    Get base path for persistent storage.
    Tries Render persistent disk first, falls back to local data/ directory.
    """
    # Render Persistent Disk paths (common mount points)
    persistent_paths = [
        '/opt/render/project/src/persistent',
        '/persistent',
        '/opt/render/project/persistent',
        os.path.join(os.getcwd(), 'persistent'),
    ]
    
    # Check if any persistent disk is mounted
    for path in persistent_paths:
        if os.path.exists(path) and os.path.isdir(path):
            # Verify it's writable (persistent disk should be)
            if os.access(path, os.W_OK):
                return path
    
    # Fallback to local data directory for development
    local_path = 'data'
    os.makedirs(local_path, exist_ok=True)
    return local_path


def get_images_dir():
    """Get directory for cached images"""
    base = get_storage_base_path()
    
    # Use persistent disk structure or local static/images/cache
    if 'persistent' in base.lower() or base == 'data':
        # On persistent disk or local dev: use persistent/images/cache
        images_dir = os.path.join(base, 'images', 'cache')
    else:
        # Fallback to static/images/cache
        images_dir = os.path.join('static', 'images', 'cache')
    
    os.makedirs(images_dir, exist_ok=True)
    return images_dir


def get_database_dir():
    """Get directory for database files"""
    base = get_storage_base_path()

    if 'persistent' in base.lower():
        # On persistent disk: use persistent/data
        db_dir = os.path.join(base, 'data')
    elif base == 'data':
        # Local dev: use data/ directly (not data/data)
        db_dir = 'data'
    else:
        # Fallback to local data/
        db_dir = 'data'

    os.makedirs(db_dir, exist_ok=True)
    return db_dir


def get_sqlite_db_path():
    """Get path for SQLite database"""
    db_dir = get_database_dir()
    return os.path.join(db_dir, 'oxford_events.db')


def get_json_db_path(filename: str):
    """Get path for JSON database files (fallback)"""
    db_dir = get_database_dir()
    return os.path.join(db_dir, filename)


def is_persistent_disk():
    """Check if running on Render persistent disk"""
    base = get_storage_base_path()
    return 'persistent' in base.lower() or os.path.exists('/opt/render/project/src/persistent')


def log_storage_setup():
    """Log current storage configuration"""
    base = get_storage_base_path()
    images_dir = get_images_dir()
    db_dir = get_database_dir()
    is_persistent = is_persistent_disk()
    
    print(f"[Storage] Base path: {base}")
    print(f"[Storage] Images dir: {images_dir}")
    print(f"[Storage] Database dir: {db_dir}")
    print(f"[Storage] Persistent disk: {'✅ Enabled' if is_persistent else '❌ Using local filesystem'}")

