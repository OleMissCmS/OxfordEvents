"""
Download NCAA team logos from klunn91/team-logos repository
Creates a local cache in static/images/ncaa-logos/
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional
import re

# Base URL for raw GitHub content
BASE_URL = "https://raw.githubusercontent.com/klunn91/team-logos/master/NCAA"
REPO_API_URL = "https://api.github.com/repos/klunn91/team-logos/contents/NCAA"

# Local cache directory
CACHE_DIR = Path("static/images/ncaa-logos")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Mapping file to store name variations
MAPPING_FILE = Path("data/ncaa_team_mappings.json")


def normalize_team_name(name: str) -> str:
    """
    Normalize team name to match repository file naming conventions.
    Removes common prefixes/suffixes and standardizes format.
    """
    # Remove common prefixes
    name = re.sub(r'^(university of|univ\.? of|u\.? of)\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^(the\s+)', '', name, flags=re.IGNORECASE)
    
    # Remove common suffixes
    name = re.sub(r'\s+(university|univ\.?)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+\([^)]+\)$', '', name)  # Remove parenthetical info like "(D2)"
    
    # Clean up whitespace
    name = ' '.join(name.split())
    
    return name.strip()


def get_repo_file_list() -> List[str]:
    """Get list of all files in the NCAA directory from GitHub API"""
    try:
        response = requests.get(REPO_API_URL, timeout=30)
        if response.status_code == 200:
            files = response.json()
            # Filter for image files only
            image_files = [
                f['name'] for f in files 
                if f['type'] == 'file' and f['name'].lower().endswith(('.png', '.jpg', '.jpeg', '.svg'))
            ]
            return image_files
        else:
            print(f"Error fetching file list: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching file list: {e}")
        return []


def download_logo(filename: str) -> bool:
    """Download a single logo file"""
    url = f"{BASE_URL}/{filename}"
    local_path = CACHE_DIR / filename
    
    # Skip if already exists
    if local_path.exists():
        return True
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {filename}")
            return True
        else:
            print(f"Failed to download {filename}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False


def create_team_mapping(filename: str) -> Dict[str, str]:
    """
    Create mapping variations for a team logo filename.
    Returns a dict mapping various name forms to the filename.
    """
    # Remove extension
    base_name = filename.rsplit('.', 1)[0]
    
    # Create variations
    variations = {
        base_name.lower(): filename,
        base_name: filename,  # Original case
        normalize_team_name(base_name).lower(): filename,
    }
    
    # Add variations without "University of"
    if "university of" in base_name.lower():
        short_name = re.sub(r'university of\s+', '', base_name, flags=re.IGNORECASE).strip()
        variations[short_name.lower()] = filename
        variations[short_name] = filename
    
    # Add variations with "University of"
    if "university of" not in base_name.lower() and not base_name.lower().startswith("u "):
        long_name = f"University of {base_name}"
        variations[long_name.lower()] = filename
        variations[long_name] = filename
    
    # Handle common abbreviations (e.g., "U of Alabama" -> "Alabama")
    if base_name.lower().startswith("u "):
        short_name = base_name[2:].strip()
        variations[short_name.lower()] = filename
        variations[short_name] = filename
    
    return variations


def build_team_mappings() -> Dict[str, str]:
    """Build comprehensive team name mapping"""
    mappings = {}
    
    # Get list of files
    files = get_repo_file_list()
    print(f"Found {len(files)} logo files in repository")
    
    for filename in files:
        file_variations = create_team_mapping(filename)
        mappings.update(file_variations)
    
    return mappings


def save_mappings(mappings: Dict[str, str]):
    """Save team name mappings to JSON file"""
    os.makedirs("data", exist_ok=True)
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(mappings)} team name mappings to {MAPPING_FILE}")


def download_all_logos():
    """Download all NCAA logos and build mappings"""
    print("Fetching list of NCAA logos...")
    files = get_repo_file_list()
    
    if not files:
        print("No files found. Exiting.")
        return
    
    print(f"Found {len(files)} logo files. Downloading...")
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for filename in files:
        if download_logo(filename):
            downloaded += 1
        else:
            if (CACHE_DIR / filename).exists():
                skipped += 1
            else:
                failed += 1
    
    print(f"\nDownload complete:")
    print(f"  Downloaded: {downloaded}")
    print(f"  Already existed: {skipped}")
    print(f"  Failed: {failed}")
    
    # Build and save mappings
    print("\nBuilding team name mappings...")
    mappings = build_team_mappings()
    save_mappings(mappings)
    
    print(f"\nSetup complete! Logos cached in {CACHE_DIR}")
    print(f"Team mappings saved to {MAPPING_FILE}")


if __name__ == "__main__":
    download_all_logos()

