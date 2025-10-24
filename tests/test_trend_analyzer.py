from src.trend_analyzer import TrendAnalyzer
import pandas as pd


def test_calculate_growth_and_trends():
    # Create sample quarterly data for one theme via topic mapping
    df = pd.DataFrame({
        'date': ['2023-01-01', '2023-04-01', '2023-07-01', '2023-10-01'],
        'topic_id': [0, 0, 0, 0],
        'title': ['a', 'a', 'a', 'a'],
        'university': ['U', 'U', 'U', 'U']
    })
    mapping = {'0': {'theme': 'AI'}}
    strategic_themes = {'AI': {}}
    ta = TrendAnalyzer(mapping, strategic_themes)
    trends = ta.analyze_theme_trends(df)
    assert 'AI' in trends
    assert isinstance(trends['AI']['growth_rate'], float)
