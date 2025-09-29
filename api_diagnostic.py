"""
Diagnostic script for CORE API issues
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test with your API key
API_KEY = os.getenv("CORE_API_KEY", "icHUxkngRzK0PqTZl1paCoyw2Y3XV8tA")

print("="*50)
print("CORE API DIAGNOSTIC TEST")
print("="*50)
print(f"\n1. API Key loaded: {'Yes' if API_KEY else 'No'}")
print(f"   Key preview: {API_KEY[:10]}..." if API_KEY else "   No key found")

# Test different API endpoints and methods
tests = [
    {
        "name": "Test v3 API with Bearer token",
        "url": "https://api.core.ac.uk/v3/search/works",
        "headers": {"Authorization": f"Bearer {API_KEY}"},
        "params": {"q": "test", "limit": 1}
    },
    {
        "name": "Test v3 API with apiKey parameter",
        "url": "https://api.core.ac.uk/v3/search/works",
        "headers": {},
        "params": {"q": "test", "limit": 1, "apiKey": API_KEY}
    },
    {
        "name": "Test without authentication (should fail)",
        "url": "https://api.core.ac.uk/v3/search/works",
        "headers": {},
        "params": {"q": "test", "limit": 1}
    }
]

for i, test in enumerate(tests, 2):
    print(f"\n{i}. {test['name']}...")
    try:
        response = requests.get(
            test['url'], 
            headers=test['headers'], 
            params=test['params'], 
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - Found {data.get('totalHits', 0)} results")
        elif response.status_code == 401:
            print(f"   ❌ UNAUTHORIZED - API key invalid or not recognized")
        elif response.status_code == 403:
            print(f"   ❌ FORBIDDEN - API key doesn't have access")
        elif response.status_code == 429:
            print(f"   ⚠️ RATE LIMITED - Too many requests")
        else:
            print(f"   ❌ ERROR: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT - Request took too long")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ CONNECTION ERROR - Cannot reach API")
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)[:100]}")

print("\n" + "="*50)
print("DIAGNOSIS COMPLETE")
print("="*50)

# Alternative: Test if we can access CORE without API key (some endpoints are public)
print("\n📝 Testing public access (no API key)...")
try:
    # Try a simple search without authentication
    response = requests.get(
        "https://core.ac.uk/api-v2/search/machine%20learning",
        params={"page": 1, "pageSize": 1},
        timeout=10
    )
    if response.status_code == 200:
        print("✅ CORE API v2 (legacy) is accessible without key")
        print("   Consider using v2 API as fallback")
except:
    print("❌ Cannot access CORE API v2 either")

print("\n💡 RECOMMENDATIONS:")
print("-" * 40)
if API_KEY:
    print("1. Your API key is loaded but may be invalid")
    print("2. Get a new key at: https://core.ac.uk/api-keys/register")
    print("3. Or use mock data for development/testing")
else:
    print("1. No API key found in environment")
    print("2. Check your .env file exists and contains:")
    print("   CORE_API_KEY=your_key_here")