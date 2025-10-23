# Emerging Topics Detector (Optional)

This document explains the optional Emerging Topics Detector: how it scores “emergingness,” generates human-readable labels (optionally via GPT), files/classes involved, inputs/outputs, and how to run it.

---

## Overview

- Goal: Identify BERTopic topics that are “emerging” based on recency, growth rate, and volume; optionally generate concise human-readable labels for each.
- Status: Optional post-processing step. The Streamlit dashboard does not require this to run.
- Outputs:
  - `data/processed/emerging_topics.json` with emerging topics, scores, and labels (if GPT used)

---

## Key Files and Roles

- `src/emerging_topics_detector.py`
  - Class: `EmergingTopicsDetector`
  - Loads a trained BERTopic model and the papers dataframe with topic assignments, computes emergingness scores, and (optionally) calls GPT for labels.

- `models/bertopic_model.pkl`
  - Trained BERTopic model from Step 3.

- `data/processed/papers_processed.csv`
  - Papers enriched with `topic_id` and dates (from Step 3).

- `data/processed/topic_mapping.json`
  - Topic → theme mapping to attach `theme`, `sub_theme`, and keywords context per topic (from Step 4).

- `.env`
  - `OPENAI_API_KEY` (optional). If absent, labels fall back to keyword-based heuristics.

---

## Class: EmergingTopicsDetector

Constructor:
- `__init__(bertopic_model_path: str, papers_df: pd.DataFrame, topic_mapping: Dict, openai_api_key: str | None = None)`
  - Loads BERTopic model and copies the papers dataframe.
  - Stores topic mapping. Sets OpenAI API key from arg or environment.

Methods:
- `calculate_emergingness_score(topic_id, recency_weight=0.4, growth_weight=0.4, volume_weight=0.2) -> Dict`
  - Recency score: exponential decay over months-old (half-life ≈ 12 months).
  - Growth score: compares recent vs older quarters; normalizes to [0,1].
  - Volume score: percentile vs all topics by paper count.
  - Returns a dict with component scores, composite `emergingness_score`, `paper_count`, `avg_citations`, `latest_date`.

- `identify_emerging_topics(min_emergingness=0.5, top_n=20) -> pd.DataFrame`
  - Iterates all topic_ids (excluding outlier -1), computes scores, attaches `theme`, `sub_theme`, and `keywords` from `topic_mapping`.
  - Filters by threshold and returns top N by `emergingness_score`.

- `_filter_noisy_keywords(keywords: List[str]) -> List[str]`
  - Removes boilerplate and web-noise tokens; caps length to 10.

- `generate_topic_label_with_gpt(keywords, theme, sub_theme=None, paper_count=0, growth_rate=0.0) -> str`
  - Uses OpenAI Chat Completions to craft a 4–8 word label. Cleans prefixes; falls back when needed.

- `generate_labels_for_emerging_topics(emerging_df, use_gpt=True) -> pd.DataFrame`
  - Produces `topic_label` for each topic; uses GPT if API key available, else keywords-based fallback.

- `save_emerging_topics(emerging_df, filepath: str)`
  - Saves list of dicts to JSON.

- `main()`
  - Loads `BERTOPIC_MODEL_PATH` and `PROCESSED_PAPERS_CSV` from config, reads mapping from `data/processed/topic_mapping.json`, identifies and labels emerging topics, and saves `data/processed/emerging_topics.json`.

---

## Inputs and Outputs

Inputs:
- `models/bertopic_model.pkl` (Step 3)
- `data/processed/papers_processed.csv` (Step 3)
- `data/processed/topic_mapping.json` (Step 4)
- `.env: OPENAI_API_KEY` (optional)

Output:
- `data/processed/emerging_topics.json` – array of objects like:
  ```json
  {
    "topic_id": 12,
    "emergingness_score": 0.73,
    "recency_score": 0.61,
    "growth_score": 0.85,
    "volume_score": 0.68,
    "paper_count": 45,
    "avg_citations": 12.3,
    "latest_date": "2024-08-15",
    "growth_rate": 75.0,
    "theme": "Cybersecurity",
    "sub_theme": "Threat_Detection",
    "keywords": ["malware", "detection", "anomaly", ...],
    "topic_label": "AI-driven Threat Detection"  
  }
  ```

---

## Example Usage

Programmatic:
```python
import pandas as pd, json
from config.settings import BERTOPIC_MODEL_PATH, PROCESSED_PAPERS_CSV
from src.emerging_topics_detector import EmergingTopicsDetector

papers_df = pd.read_csv(PROCESSED_PAPERS_CSV)
with open('data/processed/topic_mapping.json') as f:
    mapping = json.load(f)

detector = EmergingTopicsDetector(BERTOPIC_MODEL_PATH, papers_df, mapping)
emerging = detector.identify_emerging_topics(min_emergingness=0.5, top_n=20)
emerging = detector.generate_labels_for_emerging_topics(emerging, use_gpt=True)
detector.save_emerging_topics(emerging, 'data/processed/emerging_topics.json')
```

CLI-like (via module `main`):
```powershell
python -m src.emerging_topics_detector
```

---

## Notes and Tips

- Thresholds: Adjust `min_emergingness` and component weights to suit your sensitivity to recency/growth/volume.
- Missing API Key: Labels fall back to a heuristic; set `OPENAI_API_KEY` in `.env` for high-quality titles.
- Dates: Ensure `date` column is ISO-parsable; the detector converts and bins by quarter.
- Outliers: Topic `-1` is skipped.

---

## Troubleshooting

- GPT API Error: The detector catches exceptions and falls back to keyword-based labels.
- Empty/Low Emerging Topics: Lower `min_emergingness` (e.g., 0.4) or increase `top_n`.
- Incorrect Theme/Sub-theme: Ensure `topic_mapping.json` was generated with the latest model; regenerate mapping if needed.

---

## Flow diagram (Emerging Topics Detector)

```mermaid
flowchart TD
    subgraph Inputs
        Mdl[BERTopic Model\n(models/bertopic_model.pkl)]
        P[papers_processed.csv\n(data/processed)]
        Map[topic_mapping.json\n(data/processed)]
        Key[.env OPENAI_API_KEY\n(optional)]
    end

    A[EmergingTopicsDetector.__init__]
    S[identify_emerging_topics\n(recency + growth + volume)]
    L[generate_labels_for_emerging_topics\n(GPT optional)]
    J[Save emerging_topics.json]

    Mdl --> A
    P --> A
    Map --> A
    A --> S --> L --> J
    Key --> L

    classDef inp fill:#eef,stroke:#88a,stroke-width:1px;
    class Mdl,P,Map,Key inp;
```
