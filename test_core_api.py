"""
Test script to verify CORE API connection and key
"""
import requests
import json

# Your API key
API_KEY = "icHUxkngRzK0PqTZl1paCoyw2Y3XV8tA"
BASE_URL = "https://api.core.ac.uk/v3"

def test_api_connection():
    """Test if the API key works"""
    
    print("Testing CORE API connection...")
    print(f"API Key: {API_KEY[:10]}..." if API_KEY else "No API key")
    
    # Test 1: Simple search
    print("\n1. Testing basic search...")
    url = f"{BASE_URL}/search/works"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    params = {
        "q": "machine learning",
        "limit": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('totalHits', 0)} total results")
            if data.get('results'):
                print(f"Sample paper: {data['results'][0].get('title', 'No title')[:50]}...")
        elif response.status_code == 401:
            print("❌ Authentication failed - API key may be invalid")
        elif response.status_code == 429:
            print("⚠️ Rate limit exceeded - try again later")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check internet connection")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Search for Australian university
    print("\n2. Testing Australian university search...")
    params = {
        "q": 'institutionName:"University of Melbourne"',
        "limit": 2
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data.get('totalHits', 0)} papers from University of Melbourne")
        else:
            print(f"❌ Error: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check rate limits
    print("\n3. Checking rate limits...")
    if 'X-RateLimit-Limit' in response.headers:
        print(f"Rate Limit: {response.headers.get('X-RateLimit-Limit')}")
        print(f"Remaining: {response.headers.get('X-RateLimit-Remaining')}")

if __name__ == "__main__":
    test_api_connection()
    print("\n" + "="*50)
    print("If tests failed, possible solutions:")
    print("1. Check if API key is valid at: https://core.ac.uk/api-keys")
    print("2. Try a different network (some networks block APIs)")
    print("3. Wait if rate limited (usually resets in 1 hour)")
    print("4. Create a new API key if current one is invalid")