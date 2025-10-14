"""
Debug: Why is AI/ML getting so few papers?

Hypothesis 1: Keywords are too generic/common - every paper mentions "data analytics"
Hypothesis 2: Papers are captured by other themes first (Autonomous, Cybersecurity, etc.)
Hypothesis 3: Australasian universities don't publish much standalone AI/ML research
Hypothesis 4: OpenAlex search is too strict with compound terms

Let's test the actual OpenAlex query
"""

import requests
from config.settings import OPENALEX_EMAIL, ALL_UNIVERSITIES
from config.themes import BABCOCK_THEMES

# Build AI/ML query
theme_data = BABCOCK_THEMES['AI_Machine_Learning']
keywords = theme_data['keywords'][:30]
query = ' OR '.join(keywords)

# Test with 3 universities
test_unis = dict(list(ALL_UNIVERSITIES.items())[:3])
institution_ids = '|'.join(test_unis.values())

# Build OpenAlex filter
filters = []
filters.append(f"from_publication_date:2020-01-01")
filters.append(f"to_publication_date:2024-12-31")
filters.append(f"institutions.id:{institution_ids}")
filters.append(f"title_and_abstract.search:{query}")

params = {
    'filter': ','.join(filters),
    'per-page': 10,
    'cursor': '*',
    'mailto': OPENALEX_EMAIL
}

print("Testing AI/ML query with OpenAlex...")
print(f"Query: {query[:200]}...")
print(f"\nUniversities: {list(test_unis.keys())}")

response = requests.get('https://api.openalex.org/works', params=params, timeout=30)
data = response.json()

results = data.get('results', [])
meta = data.get('meta', {})
total_count = meta.get('count', 0)

print(f"\n✓ Total AI/ML papers found: {total_count}")
print(f"✓ Sample returned: {len(results)}")

if results:
    print("\nSample papers:")
    for i, work in enumerate(results[:5], 1):
        title = work.get('title', 'No title')
        year = work.get('publication_year', 'Unknown')
        print(f"{i}. [{year}] {title[:80]}...")
else:
    print("\n❌ NO PAPERS FOUND!")
    print("\nThis suggests:")
    print("1. Keywords might be too specific")
    print("2. OR Australasian universities don't have many standalone AI/ML papers")
    print("3. OR AI/ML research is embedded in other domains (autonomous, defense, etc.)")
