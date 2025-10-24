"""
Validation tests for topic modeling quality
These tests verify that discovered topics are coherent and meaningful
"""
import pandas as pd
import pytest
import json


def test_topic_coherence():
    """Validate that topic keywords are semantically coherent"""
    try:
        with open('data/processed/topic_mapping.json', 'r') as f:
            mapping = json.load(f)
    except FileNotFoundError:
        pytest.skip("No topic mapping available yet")
    
    # Check that topics have keywords
    topics_with_keywords = sum(1 for t in mapping.values() if t.get('keywords'))
    assert topics_with_keywords >= len(mapping) * 0.90, \
        "Not all topics have keywords assigned"
    
    # Check keyword diversity (not all the same)
    all_keywords = []
    for topic_data in mapping.values():
        all_keywords.extend(topic_data.get('keywords', [])[:5])
    
    unique_keywords = len(set(all_keywords))
    total_keywords = len(all_keywords)
    
    if total_keywords > 0:
        diversity = unique_keywords / total_keywords
        assert diversity >= 0.70, \
            f"Keyword diversity {diversity*100:.1f}% is too low (topics may be too similar)"


def test_topic_size_distribution():
    """Validate that topics have reasonable paper counts"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    topic_sizes = df[df['topic_id'] != -1].groupby('topic_id').size()
    
    # Check minimum topic size
    min_size = topic_sizes.min()
    assert min_size >= 5, \
        f"Smallest topic has only {min_size} papers (too small)"
    
    # Check that no topic is too large (>30% of papers)
    max_size = topic_sizes.max()
    max_pct = max_size / len(df)
    assert max_pct <= 0.30, \
        f"Largest topic has {max_pct*100:.1f}% of papers (too dominant)"
    
    # Check reasonable number of topics (not too many, not too few)
    num_topics = len(topic_sizes)
    num_papers = len(df)
    papers_per_topic = num_papers / num_topics
    
    # Adjusted for larger dataset
    assert 10 <= papers_per_topic <= 500, \
        f"Average {papers_per_topic:.0f} papers per topic (may need tuning)"


def test_confidence_scores():
    """Validate that confidence scores are reasonable and well-distributed"""
    try:
        df = pd.read_csv('data/processed/papers_processed.csv')
    except FileNotFoundError:
        pytest.skip("No processed data available yet")
    
    if 'confidence' not in df.columns:
        pytest.skip("No confidence scores available")
    
    # Filter out outliers
    assigned_papers = df[df['topic_id'] != -1].copy()
    
    if len(assigned_papers) == 0:
        pytest.skip("No assigned papers")
    
    # Normalize confidence to 0-1 range if it's in percentage
    confidence = assigned_papers['confidence'].copy()
    if confidence.max() > 1.0:
        confidence = confidence / 100
    
    # Check mean confidence
    mean_conf = confidence.mean()
    assert mean_conf >= 0.40, \
        f"Mean confidence {mean_conf:.3f} is too low (poor topic assignments)"
    
    # Check that confidence varies (not all the same)
    std_conf = confidence.std()
    assert std_conf >= 0.05, \
        f"Confidence standard deviation {std_conf:.3f} is too low (no variation)"
    
    # Check distribution - should have some high confidence papers
    high_conf_rate = (confidence >= 0.70).sum() / len(confidence)
    assert high_conf_rate >= 0.30, \
        f"Only {high_conf_rate*100:.1f}% of papers have high confidence (>70%)"


def test_theme_mapping_quality():
    """Validate that topic-to-theme mapping is reasonable"""
    try:
        with open('data/processed/topic_mapping.json', 'r') as f:
            mapping = json.load(f)
    except FileNotFoundError:
        pytest.skip("No topic mapping available yet")
    
    from config.themes import STRATEGIC_THEMES
    
    # Check that most topics are mapped to known themes
    mapped_themes = [t.get('theme') for t in mapping.values()]
    valid_themes = set(STRATEGIC_THEMES.keys()) | {'Other'}
    
    invalid_mappings = [t for t in mapped_themes if t not in valid_themes]
    assert len(invalid_mappings) == 0, \
        f"Found {len(invalid_mappings)} topics mapped to invalid themes"
    
    # Check confidence scores in mapping
    confidences = [t.get('confidence', 0) for t in mapping.values()]
    
    if confidences:
        mean_mapping_conf = sum(confidences) / len(confidences)
        assert mean_mapping_conf >= 0.01, \
            f"Mean mapping confidence {mean_mapping_conf:.3f} is very low"


def test_cross_theme_topics():
    """Validate cross-theme topics are reasonable"""
    try:
        with open('data/processed/topic_mapping.json', 'r') as f:
            mapping = json.load(f)
    except FileNotFoundError:
        pytest.skip("No topic mapping available yet")
    
    # Count topics with multiple strong theme associations
    cross_theme_count = 0
    for topic_data in mapping.values():
        all_scores = topic_data.get('all_scores', {})
        strong_themes = [t for t, score in all_scores.items() if score >= 0.3]
        if len(strong_themes) > 1:
            cross_theme_count += 1
    
    # Some cross-theme topics are expected, but not too many
    cross_theme_rate = cross_theme_count / len(mapping)
    assert cross_theme_rate <= 0.20, \
        f"{cross_theme_rate*100:.1f}% of topics are cross-theme (may indicate overlap)"


def test_sub_theme_mapping():
    """Validate sub-theme assignments if hierarchical mapping is used"""
    try:
        with open('data/processed/topic_mapping.json', 'r') as f:
            mapping = json.load(f)
    except FileNotFoundError:
        pytest.skip("No topic mapping available yet")
    
    # Check if sub-themes are being used
    topics_with_subtheme = sum(1 for t in mapping.values() if t.get('sub_theme'))
    
    if topics_with_subtheme == 0:
        pytest.skip("No sub-theme mapping in use")
    
    # If sub-themes are used, check coverage
    sub_theme_rate = topics_with_subtheme / len(mapping)
    assert sub_theme_rate >= 0.50, \
        f"Only {sub_theme_rate*100:.1f}% of topics have sub-themes (low coverage)"
    
    # Check sub-theme confidence scores
    sub_confidences = [
        t.get('sub_theme_confidence', 0) 
        for t in mapping.values() 
        if t.get('sub_theme')
    ]
    
    if sub_confidences:
        mean_sub_conf = sum(sub_confidences) / len(sub_confidences)
        assert mean_sub_conf >= 0.01, \
            f"Mean sub-theme confidence {mean_sub_conf:.3f} is very low"
