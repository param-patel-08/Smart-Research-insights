"""
Fix papers_processed.csv by merging with papers_raw.csv
"""
import pandas as pd
from pathlib import Path

print("\n" + "="*80)
print("  FIXING papers_processed.csv")
print("="*80 + "\n")

# Load both files
papers_raw = pd.read_csv('data/raw/papers_raw.csv')
papers_processed = pd.read_csv('data/processed/papers_processed.csv')

print(f"papers_raw.csv: {len(papers_raw)} rows, {len(papers_raw.columns)} columns")
print(f"papers_processed.csv: {len(papers_processed)} rows, {len(papers_processed.columns)} columns")

# Merge on title (common column)
merged = pd.merge(
    papers_processed,
    papers_raw,
    on='title',
    how='left',
    suffixes=('_processed', '_raw')
)

# Keep the best columns from each
final_columns = [
    'openalex_id', 'type', 'source_type', 'title', 'abstract', 'date', 'year',
    'authors', 'university', 'journal', 'citations', 'doi',
    'theme', 'concepts', 'confidence_score', 'relevance_score',
    'topic_id', 'topic_probability'
]

# Use _raw columns where available, otherwise use _processed
for col in ['date', 'authors', 'university', 'journal', 'citations']:
    if f'{col}_raw' in merged.columns:
        merged[col] = merged[f'{col}_raw']
    elif f'{col}_processed' in merged.columns:
        merged[col] = merged[f'{col}_processed']

# Select final columns (only those that exist)
available_cols = [col for col in final_columns if col in merged.columns]
merged_final = merged[available_cols]

print(f"\nMerged: {len(merged_final)} rows, {len(merged_final.columns)} columns")
print(f"Columns: {', '.join(merged_final.columns)}")

# Save
merged_final.to_csv('data/processed/papers_processed.csv', index=False)
print(f"\n[OK] Saved fixed papers_processed.csv")

# Verify
print("\nVerifying...")
df = pd.read_csv('data/processed/papers_processed.csv')
print(f"  Rows: {len(df)}")
print(f"  Columns: {', '.join(df.columns.tolist())}")

required = ['openalex_id', 'title', 'year', 'university', 'theme', 'confidence_score', 'topic_id']
missing = [col for col in required if col not in df.columns]
if missing:
    print(f"  [WARNING] Still missing: {missing}")
else:
    print(f"  [OK] All required columns present!")

print("\n" + "="*80)
print("  COMPLETE")
print("="*80 + "\n")
