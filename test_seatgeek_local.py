"""
Test script to test SeatGeek API integration locally
"""
import os
import requests
import json
from lib.event_scraper import fetch_seatgeek_events

def test_seatgeek_direct():
    """Test SeatGeek API directly"""
    api_key = os.environ.get('SEATGEEK_API_KEY', '')
    if not api_key:
        print("[ERROR] No SEATGEEK_API_KEY found in environment")
        print("Set it with: $env:SEATGEEK_API_KEY='your_key'")
        return False
    
    # Oxford, MS coordinates
    lat = 34.3665
    lon = -89.5192
    
    events = fetch_seatgeek_events(lat, lon, "25mi")
    
    print(f"\n[SeatGeek Results]")
    print(f"   Total events found: {len(events)}")
    
    if events:
        print(f"\n[Sample events (first 10)]:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n   {i}. {event.get('title', 'Untitled')}")
            print(f"      Date: {event.get('start_iso', 'N/A')}")
            print(f"      Location: {event.get('location', 'N/A')}")
            print(f"      Category: {event.get('category', 'N/A')}")
            print(f"      Cost: {event.get('cost', 'N/A')}")
            print(f"      Link: {event.get('link', 'N/A')}")
        return True
    return False

def test_deployed_site():
    """Test deployed site for SeatGeek events"""
    print("[TEST] Testing deployed site...")
    try:
        url = "https://oxfordevents.onrender.com/api/events"
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                events = data
            else:
                events = data.get('events', [])
            
            seatgeek_events = [e for e in events if e.get('source') == 'SeatGeek' or e.get('category') == 'SeatGeek']
            
            print(f"[TEST] Total events on site: {len(events)}")
            print(f"[TEST] SeatGeek events found: {len(seatgeek_events)}")
            
            if seatgeek_events:
                print(f"\n[TEST] Sample SeatGeek events (first 5):")
                for i, e in enumerate(seatgeek_events[:5], 1):
                    print(f"  {i+1}. {e.get('title', 'N/A')[:50]} - {e.get('start_iso', 'N/A')[:10]}")
                return True
            else:
                print("[TEST] No SeatGeek events found on deployed site")
                print("[TEST] This could mean:")
                print("  - API key not set up correctly in Render")
                print("  - No events in Oxford, MS area")
                print("  - Events filtered out (past dates, etc.)")
                return False
        else:
            print(f"[TEST] ERROR: Deployed site returned status code {response.status_code}")
            print(f"[TEST] Response: {response.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[TEST] ERROR testing deployed site: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING SEATGEEK INTEGRATION")
    print("=" * 60)
    
    # Test 1: Direct API test
    print("\n1. Testing SeatGeek API directly...")
    direct_success = test_seatgeek_direct()
    
    # Test 2: Deployed site test
    print("\n2. Testing deployed site for SeatGeek events...")
    deployed_success = test_deployed_site()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"  Direct API Test: {'[PASS]' if direct_success else '[FAIL - need API key]'}")
    print(f"  Deployed Site Test: {'[PASS]' if deployed_success else '[FAIL]'}")
    print("=" * 60)

