"""
Utility script to clear cached event images so fresh artwork can be generated.

This deletes every record from the EventImage table and removes any files under
the configured image cache directory (local static cache or persistent disk on
Render). Run it locally or on the server whenever you need to force new images.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(PROJECT_ROOT))

from lib.database import EventImage, get_session, init_database
from utils.storage import get_images_dir


def reset_event_images() -> tuple[int, int, str]:
    """Clear EventImage rows and delete cached image files."""
    init_database()
    session = get_session()
    deleted_rows = 0
    try:
        deleted_rows = session.query(EventImage).delete()
        session.commit()
    finally:
        session.close()

    images_dir = Path(get_images_dir())
    removed_files = 0
    if images_dir.exists():
        for entry in images_dir.iterdir():
            try:
                if entry.is_file() or entry.is_symlink():
                    entry.unlink()
                    removed_files += 1
                elif entry.is_dir():
                    shutil.rmtree(entry)
                    removed_files += 1
            except Exception as exc:  # pragma: no cover - log and continue
                print(f"[reset_event_images] Failed to remove {entry}: {exc}")
    return deleted_rows, removed_files, str(images_dir)


def main():
    deleted_rows, removed_files, images_dir = reset_event_images()
    print(f"Deleted {deleted_rows} EventImage rows")
    print(f"Removed {removed_files} cached files from {images_dir}")


if __name__ == "__main__":
    main()

