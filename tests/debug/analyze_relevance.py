"""Quick analysis of relevance filtering results."""
import pandas as pd

df = pd.read_csv('data/raw/papers_theme_filtered.csv')

print(f"Total papers: {len(df)}")
print(f"\nRelevance score distribution:")
print(df['relevance_score'].describe())

print(f"\n{'='*100}")
print("SAMPLE PAPERS BY RELEVANCE LEVEL")
print('='*100)

print("\n🔥 HIGH RELEVANCE (>0.7):")
high = df[df['relevance_score'] > 0.7].head(5)
for i, row in high.iterrows():
    print(f"\n{row['relevance_score']:.3f} - {row['title']}")
    print(f"       Theme: {row['theme']}")
    print(f"       Concepts: {row['concepts'][:120]}...")

print("\n\n⚡ MEDIUM RELEVANCE (0.6-0.7):")
med = df[(df['relevance_score'] >= 0.6) & (df['relevance_score'] < 0.7)].head(5)
for i, row in med.iterrows():
    print(f"\n{row['relevance_score']:.3f} - {row['title']}")
    print(f"       Theme: {row['theme']}")
    print(f"       Concepts: {row['concepts'][:120]}...")

print("\n\n⚠️  BORDERLINE (0.5-0.6):")
border = df[(df['relevance_score'] >= 0.5) & (df['relevance_score'] < 0.6)].head(5)
for i, row in border.iterrows():
    print(f"\n{row['relevance_score']:.3f} - {row['title']}")
    print(f"       Theme: {row['theme']}")
    print(f"       Concepts: {row['concepts'][:120]}...")

print("\n\n📊 Theme distribution:")
print(df['theme'].value_counts())
