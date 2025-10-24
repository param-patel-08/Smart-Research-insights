import pandas as pd
from src.paper_preprocessor import PaperPreprocessor


def test_clean_text_and_tokenize():
    p = PaperPreprocessor(min_abstract_length=10)
    text = "This is a TEST abstract. Visit http://example.com. Email: a@b.com"
    cleaned = p.clean_text(text)
    assert 'http' not in cleaned and 'a@b.com' not in cleaned
    tokens = p.tokenize_and_lemmatize(cleaned)
    assert isinstance(tokens, list)
    assert all(isinstance(t, str) for t in tokens)


def test_preprocess_abstracts_filters_short():
    df = pd.DataFrame({
        'abstract': ['short', 'This is a sufficiently long abstract for testing.'],
        'title': ['t1', 't2'],
        'date': ['2023-01-01', '2023-01-02'],
        'university': ['U1', 'U2']
    })
    p = PaperPreprocessor(min_abstract_length=20)
    out = p.preprocess_abstracts(df)
    assert len(out) == 1
