"""
Quick Results Viewer for Babcock Research Trends
View analysis results without launching the dashboard
"""

import json
import pandas as pd
from config.settings import (
    PROCESSED_PAPERS_CSV,
    TREND_ANALYSIS_PATH,
    TOPIC_MAPPING_PATH
)


def print_banner(text):
    """Print a nice banner"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")


def main():
    """Display analysis results"""
    
    print_banner("BABCOCK RESEARCH TRENDS - RESULTS SUMMARY")
    
    # Load data
    try:
        papers_df = pd.read_csv(PROCESSED_PAPERS_CSV)
        with open(TREND_ANALYSIS_PATH, 'r') as f:
            trends = json.load(f)
        with open(TOPIC_MAPPING_PATH, 'r') as f:
            mapping = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Error: Results files not found. Run the analysis first!")
        print(f"   Missing file: {e.filename}")
        print(f"\n   Run: python run_full_analysis.py")
        return
    
    # ==================== OVERVIEW ====================
    
    print_banner("OVERVIEW")
    
    print(f"📄 Total Papers Analyzed: {len(papers_df):,}")
    print(f"🔬 Topics Discovered: {len(mapping)}")
    print(f"🎯 Strategic Themes: 9")
    print(f"🏛️  Universities: {papers_df['university'].nunique()}")
    print(f"📅 Date Range: {papers_df['date'].min()} to {papers_df['date'].max()}")
    
    # ==================== STRATEGIC PRIORITIES ====================
    
    print_banner("STRATEGIC PRIORITIES")
    
    priorities = trends['strategic_priorities']
    
    for i, priority in enumerate(priorities, 1):
        theme = priority['theme'].replace('_', ' ').title()
        category = priority['category']
        growth = priority['growth_rate']
        papers = priority['total_papers']
        
        # Emoji based on category
        emoji = "🚀" if category == "HIGH" else "📈" if category == "MEDIUM" else "➡️"
        
        print(f"{i}. {emoji} {theme} ({category})")
        print(f"   Growth: {growth*100:+.1f}% | Papers: {papers:,}")
        print()
    
    # ==================== EMERGING TOPICS ====================
    
    print_banner("TOP 10 EMERGING TOPICS")
    
    emerging = trends['emerging_topics'][:10]
    
    for i, topic in enumerate(emerging, 1):
        keywords = ', '.join(topic['keywords'][:5])
        theme = topic['theme'].replace('_', ' ').title()
        growth = topic['growth_rate']
        count = topic['recent_count']
        
        print(f"{i}. {keywords}")
        print(f"   Theme: {theme} | Growth: {growth*100:+.1f}% | Papers: {count}")
        print()
    
    # ==================== THEME BREAKDOWN ====================
    
    print_banner("PAPERS PER THEME")
    
    # Add theme to papers
    papers_df['theme'] = papers_df['topic_id'].astype(str).map(
        lambda tid: mapping.get(tid, {}).get('theme', 'Other')
    )
    
    theme_counts = papers_df['theme'].value_counts()
    
    for theme, count in theme_counts.items():
        if theme == 'Other':
            continue
        percentage = count / len(papers_df) * 100
        bar = "█" * int(percentage / 2)
        print(f"{theme.replace('_', ' ').title():30s} {bar} {count:4d} ({percentage:5.1f}%)")
    
    # ==================== TOP UNIVERSITIES ====================
    
    print_banner("TOP 10 UNIVERSITIES BY OUTPUT")
    
    uni_counts = papers_df['university'].value_counts().head(10)
    
    for i, (uni, count) in enumerate(uni_counts.items(), 1):
        percentage = count / len(papers_df) * 100
        print(f"{i:2d}. {uni:40s} {count:4d} papers ({percentage:5.1f}%)")
    
    # ==================== TEMPORAL TRENDS ====================
    
    print_banner("QUARTERLY TREND")
    
    papers_df['quarter'] = pd.to_datetime(papers_df['date']).dt.to_period('Q')
    quarterly = papers_df.groupby('quarter').size()
    
    print("Papers published per quarter:\n")
    
    max_count = quarterly.max()
    for quarter, count in quarterly.items():
        bar_length = int((count / max_count) * 40)
        bar = "█" * bar_length
        print(f"{str(quarter):8s} {bar} {count:4d}")
    
    # ==================== NEXT STEPS ====================
    
    print_banner("NEXT STEPS")
    
    print("📊 Launch Interactive Dashboard:")
    print("   streamlit run dashboard/app.py")
    print()
    print("📄 Generate PDF Report:")
    print("   python scripts/generate_report.py")
    print()
    print("🔍 Explore Data:")
    print(f"   Papers: {PROCESSED_PAPERS_CSV}")
    print(f"   Trends: {TREND_ANALYSIS_PATH}")
    print(f"   Mapping: {TOPIC_MAPPING_PATH}")
    
    print_banner("✓ RESULTS DISPLAYED")


if __name__ == "__main__":
    main()