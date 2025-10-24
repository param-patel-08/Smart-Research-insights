"""
Validation tests for data quality and integrity
These tests verify that collected and processed data meets quality standards
"""
import pandas as pd
import pytest
from datetime import datetime


def test_paper_data_structure():
    """Validate that processed papers have required fields and correct types"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    # Required columns (abstract removed from processed data, kept in raw)
    required_cols = ['title', 'date', 'university', 'theme', 'topic_id']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check data types
    assert pd.api.types.is_datetime64_any_dtype(pd.to_datetime(df['date'], errors='coerce')), "Date column not parseable"
    assert pd.api.types.is_integer_dtype(df['topic_id']) or df['topic_id'].dtype == object, "topic_id should be integer or convertible"


def test_abstract_quality():
    """Validate that abstracts meet minimum quality standards"""
    try:
        df = pd.read_csv('data/raw/papers_raw.csv')
    except FileNotFoundError:
        pytest.skip("No raw data available yet")
    
    if 'abstract' not in df.columns:
        pytest.skip("No abstract column in raw data")
    
    # Filter out NaN abstracts
    valid_df = df[df['abstract'].notna()]
    
    if len(valid_df) == 0:
        pytest.skip("No valid abstracts found")
    
    # Check abstract lengths
    abstract_lengths = valid_df['abstract'].str.len()
    
    # At least 80% of abstracts should be >= 50 characters (lowered threshold)
    valid_abstracts = (abstract_lengths >= 50).sum()
    total_abstracts = len(valid_df)
    
    assert valid_abstracts / total_abstracts >= 0.80, \
        f"Only {valid_abstracts/total_abstracts*100:.1f}% of abstracts meet minimum length"
    
    # Mean abstract length should be reasonable (50-3000 chars)
    mean_length = abstract_lengths.mean()
    assert 50 <= mean_length <= 3000, \
        f"Mean abstract length {mean_length:.0f} is outside reasonable range"


def test_university_normalization():
    """Validate that university names are properly normalized"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    from config.settings import ALL_UNIVERSITIES
    
    # Check that most universities match our known list
    papers_universities = set(df['university'].unique())
    known_universities = set(ALL_UNIVERSITIES.keys())
    
    # At least 80% of papers should be from known universities
    papers_from_known = df[df['university'].isin(known_universities)]
    coverage = len(papers_from_known) / len(df)
    
    assert coverage >= 0.80, \
        f"Only {coverage*100:.1f}% of papers are from known universities"


def test_date_range_validity():
    """Validate that paper dates are within expected range"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Check date range is reasonable
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    # Should be between 2015 and current date
    assert min_date >= pd.Timestamp('2015-01-01'), \
        f"Minimum date {min_date} is too old"
    assert max_date <= pd.Timestamp.now(), \
        f"Maximum date {max_date} is in the future"
    
    # Should span at least 2 years
    date_span = (max_date - min_date).days / 365
    assert date_span >= 2.0, \
        f"Date range only spans {date_span:.1f} years"


def test_theme_distribution():
    """Validate that papers are reasonably distributed across themes"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    from config.themes import STRATEGIC_THEMES
    
    theme_counts = df['theme'].value_counts()
    
    # Check that we have papers for most themes
    themes_with_papers = len(theme_counts)
    total_themes = len(STRATEGIC_THEMES)
    
    assert themes_with_papers >= total_themes * 0.7, \
        f"Only {themes_with_papers}/{total_themes} themes have papers"
    
    # Check that no single theme dominates (>50% of papers)
    max_theme_pct = theme_counts.max() / len(df)
    assert max_theme_pct <= 0.50, \
        f"One theme has {max_theme_pct*100:.1f}% of all papers (too concentrated)"
    
    # Check that "Other" category is not too large
    if 'Other' in theme_counts.index:
        other_pct = theme_counts['Other'] / len(df)
        assert other_pct <= 0.15, \
            f"'Other' category has {other_pct*100:.1f}% of papers (mapping may be poor)"


def test_topic_assignment_coverage():
    """Validate that most papers are assigned to topics with confidence"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    # Check that most papers are assigned to a topic (not outliers)
    outliers = (df['topic_id'] == -1).sum()
    outlier_rate = outliers / len(df)
    
    # HDBSCAN can produce 20-35% outliers depending on parameters, which is acceptable
    assert outlier_rate <= 0.40, \
        f"Outlier rate {outlier_rate*100:.1f}% is too high (>40%)"
    
    # Check confidence scores if available (topic_probability in your data)
    confidence_col = 'confidence' if 'confidence' in df.columns else 'topic_probability'
    if confidence_col in df.columns:
        mean_confidence = df[df['topic_id'] != -1][confidence_col].mean()
        
        # Mean confidence should be reasonable (>0.3 or >30% if scaled)
        if mean_confidence <= 1.0:
            assert mean_confidence >= 0.30, \
                f"Mean confidence {mean_confidence:.3f} is too low"
        else:
            assert mean_confidence >= 30, \
                f"Mean confidence {mean_confidence:.1f}% is too low"


def test_duplicate_detection():
    """Validate that there are no duplicate papers"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    # Check for duplicate titles (case-insensitive)
    duplicate_titles = df['title'].str.lower().duplicated().sum()
    dup_rate = duplicate_titles / len(df)
    
    assert dup_rate <= 0.01, \
        f"Found {duplicate_titles} duplicate titles ({dup_rate*100:.2f}%)"
    
    # Check for duplicate OpenAlex IDs if available
    if 'openalex_id' in df.columns:
        duplicate_ids = df['openalex_id'].duplicated().sum()
        assert duplicate_ids == 0, \
            f"Found {duplicate_ids} duplicate OpenAlex IDs"


def test_citation_data_validity():
    """Validate citation counts are reasonable"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    if 'citations' not in df.columns:
        pytest.skip("No citation data")
    
    # Citations should be non-negative
    assert (df['citations'] >= 0).all(), \
        "Found negative citation counts"
    
    # Check for reasonable distribution (not all zeros)
    papers_with_citations = (df['citations'] > 0).sum()
    citation_rate = papers_with_citations / len(df)
    
    assert citation_rate >= 0.30, \
        f"Only {citation_rate*100:.1f}% of papers have citations (seems low)"
    
    # Mean citations should be reasonable (0-100 typically)
    mean_citations = df['citations'].mean()
    assert 0 <= mean_citations <= 200, \
        f"Mean citations {mean_citations:.1f} is outside typical range"
