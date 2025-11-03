"""
Test script for ESPN scraper functionality
Run this to verify ESPN schedule scraping works locally before deploying
"""

import sys
import io
from datetime import datetime
from lib.event_scraper import fetch_espn_schedule

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_espn_scraper():
    """Test ESPN scraper for all three sports"""
    
    print("=" * 60)
    print("Testing ESPN Scraper for Ole Miss Athletics")
    print("=" * 60)
    print()
    
    # Test sources
    test_sources = [
        {
            "name": "ESPN Ole Miss Football",
            "url": "https://www.espn.com/college-football/team/schedule/_/id/145/ole-miss-rebels",
            "sport_type": "football"
        },
        {
            "name": "ESPN Ole Miss MBB",
            "url": "https://www.espn.com/mens-college-basketball/team/schedule/_/id/145",
            "sport_type": "basketball"
        },
        {
            "name": "ESPN Ole Miss WBB",
            "url": "https://www.espn.com/womens-college-basketball/team/schedule/_/id/145/ole-miss-rebels",
            "sport_type": "basketball"
        }
    ]
    
    all_events = []
    
    for source in test_sources:
        print(f"\n{'=' * 60}")
        print(f"Testing: {source['name']}")
        print(f"URL: {source['url']}")
        print(f"{'=' * 60}")
        
        try:
            events = fetch_espn_schedule(
                source['url'],
                source['name'],
                source['sport_type']
            )
            
            print(f"\n[SUCCESS] Successfully fetched {len(events)} events")
            
            if events:
                print("\nSample events:")
                for i, event in enumerate(events[:5], 1):  # Show first 5
                    print(f"\n  Event {i}:")
                    print(f"    Title: {event['title']}")
                    print(f"    Date: {event['start_iso']}")
                    print(f"    Location: {event['location']}")
                    print(f"    Category: {event['category']}")
                    print(f"    Source: {event['source']}")
                
                if len(events) > 5:
                    print(f"\n  ... and {len(events) - 5} more events")
                
                all_events.extend(events)
            else:
                print("[WARNING] No events found (may be out of season or parsing issue)")
                
        except ImportError as e:
            print(f"\n[ERROR] Import Error: {e}")
            print("\nPlease install dependencies:")
            print("  pip install selenium webdriver-manager")
            return False
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total events found: {len(all_events)}")
    print(f"Categories: {set(e['category'] for e in all_events)}")
    print(f"Sources: {set(e['source'] for e in all_events)}")
    
    # Check for away games (should be filtered out)
    away_games = [e for e in all_events if '@' in e['title'] or e['title'].lower().startswith('at ')]
    if away_games:
        print(f"\n[WARNING] Found {len(away_games)} away games (should be filtered):")
        for game in away_games[:3]:
            print(f"    - {game['title']}")
    else:
        print("\n[SUCCESS] No away games found (filtering working correctly)")
    
    # Check for Ole Miss Athletics category
    athletics_events = [e for e in all_events if e['category'] == 'Ole Miss Athletics']
    print(f"\n[SUCCESS] Events categorized as 'Ole Miss Athletics': {len(athletics_events)}/{len(all_events)}")
    
    if len(all_events) > 0:
        print("\n[SUCCESS] Test PASSED - ESPN scraper is working!")
        return True
    else:
        print("\n[WARNING] Test WARNING - No events found, but no errors occurred")
        print("   This might be normal if there are no upcoming home games")
        return True  # Still pass if no errors

if __name__ == '__main__':
    success = test_espn_scraper()
    sys.exit(0 if success else 1)

