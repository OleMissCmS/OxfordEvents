"""Test the Ole Miss Athletics scraper"""
from lib.olemiss_athletics_scraper import fetch_olemiss_schedule

test_urls = [
    ("Football", "https://olemisssports.com/sports/football/schedule", "football"),
    ("Men's Basketball", "https://olemisssports.com/sports/mens-basketball/schedule", "basketball"),
    ("Women's Basketball", "https://olemisssports.com/sports/womens-basketball/schedule", "basketball"),
]

print("=" * 60)
print("Testing Ole Miss Athletics Scraper")
print("=" * 60)

all_events = []
for name, url, sport_type in test_urls:
    print(f"\nTesting: {name}")
    print(f"URL: {url}")
    events = fetch_olemiss_schedule(url, f"Ole Miss {name}", sport_type)
    print(f"Found: {len(events)} events")
    
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:3], 1):
            print(f"  {i}. {event['title']} - {event['start_iso']} at {event['location']}")
    else:
        print("[WARNING] No events found!")
    
    all_events.extend(events)

print(f"\n{'=' * 60}")
print(f"SUMMARY: {len(all_events)} total events found")
if len(all_events) == 0:
    print("[ALERT] NO EVENTS FOUND - Scraper may need adjustment")

