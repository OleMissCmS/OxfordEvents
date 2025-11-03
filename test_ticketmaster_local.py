"""
Test Ticketmaster API integration locally or on deployed site
"""
import os
import sys
import requests

def test_ticketmaster_api_direct():
    """Test Ticketmaster API directly with API key"""
    api_key = os.environ.get('TICKETMASTER_API_KEY', '')
    
    if not api_key:
        print("[ERROR] No TICKETMASTER_API_KEY found in environment")
        print("Set it with: $env:TICKETMASTER_API_KEY='your_key'")
        return
    
    print(f"[TEST] Testing Ticketmaster API with key (first 8 chars: {api_key[:8]}...)")
    
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        'apikey': api_key,
        'city': 'Oxford',
        'stateCode': 'MS',
        'size': 10
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"[TEST] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('_embedded', {}).get('events', [])
            print(f"[TEST] SUCCESS: Found {len(events)} events")
            
            if events:
                print("\n[Sample Events]:")
                for i, event in enumerate(events[:5], 1):
                    print(f"\n  {i}. {event.get('name', 'N/A')}")
                    print(f"     Date: {event.get('dates', {}).get('start', {}).get('localDate', 'N/A')}")
                    venue = event.get('_embedded', {}).get('venues', [{}])[0]
                    print(f"     Venue: {venue.get('name', 'N/A')}")
            return True
        else:
            print(f"[TEST] ERROR: Got status {response.status_code}")
            try:
                error_data = response.json()
                print(f"[TEST] Error: {error_data}")
            except:
                print(f"[TEST] Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"[TEST] ERROR: {e}")
        return False


def test_deployed_site():
    """Test the deployed site to see if Ticketmaster events are showing up"""
    print("[TEST] Testing deployed site...")
    
    try:
        url = "https://oxfordevents.onrender.com/api/events"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, list):
                events = data
            else:
                events = data.get('events', [])
            
            # Filter for Ticketmaster events
            ticketmaster_events = [e for e in events if e.get('source') == 'Ticketmaster' or e.get('category') == 'Ticketmaster']
            
            print(f"[TEST] Total events on site: {len(events)}")
            print(f"[TEST] Ticketmaster events found: {len(ticketmaster_events)}")
            
            if ticketmaster_events:
                print("\n[Ticketmaster Events on Site]:")
                for i, event in enumerate(ticketmaster_events[:5], 1):
                    print(f"\n  {i}. {event.get('title', 'N/A')}")
                    print(f"     Date: {event.get('start_iso', 'N/A')}")
                    print(f"     Location: {event.get('location', 'N/A')}")
                return True
            else:
                print("\n[TEST] No Ticketmaster events found on deployed site")
                print("[TEST] This could mean:")
                print("  - API key not set up correctly in Render")
                print("  - No events in Oxford, MS area")
                print("  - Events filtered out (past dates, etc.)")
                return False
        else:
            print(f"[TEST] ERROR: Site returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[TEST] ERROR testing deployed site: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING TICKETMASTER INTEGRATION")
    print("=" * 60)
    
    # Test 1: Direct API test (requires local API key)
    print("\n1. Testing Ticketmaster API directly...")
    direct_success = test_ticketmaster_api_direct()
    
    # Test 2: Deployed site test
    print("\n2. Testing deployed site for Ticketmaster events...")
    deployed_success = test_deployed_site()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"  Direct API Test: {'[PASS]' if direct_success else '[FAIL - need API key]'}")
    print(f"  Deployed Site Test: {'[PASS]' if deployed_success else '[FAIL]'}")
    print("=" * 60)

