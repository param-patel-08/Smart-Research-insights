"""Test AI/ML theme query to debug low paper counts"""
from config.themes import BABCOCK_THEMES

theme = BABCOCK_THEMES['AI_Machine_Learning']
keywords = theme['keywords'][:30]
query = ' OR '.join(keywords)

print("AI/ML Query (first 30 keywords):")
print(query[:500])
print("...")
print(f"\nTotal keywords: {len(theme['keywords'])}")
print(f"Keywords used in query: 30")

print("\n" + "="*80)
print("PROBLEM ANALYSIS:")
print("="*80)

# Check for overlaps with other themes
print("\nChecking keyword overlaps with other themes:")
ai_keywords = set(theme['keywords'])

for other_theme, other_data in BABCOCK_THEMES.items():
    if other_theme == 'AI_Machine_Learning':
        continue
    other_keywords = set(other_data['keywords'])
    overlap = ai_keywords.intersection(other_keywords)
    if overlap:
        print(f"\n{other_theme}: {len(overlap)} overlapping keywords")
        print(f"  {list(overlap)[:5]}...")

print("\n" + "="*80)
print("ISSUE: AI/ML papers likely being captured by Autonomous_Systems theme!")
print("="*80)
print("\nSolution: Separate AI/ML into its own category with unique keywords")
print("          OR: Accept that AI/ML is integrated into other themes")
