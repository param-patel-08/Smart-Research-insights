"""
Trend Analyzer for Babcock Research Trends
Analyzes temporal trends across Babcock themes
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Analyze temporal trends across Babcock themes
    """
    
    def __init__(self, topic_theme_mapping: Dict, babcock_themes: Dict):
        """
        Initialize analyzer
        
        Args:
            topic_theme_mapping: Mapping of topics to themes
            babcock_themes: Babcock strategic themes
        """
        self.topic_theme_mapping = topic_theme_mapping
        self.babcock_themes = babcock_themes
        logger.info("Trend Analyzer initialized")
    
    def calculate_growth_rate(self, counts: List[int]) -> float:
        """
        Calculate average quarter-over-quarter growth rate
        
        Args:
            counts: List of paper counts per quarter
            
        Returns:
            Average growth rate (e.g., 0.67 for 67%)
        """
        if len(counts) < 2:
            return 0.0
        
        growth_rates = []
        for i in range(1, len(counts)):
            if counts[i-1] > 0:
                rate = (counts[i] - counts[i-1]) / counts[i-1]
                growth_rates.append(rate)
        
        return np.mean(growth_rates) if growth_rates else 0.0
    
    def analyze_theme_trends(self, 
                            papers_df: pd.DataFrame,
                            topics_over_time: pd.DataFrame = None) -> Dict:
        """
        Analyze trends for each Babcock theme
        
        Args:
            papers_df: DataFrame with papers and topic assignments
            topics_over_time: BERTopic temporal analysis output (optional)
            
        Returns:
            Dictionary with trend data per theme
        """
        logger.info("\n" + "="*80)
        logger.info("ANALYZING TRENDS PER THEME")
        logger.info("="*80)
        
        # Use the original theme from collection if available, otherwise fall back to topic mapping
        if 'theme' not in papers_df.columns:
            logger.info("Using topic-based theme mapping (no original theme column)")
            papers_df['theme'] = papers_df['topic_id'].astype(str).map(
                lambda tid: self.topic_theme_mapping.get(tid, {}).get('theme', 'Uncategorized')
            )
        else:
            logger.info("Using original theme from collection (concept-based)")
        
        # Group by theme and quarter
        papers_df['quarter'] = pd.to_datetime(papers_df['date']).dt.to_period('Q')
        
        theme_trends = {}
        all_themes = list(self.babcock_themes.keys())
        
        for theme in all_themes:
            theme_papers = papers_df[papers_df['theme'] == theme]
            
            if theme_papers.empty:
                theme_trends[theme] = {
                    'total_papers': 0,
                    'growth_rate': 0.0,
                    'quarterly_counts': {},
                    'top_topics': {},
                    'universities': {}
                }
                logger.info(f"  {theme}: 0 papers, +0.0% avg growth (no assignments)")
                continue
            
            quarterly_counts = theme_papers.groupby('quarter').size()
            total_papers = len(theme_papers)
            growth_rate = self.calculate_growth_rate(quarterly_counts.tolist())
            topic_counts = theme_papers['topic_id'].value_counts()
            uni_counts = theme_papers['university'].value_counts()
            
            theme_trends[theme] = {
                'total_papers': int(total_papers),
                'growth_rate': float(growth_rate),
                'quarterly_counts': {str(k): int(v) for k, v in quarterly_counts.to_dict().items()},
                'top_topics': {int(k): int(v) for k, v in topic_counts.head(5).to_dict().items()},
                'universities': {k: int(v) for k, v in uni_counts.head(5).to_dict().items()}
            }
            
            logger.info(f"  {theme}: {total_papers} papers, {growth_rate*100:+.1f}% avg growth")
        
        return theme_trends
    
    def identify_emerging_topics(self,
                                papers_df: pd.DataFrame,
                                threshold: float = 0.5,
                                recent_quarters: int = 2) -> List[Dict]:
        """
        Identify topics with high growth in recent quarters
        
        Args:
            papers_df: DataFrame with papers and topics
            threshold: Minimum growth rate (0.5 = 50%)
            recent_quarters: Number of recent quarters to analyze
            
        Returns:
            List of emerging topics
        """
        logger.info("\nIdentifying emerging topics...")
        
        # Use original theme if available, otherwise map from topics
        if 'theme' not in papers_df.columns:
            papers_df['theme'] = papers_df['topic_id'].astype(str).map(
                lambda tid: self.topic_theme_mapping.get(tid, {}).get('theme', 'Unknown')
            )
        
        # Group by topic and quarter
        papers_df['quarter'] = pd.to_datetime(papers_df['date']).dt.to_period('Q')
        
        emerging = []
        
        for topic_id in papers_df['topic_id'].unique():
            if topic_id == -1:
                continue
            
            topic_papers = papers_df[papers_df['topic_id'] == topic_id]
            quarterly_counts = topic_papers.groupby('quarter').size()
            
            if len(quarterly_counts) < 2:
                continue
            
            # Get counts for recent quarters
            counts = quarterly_counts.tolist()
            
            # Calculate growth
            growth = self.calculate_growth_rate(counts[-recent_quarters:])
            
            if growth > threshold:
                topic_str = str(topic_id)
                theme = self.topic_theme_mapping.get(topic_str, {}).get('theme', 'Unknown')
                keywords = self.topic_theme_mapping.get(topic_str, {}).get('keywords', [])
                
                emerging.append({
                    'topic_id': int(topic_id),
                    'theme': theme,
                    'growth_rate': float(growth),
                    'keywords': keywords,
                    'recent_count': int(counts[-1]) if counts else 0,
                    'previous_count': int(counts[-2]) if len(counts) > 1 else 0
                })
        
        # Sort by growth rate
        emerging.sort(key=lambda x: x['growth_rate'], reverse=True)
        
        logger.info(f"[OK] Found {len(emerging)} emerging topics (>{threshold*100:.0f}% growth)")
        
        return emerging
    
    def rank_universities_by_theme(self, papers_df: pd.DataFrame, theme: str) -> pd.DataFrame:
        """
        Rank universities by output in specific theme
        
        Args:
            papers_df: DataFrame with papers
            theme: Theme name
            
        Returns:
            DataFrame with university rankings
        """
        # Add theme
        papers_df['theme'] = papers_df['topic_id'].astype(str).map(
            lambda tid: self.topic_theme_mapping.get(tid, {}).get('theme', 'Unknown')
        )
        
        theme_papers = papers_df[papers_df['theme'] == theme]
        
        rankings = theme_papers.groupby('university').agg({
            'title': 'count',
            'date': lambda x: (pd.to_datetime(x).max() - pd.to_datetime(x).min()).days
        }).rename(columns={'title': 'paper_count', 'date': 'active_days'})
        
        rankings = rankings.sort_values('paper_count', ascending=False)
        
        return rankings
    
    def calculate_strategic_priority(self, theme_trends: Dict) -> List[Dict]:
        """
        Calculate strategic priority score for each theme
        
        Priority = growth_rate * babcock_relevance_weight * paper_volume_factor
        
        Returns:
            List of themes with priority scores
        """
        logger.info("\nCalculating strategic priorities...")
        
        priorities = []
        
        for theme, data in theme_trends.items():
            # Get Babcock's stated priority for this theme
            babcock_priority = self.babcock_themes.get(theme, {}).get('strategic_priority', 'MEDIUM')
            
            priority_weights = {'HIGH': 1.5, 'MEDIUM': 1.0, 'LOW': 0.5}
            weight = priority_weights.get(babcock_priority, 1.0)
            
            # Calculate composite score
            growth_score = max(0, data['growth_rate'])  # Negative growth = 0
            volume_score = min(1.0, data['total_papers'] / 1000)  # Normalize by volume
            
            priority_score = growth_score * weight * (1 + volume_score)
            
            # Categorize
            if priority_score > 0.75:
                category = 'HIGH'
            elif priority_score > 0.3:
                category = 'MEDIUM'
            else:
                category = 'LOW'
            
            priorities.append({
                'theme': theme,
                'priority_score': float(priority_score),
                'category': category,
                'growth_rate': float(data['growth_rate']),
                'total_papers': int(data['total_papers']),
                'babcock_priority': babcock_priority
            })
        
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        logger.info(f"[OK] Strategic priorities calculated")
        
        return priorities


