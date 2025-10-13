"""
Quick verification script to check if dashboard data is ready
"""
import pandas as pd
import json
from pathlib import Path

print("\n" + "="*80)
print("  DASHBOARD DATA VERIFICATION")
print("="*80 + "\n")

# Check required files
required_files = {
    'papers_processed.csv': 'data/processed/papers_processed.csv',
    'trend_analysis.json': 'data/processed/trend_analysis.json',
    'topic_mapping.json': 'data/processed/topic_mapping.json'
}

all_exist = True
for name, path in required_files.items():
    if Path(path).exists():
        print(f"[OK] {name}: EXISTS")
    else:
        print(f"[MISSING] {name}: MISSING")
        all_exist = False

if not all_exist:
    print("\n[ERROR] Some required files are missing!")
    print("Run: python run_steps_3_to_5.py")
    exit(1)

print("\n" + "-"*80)
print("CHECKING DATA QUALITY")
print("-"*80 + "\n")

# Load and check papers
papers = pd.read_csv('data/processed/papers_processed.csv')
print(f"Papers: {len(papers)} total")
print(f"   Columns: {', '.join(papers.columns.tolist())}")

# Check required columns
required_cols = ['openalex_id', 'title', 'year', 'university', 'theme', 'confidence_score']
missing_cols = [col for col in required_cols if col not in papers.columns]
if missing_cols:
    print(f"   [WARNING] Missing columns: {missing_cols}")
else:
    print(f"   [OK] All required columns present")

# Check theme distribution
print(f"\nTheme Distribution:")
theme_counts = papers['theme'].value_counts() if 'theme' in papers.columns else pd.Series()
for theme, count in theme_counts.items():
    print(f"   {theme}: {count} papers")

if len(theme_counts) == 0:
    print("   [WARNING] No theme column found!")
elif len(theme_counts) < 3:
    print(f"   [WARNING] Only {len(theme_counts)} themes have papers (expected 7-9)")

# Check year range
if 'year' in papers.columns:
    print(f"\nYear Range: {papers['year'].min()} - {papers['year'].max()}")

# Check universities
if 'university' in papers.columns:
    print(f"\nUniversities: {papers['university'].nunique()} unique")

# Check confidence scores
if 'confidence_score' in papers.columns:
    print(f"\nConfidence Scores:")
    print(f"   Mean: {papers['confidence_score'].mean():.2f}")
    print(f"   Range: {papers['confidence_score'].min():.2f} - {papers['confidence_score'].max():.2f}")
    
    # Distribution
    score_dist = papers['confidence_score'].value_counts().sort_index()
    for score, count in score_dist.items():
        print(f"   {score}: {count} papers ({count/len(papers)*100:.1f}%)")

# Check trend analysis
print(f"\n" + "-"*80)
print("CHECKING TREND ANALYSIS")
print("-"*80 + "\n")

with open('data/processed/trend_analysis.json', 'r') as f:
    trends = json.load(f)

print(f"Trend Analysis Keys: {list(trends.keys())}")

if 'theme_trends' in trends:
    theme_list = trends['theme_trends'] if isinstance(trends['theme_trends'], list) else list(trends['theme_trends'].values())
    print(f"   Theme Trends: {len(theme_list)} themes")
    for theme_data in theme_list[:3]:  # Show first 3
        theme = theme_data.get('theme', 'Unknown')
        papers = theme_data.get('total_papers', 0)
        growth = theme_data.get('avg_growth_rate', 0)
        print(f"   - {theme}: {papers} papers, {growth:.1f}% growth")

if 'emerging_topics' in trends:
    print(f"   Emerging Topics: {len(trends['emerging_topics'])}")

# Check topic mapping
print(f"\n" + "-"*80)
print("CHECKING TOPIC MAPPING")
print("-"*80 + "\n")

with open('data/processed/topic_mapping.json', 'r') as f:
    mapping = json.load(f)

print(f"Topic Mapping: {len(mapping)} topics mapped")
for topic_id, topic_data in list(mapping.items())[:3]:  # Show first 3
    theme = topic_data.get('primary_theme', 'Unknown')
    conf = topic_data.get('confidence', 0)
    print(f"   Topic {topic_id}: {theme} (confidence: {conf:.2f})")

print("\n" + "="*80)
print("  VERIFICATION COMPLETE")
print("="*80)
print("\n[OK] Dashboard is ready to launch!")
print("\nRun: python launch_dashboard.py")
print("Or:  streamlit run dashboard/app.py")
print()
