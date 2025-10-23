# Full Project Overview

This document explains the end-to-end system: purpose, architecture, pipeline stages, key files/classes, data contracts, how to run, troubleshooting, and a final full-system flowchart.

---

## What this project does

Smarter Research Insights collects AU/NZ academic papers aligned to Babcock's 9 strategic themes, preprocesses and models topics using BERTopic, maps topics to (parent) themes and hierarchical sub-themes, analyzes trends and emerging areas, and presents everything in a modern Streamlit dashboard for discovery and reporting.

---

## Architecture at a glance

- Configuration: `config/settings.py`, `config/themes.py`
- Data collection: `src/paper_collector.py` → `data/raw/papers_raw.csv`
- Preprocessing: `src/paper_preprocessor.py` → `data/processed/metadata.csv`, `documents.txt`
- Topic modeling: `src/topic_analyzer.py` → `models/bertopic_model.pkl`, `topics_over_time.csv`, `papers_processed.csv`
- Theme mapping: `src/theme_mapper.py` → `data/processed/topic_mapping.json`
- Trend analysis: `src/trend_analyzer.py` → `data/processed/trend_analysis.json`
- Optional: `src/emerging_topics_detector.py` → `data/processed/emerging_topics.json`
- Visual analytics: `dashboard/app.py` (+ tabs, utils) consumes processed data and JSONs
- Scripts: `scripts/run_full_analysis.py` orchestrates steps 1–5; `scripts/launch_dashboard.py` starts the UI

---

## End-to-end pipeline

0) Configuration
- Files: `config/settings.py`, `config/themes.py`
- Purpose: Centralize dates, file paths, OpenAlex polite pool email, university list; define Babcock themes (flat + hierarchical with sub-themes).

1) Data Collection (OpenAlex)
- File/Class: `src/paper_collector.py` → `PaperCollector`
- Inputs: `OPENALEX_EMAIL`, date range, AU/NZ filter, theme keywords (and curated concept IDs)
- Output: `data/raw/papers_raw.csv` (AU/NZ, theme-tagged, deduplicated, scored)
- Notes: Cursor pagination; concept-based filtering; relevance score; deduplication.

2) Text Preprocessing
- File/Class: `src/paper_preprocessor.py` → `PaperPreprocessor`
- Input: `data/raw/papers_raw.csv`
- Outputs:
  - `data/processed/metadata.csv` (title, university, date, authors, journal, citations, theme)
  - `data/processed/documents.txt` (cleaned, tokenized text; one per line)
- Notes: Optional NLTK lemmatization; minimum abstract length filtering.

3) Topic Modeling (BERTopic)
- File/Class: `src/topic_analyzer.py` → `BabcockTopicAnalyzer`
- Inputs: `data/processed/documents.txt`, timestamps from `metadata.csv`
- Outputs:
  - `models/bertopic_model.pkl` (serialized model)
  - `data/processed/topics_over_time.csv`
  - `data/processed/papers_processed.csv` (metadata + topic_id, topic_probability)
  - Optional: `data/processed/embeddings.npy` (cached)
- Notes: SBERT embeddings, UMAP reduction, HDBSCAN clustering, CountVectorizer topic terms.

4) Theme Mapping (and Sub-Themes)
- File/Class: `src/theme_mapper.py` → `ThemeMapper`
- Inputs: `models/bertopic_model.pkl`, `config/themes.py`
- Output: `data/processed/topic_mapping.json` (theme, confidence, all_scores, keywords, counts, optional sub_theme & confidence)
- Notes: TF-IDF cosine similarity; per-theme threshold overrides; hierarchical mapping supported.

5) Trend Analysis
- File/Class: `src/trend_analyzer.py` → `TrendAnalyzer`
- Inputs: `data/processed/papers_processed.csv`, `data/processed/topic_mapping.json`
- Output: `data/processed/trend_analysis.json` (theme_trends, emerging_topics, strategic_priorities)
- Notes: Uses original concept-based theme if present; quarterly growth; strategic priority mixes growth, Babcock priority, and volume.

6) Visual Analytics & Dashboard
- Entrypoint: `dashboard/app.py`
- Inputs: `papers_processed.csv`, `topic_mapping.json`, `trend_analysis.json`
- Tabs: Overview, Theme Analysis, Universities, Trends, Emerging Topics
- Notes: Filters, insights, Plotly visuals, sub-theme hierarchy, Sankey flow, lifecycle lines, bubble analysis.

Optional: Emerging Topic Labeling (LLM)
- File/Class: `src/emerging_topics_detector.py` → `EmergingTopicsDetector`
- Inputs: `models/bertopic_model.pkl`, `papers_processed.csv`, `topic_mapping.json`, `OPENAI_API_KEY`
- Output: `data/processed/emerging_topics.json` (labeled topics with emergingness scores)
- Notes: GPT usage is optional; dashboard does not require this file to run.