# ==================== USAGE EXAMPLE ====================

def main():
    """
    Example usage of TrendAnalyzer
    """
    from config.settings import (
        PROCESSED_PAPERS_CSV,
        TOPICS_OVER_TIME_CSV,
        TOPIC_MAPPING_PATH,
        TREND_ANALYSIS_PATH
    )
    from config.themes import BABCOCK_THEMES
    
    logger.info("="*80)
    logger.info("TREND ANALYSIS")
    logger.info("="*80)
    
    # Load data
    logger.info("\nLoading data...")
    papers_df = pd.read_csv(PROCESSED_PAPERS_CSV)
    logger.info(f"[OK] Loaded {len(papers_df)} papers")
    
    # Load theme mapping
    with open(TOPIC_MAPPING_PATH, 'r') as f:
        mapping = json.load(f)
    logger.info(f"[OK] Loaded topic-theme mapping")
    
    # Initialize analyzer
    trend_analyzer = TrendAnalyzer(mapping, BABCOCK_THEMES)
    
    # Analyze trends
    theme_trends = trend_analyzer.analyze_theme_trends(papers_df)
    emerging_topics = trend_analyzer.identify_emerging_topics(papers_df, threshold=0.5)
    strategic_priorities = trend_analyzer.calculate_strategic_priority(theme_trends)
    
    # Show priorities
    logger.info("\n" + "="*80)
    logger.info("STRATEGIC PRIORITIES")
    logger.info("="*80)
    
    for priority in strategic_priorities:
        logger.info(f"\n{priority['theme']} ({priority['category']})")
        logger.info(f"  Growth: {priority['growth_rate']*100:+.1f}%")
        logger.info(f"  Papers: {priority['total_papers']}")
        logger.info(f"  Priority Score: {priority['priority_score']:.2f}")
    
    # Show top emerging topics
    logger.info("\n" + "="*80)
    logger.info("TOP 5 EMERGING TOPICS")
    logger.info("="*80)
    
    for topic in emerging_topics[:5]:
        logger.info(f"\nTopic {topic['topic_id']} ({topic['theme']})")
        logger.info(f"  Keywords: {', '.join(topic['keywords'][:5])}")
        logger.info(f"  Growth: {topic['growth_rate']*100:+.1f}%")
        logger.info(f"  Recent papers: {topic['recent_count']}")
    
    # Save results
    logger.info("\nSaving results...")
    results = {
        'theme_trends': theme_trends,
        'emerging_topics': emerging_topics,
        'strategic_priorities': strategic_priorities
    }
    
    with open(TREND_ANALYSIS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"[OK] Saved trend analysis to {TREND_ANALYSIS_PATH}")
    logger.info("\n[OK] Trend analysis complete!")


if __name__ == "__main__":
    main()
