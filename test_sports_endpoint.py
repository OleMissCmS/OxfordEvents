"""Test the sports-image endpoint with actual event titles"""
import requests
from urllib.parse import quote

titles = [
    'Miami Hurricanes at Ole Miss Rebels Mens Basketball',
    'Longwood Lancers at Ole Miss Rebels Womens Basketball',
    'Ice Hockey Club (D2) vs Alabama at Mid-South Ice House',
    'Notre Dame Fighting Irish at Ole Miss Rebels Womens Basketball'
]

base_url = "http://localhost:5000/api/sports-image"

for title in titles:
    url = f"{base_url}/{quote(title)}"
    print(f"\nTesting: {title}")
    print(f"URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Image size: {len(response.content)} bytes")
        else:
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")

