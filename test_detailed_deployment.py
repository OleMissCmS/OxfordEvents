"""
Detailed deployment test - check for actual issues
"""
import requests
import json
import sys

BASE_URL = "https://oxfordevents.onrender.com"

def test_main_page():
    """Test main page and check for common issues"""
    print("\n" + "="*60)
    print("Testing Main Page")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code != 200:
            print(f"[ERROR] Non-200 status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        content = response.text
        print(f"Content Length: {len(content)} bytes")
        
        # Check for common issues in HTML
        issues = []
        
        if "Traceback" in content or "Error" in content[:1000]:
            issues.append("Contains error messages")
        
        if "Exception" in content[:1000]:
            issues.append("Contains exception text")
        
        if len(content) < 1000:
            issues.append("Response too short (might be error page)")
        
        # Check for expected content
        expected = [
            "Concerts & Events in Oxford",
            "event-card",
            "filter-pill"
        ]
        
        found_expected = []
        for item in expected:
            if item in content:
                found_expected.append(item)
        
        print(f"Found expected elements: {len(found_expected)}/{len(expected)}")
        if len(found_expected) < len(expected):
            issues.append(f"Missing expected content: {set(expected) - set(found_expected)}")
        
        if issues:
            print(f"[WARNINGS] {len(issues)} potential issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("[SUCCESS] Main page looks good")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False

def test_events_api():
    """Test events API"""
    print("\n" + "="*60)
    print("Testing Events API")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/events", timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code != 200:
            print(f"[ERROR] Non-200 status: {response.status_code}")
            return False
        
        try:
            data = response.json()
            if not isinstance(data, list):
                print(f"[ERROR] Events API returned non-list: {type(data)}")
                return False
            
            print(f"Events Count: {len(data)}")
            
            if len(data) == 0:
                print("[WARNING] No events returned")
                return True  # Not an error, just no events
            
            # Check event structure
            sample = data[0] if data else {}
            required_fields = ['title', 'start_iso', 'location', 'category']
            missing = [f for f in required_fields if f not in sample]
            
            if missing:
                print(f"[WARNING] Events missing fields: {missing}")
            
            # Check categories
            categories = set(e.get('category') for e in data if e.get('category'))
            print(f"Categories: {sorted(categories)}")
            
            print("[SUCCESS] Events API working correctly")
            return True
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON response: {e}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False

def test_status_api():
    """Test status API"""
    print("\n" + "="*60)
    print("Testing Status API")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ERROR] Non-200 status: {response.status_code}")
            return False
        
        data = response.json()
        print(f"Status: {data.get('status', 'unknown')}")
        print(f"Message: {data.get('message', 'N/A')}")
        
        print("[SUCCESS] Status API working")
        return True
        
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False

def test_image_endpoints():
    """Test image endpoints for errors"""
    print("\n" + "="*60)
    print("Testing Image Endpoints")
    print("="*60)
    
    endpoints = [
        "/api/category-image/Test/Test?location=Test",
        "/api/sports-image/Ole%20Miss%20vs%20Alabama"
    ]
    
    all_ok = True
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code >= 500:
                print(f"[ERROR] {endpoint}: Status {response.status_code}")
                all_ok = False
            elif response.status_code >= 400:
                print(f"[WARNING] {endpoint}: Status {response.status_code}")
            else:
                print(f"[OK] {endpoint}: Status {response.status_code}")
        except Exception as e:
            print(f"[ERROR] {endpoint}: {e}")
            all_ok = False
    
    return all_ok

if __name__ == "__main__":
    print("="*60)
    print("DETAILED DEPLOYMENT TEST")
    print("="*60)
    
    results = []
    
    results.append(("Main Page", test_main_page()))
    results.append(("Events API", test_events_api()))
    results.append(("Status API", test_status_api()))
    results.append(("Image Endpoints", test_image_endpoints()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("\n[ERROR] Some tests failed - check issues above")
        sys.exit(1)

