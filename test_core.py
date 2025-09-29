"""
Complete CORE API v3 Test Script
Tests your valid API key with proper authentication
"""

# IMPORT ALL REQUIRED LIBRARIES
import requests
import json
import time
import pandas as pd
from datetime import datetime

# Your VALID API key (expires Sept 30, 2025)
API_KEY = "icHUxkngRzK0PqTZl1paCoyw2Y3XV8tA"

def test_core_api():
    """Test CORE API v3 with correct authentication"""
    
    print("=" * 60)
    print("TESTING CORE API v3")
    print("=" * 60)
    print(f"API Key: {API_KEY[:10]}...")
    print(f"Test Time: {datetime.now()}")
    print("-" * 60)
    
    # Test 1: Simple search
    print("\n1. Testing basic search...")
    
    url = "https://api.core.ac.uk/v3/search/works"
    
    # CORRECT way - API key in params
    params = {
        "q": "machine learning",
        "limit": 5,
        "apiKey": API_KEY  # Must be 'apiKey' exactly
    }
    
    try:
        print(f"   Calling: {url}")
        print(f"   Query: machine learning")
        
        response = requests.get(url, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('totalHits', 0)
            results = data.get('results', [])
            
            print(f"\n   ✅ SUCCESS! Found {total:,} total papers")
            print(f"   Retrieved {len(results)} papers in this request")
            
            if results:
                print("\n   Sample paper:")
                paper = results[0]
                print(f"   - Title: {paper.get('title', 'N/A')[:80]}...")
                print(f"   - Year: {paper.get('yearPublished', 'N/A')}")
                print(f"   - DOI: {paper.get('doi', 'N/A')}")
            
            return True
            
        elif response.status_code == 401:
            print("\n   ❌ AUTHENTICATION FAILED")
            print("   The API key was not recognized")
            print(f"   Full URL called: {response.url}")
            
        elif response.status_code == 429:
            print("\n   ⚠️ RATE LIMIT EXCEEDED")
            print("   Wait 10 seconds before trying again")
            
        elif response.status_code == 403:
            print("\n   ❌ FORBIDDEN")
            print("   Your API key doesn't have access to this resource")
            
        else:
            print(f"\n   ❌ ERROR {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("\n   ❌ REQUEST TIMED OUT")
        print("   The API took too long to respond")
        
    except requests.exceptions.ConnectionError:
        print("\n   ❌ CONNECTION ERROR")
        print("   Could not connect to api.core.ac.uk")
        print("   Check your internet connection or firewall")
        
    except Exception as e:
        print(f"\n   ❌ UNEXPECTED ERROR: {e}")
    
    return False

def test_university_search():
    """Test searching for Australian university papers"""
    
    print("\n2. Testing Australian university search...")
    
    url = "https://api.core.ac.uk/v3/search/works"
    
    # Search for papers from University of Melbourne
    params = {
        "q": 'institutionName:"University of Melbourne"',
        "limit": 3,
        "apiKey": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('totalHits', 0)
            print(f"   ✅ Found {total:,} papers from University of Melbourne")
            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return False

def main():
    """Run all tests"""
    
    # Test basic search
    success1 = test_core_api()
    
    # Wait to avoid rate limiting
    if success1:
        print("\n   Waiting 2 seconds to avoid rate limits...")
        time.sleep(2)
        
        # Test university search
        success2 = test_university_search()
    else:
        success2 = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if success1 and success2:
        print("✅ ALL TESTS PASSED!")
        print("\nYour CORE API key is working correctly!")
        print("The key is valid until September 30, 2025")
        print("\nYou can now use it in your application.")
    else:
        print("❌ TESTS FAILED")
        print("\nPossible issues:")
        print("1. Network/firewall blocking api.core.ac.uk")
        print("2. VPN or proxy interference")
        print("3. Temporary API service issue")
        print("\nTry:")
        print("- Testing from a different network")
        print("- Disabling VPN if using one")
        print("- Waiting a few minutes and trying again")
        print("\nAlternatively, use Semantic Scholar API (no key required)")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()