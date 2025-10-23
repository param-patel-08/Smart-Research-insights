# Theme Mapping (Step 4)

This document explains how BERTopic topics are mapped to Babcock's strategic themes (and sub-themes), including thresholds, methods, and outputs.

---

## Overview

- Goal: Assign each discovered BERTopic topic to one of Babcock's 9 strategic themes, and optionally to a hierarchical sub-theme.
- Method: Cosine similarity between topic keywords (from BERTopic) and theme keyword sets (from `config/themes.py`) using TF-IDF.
- Outputs:
  - Topic→Theme mapping JSON (`data/processed/topic_mapping.json`), with optional sub-theme and confidence scores.

---

## Key Files and Roles

- `src/theme_mapper.py`
  - Class: `ThemeMapper`
  - Calculates cosine similarity, assigns best theme, supports hierarchical sub-theme mapping, and persists mapping.
- `config/themes.py`
  - `BABCOCK_THEMES`: Flat theme dictionary with keyword lists and `strategic_priority`.
  - `BABCOCK_THEMES_HIERARCHICAL`: Parent themes with `sub_themes` (keyword lists) for finer mapping.
- `config/settings.py`
  - `TOPIC_MAPPING_PATH` – output JSON path.
- `models/bertopic_model.pkl`
  - Input BERTopic model with topics and keywords.

---

## Class: ThemeMapper

Constructor:
- `__init__(babcock_themes: Dict, min_similarity: float = 0.01, theme_thresholds: Optional[Dict[str, float]] = None)`
  - `babcock_themes`: Theme keywords structure from `config/themes.py`
  - `min_similarity`: Default similarity threshold for assigning a theme
  - `theme_thresholds`: Theme-specific overrides (e.g., `DEFAULT_THEME_THRESHOLDS` contains a lower threshold for `Defense_Security`)

Core methods:
- `calculate_keyword_similarity(topic_keywords, theme_keywords) -> float`
  - Builds TF-IDF vectors from topic keywords and theme keyword lists, then computes cosine similarity.

- `map_topic_to_theme(topic_id, topic_keywords) -> (best_theme, best_score, all_scores)`
  - Scores against all themes and returns the best theme, its score, and a dict of all theme scores. Applies thresholding (theme-specific or default `min_similarity`).

- `map_topic_to_sub_theme(topic_keywords, parent_theme, hierarchical_themes) -> (sub_theme, confidence)`
  - Optional: given a parent theme and hierarchical structure, finds the best sub-theme by similarity.

- `create_theme_mapping(topic_model, hierarchical_themes: Optional[Dict] = None) -> Dict[str, Dict]`
  - Iterates over all non-outlier topics in the BERTopic model, computes theme (and optionally sub-theme) assignments, and returns a mapping of:
    ```json
    {
      "<topic_id>": {
        "theme": "Cybersecurity",
        "confidence": 0.123,
        "all_scores": {"AI_Machine_Learning": 0.02, ...},
        "keywords": ["threat", "detection", ...],
        "count": 37,
        "sub_theme": "Threat_Detection",
        "sub_theme_confidence": 0.211
      }
    }
    ```

- `identify_cross_theme_topics(threshold=0.6) -> List[Dict]`
  - Finds topics strongly related to multiple themes (useful for spotting interdisciplinary topics).

- `save_mapping(filepath)` / `load_mapping(filepath)`
  - Persist/load the mapping JSON.

---

## Inputs and Outputs

Inputs:
- `models/bertopic_model.pkl` – trained BERTopic model
- `config/themes.py` – theme keywords and hierarchical structure

Outputs:
- `data/processed/topic_mapping.json` – topic→theme(+sub-theme) mapping with confidence and counts

---

## Example Usage

Minimal (inside `theme_mapper.py`):
```python
from bertopic import BERTopic
from config.themes import BABCOCK_THEMES, BABCOCK_THEMES_HIERARCHICAL
from config.settings import BERTOPIC_MODEL_PATH, TOPIC_MAPPING_PATH

model = BERTopic.load(BERTOPIC_MODEL_PATH)
mapper = ThemeMapper(BABCOCK_THEMES)

mapping = mapper.create_theme_mapping(model, hierarchical_themes=BABCOCK_THEMES_HIERARCHICAL)
mapper.save_mapping(TOPIC_MAPPING_PATH)
```

Pipeline (auto-run in Step 4):
```powershell
python scripts/run_full_analysis.py
```

---

## Notes and Tips

- You can relax/tighten theme assignment by modifying `min_similarity` or per-theme thresholds.
- Hierarchical mapping adds sub-theme insight that powers richer dashboard visuals.
- Cross-theme identification helps identify overlaps and collaboration opportunities.

---

## Flow diagram (Theme Mapping)

```mermaid
flowchart TD
    subgraph Inputs
        Mdl[BERTopic Model\n(models/bertopic_model.pkl)]
        Thm[config.themes\nBABCOCK_THEMES]
        H[config.themes\nBABCOCK_THEMES_HIERARCHICAL]
        Cfg[config.settings\nTOPIC_MAPPING_PATH]
    end

    A[ThemeMapper.__init__\n(min_similarity, thresholds)]
    B[create_theme_mapping\n(iterate topics)]
    C[map_topic_to_theme\n(TF-IDF cosine sim)]
    D[map_topic_to_sub_theme\n(optional)]
    E[identify_cross_theme_topics\n(optional)]
    S[save_mapping -> topic_mapping.json]

    Mdl --> B
    Thm --> A --> B --> C --> D --> S
    H --> D
    B --> E

    classDef inp fill:#eef,stroke:#88a,stroke-width:1px;
    class Mdl,Thm,H,Cfg inp;
```
