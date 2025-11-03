"""Quick script to check if ESPN events are in the deployed API"""
import requests
import json

try:
    r = requests.get('https://oxfordevents.onrender.com/api/events', timeout=10)
    r.raise_for_status()
    events = r.json()
    
    athletics = [e for e in events if e.get('category') == 'Ole Miss Athletics']
    espn_events = [e for e in athletics if 'ESPN' in e.get('source', '')]
    
    print(f"Total events: {len(events)}")
    print(f"Ole Miss Athletics events: {len(athletics)}")
    print(f"ESPN-sourced events: {len(espn_events)}")
    
    if espn_events:
        print("\nFirst 5 ESPN events:")
        for e in espn_events[:5]:
            print(f"  - {e['title']} ({e.get('source', 'unknown')})")
    else:
        print("\n[WARNING] No ESPN events found!")
        print("This might mean:")
        print("  1. The scraper is failing (check Render logs)")
        print("  2. There are no upcoming home games")
        print("  3. The cache hasn't refreshed yet")
        
except Exception as e:
    print(f"Error checking API: {e}")

