"""Diagnose why athletics scrapers aren't returning events"""
import sys
import io
from datetime import datetime, timedelta
from dateutil import parser as dtp

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Test current date filtering
now = datetime.now()
cutoff = now + timedelta(days=21)

print("=" * 70)
print("Diagnosing Athletics Scrapers")
print("=" * 70)
print(f"\nCurrent time: {now.isoformat()}")
print(f"3-week cutoff: {cutoff.isoformat()}")
print(f"Looking for events between: {now.date()} and {cutoff.date()}")

# Test each scraper
from lib.olemiss_athletics_scraper import fetch_olemiss_schedule

test_sources = [
    ("Football", "https://olemisssports.com/sports/football/schedule", "football"),
    ("Men's Basketball", "https://olemisssports.com/sports/mens-basketball/schedule", "basketball"),
    ("Women's Basketball", "https://olemisssports.com/sports/womens-basketball/schedule", "basketball"),
    ("Baseball", "https://olemisssports.com/sports/baseball/schedule", "baseball"),
    ("Softball", "https://olemisssports.com/sports/softball/schedule", "softball"),
    ("Volleyball", "https://olemisssports.com/sports/womens-volleyball/schedule", "volleyball"),
]

print("\n" + "=" * 70)
print("Testing Each Scraper")
print("=" * 70)

all_events = []
in_window_events = []

for name, url, sport_type in test_sources:
    print(f"\n[{name}]")
    try:
        events = fetch_olemiss_schedule(url, f"Test {name}", sport_type)
        print(f"  Total events found: {len(events)}")
        
        if events:
            print(f"  Sample events:")
            for i, event in enumerate(events[:3], 1):
                date_str = event.get('start_iso', '')
                try:
                    event_date = dtp.parse(date_str)
                    is_in_window = now <= event_date <= cutoff
                    status = "[IN WINDOW]" if is_in_window else "[OUTSIDE WINDOW]"
                    print(f"    {i}. {event.get('title', '')[:50]}")
                    print(f"       Date: {date_str[:19]} {status}")
                    
                    if is_in_window:
                        in_window_events.append(event)
                except Exception as e:
                    print(f"    {i}. {event.get('title', '')[:50]}")
                    print(f"       Date: {date_str[:19]} [ERROR: {e}]")
        else:
            print(f"  [WARNING] No events returned!")
        
        all_events.extend(events)
    except Exception as e:
        print(f"  [ERROR] Scraper failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print(f"Total events found: {len(all_events)}")
print(f"Events within 3-week window: {len(in_window_events)}")

if len(in_window_events) == 0 and len(all_events) > 0:
    print("\n[DIAGNOSIS] Events found but all filtered out by date range!")
    print("  All events are either:")
    print("  - In the past")
    print("  - More than 3 weeks in the future")
    print("\n  Solution: Consider expanding date range for athletics events")
elif len(all_events) == 0:
    print("\n[DIAGNOSIS] No events found - scrapers may be failing!")
elif len(in_window_events) > 0:
    print(f"\n[OK] {len(in_window_events)} events should appear in deployment")

