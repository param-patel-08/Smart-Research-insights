"""
Debug script to check why AU/NZ institutions aren't being found in authorships
"""
import pandas as pd
from config.settings import ALL_UNIVERSITIES

# Load raw data
df = pd.read_csv('data/raw/papers_raw.csv')

# Get AU/NZ university names
australasian_unis = set(ALL_UNIVERSITIES.keys())

# Check papers without AU/NZ universities
non_aus = df[~df['university'].isin(australasian_unis)]

print(f"Total papers: {len(df)}")
print(f"Papers WITH AU/NZ university: {len(df) - len(non_aus)} ({(len(df) - len(non_aus))/len(df)*100:.1f}%)")
print(f"Papers WITHOUT AU/NZ university: {len(non_aus)} ({len(non_aus)/len(df)*100:.1f}%)")

print("\n" + "="*80)
print("Sample of papers WITHOUT AU/NZ university:")
print("="*80)

for idx, row in non_aus.head(5).iterrows():
    print(f"\nPaper ID: {row.get('openalex_id', 'N/A')}")
    print(f"Title: {row['title'][:80]}...")
    print(f"University: {row['university']}")
    print(f"Theme: {row['theme']}")
    
print("\n" + "="*80)
print("EXPLANATION:")
print("="*80)
print("""
These papers are returned by OpenAlex because they match:
1. Institution filter (at least ONE author from AU/NZ institution)
2. Concept filter (matches theme concepts)
3. Date range (2020-2024)

However, the 'university' field shows non-AU/NZ institution because:
- The authorship data in the API response doesn't include institution info
- OR the institution display_name doesn't exactly match our ALL_UNIVERSITIES list
- OR the first author isn't from AU/NZ and we couldn't find the AU/NZ co-author

The parsing code looks through ALL authorships to find AU/NZ institution,
but if OpenAlex doesn't provide complete authorship.institutions data,
we fall back to the first author's first institution.
""")
