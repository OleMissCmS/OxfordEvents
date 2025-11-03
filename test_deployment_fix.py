"""
Test deployment to identify and fix errors
"""
import requests
import json
import sys

BASE_URL = "https://oxfordevents.onrender.com"

def test_endpoint(path, description):
    """Test an endpoint and report results"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            print("[SUCCESS]")
            if 'application/json' in response.headers.get('Content-Type', ''):
                try:
                    data = response.json()
                    print(f"JSON Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                except:
                    print("Response: (non-JSON)")
            else:
                content_length = len(response.content)
                print(f"Response Size: {content_length} bytes")
                if content_length > 0:
                    print("[SUCCESS] Page loaded successfully")
        else:
            print(f"[ERROR] Status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timed out after 30s")
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection failed - {e}")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("Testing Oxford Events Deployment")
    print(f"Base URL: {BASE_URL}")
    
    # Test main page
    test_endpoint("/", "Main Page")
    
    # Test API endpoints
    test_endpoint("/api/events", "Events API")
    test_endpoint("/api/status", "Status API")
    
    # Test image endpoints (might fail, that's ok)
    test_endpoint("/api/category-image/Test/Test?location=Test", "Category Image Endpoint")
    
    print("\n" + "="*60)
    print("Testing complete!")

