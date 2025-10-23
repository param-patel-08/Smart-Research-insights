# Trend Analysis (Step 5)

This document explains how temporal trends are analyzed across themes and topics, how emerging topics are identified, and how strategic priorities are computed.

---

## Overview

- Goal: Quantify research activity over time, identify emerging topics, and rank themes by strategic priority.
- Inputs: Papers with topic assignments, topic→theme mapping.
- Outputs: Consolidated trend analysis JSON consumed by the dashboard.

---

## Key Files and Roles

- `src/trend_analyzer.py`
  - Class: `TrendAnalyzer`
  - Computes per-theme trends, emergent topics, university rankings by theme, and strategic priority scores.
- `config/settings.py`
  - `TREND_ANALYSIS_PATH` – output JSON path
  - Re-uses `PROCESSED_PAPERS_CSV` and `TOPIC_MAPPING_PATH` as inputs.

---

## Class: TrendAnalyzer

Constructor:
- `__init__(topic_theme_mapping: Dict, babcock_themes: Dict)`
  - `topic_theme_mapping`: Loaded from `data/processed/topic_mapping.json`
  - `babcock_themes`: From `config/themes.py` (`BABCOCK_THEMES`)

Methods:
- `calculate_growth_rate(counts: List[int]) -> float`
  - Average sequential growth across a sequence (e.g., quarterly counts).

- `analyze_theme_trends(papers_df, topics_over_time: pd.DataFrame = None) -> Dict`
  - Uses original concept-based `theme` column if present, otherwise maps from `topic_id` via `topic_theme_mapping`.
  - Produces per-theme:
    - `total_papers`, `growth_rate`, `quarterly_counts`, `top_topics`, `universities` (top-5)

- `identify_emerging_topics(papers_df, threshold: float = 0.5, recent_quarters: int = 2) -> List[Dict]`
  - Finds topics with high recent growth, excluding outliers. Returns `topic_id`, `theme`, `growth_rate`, `keywords`, `recent_count`, `previous_count`.

- `rank_universities_by_theme(papers_df, theme: str) -> pd.DataFrame`
  - Ranks universities by count within a theme (also computes active window in days).

- `calculate_strategic_priority(theme_trends: Dict) -> List[Dict]`
  - Combines growth rate, Babcock’s stated priority (HIGH/MEDIUM/LOW), and paper volume factor into a `priority_score`, categorized into HIGH/MEDIUM/LOW.

---

## Inputs and Outputs

Inputs:
- `data/processed/papers_processed.csv` – includes `topic_id`, `theme`, `date`, `university`, etc.
- `data/processed/topic_mapping.json` – to map topics back to themes and show keyword context.

Output:
- `data/processed/trend_analysis.json` – JSON with keys:
  - `theme_trends` (per-theme stats)
  - `emerging_topics` (sorted descending by growth)
  - `strategic_priorities` (sorted by `priority_score`)

---

## Example Usage

Minimal (inside `trend_analyzer.py`):
```python
from config.settings import PROCESSED_PAPERS_CSV, TOPIC_MAPPING_PATH, TREND_ANALYSIS_PATH
from config.themes import BABCOCK_THEMES
import pandas as pd, json

papers_df = pd.read_csv(PROCESSED_PAPERS_CSV)
with open(TOPIC_MAPPING_PATH) as f:
    mapping = json.load(f)

an = TrendAnalyzer(mapping, BABCOCK_THEMES)

theme_trends = an.analyze_theme_trends(papers_df)
emerging = an.identify_emerging_topics(papers_df, threshold=0.5)
priorities = an.calculate_strategic_priority(theme_trends)
```

Pipeline (auto-run in Step 5):
```powershell
python scripts/run_full_analysis.py
```

---

## Notes and Tips

- If the collection step already assigned a `theme` to each paper, trend analysis prioritizes that concept-based label for fidelity.
- Growth calculations use quarters by default (`df['date'].dt.to_period('Q')`).
- Adjust `threshold` and `recent_quarters` to tune emerging topic sensitivity.

---

## Flow diagram (Trend Analysis)

```mermaid
flowchart TD
    subgraph Inputs
        P[papers_processed.csv\n(data/processed)]
        Map[topic_mapping.json\n(data/processed)]
        Cfg[config.settings\nTREND_ANALYSIS_PATH]
    end

    A[TrendAnalyzer.__init__\n(mapping, BABCOCK_THEMES)]
    B[analyze_theme_trends\n(quarterly counts, growth)]
    C[identify_emerging_topics\n(recent growth)]
    D[calculate_strategic_priority\n(growth x priority x volume)]
    S[Save trend_analysis.json]

    P --> B
    Map --> A --> B --> C --> D --> S

    classDef inp fill:#eef,stroke:#88a,stroke-width:1px;
    class P,Map,Cfg inp;
```
