from src.paper_collector import PaperCollector
from datetime import datetime
import pandas as pd


def test_build_theme_query_and_relevance():
    collector = PaperCollector(email='tester@example.com', start_date=datetime(2020, 1, 1), end_date=datetime(2021, 1, 1))
    # Use a theme from the config; this tests that the query builds and scoring runs
    from config.themes import STRATEGIC_THEMES
    theme = list(STRATEGIC_THEMES.keys())[0]
    q = collector.build_theme_query(theme, top_n_keywords=5)
    assert isinstance(q, str) and len(q) > 0

    # Basic paper dict for relevance scoring
    paper = {
        'title': 'Autonomous system design study',
        'abstract': 'We propose a design for autonomous maritime system with sensors and control.',
        'concepts': 'maritime; robotics'
    }
    score = collector.calculate_relevance_score(paper, theme)
    assert 0.0 <= score <= 1.0

    # Filter_by_relevance should return input schema with relevance_score column
    df = pd.DataFrame([{
        'title': paper['title'],
        'abstract': paper['abstract'],
        'theme': theme,
        'date': '2020-06-01',
        'university': 'Univ A'
    }])
    out = collector.filter_by_relevance(df, min_score=0.0)
    assert 'relevance_score' in out.columns
