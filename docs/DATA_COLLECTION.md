# Data Collection (Data Acquisition)

This document explains how the data acquisition pipeline works: which files participate, the main classes and methods, how the OpenAlex API is queried, relevance filtering, deduplication, outputs, and how Step 1 integrates into the full pipeline.

---

## Overview

- Source: OpenAlex API (https://api.openalex.org/)
- Goal: Collect AU/NZ research papers aligned with Babcock International's 9 strategic themes.
- Strategy:
  1. Use OpenAlex concept filters to retrieve high-signal papers per theme (no fuzzy free-text search).
  2. Parse and normalize each result (title, abstract, authors, journal, date, concepts, etc.).
  3. Assign a Babcock-specific relevance score per paper (0.0–1.0).
  4. Filter by a minimum relevance threshold and deduplicate results.
  5. Save the theme-tagged, AU/NZ-only set to CSV for downstream processing.

---

## Key Files and Roles

- `src/paper_collector.py`
  - Implements the theme-aware OpenAlex collection.
  - Class: `PaperCollector` with methods to query, parse, score, filter, deduplicate, and save.

- `config/themes.py`
  - `BABCOCK_THEMES`: Dict of 9 strategic themes, each with keywords and `strategic_priority`.
  - `BABCOCK_THEMES_HIERARCHICAL`: Optional hierarchical/child themes (used later in mapping).

- `config/settings.py`
  - `OPENALEX_EMAIL`: Polite pool email required by OpenAlex.
  - `ANALYSIS_START_DATE`, `ANALYSIS_END_DATE`: Collection window.
  - `ALL_UNIVERSITIES`: Dict of major AU/NZ universities (names and IDs for reference).
  - I/O paths used by the pipeline (e.g., `RAW_PAPERS_CSV`).

- `scripts/run_full_analysis.py` (Step 1)
  - Imports `PaperCollector` and orchestrates collection options:
    - Quick/Medium/Full mode
    - `max_per_theme`, `priority_only`, `min_relevance`
  - Saves CSV at `data/raw/papers_raw.csv` (filtered to major universities only).

---

## Class: PaperCollector

Constructor:
- `__init__(email: str, start_date: datetime, end_date: datetime)`
  - Configures polite pool email and the date range. Sets API base URL, session, etc.

Public API:
- `build_theme_query(theme_name: str, top_n_keywords: int = 30) -> str`
  - Builds a keyword-only query string from theme keywords (kept for reference/documentation). The active implementation relies on OpenAlex concepts instead of text search.

- `fetch_papers_for_theme(theme_name: str, universities: Dict[str, str], max_papers: Optional[int] = 500, per_page: int = 200) -> pd.DataFrame`
  - Queries OpenAlex for a single theme using reliable, curated concept IDs.
  - Filters:
    - `from_publication_date` / `to_publication_date` (from constructor)
    - `institutions.country_code: AU|NZ` (country-level filter ensures AU/NZ coverage)
    - `concepts.id: ...` (theme-specific concept filters)
  - Pagination: Uses `cursor=*` and iterates via `meta.next_cursor` until limit or no more results.
  - Rate limiting: Sleeps briefly between cursor requests.
  - Parsing: Each `work` is normalized by `_parse_work`.
  - Returns a DataFrame of parsed papers tagged with `theme`.

- `calculate_relevance_score(paper: Dict, theme_name: str) -> float`
  - Babcock-specific scoring model (0.0–1.0) combining:
    - Theme keyword matches in title/abstract (40%)
    - Technical/engineering context terms (30%)
    - Babcock domain indicators (naval, defense, cyber, etc.) and OpenAlex concepts (30%)

- `filter_by_relevance(df: pd.DataFrame, min_score: float = 0.2) -> pd.DataFrame`
  - Adds `relevance_score` column using the above scoring.
  - Filters out papers below `min_score`.
  - Logs distribution stats (mean/min/max, retention percentage).

- `fetch_all_themes(universities: Dict[str, str], max_per_theme: Optional[int] = 500, priority_only: bool = False, min_relevance: float = 0.5) -> pd.DataFrame`
  - Iterates themes from `BABCOCK_THEMES` (optionally only HIGH priority).
  - Fetch order prioritizes `AI_Machine_Learning` first (reduces cross-theme leakage).
  - Concatenates results and applies relevance filtering.
  - Returns combined DataFrame for all themes.

- `deduplicate_papers(df: pd.DataFrame) -> pd.DataFrame`
  - Drops duplicates by `openalex_id`. Logs removal percentage.

- `save_to_csv(df: pd.DataFrame, filepath: str)`
  - Writes to CSV path and logs row count.

Important helpers:
- `_parse_work(work: Dict, theme_name: str) -> Optional[Dict]`
  - Validates presence of title and abstract; reconstructs `abstract` from OpenAlex `abstract_inverted_index` via `_reconstruct_abstract`.
  - Derives `date`, `year`, `authors`, `journal`, `doi`, `citations`.
  - Determines AU/NZ university name directly from OpenAlex authorship institutions (`country_code` AU|NZ), falling back gracefully.
  - Attaches short list of OpenAlex `concepts` and the `theme` label.

- `_reconstruct_abstract(inverted_index: Dict) -> Optional[str]`
  - Converts the OpenAlex inverted index to a readable abstract string.

---

## OpenAlex Request Details

- Base endpoint: `https://api.openalex.org/works`
- Query strategy:
  - No free-text `search=` parameter (intentionally avoided).
  - Strong signal via `concepts.id` filter per theme.
  - Country filter: `institutions.country_code:AU|NZ` (captures all AU/NZ research orgs).
  - Date filters bound the analysis window.
- Response handling:
  - Pagination via `cursor=*` and `meta.next_cursor`.
  - `select=` reduces payload to required fields for speed.

Example `params` (concepts truncated for brevity):
```
{
  'filter': 'from_publication_date:YYYY-MM-DD,to_publication_date:YYYY-MM-DD,institutions.country_code:AU|NZ,concepts.id:C154945302|C119857082',
  'per-page': 200,
  'cursor': '*',
  'mailto': OPENALEX_EMAIL,
  'select': 'id,title,abstract_inverted_index,publication_date,publication_year,authorships,primary_location,doi,cited_by_count,concepts'
}
```

---

## End-to-End Workflow (Step 1 in Pipeline)

1. `scripts/run_full_analysis.py` prompts for scope (Quick/Medium/Full) and sets:
   - `max_per_theme` (e.g., 500, 2000, 10000)
   - `priority_only` (boolean: only HIGH priority themes or all 9)
   - `min_relevance` (e.g., 0.15–0.5; lower for larger recall)
2. Instantiate `PaperCollector(email, start_date, end_date)` using `config.settings`.
3. Call `fetch_all_themes()` returning a filtered, theme-tagged DataFrame.
4. `deduplicate_papers()` by `openalex_id`.
5. Filter to major AU/NZ universities (post-collection safeguard).
6. Save to `RAW_PAPERS_CSV` (e.g., `data/raw/papers_raw.csv`).

Downstream steps (for context):
- Step 2: `PaperPreprocessor` creates cleaned `documents.txt` and `metadata.csv` (retains `theme`).
- Step 3: Topic modeling (BERTopic) saves `models/bertopic_model.pkl` and `topics_over_time.csv`.
- Step 4: Theme mapping using `BABCOCK_THEMES_HIERARCHICAL`.
- Step 5: Trend analysis emits `trend_analysis.json`.

---

## Configuration Reference

From `config/settings.py`:
- `OPENALEX_EMAIL`: Required by OpenAlex (polite pool); set in your `.env`.
- `ANALYSIS_START_DATE` / `ANALYSIS_END_DATE`: Inclusive date range.
- `ALL_UNIVERSITIES`: Names of supported institutions (also used later to filter to majors).
- I/O paths: `RAW_PAPERS_CSV`, etc.

From `config/themes.py`:
- `BABCOCK_THEMES`: Dict keyed by theme name with fields like:
  - `keywords`: List[str]
  - `strategic_priority`: 'HIGH' | 'MEDIUM' | 'LOW'

---

## Outputs

- Primary CSV produced by Step 1: `data/raw/papers_raw.csv`
  - Columns (typical): `openalex_id, title, abstract, date, year, authors, university, journal, citations, doi, theme, concepts, relevance_score`
- Intermediate/debug CSV (optional during dev): `data/raw/papers_theme_filtered.csv` (when running `__main__` in `paper_collector.py`).

---

## Example Usage

Minimal standalone (quick test):
```python
from datetime import datetime
from config.settings import OPENALEX_EMAIL, ALL_UNIVERSITIES
from src.paper_collector import PaperCollector

collector = PaperCollector(
    email=OPENALEX_EMAIL,
    start_date=datetime(2022, 1, 1),
    end_date=datetime(2024, 12, 31),
)

# Subset of universities for a quick run
test_unis = dict(list(ALL_UNIVERSITIES.items())[:3])

df = collector.fetch_all_themes(
    universities=test_unis,
    max_per_theme=100,
    priority_only=True,
    min_relevance=0.5,
)

df = collector.deduplicate_papers(df)
collector.save_to_csv(df, 'data/raw/papers_raw.csv')
```

Full pipeline (interactive):
```powershell
python scripts/run_full_analysis.py
```

---

## Performance and Limits

- Pagination: `per-page` defaults to 200 (OpenAlex maximum).
- Rate limiting: Short `time.sleep` between cursor pages and theme loops.
- Recall vs precision: `min_relevance` controls strictness; lower for broader recall.
- Overlap handling: Fetch order prioritizes AI/ML first to reduce cross-theme capture.

---

## Troubleshooting

- `ModuleNotFoundError: No module named 'config'`
  - Run scripts from the repo root (use `python scripts/...`). Ensure your venv is active.
- `403` or slow responses
  - Ensure `OPENALEX_EMAIL` is set in `.env` and loaded in `config/settings.py`.
- Empty collections
  - Check date range and theme concept mapping. Try lowering `min_relevance`.

---

## Extending/Customizing

- Add/adjust theme concept IDs in `paper_collector.py` for better coverage.
- Tune keyword lists in `config/themes.py` to refine relevance scoring.
- Adjust `min_relevance` in `run_full_analysis.py` based on recall needs.
- Expand `technical_terms` / `domain_indicators` in `calculate_relevance_score` for your domain.

---

## Flow diagram (Data Collection)

```mermaid
flowchart TD
  subgraph Config
    S1[config.settings\nOPENALEX_EMAIL,\nANALYSIS_START_DATE,\nANALYSIS_END_DATE, paths]
    S2[config.themes\nBABCOCK_THEMES]
    S3[config.settings\nALL_UNIVERSITIES]
  end

  A[PaperCollector.__init__\n(email, start_date, end_date)]
  B[run_full_analysis.py\nStep 1 orchestrator]
  C[fetch_all_themes(universities,\nmax_per_theme, priority_only,\nmin_relevance)]
  D[OpenAlex API /works\nfilter: concepts.id, AU|NZ, dates\nper-page=200, cursor=*]
  E[_parse_work + _reconstruct_abstract]
  F[calculate_relevance_score]
  G[filter_by_relevance(min_relevance)]
  H[deduplicate_papers]
  I[CSV: data/raw/papers_raw.csv]

  S1 --> A
  S2 --> C
  S3 --> C
  A --> B
  B --> C
  C -->|per theme| D
  D --> E
  E --> F
  F --> G
  G --> H
  H --> I

  classDef cfg fill:#eef,stroke:#88a,stroke-width:1px;
  class S1,S2,S3 cfg;
```
