"""Test the deployed API to diagnose athletic events issue"""
import requests
import json
import sys
import io
from datetime import datetime, timedelta

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_URL = "https://oxfordevents.onrender.com/api/events"

print("=" * 70)
print("Testing OxfordEvents Deployment")
print("=" * 70)

try:
    print(f"\n1. Fetching events from: {API_URL}")
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    events = response.json()
    
    print(f"[OK] Total events received: {len(events)}")
    
    # Check athletics events
    athletics = [e for e in events if e.get('category') == 'Ole Miss Athletics']
    print(f"\n2. Athletics events: {len(athletics)}")
    
    if athletics:
        print("\n   Sample athletics events:")
        for i, event in enumerate(athletics[:5], 1):
            print(f"   {i}. {event.get('title', 'No title')}")
            print(f"      Source: {event.get('source', 'unknown')}")
            print(f"      Date: {event.get('start_iso', 'no date')}")
            print(f"      Location: {event.get('location', 'unknown')}")
            print()
    else:
        print("   [WARNING] NO ATHLETICS EVENTS FOUND!")
    
    # Check by source
    print("\n3. Events by source:")
    sources = {}
    for event in events:
        source = event.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    for source, count in sorted(sources.items()):
        marker = "[WARNING]" if "Ole Miss" in source and count == 0 else "[OK]"
        print(f"   {marker} {source}: {count} events")
    
    # Check date filtering
    print("\n4. Date filtering analysis:")
    now = datetime.now()
    cutoff = now + timedelta(days=21)
    print(f"   Current time: {now.isoformat()}")
    print(f"   3-week cutoff: {cutoff.isoformat()}")
    
    athletics_with_dates = [e for e in athletics if e.get('start_iso')]
    print(f"\n   Athletics events with dates: {len(athletics_with_dates)}")
    
    if athletics_with_dates:
        print("\n   Sample dates from athletics events:")
        for event in athletics_with_dates[:5]:
            date_str = event.get('start_iso', '')
            try:
                event_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                is_future = event_date > now
                is_in_window = now <= event_date <= cutoff
                status = "[IN WINDOW]" if is_in_window else ("[FUTURE]" if is_future else "[PAST]")
                print(f"   {date_str[:19]} - {status} - {event.get('title', '')[:50]}")
            except:
                print(f"   {date_str} - ERROR parsing date")
    
    # Check for specific scraper sources
    print("\n5. Checking specific scraper sources:")
    scraper_sources = {
        'ESPN Ole Miss Football': 0,
        'ESPN Ole Miss MBB': 0,
        'ESPN Ole Miss WBB': 0,
        'Ole Miss Baseball Schedule': 0,
        'Ole Miss Softball Schedule': 0,
        'Ole Miss Women\'s Volleyball Schedule': 0,
    }
    
    for event in events:
        source = event.get('source', '')
        for key in scraper_sources:
            if key in source:
                scraper_sources[key] += 1
    
    for source, count in scraper_sources.items():
        marker = "[MISSING]" if count == 0 else "[OK]"
        print(f"   {marker} {source}: {count} events")
    
    print("\n" + "=" * 70)
    if len(athletics) == 0:
        print("[DIAGNOSIS] No athletics events found!")
        print("   Possible causes:")
        print("   1. Scrapers returning 0 events (check Render logs)")
        print("   2. Date filter removing all events (check dates)")
        print("   3. Events not being categorized correctly")
    else:
        print("[OK] Athletics events found, but may be filtered by date range")
    
except requests.exceptions.RequestException as e:
    print(f"[ERROR] Error fetching from API: {e}")
except json.JSONDecodeError as e:
    print(f"[ERROR] Error decoding JSON: {e}")
    print(f"   Response content: {response.text[:500]}")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()

