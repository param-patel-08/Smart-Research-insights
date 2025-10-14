"""
Test the actual AI/ML query being used in the collection
"""
import requests
from config.settings import ALL_UNIVERSITIES, OPENALEX_EMAIL
from config.themes import BABCOCK_THEMES

# Get AI/ML keywords
aiml_keywords = BABCOCK_THEMES['AI_Machine_Learning']['keywords'][:30]
keyword_query = ' OR '.join(aiml_keywords)

# Build filters exactly as theme_based_collector does
filters = []
filters.append("from_publication_date:2020-01-01")
filters.append("to_publication_date:2024-12-31")

# Get university IDs
institution_ids = '|'.join(ALL_UNIVERSITIES.values())
filters.append(f"institutions.id:{institution_ids}")

# Add keyword search
filters.append(f"title_and_abstract.search:{keyword_query}")

# Build request
params = {
    'filter': ','.join(filters),
    'per-page': 10,
    'cursor': '*',
    'mailto': OPENALEX_EMAIL,
    'select': 'id,title,publication_year'
}

print("TESTING ACTUAL AI/ML QUERY")
print("="*80)
print(f"\nKeywords (first 30): {keyword_query[:200]}...")
print(f"\nUniversities: {len(ALL_UNIVERSITIES)} institutions")
print(f"\nDate range: 2020-01-01 to 2024-12-31")
print("\nFull filter string:")
print(','.join(filters))
print("\n" + "="*80)

try:
    response = requests.get('https://api.openalex.org/works', params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    results = data.get('results', [])
    meta = data.get('meta', {})
    
    print(f"\n✓ Query SUCCESS!")
    print(f"Results found: {meta.get('count', 0)}")
    print(f"Results in this page: {len(results)}")
    
    if results:
        print(f"\nSample papers:")
        for i, work in enumerate(results[:5], 1):
            print(f"  {i}. [{work.get('publication_year')}] {work.get('title', 'No title')}")
    else:
        print("\n✗ No results found!")
        print("\nPossible issues:")
        print("1. Keyword query too complex (92 keywords with OR)")
        print("2. None of these keywords match papers from these 43 universities")
        print("3. OpenAlex filter syntax issue")
        
except Exception as e:
    print(f"\n✗ Query FAILED: {e}")
    print("\nTrying simplified query...")
    
    # Try with just 5 keywords
    simple_keywords = ' OR '.join(aiml_keywords[:5])
    filters[-1] = f"title_and_abstract.search:{simple_keywords}"
    params['filter'] = ','.join(filters)
    
    print(f"\nSimplified keywords: {simple_keywords}")
    
    try:
        response = requests.get('https://api.openalex.org/works', params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        meta = data.get('meta', {})
        
        print(f"\n✓ Simplified query SUCCESS!")
        print(f"Results found: {meta.get('count', 0)}")
        print(f"Results in this page: {len(results)}")
        
        if meta.get('count', 0) > 0:
            print("\n🔥 PROBLEM IDENTIFIED: Query has TOO MANY keywords!")
            print(f"   With 5 keywords: {meta.get('count', 0)} papers")
            print(f"   With 30 keywords: 0 papers")
            print("\n   Solution: Use fewer, more specific keywords for AI/ML")
            
    except Exception as e2:
        print(f"✗ Simplified query also failed: {e2}")