---

## Data contracts (key columns)

- `data/raw/papers_raw.csv`: `openalex_id, title, abstract, date, year, authors, university, journal, citations, doi, theme, concepts, relevance_score`
- `data/processed/metadata.csv`: `title, university, date, authors, journal, citations, theme`
- `data/processed/papers_processed.csv`: all `metadata.csv` + `topic_id, topic_probability`
- `data/processed/topics_over_time.csv`: BERTopic topics_over_time output
- `data/processed/topic_mapping.json`: `{ topic_id: { theme, confidence, all_scores, keywords, count, [sub_theme], [sub_theme_confidence] } }`
- `data/processed/trend_analysis.json`: `{ theme_trends, emerging_topics, strategic_priorities }`

---

## How to run

- Full pipeline (1–5):
```powershell
python scripts\run_full_analysis.py
```

- Dashboard:
```powershell
streamlit run dashboard\app.py
```

- Tips:
  - Run from the repository root so imports like `config.*` resolve.
  - Ensure your virtual environment is active and dependencies from `requirements.txt` are installed.
  - Set `.env` with `OPENALEX_EMAIL` (and optionally `OPENAI_API_KEY`).

---

## Troubleshooting (quick)

- "No module named 'config'": run commands from the project root, or use `python -m scripts.run_full_analysis`.
- Dashboard missing data error: ensure `papers_processed.csv`, `topic_mapping.json`, and `trend_analysis.json` exist (run the pipeline first).
- Slow or 403 on OpenAlex: set `OPENALEX_EMAIL` in `.env` (polite pool) and confirm date range.

---

## Final flowchart (entire system)

```mermaid
flowchart TD
    %% CONFIG
    subgraph Config
        S[config.settings\n(dates, paths, email, universities)]
        T[config.themes\n(BABCOCK_THEMES + HIERARCHICAL)]
    end

    %% STEP 1: COLLECTION
    subgraph Step1[Step 1 • Data Collection]
        C1[PaperCollector\nOpenAlex /works\nAU|NZ, concepts, cursor]
        RCSV[data/raw/papers_raw.csv]
    end

    %% STEP 2: PREPROCESSING
    subgraph Step2[Step 2 • Preprocessing]
        P2[PaperPreprocessor\nclean → tokenize → processed_text]
        META[data/processed/metadata.csv]
        DOCS[data/processed/documents.txt]
    end

    %% STEP 3: TOPIC MODELING
    subgraph Step3[Step 3 • Topic Modeling]
        TM[BabcockTopicAnalyzer\nBERTopic (SBERT+UMAP+HDBSCAN+CV)]
        MODEL[models/bertopic_model.pkl]
        TOT[data/processed/topics_over_time.csv]
        PP[data/processed/papers_processed.csv]
        EMB[data/processed/embeddings.npy]
    end

    %% STEP 4: THEME MAPPING
    subgraph Step4[Step 4 • Theme Mapping]
        MPR[ThemeMapper\nTF-IDF cosine similarity]
        MAP[data/processed/topic_mapping.json]
    end

    %% STEP 5: TREND ANALYSIS
    subgraph Step5[Step 5 • Trend Analysis]
        TA[TrendAnalyzer\nquarterly trends, priorities]
        TRJ[data/processed/trend_analysis.json]
    end

    %% OPTIONAL: LLM LABELING
    subgraph OptionalLLM[Optional • Emerging Topic Labeling]
        ETD[EmergingTopicsDetector\n(GPT labeler)]
        ETJ[data/processed/emerging_topics.json]
    end

    %% DASHBOARD
    subgraph UI[Visual Analytics & Dashboard]
        APP[Streamlit app.py\nOverview, Theme, Unis, Trends, Emerging]
    end

    %% FLOWS
    S --> C1
    T --> C1
    C1 --> RCSV

    RCSV --> P2
    P2 --> META
    P2 --> DOCS

    DOCS --> TM
    META --> TM
    TM --> MODEL
    TM --> TOT
    TM --> PP

    MODEL --> MPR
    T --> MPR
    MPR --> MAP

    PP --> TA
    MAP --> TA
    TA --> TRJ

    %% Optional LLM
    MODEL --> ETD
    PP --> ETD
    MAP --> ETD
    ETD --> ETJ

    %% UI inputs
    PP --> APP
    MAP --> APP
    TRJ --> APP

    classDef cfg fill:#eef,stroke:#88a,stroke-width:1px;
    class S,T cfg;
    classDef data fill:#f0f9ff,stroke:#38bdf8,stroke-width:1px;
    class RCSV,META,DOCS,MODEL,TOT,PP,EMB,MAP,TRJ,ETJ data;
```
