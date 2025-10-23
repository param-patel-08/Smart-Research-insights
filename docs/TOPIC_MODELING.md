# Topic Modeling (Step 3)

This document explains how topic modeling works in the project: the classes and methods, how BERTopic is configured and trained, what files it reads/writes, and how it fits into the pipeline.

---

## Overview

- Goal: Discover research topics from preprocessed paper texts and analyze their evolution over time.
- Technique: BERTopic (SentenceTransformer embeddings + UMAP + HDBSCAN + CountVectorizer)
- Outputs:
  - Saved BERTopic model (`models/bertopic_model.pkl`)
  - Topic assignments and probabilities merged into metadata (`data/processed/papers_processed.csv`)
  - Topics-over-time time series (`data/processed/topics_over_time.csv`)
  - Cached embeddings (optional) (`data/processed/embeddings.npy`)

---

## Key Files and Roles

- `src/topic_analyzer.py`
  - Class: `BabcockTopicAnalyzer`
  - Orchestrates BERTopic creation, training, temporal analysis, and model I/O.
- `config/settings.py`
  - Paths: `EMBEDDINGS_PATH`, `BERTOPIC_MODEL_PATH`, `PROCESSED_PAPERS_CSV`, `TOPICS_OVER_TIME_CSV`, `METADATA_CSV`, `NR_TIME_BINS`
- `data/processed/metadata.csv`
  - Input documents are read from `documents.txt` (same folder), timestamps from `metadata.csv`
- `scripts/run_full_analysis.py`
  - Calls Step 3 in sequence after preprocessing.

---

## Class: BabcockTopicAnalyzer

Constructor:
- `__init__(min_topic_size: int = 15, nr_topics: int = 60)`
  - Configures minimum cluster size and target number of topics (let BERTopic auto if `None`).

Methods:
- `create_bertopic_model()`
  - Embedding model: `all-MiniLM-L6-v2` (SentenceTransformers)
  - UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine')
  - HDBSCAN(min_cluster_size=min_topic_size, min_samples=5, selection='eom')
  - CountVectorizer(ngram_range=(1,3), stop_words='english', min_df=2, max_df=0.95)
  - Creates `self.topic_model` configured for academic text.

- `fit_transform(documents: List[str], embeddings_path: str = None) -> Tuple[topics, probabilities]`
  - Trains BERTopic on the list of `documents`.
  - Optionally loads cached embeddings from `embeddings_path` and verifies matching length; otherwise encodes and can save fresh embeddings to cache.
  - Logs outliers and per-topic stats.

- `get_topics_over_time(documents, timestamps, topics, nr_bins=8) -> pd.DataFrame`
  - Computes topic evolution over time using BERTopic's `topics_over_time`.

- `get_topic_info() -> pd.DataFrame`
  - Returns BERTopic topic summary (topic id, keyword representation, counts).

- `get_representative_docs(topic_id, n_docs=5) -> List[str]`
  - Retrieves the most representative documents per topic.

- `save_model(filepath)` / `load_model(filepath)`
  - Persist/load the BERTopic model.

- `get_topic_keywords(topic_id, n_words=10) -> List[str]`
  - Shortcut to fetch top keywords per topic.

---

## Inputs and Outputs

Inputs:
- `data/processed/documents.txt` (one preprocessed document per line)
- `data/processed/metadata.csv` (for timestamps; must align with `documents.txt`)

Outputs:
- `models/bertopic_model.pkl` – serialized BERTopic model
- `data/processed/papers_processed.csv` – `metadata.csv` + columns: `topic_id`, `topic_probability`
- `data/processed/topics_over_time.csv` – time series of topic activity (binning via `NR_TIME_BINS`)
- `data/processed/embeddings.npy` – cached embeddings (optional)

---

## Example Usage

Minimal (inside `topic_analyzer.py`):
```python
analyzer = BabcockTopicAnalyzer(min_topic_size=15, nr_topics=60)

# Train
topics, probs = analyzer.fit_transform(documents, embeddings_path=EMBEDDINGS_PATH)

# Temporal analysis
topics_over_time = analyzer.get_topics_over_time(documents, timestamps, topics, nr_bins=NR_TIME_BINS)

# Save
analyzer.save_model(BERTOPIC_MODEL_PATH)
```

Pipeline (auto-run in Step 3):
```powershell
python scripts/run_full_analysis.py
```

---

## Notes and Tips

- Adjust `min_topic_size`/`nr_topics` in `BabcockTopicAnalyzer` or tune in `config.settings.TOPIC_MODEL_PARAMS` if you expose them there.
- Cached embeddings speed up reruns when the corpus is unchanged in length.
- Outliers (topic -1) are excluded from topic counts and summaries by design.

---

## Flow diagram (Topic Modeling)

```mermaid
flowchart TD
    subgraph Inputs
        D[documents.txt\n(data/processed)]
        M[metadata.csv\n(data/processed)]
        Cfg[config.settings\npaths, NR_TIME_BINS]
    end

    A[BabcockTopicAnalyzer.__init__\n(min_topic_size, nr_topics)]
    B[create_bertopic_model\n(SBERT + UMAP + HDBSCAN + CV)]
    C[fit_transform(documents,\nembeddings cache?)]
    T[get_topics_over_time]
    S[save_model -> models/bertopic_model.pkl]
    P[Save papers_processed.csv\n+ topic_id, topic_probability]
    O[Save topics_over_time.csv]

    D --> C
    M --> T
    Cfg --> A --> B --> C --> T --> O
    C --> P
    C --> S

    classDef inp fill:#eef,stroke:#88a,stroke-width:1px;
    class D,M,Cfg inp;
```
