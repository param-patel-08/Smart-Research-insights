import pandas as pd
from src.emerging_topics_detector import EmergingTopicsDetector


def test_emergingness_and_label_fallback():
    # Create detector instance without invoking BERTopic loading
    det = EmergingTopicsDetector.__new__(EmergingTopicsDetector)
    df = pd.DataFrame({
        'topic_id': [1, 1, 1],
        'date': ['2024-01-01', '2024-06-01', '2024-09-01'],
        'citations': [1, 2, 3]
    })
    det.papers_df = df.copy()
    det.topic_mapping = {'1': {'theme': 'AI', 'keywords': ['deep learning', 'cnn']}}
    det.openai_api_key = None

    scores = det.calculate_emergingness_score(1)
    assert 'emergingness_score' in scores

    em = det.identify_emerging_topics(min_emergingness=0.0, top_n=5)
    assert isinstance(em, pd.DataFrame)

    # Test label generation fallback (no GPT)
    em2 = det.generate_labels_for_emerging_topics(em, use_gpt=False)
    assert 'topic_label' in em2.columns
