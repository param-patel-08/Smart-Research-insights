"""
Test script to debug and fix CORE API paper fetching
This will show exactly what's happening and why you're not getting papers
"""

import requests
import json
import pandas as pd
import time

# Your valid API key
API_KEY = "icHUxkngRzK0PqTZl1paCoyw2Y3XV8tA"
BASE_URL = "https://api.core.ac.uk/v3"

def test_basic_search():
    """Test 1: Basic search to verify API works"""
    print("=" * 60)
    print("TEST 1: Basic Search (should return lots of results)")
    print("=" * 60)
    
    url = f"{BASE_URL}/search/works"
    params = {
        "q": "*",  # Wildcard to get ANY papers
        "limit": 5,
        "apiKey": API_KEY
    }
    
    response = requests.get(url, params=params, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total papers in CORE: {data.get('totalHits', 0):,}")
        results = data.get('results', [])
        if results:
            print(f"Sample paper: {results[0].get('title', 'N/A')[:80]}")
        return True
    else:
        print(f"❌ Error: {response.text[:200]}")
        return False

def test_university_search_methods():
    """Test 2: Different ways to search for university papers"""
    print("\n" + "=" * 60)
    print("TEST 2: University Search Methods")
    print("=" * 60)
    
    universities = [
        "University of Melbourne",
        "University of Sydney",
        "Australian National University"
    ]
    
    for uni in universities:
        print(f"\nTesting: {uni}")
        print("-" * 40)
        
        # Method 1: Using institutionName
        url = f"{BASE_URL}/search/works"
        
        # Try different query formats
        queries = [
            f'institutionName:"{uni}"',  # Exact match with quotes
            f'institutionName:{uni}',     # Without quotes
            f'"{uni}"',                   # Just the university name in quotes
            uni,                          # Just the university name
            f'affiliation:"{uni}"',       # Try affiliation field
            f'authors.affiliations:"{uni}"'  # Try nested field
        ]
        
        for query in queries:
            params = {
                "q": query,
                "limit": 5,
                "apiKey": API_KEY
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get('totalHits', 0)
                    if hits > 0:
                        print(f"  ✅ Query '{query[:30]}...' found {hits:,} papers")
                        # Get first paper details
                        if data.get('results'):
                            paper = data['results'][0]
                            print(f"     Sample: {paper.get('title', 'N/A')[:60]}...")
                            # Check if paper actually has the university
                            if paper.get('authors'):
                                for author in paper['authors'][:3]:
                                    if author.get('affiliations'):
                                        print(f"     Author affiliation: {author['affiliations'][:100]}")
                        break  # Found results, move to next university
                    else:
                        print(f"  ❌ Query '{query[:30]}...' found 0 papers")
            except Exception as e:
                print(f"  ❌ Error with query '{query[:30]}...': {e}")
            
            time.sleep(1)  # Rate limiting

def test_year_filter():
    """Test 3: Check if year filtering works"""
    print("\n" + "=" * 60)
    print("TEST 3: Year Filter Test")
    print("=" * 60)
    
    queries = [
        'yearPublished>=2023',
        'yearPublished:2023',
        'yearPublished:[2023 TO 2024]',
        'publishedDate>=2023-01-01'
    ]
    
    for query in queries:
        params = {
            "q": query,
            "limit": 5,
            "apiKey": API_KEY
        }
        
        response = requests.get(f"{BASE_URL}/search/works", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            hits = data.get('totalHits', 0)
            print(f"Query '{query}': {hits:,} papers")
            if data.get('results'):
                years = [p.get('yearPublished', 'N/A') for p in data['results']]
                print(f"  Years in results: {years}")

def get_papers_simple_method():
    """Test 4: Simplest possible method to get Australian papers"""
    print("\n" + "=" * 60)
    print("TEST 4: Simple Search for Australian Papers")
    print("=" * 60)
    
    # Just search for papers mentioning Australia or Australian universities
    simple_queries = [
        'Australia',
        'Australian university',
        'Melbourne Sydney',
        '"University of" AND Australia',
        'research Australia 2023',
        'Australia 2024'
    ]
    
    all_papers = []
    
    for query in simple_queries:
        print(f"\nSearching: {query}")
        
        params = {
            "q": query,
            "limit": 20,
            "apiKey": API_KEY
        }
        
        response = requests.get(f"{BASE_URL}/search/works", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get('totalHits', 0)
            results = data.get('results', [])
            
            print(f"  Found {hits:,} total papers")
            
            for paper in results:
                # Check if it's from an Australian institution
                is_australian = False
                institution_info = "Unknown"
                
                if paper.get('authors'):
                    for author in paper['authors']:
                        if author.get('affiliations'):
                            aff_lower = author['affiliations'].lower()
                            if 'australia' in aff_lower or 'sydney' in aff_lower or 'melbourne' in aff_lower:
                                is_australian = True
                                institution_info = author['affiliations'][:100]
                                break
                
                paper_info = {
                    'title': paper.get('title', 'No Title'),
                    'abstract': paper.get('abstract', ''),
                    'year': paper.get('yearPublished', 2023),
                    'doi': paper.get('doi', ''),
                    'is_australian': is_australian,
                    'institution': institution_info
                }
                
                all_papers.append(paper_info)
            
            # Show sample of Australian papers found
            aus_papers = [p for p in all_papers if p['is_australian']]
            print(f"  Australian papers found so far: {len(aus_papers)}")
            
        time.sleep(1)  # Rate limiting
    
    # Convert to DataFrame and show summary
    df = pd.DataFrame(all_papers)
    if not df.empty:
        aus_df = df[df['is_australian'] == True]
        print(f"\n📊 SUMMARY: Found {len(aus_df)} Australian papers out of {len(df)} total")
        if len(aus_df) > 0:
            print("\nSample Australian papers:")
            for idx, row in aus_df.head(3).iterrows():
                print(f"- {row['title'][:80]}...")
                print(f"  Institution: {row['institution']}")
    
    return df

def test_data_providers():
    """Test 5: Check what data providers (repositories) are available"""
    print("\n" + "=" * 60)
    print("TEST 5: Check Available Data Providers")
    print("=" * 60)
    
    # Try to get data providers endpoint
    url = f"{BASE_URL}/data-providers"
    params = {"apiKey": API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Data providers endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Some data providers available in CORE:")
            # This might show us which repositories are indexed
    except:
        print("Data providers endpoint not accessible")
    
    # Alternative: Search for papers and see what sources come up
    print("\nChecking sources in search results...")
    params = {
        "q": "University Australia",
        "limit": 10,
        "apiKey": API_KEY
    }
    
    response = requests.get(f"{BASE_URL}/search/works", params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
        for paper in data.get('results', []):
            if paper.get('dataProvider'):
                print(f"  Data Provider: {paper['dataProvider'].get('name', 'Unknown')}")

def main():
    """Run all tests"""
    print("CORE API COMPREHENSIVE TEST")
    print("=" * 60)
    print(f"API Key: {API_KEY[:10]}...")
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Test 1: Basic functionality
    if not test_basic_search():
        print("\n⚠️ Basic search failed. API key might be invalid.")
        return
    
    # Test 2: University search methods
    test_university_search_methods()
    
    # Test 3: Year filtering
    test_year_filter()
    
    # Test 4: Get papers using simple method
    papers_df = get_papers_simple_method()
    
    # Test 5: Data providers
    test_data_providers()
    
    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    
    if not papers_df.empty:
        aus_count = len(papers_df[papers_df['is_australian'] == True])
        if aus_count > 0:
            print(f"✅ Successfully found {aus_count} Australian papers!")
            print("\n💡 SOLUTION: Use broader search terms and filter results")
            print("   Don't rely on institutionName field - it might not work")
            print("   Instead, search broadly and check author affiliations")
        else:
            print("⚠️ Found papers but none from Australian universities")
    else:
        print("❌ No papers found at all")
    
    print("\n📝 Next Steps:")
    print("1. Use simple search queries like 'Australia 2023'")
    print("2. Check author affiliations to identify university")
    print("3. Don't filter too early - get papers first, filter later")

if __name__ == "__main__":
    main()