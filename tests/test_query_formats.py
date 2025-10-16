"""Test different query formats for OpenAlex"""
import requests
from config.settings import OPENALEX_EMAIL, ALL_UNIVERSITIES

test_unis = dict(list(ALL_UNIVERSITIES.items())[:3])
institution_ids = '|'.join(test_unis.values())

base_filters = [
    f"from_publication_date:2020-01-01",
    f"to_publication_date:2024-12-31",
    f"institutions.id:{institution_ids}"
]

# Test 1: Multi-word terms with spaces (current approach)
test1_query = "artificial intelligence OR machine learning OR deep learning"
filters1 = base_filters + [f"title_and_abstract.search:{test1_query}"]
params1 = {'filter': ','.join(filters1), 'per-page': 1, 'mailto': OPENALEX_EMAIL}
response1 = requests.get('https://api.openalex.org/works', params=params1, timeout=30)
count1 = response1.json().get('meta', {}).get('count', 0)
print(f"Test 1 - Multi-word with spaces: {count1} papers")
print(f"  Query: {test1_query}")

# Test 2: Simpler single-word terms
test2_query = "learning OR intelligence OR robotics"
filters2 = base_filters + [f"title_and_abstract.search:{test2_query}"]
params2 = {'filter': ','.join(filters2), 'per-page': 1, 'mailto': OPENALEX_EMAIL}
response2 = requests.get('https://api.openalex.org/works', params=params2, timeout=30)
count2 = response2.json().get('meta', {}).get('count', 0)
print(f"\nTest 2 - Single words: {count2} papers")
print(f"  Query: {test2_query}")

# Test 3: Just "machine learning" alone
test3_query = "machine learning"
filters3 = base_filters + [f"title_and_abstract.search:{test3_query}"]
params3 = {'filter': ','.join(filters3), 'per-page': 1, 'mailto': OPENALEX_EMAIL}
response3 = requests.get('https://api.openalex.org/works', params=params3, timeout=30)
count3 = response3.json().get('meta', {}).get('count', 0)
print(f"\nTest 3 - Just 'machine learning': {count3} papers")
print(f"  Query: {test3_query}")

# Test 4: Quoted phrases
test4_query = '"machine learning" OR "deep learning" OR "neural network"'
filters4 = base_filters + [f"title_and_abstract.search:{test4_query}"]
params4 = {'filter': ','.join(filters4), 'per-page': 1, 'mailto': OPENALEX_EMAIL}
response4 = requests.get('https://api.openalex.org/works', params=params4, timeout=30)
count4 = response4.json().get('meta', {}).get('count', 0)
print(f"\nTest 4 - Quoted phrases: {count4} papers")
print(f"  Query: {test4_query}")

print("\n" + "="*80)
if count3 > 0:
    print("✓ Solution: Multi-word terms work fine!")
    print("  The problem must be elsewhere (relevance filtering, deduplication, etc.)")
else:
    print("✗ Problem: Multi-word search terms are not working!")
    print("  Need to fix query building logic")
