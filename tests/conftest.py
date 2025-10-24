import os
import sys

# Ensure repository root is on sys.path for imports like `src` and `dashboard`
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Create lightweight stubs for heavy optional dependencies so test collection is fast and
# deterministic in CI without needing to install large ML packages.
import types

def _make_stub(name, attrs=None):
    m = types.ModuleType(name)
    for k, v in (attrs or {}).items():
        setattr(m, k, v)
    return m

if 'bertopic' not in sys.modules:
    class _BERTopicStub:
        def __init__(self, *a, **k):
            pass
        def fit_transform(self, docs, embeddings=None):
            return [0]*len(docs), [[] for _ in docs]
        def get_topic(self, topic_id):
            return []
        def get_topic_info(self):
            import pandas as _pd
            return _pd.DataFrame([])
        def save(self, filepath, serialization=None):
            pass
        @staticmethod
        def load(path):
            return _BERTopicStub()

    sys.modules['bertopic'] = _make_stub('bertopic', {'BERTopic': _BERTopicStub})

if 'sentence_transformers' not in sys.modules:
    class _STStub:
        def __init__(self, *a, **k):
            pass
        def encode(self, docs, **kwargs):
            import numpy as _np
            return _np.zeros((len(docs), 384))
    sys.modules['sentence_transformers'] = _make_stub('sentence_transformers', {'SentenceTransformer': _STStub})

if 'umap' not in sys.modules:
    sys.modules['umap'] = _make_stub('umap', {'UMAP': lambda *a, **k: object()})

if 'hdbscan' not in sys.modules:
    sys.modules['hdbscan'] = _make_stub('hdbscan', {'HDBSCAN': lambda *a, **k: object()})

if 'openai' not in sys.modules:
    sys.modules['openai'] = _make_stub('openai', {'chat': _make_stub('chat', {'completions': _make_stub('completions', {'create': lambda *a, **k: {'choices':[{'message':{'content':'Fallback Label'}}]}})})})

if 'nltk' not in sys.modules:
    # Minimal nltk stub to avoid automatic downloads during tests
    _nltk = _make_stub('nltk', {'download': lambda *a, **k: None})
    sys.modules['nltk'] = _nltk
