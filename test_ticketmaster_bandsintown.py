"""
Test script to check Ticketmaster and Bandsintown events
"""
import os
import sys
import requests
from bs4 import BeautifulSoup
from lib.event_scraper import fetch_ticketmaster_events, fetch_html_events

def test_ticketmaster():
    """Test Ticketmaster API"""
    print("=" * 60)
    print("TESTING TICKETMASTER API")
    print("=" * 60)
    
    api_key = os.environ.get('TICKETMASTER_API_KEY', '')
    if not api_key:
        print("[ERROR] No TICKETMASTER_API_KEY found in environment")
        print("   Set it with: export TICKETMASTER_API_KEY=your_key")
        return
    
    events = fetch_ticketmaster_events("Oxford", "MS")
    
    print(f"\n[Ticketmaster Results]")
    print(f"   Total events found: {len(events)}")
    
    if events:
        print(f"\n[Sample events (first 10)]:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n   {i}. {event.get('title', 'Untitled')}")
            print(f"      Date: {event.get('start_iso', 'N/A')}")
            print(f"      Location: {event.get('location', 'N/A')}")
            print(f"      Category: {event.get('category', 'N/A')}")
            print(f"      Link: {event.get('link', 'N/A')}")
    
    # Also try broader area (Mississippi)
    print("\n" + "=" * 60)
    print("Testing broader area (Mississippi, not just Oxford)")
    print("=" * 60)
    
    # Get events from broader area by using lat/lon or zip
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        'apikey': api_key,
        'stateCode': 'MS',
        'size': 100,
        'sort': 'date,asc'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            all_events = data.get('_embedded', {}).get('events', [])
            print(f"\n[All Mississippi events]: {len(all_events)}")
            
            # Filter for events near Oxford (within ~50 miles)
            # Oxford is approximately at: 34.3665° N, 89.5192° W
            oxford_nearby = []
            for item in all_events:
                venues = item.get('_embedded', {}).get('venues', [])
                if venues:
                    venue_name = venues[0].get('name', '')
                    city = venues[0].get('city', {}).get('name', '')
                    # Check if venue mentions Oxford or nearby cities
                    nearby_cities = ['oxford', 'tupelo', 'southaven', 'memphis', 'batesville', 'grenada']
                    if any(nc in (venue_name + ' ' + city).lower() for nc in nearby_cities):
                        oxford_nearby.append(item)
            
            print(f"[Events near Oxford area]: {len(oxford_nearby)}")
            
            if oxford_nearby:
                print(f"\n[Nearby events (first 10)]:")
                for i, item in enumerate(oxford_nearby[:10], 1):
                    venue = item.get('_embedded', {}).get('venues', [{}])[0]
                    print(f"\n   {i}. {item.get('name', 'Untitled')}")
                    print(f"      Venue: {venue.get('name', 'N/A')}")
                    print(f"      City: {venue.get('city', {}).get('name', 'N/A')}")
                    print(f"      Date: {item.get('dates', {}).get('start', {}).get('localDate', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] Error testing broader area: {e}")


def test_bandsintown():
    """Test Bandsintown scraper"""
    print("\n" + "=" * 60)
    print("TESTING BANDSINTOWN")
    print("=" * 60)
    
    url = "https://www.bandsintown.com/c/oxford-ms"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        response = requests.get(url, timeout=10, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for event listings
            print("\n[Analyzing Bandsintown page structure...]")
            
            # Try to find event elements
            event_elements = soup.find_all(['div', 'article', 'li'], class_=lambda x: x and ('event' in str(x).lower() or 'concert' in str(x).lower()) if x else False)
            print(f"   Found {len(event_elements)} potential event elements")
            
            # Also check for links
            all_links = soup.find_all('a', href=True)
            event_links = [link for link in all_links if any(keyword in link.get('href', '').lower() for keyword in ['event', 'concert', 'artist', 'show'])]
            print(f"   Found {len(event_links)} potential event links")
            
            # Try the actual scraper
            events = fetch_html_events(url, "Bandsintown", parser="bandsintown")
            print(f"\n[Bandsintown scraper results]:")
            print(f"   Total events found: {len(events)}")
            
            if events:
                print(f"\n[Events (first 10)]:")
                for i, event in enumerate(events[:10], 1):
                    print(f"\n   {i}. {event.get('title', 'Untitled')}")
                    print(f"      Date: {event.get('start_iso', 'N/A')}")
                    print(f"      Location: {event.get('location', 'N/A')}")
                    print(f"      Category: {event.get('category', 'N/A')}")
                    print(f"      Link: {event.get('link', 'N/A')}")
            else:
                print("\n[WARNING] No events found - page structure may have changed")
                print("   Saving page HTML for inspection...")
                with open('bandsintown_page.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                print("   Saved to bandsintown_page.html")
        else:
            print(f"[ERROR] Error: Got status code {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error testing Bandsintown: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Testing Event Sources")
    print("=" * 60)
    
    test_ticketmaster()
    test_bandsintown()
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)

