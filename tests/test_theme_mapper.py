from src.theme_mapper import ThemeMapper
import pandas as pd


def test_mapping_simple():
    strategic_themes = {
        'AI': {'keywords': ['machine learning', 'deep learning']},
        'Other': {'keywords': ['misc']}
    }
    mapper = ThemeMapper(strategic_themes)

    class DummyModel:
        def get_topic_info(self):
            return pd.DataFrame([{'Topic': 0, 'Count': 5}])

        def get_topic(self, topic_id):
            return [('machine learning', 0.6), ('neural', 0.3)]

    mapping = mapper.create_theme_mapping(DummyModel())
    assert '0' in mapping
    assert isinstance(mapping['0']['theme'], str)
