"""
Test script to check Ole Miss Athletics event descriptions after deployment
"""
import requests
import json

def test_athletics_events():
    """Test the deployed site for Ole Miss Athletics events"""
    print("=" * 60)
    print("TESTING OLE MISS ATHLETICS EVENTS")
    print("=" * 60)
    
    try:
        url = "https://oxfordevents.onrender.com/api/events"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            events = data if isinstance(data, list) else data.get('events', [])
            
            # Filter for Ole Miss Athletics events
            athletics_events = [e for e in events if e.get('category') == 'Ole Miss Athletics']
            
            print(f"\n[Total Athletics Events]: {len(athletics_events)}")
            
            if athletics_events:
                # Check for basketball events
                basketball_events = [e for e in athletics_events if 'basketball' in e.get('title', '').lower()]
                print(f"\n[Basketball Events]: {len(basketball_events)}")
                
                for event in basketball_events:
                    print(f"\n  Title: {event.get('title', 'N/A')}")
                    print(f"  Description: {event.get('description', 'N/A')}")
                    print(f"  Source: {event.get('source', 'N/A')}")
                    print(f"  Date: {event.get('start_iso', 'N/A')[:10]}")
                
                # Check for football events with date patterns in title
                football_events = [e for e in athletics_events if 'football' in e.get('description', '').lower() or 'football' in e.get('source', '').lower()]
                print(f"\n[Football Events]: {len(football_events)}")
                
                # Look for duplicates or titles with date patterns
                print(f"\n[Checking for issues]:")
                duplicates_found = []
                date_in_title = []
                
                for event in athletics_events:
                    title = event.get('title', '')
                    # Check for date patterns in title
                    import re
                    if re.search(r'[A-Z][a-z]{2}\s+\d{1,2}\s*/\s*(Noon|\d{1,2}\s*[AP]M)', title, re.IGNORECASE):
                        date_in_title.append(event)
                
                if date_in_title:
                    print(f"  [ISSUE] Found {len(date_in_title)} events with date patterns in title:")
                    for event in date_in_title:
                        print(f"    - {event.get('title', 'N/A')}")
                else:
                    print(f"  [OK] No date patterns found in titles")
                
                # Check for duplicate titles on same date
                title_date_map = {}
                for event in athletics_events:
                    key = f"{event.get('title', '').lower()}_{event.get('start_iso', '')[:10]}"
                    if key in title_date_map:
                        duplicates_found.append((event, title_date_map[key]))
                    else:
                        title_date_map[key] = event
                
                if duplicates_found:
                    print(f"  [ISSUE] Found {len(duplicates_found)} potential duplicates:")
                    for event1, event2 in duplicates_found:
                        print(f"    - {event1.get('title', 'N/A')} on {event1.get('start_iso', 'N/A')[:10]}")
                        print(f"      Source 1: {event1.get('source', 'N/A')}")
                        print(f"      Source 2: {event2.get('source', 'N/A')}")
                else:
                    print(f"  [OK] No duplicates found")
                
                # Show sample events
                print(f"\n[Sample Athletics Events (first 10)]:")
                for i, event in enumerate(athletics_events[:10], 1):
                    print(f"\n  {i}. {event.get('title', 'N/A')}")
                    print(f"     Description: {event.get('description', 'N/A')}")
                    print(f"     Source: {event.get('source', 'N/A')}")
                    print(f"     Date: {event.get('start_iso', 'N/A')[:10]}")
            else:
                print("\n[WARNING] No Ole Miss Athletics events found")
                print("  Check if athletic events are being scraped correctly")
        else:
            print(f"[ERROR] Site returned status {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Error testing athletics events: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_athletics_events()

