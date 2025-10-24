from src.topic_analyzer import TopicAnalyzer


def test_get_topic_keywords_and_info_monkeypatch():
    ta = TopicAnalyzer()

    class DummyModel:
        def get_topic(self, tid):
            return [('term1', 0.5), ('term2', 0.3)]

        def get_topic_info(self):
            import pandas as pd
            return pd.DataFrame([{'Topic': 0, 'Count': 2}])

    ta.topic_model = DummyModel()
    kws = ta.get_topic_keywords(0, n_words=2)
    assert isinstance(kws, list)
    assert 'term1' in kws
