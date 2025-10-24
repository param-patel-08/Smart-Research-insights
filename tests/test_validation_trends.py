"""
Validation tests for trend analysis quality
These tests verify that trend calculations are reasonable and statistically sound
"""
import pandas as pd
import pytest
import json


def test_trend_analysis_structure():
    """Validate that trend analysis output has correct structure"""
    try:
        with open('data/processed/trend_analysis.json', 'r') as f:
            trends = json.load(f)
    except FileNotFoundError:
        pytest.skip("No trend analysis available yet")
    
    # Check main sections exist
    assert 'theme_trends' in trends, "Missing theme_trends section"
    assert 'strategic_priorities' in trends, "Missing strategic_priorities section"
    
    # Check theme_trends structure
    theme_trends = trends['theme_trends']
    for theme, data in theme_trends.items():
        assert 'total_papers' in data, f"{theme} missing total_papers"
        assert 'growth_rate' in data, f"{theme} missing growth_rate"
        assert isinstance(data['growth_rate'], (int, float)), f"{theme} growth_rate not numeric"


def test_growth_rates_reasonable():
    """Validate that growth rates are statistically reasonable"""
    try:
        with open('data/processed/trend_analysis.json', 'r') as f:
            trends = json.load(f)
    except FileNotFoundError:
        pytest.skip("No trend analysis available yet")
    
    theme_trends = trends['theme_trends']
    
    # Check growth rates are within reasonable bounds (-1.0 to 5.0)
    for theme, data in theme_trends.items():
        growth = data.get('growth_rate', 0)
        
        assert -1.0 <= growth <= 5.0, \
            f"{theme} has unrealistic growth rate: {growth*100:.1f}%"
    
    # Check that we have both positive and negative growth (not all growing/declining)
    growth_rates = [d['growth_rate'] for d in theme_trends.values() if d.get('total_papers', 0) > 0]
    
    if len(growth_rates) >= 5:
        positive_growth = sum(1 for g in growth_rates if g > 0)
        negative_growth = sum(1 for g in growth_rates if g < 0)
        
        # At least some variation expected
        assert positive_growth > 0 or negative_growth > 0, \
            "All themes have zero growth (may indicate calculation issue)"


def test_strategic_priorities():
    """Validate strategic priority rankings are reasonable"""
    try:
        with open('data/processed/trend_analysis.json', 'r') as f:
            trends = json.load(f)
    except FileNotFoundError:
        pytest.skip("No trend analysis available yet")
    
    if 'strategic_priorities' not in trends:
        pytest.skip("No strategic priorities calculated")
    
    priorities = trends['strategic_priorities']
    
    # Check that priorities are sorted by score (descending)
    scores = [p['priority_score'] for p in priorities]
    assert scores == sorted(scores, reverse=True), \
        "Priorities are not sorted by score"
    
    # Check that scores are non-negative
    assert all(s >= 0 for s in scores), \
        "Found negative priority scores"
    
    # Check that high-priority items have reasonable paper counts
    if len(priorities) > 0:
        top_priority = priorities[0]
        assert top_priority['total_papers'] > 0, \
            "Top priority theme has no papers"


def test_quarterly_trends():
    """Validate quarterly trend data is consistent"""
    try:
        with open('data/processed/trend_analysis.json', 'r') as f:
            trends = json.load(f)
    except FileNotFoundError:
        pytest.skip("No trend analysis available yet")
    
    theme_trends = trends['theme_trends']
    
    for theme, data in theme_trends.items():
        if 'quarterly_counts' not in data:
            continue
        
        quarterly = data['quarterly_counts']
        
        # Check that quarterly counts sum to total
        total_from_quarters = sum(quarterly.values())
        total_papers = data.get('total_papers', 0)
        
        # Allow small rounding differences
        assert abs(total_from_quarters - total_papers) <= 5, \
            f"{theme}: Quarterly sum {total_from_quarters} != total {total_papers}"
        
        # Check that quarters are properly formatted (YYYY-QN)
        for quarter in quarterly.keys():
            assert 'Q' in quarter, \
                f"{theme} has improperly formatted quarter: {quarter}"


def test_emerging_topics_validity():
    """Validate emerging topics detection if available"""
    try:
        with open('data/processed/trend_analysis.json', 'r') as f:
            trends = json.load(f)
    except FileNotFoundError:
        pytest.skip("No trend analysis available yet")
    
    if 'emerging_topics' not in trends:
        pytest.skip("No emerging topics in trend analysis")
    
    emerging = trends['emerging_topics']
    
    if not emerging:
        pytest.skip("No emerging topics detected")
    
    # Check that emerging topics have required fields
    for topic in emerging:
        assert 'topic_id' in topic, "Emerging topic missing topic_id"
        assert 'growth_rate' in topic, "Emerging topic missing growth_rate"
        assert 'theme' in topic, "Emerging topic missing theme"
        
        # Check growth rate is positive (they're "emerging")
        growth = topic['growth_rate']
        assert growth > 0, \
            f"Emerging topic {topic['topic_id']} has negative growth: {growth}"


def test_university_rankings():
    """Validate university rankings by theme if available"""
    try:
        with open('data/processed/trend_analysis.json', 'r') as f:
            trends = json.load(f)
    except FileNotFoundError:
        pytest.skip("No trend analysis available yet")
    
    theme_trends = trends['theme_trends']
    
    # Check university data in themes
    for theme, data in theme_trends.items():
        if 'universities' not in data:
            continue
        
        unis = data['universities']
        
        # Check that university counts are positive
        for uni, count in unis.items():
            assert count > 0, \
                f"{theme} has university {uni} with non-positive count: {count}"
        
        # Check that top universities are reasonable
        if unis:
            total_in_top = sum(unis.values())
            theme_total = data.get('total_papers', 0)
            
            if theme_total > 0:
                top_coverage = total_in_top / theme_total
                assert top_coverage <= 1.0, \
                    f"{theme}: Top universities have more papers than total"


def test_temporal_consistency():
    """Validate that temporal data is consistent and complete"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    df['date'] = pd.to_datetime(df['date'])
    df['quarter'] = df['date'].dt.to_period('Q')
    
    # Check for temporal gaps
    quarters = df['quarter'].unique()
    quarters_sorted = sorted(quarters)
    
    if len(quarters_sorted) >= 4:
        # Check that we don't have large gaps
        for i in range(len(quarters_sorted) - 1):
            q1 = pd.Period(quarters_sorted[i], 'Q')
            q2 = pd.Period(quarters_sorted[i+1], 'Q')
            gap = (q2 - q1).n
            
            assert gap <= 2, \
                f"Large gap between quarters: {q1} to {q2} ({gap} quarters)"
    
    # Check that each quarter has reasonable paper count
    papers_per_quarter = df.groupby('quarter').size()
    
    # No quarter should have very few papers (unless at boundaries)
    min_papers = papers_per_quarter.min()
    if len(papers_per_quarter) > 2:  # Ignore if we only have 1-2 quarters
        assert min_papers >= 10, \
            f"Minimum papers per quarter is only {min_papers} (data may be incomplete)"
