import pandas as pd
from config.settings import ALL_UNIVERSITIES

# Check test universities
test_unis = dict(list(ALL_UNIVERSITIES.items())[:3])
print("Test universities being queried:")
for name, uni_id in test_unis.items():
    print(f"  - {name} (ID: {uni_id})")

# Check what's in raw data
df = pd.read_csv('data/raw/papers_raw.csv')
print(f"\nTop 10 universities in collected data:")
print(df['university'].value_counts().head(10))

# Check if ANY are AU/NZ
australasian_unis = set(ALL_UNIVERSITIES.keys())
aus_count = df[df['university'].isin(australasian_unis)]['university'].value_counts()
print(f"\nAU/NZ universities found ({len(aus_count)} total):")
print(aus_count)

# Sample a few papers to see what's happening
print("\nSample of 5 papers:")
for idx, row in df.head(5).iterrows():
    print(f"\n  {idx+1}. {row['title'][:60]}...")
    print(f"     University: {row['university']}")
